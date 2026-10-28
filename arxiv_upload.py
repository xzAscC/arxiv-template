#!/usr/bin/env python3
"""Make arxiv-upload.zip from arxiv/main.tex. arXiv publishes the source, so the upload holds one
main.tex with sections/ and macro.tex inlined and with comments and review notes removed, plus
only the files the build reads. Run from the project root: python3 arxiv_upload.py"""
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'arxiv'
out = root / 'arxiv-upload'


def strip_command(tex, names, keep):
    """Remove \\name{...} for each name; keep=True keeps the argument's text."""
    pattern = re.compile(r'\\(?:%s)\{' % '|'.join(names))
    parts, i = [], 0
    while m := pattern.search(tex, i):
        j, depth = m.end(), 1
        while depth:  # find the matching brace; \{ and \} do not count
            if tex[j] == '\\':
                j += 2
                continue
            depth += {'{': 1, '}': -1}.get(tex[j], 0)
            j += 1
        parts += [tex[i:m.start()], tex[m.end():j - 1] if keep else '']
        i = j
    return ''.join(parts) + tex[i:]


# A fresh build; pdflatex records every file it reads in main.fls
subprocess.run(['latexmk', '-pdf', '-silent', 'main.tex'], cwd=src, check=True)
build = src / '.build' if (src / '.build' / 'main.fls').exists() else src

# One main.tex: latexpand inlines the \input files and drops comments; --empty-comments keeps
# the % at a line's end, so lines joined by % stay joined
tex = subprocess.run(['latexpand', '--fatal', '--empty-comments', 'main.tex'], cwd=src,
                     check=True, capture_output=True, text=True).stdout
tex = strip_command(tex, ['zz', 'xz'], keep=False)
tex = strip_command(tex, ['zzrevise', 'revise', 'edit'], keep=True)
# Files beside the project root, e.g. ../figs/, go into the upload's own folder
tex = tex.replace('{../', '{')

shutil.rmtree(out, ignore_errors=True)
out.mkdir()
(out / 'main.tex').write_text(tex)

# The other files the build read inside the project: the style file, the logo, the figures.
# A file named by a relative path keeps it (../figs/a.pdf becomes figs/a.pdf); a file found
# through the search paths of latexmkrc is opened by bare name, so it goes to the top folder.
for line in (build / 'main.fls').read_text().splitlines():
    if not line.startswith('INPUT '):
        continue
    name = line[len('INPUT '):]
    path = (src / name).resolve()
    if (not path.is_relative_to(root) or path.suffix == '.tex'
            or path.is_relative_to(build) or path.parent == src and path.stem == 'main'):
        continue
    if Path(name).is_absolute():
        dest = out / path.name
    elif path.is_relative_to(src):
        dest = out / path.relative_to(src)
    else:
        dest = out / path.relative_to(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)

# The bibliography: arXiv runs BibTeX on the .bib files since November 2025; main.bbl is the
# same bibliography already built, for a check or an older pipeline
for bib in re.findall(r'\\bibliography\{([^}]*)\}', tex):
    for name in bib.split(','):
        shutil.copy2(src / f'{name.strip()}.bib', out)
shutil.copy2(build / 'main.bbl', out)

with zipfile.ZipFile(root / 'arxiv-upload.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(out.rglob('*')):
        z.write(f, f.relative_to(out))
print('\n'.join(str(f.relative_to(out)) for f in sorted(out.rglob('*')) if f.is_file()))
