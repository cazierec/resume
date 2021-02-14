import os
import json
import subprocess
import pathlib

import arrow
from jinja2 import Template


def load_json(filename: str = 'resume.json') -> dict:
    path = pathlib.Path(os.getcwd(), filename).absolute()

    with open(path, 'r') as json_file:
        return json.load(fp=json_file)

def format_data(data: dict):
    # Fix Profiles
    profiles = {i['network'].lower(): i for i in data["basics"]["profiles"]}
    data["basics"]["profiles"] = profiles

    # Fix Phone Number
    phone = "".join(c for c in data["basics"]["phone"] if c in "0123456798")
    data["basics"]["phoneNumber"] = phone

    # Fix Languages
    languages = list(zip(*(i.values() for i in data["languages"])))
    data["zipLanguages"] = languages

    # Fix Dates
    for category in {'work', 'volunteer', 'education', 'awards', 'publications'}.intersection(data.keys()):
        for index, item in enumerate(data[category]):
            for detail in item.keys():
                if "date" in detail.lower():
                    data[category][index][detail] = arrow.get(item[detail])

    return data

# def fonts(theme: str) -> None:
#     ### DON'T FORGET TO INSTALL RELEVANT FONTS TO /USR/LOCAL/SHARE/FONTS
#     source = pathlib.Path(os.getcwd(), theme, 'fonts').absolute()
#     destination = pathlib.Path(os.getcwd(), "out", theme, 'fonts').absolute()

#     if not destination.exists():
#         shutil.copytree(src = source, dst = destination)


def render(data: dict, ext: str, theme: str = "handmade"):
    if ext in ("html", "pdf"):
        path = pathlib.Path(os.getcwd(), theme, "template.html").absolute()
    
    elif ext == "txt":
        path = pathlib.Path(os.getcwd(), theme, "template.txt").absolute()

    with open(path, 'r') as template_file:
        template = Template(template_file.read())    

    output = template.render({'data': data, 'ext': ext})

    return output


if __name__ == "__main__":
    data = load_json(filename="short-resume.json")
    data = format_data(data=data)

    # fonts(theme='handmade')

    # for out in ("pdf", "html", "txt"):
    for out in ('html', 'txt', 'pdf'):
        page = render(data=data, ext=out)

        path = pathlib.Path(os.getcwd(), 'out', 'handmade', f'resume.{out}')

        if type(page) == str:
            with open(path, 'w') as file:
                file.write(page)
                
        if out == "pdf":
            subprocess.run(['mv', 'out/handmade/resume.pdf', 'out/handmade/pdf.html'])
            subprocess.run(["wkhtmltopdf", "--page-size", "Letter", "page", "out/handmade/pdf.html", "--viewport-size", "1920x1080", "--enable-local-file-access", "--print-media-type", "out/handmade/resume.pdf"])
            subprocess.run(['rm', 'out/handmade/pdf.html'])


            print("wkhtmltopdf --page-size Letter page resume.html --viewport-size 1920x1080 --enable-local-file-access --print-media-type resume.pdf")