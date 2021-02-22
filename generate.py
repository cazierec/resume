import os
import sys
import json
import pathlib
import argparse
import subprocess

import arrow
from jinja2 import Template

SUPPORTED_FORMATS = {"html", "pdf", "txt"}
SUPPORTED_THEMES = {"handmade"}


def format_data(data: dict, phone: str, email: str) -> dict:
    # Fix Profiles
    profiles: dict = {i["network"].lower(): i for i in data["basics"]["profiles"]}
    data["basics"]["profiles"] = profiles

    data["basics"]["phone"] = f"({phone[:3]}) {phone[3:6]} - {phone[6:]}"
    data["basics"]["email"] = email

    # Fix Languages
    languages: list = list(zip(*(i.values() for i in data["languages"])))
    data["zipLanguages"] = languages

    # Fix Dates
    for category in {"work", "volunteer", "education", "awards", "publications"}.intersection(data.keys()):
        for index, item in enumerate(data[category]):
            for detail in item.keys():
                if "date" in detail.lower():
                    data[category][index][detail] = arrow.get(item[detail])

    return data


def render(data: dict, ext: str, theme: str = "handmade") -> str:
    if ext in ("html", "pdf"):
        path = pathlib.Path(os.getcwd(), theme, "template.html").absolute()

    elif ext == "txt":
        path = pathlib.Path(os.getcwd(), theme, "template.txt").absolute()

    with open(path, "r") as template_file:
        template = Template(template_file.read())

    output = template.render({"data": data, "ext": ext})

    return output


def create(
    _input: str, _output: str, themes: str, formats: str, overwrite: bool, use_name: bool, phone: str, email: str
) -> None:
    _input = pathlib.Path(_input).absolute()

    if _input.suffix.lower() != ".json":
        sys.exit("Input file must be a .json file")

    formats = set(formats.split(","))

    if not formats.issubset(SUPPORTED_FORMATS):
        sys.exit(f"Output formats can only be: {', '.join(SUPPORTED_FORMATS)}")

    themes = set(themes.split(","))

    if not themes.issubset(SUPPORTED_THEMES):
        sys.exit(f"Theme can only be one of: {', '.join(SUPPORTED_THEMES)}")

    with open(_input, "r") as json_file:
        data = json.load(fp=json_file)

    data = format_data(data=data, phone=phone, email=email)

    if use_name:
        output_name = data["basics"]["name"]

    else:
        output_name = _input.stem

    for theme in themes:
        theme_dir = pathlib.Path(_output, theme)

        if not theme_dir.exists():
            theme_dir.mkdir(parents=True, exist_ok=True)

        for ext in formats:
            page = render(data=data, ext=ext, theme=theme)

            if (_output := pathlib.Path(theme_dir, f"{output_name}.{ext}")).exists and not overwrite:
                _overwrite_file = input(f"{_output} exists. Overwrite? (y/N) ").lower() == "y"

            else:
                _overwrite_file = True

            if type(page) == str and (_overwrite_file or overwrite):
                with open(_output, "w") as file:
                    file.write(page)

                if ext == "pdf":
                    subprocess.run(["mv", _output, pathlib.Path(_output.parent, "pdf.html")])
                    subprocess.run(
                        [
                            "wkhtmltopdf",
                            "--page-size",
                            "Letter",
                            "page",
                            pathlib.Path(_output.parent, "pdf.html"),
                            "--viewport-size",
                            "1920x1080",
                            "--enable-local-file-access",
                            "--print-media-type",
                            _output,
                        ],
                        capture_output=True,
                    )
                    subprocess.run(["rm", pathlib.Path(_output.parent, "pdf.html")])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate resume in various formats from a single json input")
    parser.add_argument(
        "--input", required=False, metavar="INPUT", type=str, help="an input file [resume.json]", default="resume.json"
    )
    parser.add_argument(
        "--output", required=False, metavar="OUTPUT", type=str, help="an output directory [./out/]", default="./out/"
    )
    parser.add_argument(
        "--themes",
        required=False,
        metavar="THEMES",
        type=str,
        help="a comma-separated list of themes to apply [handmade]",
        default="handmade",
    )
    parser.add_argument(
        "--formats",
        required=False,
        metavar="FORMATS",
        type=str,
        help="a comma-separated list of file formats to generate [pdf,html,txt]",
        default="pdf,html,txt",
    )
    parser.add_argument(
        "--overwrite", required=False, action="store_true", help="overwrite existing files [False]", default=False
    )
    parser.add_argument(
        "--use-name-in-files",
        dest="use_name",
        required=False,
        action="store_true",
        help="save files as the name in the resume [False]",
        default=False,
    )

    parser.add_argument(
        "--phone",
        required=False,
        metavar="PHONE",
        type=str,
        help="the phone number to add to the top of the page",
        default="5555555555",
    )

    parser.add_argument(
        "--email",
        required=False,
        metavar="EMAIL",
        type=str,
        help="the email address to add to the top of the page",
        default="user@email.whom",
    )

    args = parser.parse_args()

    create(
        _input=args.input,
        _output=args.output,
        themes=args.themes,
        formats=args.formats,
        overwrite=args.overwrite,
        use_name=args.use_name,
        phone=args.phone,
        email=args.email,
    )
