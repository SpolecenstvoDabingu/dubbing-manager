import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
from django.core.files.uploadedfile import UploadedFile
import requests
from core.settingz.paths import LATEX_TEMPLATE_PATH
from core.settingz.config import SCRIPT_COMPILER_URL
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
            pattern = r"\\([a-zA-Z]|[bius][01]|f(s\d+|n[a-zA-Z0-9]+)|((?:[234]?c)|alpha)&H[a-fA-F0-9]+|(bord|shad|xshad)\d+|pos\d+,\d+|move\d+,\d+,\d+,\d+|org\d+,\d+|fad\(\d+,\d+\)|t\([^)]*\))"
            text = re.sub(pattern, " ", parts[9]).strip()

            characters_used.add((actor_raw, actor, actor_raw!=actor))
            dialog_lines.append(f"\\characterLine{{{actor_raw}}}{{{remove_ms(start_time)}}}{{{text}}}")

    return dialog_lines, characters_used


def is_character_constant(dubbing_id, character_name):
    character = Character.objects.filter(name=character_name).filter(dubbing__id=dubbing_id)
    return character.exists()


def compile_latex(tex_path, output_path, work_dir):
    """
    Send a LaTeX project archive (tar/zip) to SCRIPT_COMPILER_URL /compile endpoint,
    save the returned PDF to output_path.
    """
    archive_path = work_dir / "upload.tar"

    # --- pack all work_dir into .tar ---
    import tarfile
    with tarfile.open(archive_path, "w") as tar:
        for f in work_dir.iterdir():
            tar.add(f, arcname=f.name)

    try:
        with open(archive_path, "rb") as f:
            files = {"file": ("upload.tar", f, "application/x-tar")}
            r = requests.post(f"{SCRIPT_COMPILER_URL}/compile", files=files, stream=True)

        if r.status_code == 200:
            with open(output_path, "wb") as out:
                shutil.copyfileobj(r.raw, out)
            return True
        else:
            print("Compile service failed:", r.status_code, r.text)
            return False

    except Exception as e:
        print("Failed to contact compile service:", e)
        return False
