import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
from django.core.files.uploadedfile import UploadedFile
from core.settingz.paths import LATEX_TEMPLATE_PATH
from database.models import Character
from django.core.files.base import ContentFile
import re


def handle_uploaded_script(file: UploadedFile, dubbing_id=None, dubbing_title=None, serie_number=None, episode_number=None, title=None):
    if not file:
        return None, []

    ext = os.path.splitext(file.name)[-1].lower()

    if ext == ".pdf":
        return file, []
    
    if ext == ".ass":
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            content = file.read().decode("utf-8", errors="ignore")
            script_lines, characters_used = parse_ass(content)

            # Write script.tex
            script_tex_path = temp_path / "script.tex"
            with open(script_tex_path, "w", encoding="utf-8") as f:
                for line in script_lines:
                    f.write(line + "\n")

            # Write postavy.tex WITHOUT user info
            postavy_tex_path = temp_path / "postavy.tex"
            character_list = []
            with open(postavy_tex_path, "w", encoding="utf-8") as f:
                f.write(r"\begin{pycode}" + "\n")
                f.write("characters = {\n")
                for char_raw, char, skip in characters_used:
                    constant = is_character_constant(dubbing_id, char)
                    if not skip:
                        character_list.append(char)
                    f.write(f'    "{char_raw}": {{\n')
                    f.write(f'        "name": "{char}",\n')
                    f.write(f'        "constant": {str(constant)},\n')
                    f.write(f'        "skip": {skip},\n')
                    f.write("    },\n")
                f.write("}\n")
                f.write(r"\end{pycode}" + "\n")

            front_page_tex_path = temp_path / "front_page.tex"
            with open(front_page_tex_path, "w", encoding="utf-8") as f:
                f.write(r"\def\myanime{" + dubbing_title + r"}" + "\n")
                if serie_number is not None and episode_number is not None:
                    f.write(r"\def\myserie{" + serie_number + r"}" + "\n")
                    f.write(r"\def\myepisode{" + episode_number + r"}" + "\n")
                else:
                    f.write(r"\def\myserie{}" + "\n")
                    f.write(r"\def\myepisode{}" + "\n")
                f.write(r"\def\myepisodename{" + title + r"}" + "\n")
                f.write(r"\def\mytimes{}" + "\n")
                f.write(r"\def\myauthor{Makhuta}" + "\n")


            shutil.copytree(LATEX_TEMPLATE_PATH, temp_path, dirs_exist_ok=True)

            pdf_path = temp_path / "main.pdf"
            success = compile_latex(temp_path / "main.tex", output_path=pdf_path, work_dir=temp_path)

            if success and pdf_path.exists():
                return ContentFile(pdf_path.read_bytes(), name="compiled_script.pdf"), character_list

    return None, []

def remove_ms(t: str) -> str:
    out = t
    try:
        out = t.split(".")[0]
    except:
        pass

    return out

def parse_ass(ass_content):
    lines = ass_content.splitlines()
    dialog_lines = []
    characters_used = set()

    for line in lines:
        if line.startswith("Dialogue:"):
            parts = line.split(",", 9)
            if len(parts) < 10:
                continue

            start_time = parts[1].strip()
            actor_raw = parts[4].strip()
            actor = " MYBREAK ".join(actor_raw.split("/"))
            text = re.sub(r"{.*?}", "", parts[9]).strip()

            characters_used.add((actor_raw, actor, actor_raw!=actor))
            dialog_lines.append(f"\\characterLine{{{actor_raw}}}{{{remove_ms(start_time)}}}{{{text}}}")

    return dialog_lines, characters_used


def is_character_constant(dubbing_id, character_name):
    character = Character.objects.filter(name=character_name).filter(dubbing__id=dubbing_id)
    return character.exists()


def compile_latex(tex_path, output_path, work_dir):
    main_tex_name = tex_path.name

    try:
        subprocess.run(
            [
                "latexmk",
                "-synctex=1",
                "-interaction=nonstopmode",
                "-file-line-error",
                "-pdf",
                "-outdir=" + str(work_dir),
                "--shell-escape",
                str(tex_path),
            ],
            check=True,
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        subprocess.run(
            [
                "pythontex",
                "--interpreter",
                "python:" + sys.executable,
                str(work_dir / main_tex_name)
            ],
            check=True,
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        subprocess.run(
            [
                "latexmk",
                "-synctex=1",
                "-interaction=nonstopmode",
                "-file-line-error",
                "-pdf",
                "-outdir=" + str(work_dir),
                "--shell-escape",
                str(tex_path),
            ],
            check=True,
            cwd=work_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return output_path.exists()

    except subprocess.CalledProcessError as e:
        print("Latex compilation failed.")
        print("Command:", e.cmd)
        print("Exit code:", e.returncode)
        print("Stdout:\n", e.stdout.decode())
        print("Stderr:\n", e.stderr.decode())
        return False
