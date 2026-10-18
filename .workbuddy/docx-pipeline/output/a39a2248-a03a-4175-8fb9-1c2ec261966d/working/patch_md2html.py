# -*- coding: utf-8 -*-
"""patch_md2html.py — 给 md2html.py 增加图片（figure）支持。"""
from pathlib import Path

BASE = Path(r"G:\Java_713\JavaWeb\DevFlow-AI\.workbuddy\docx-pipeline\output\a39a2248-a03a-4175-8fb9-1c2ec261966d")
p = BASE / "working" / "md2html.py"
s = p.read_text(encoding="utf-8")

REPS = [
# a. import base64
("import html as htmlmod\nimport re\nfrom pathlib import Path",
 "import base64\nimport html as htmlmod\nimport re\nfrom pathlib import Path"),

# b. 解析 ![caption](path) 块
('''    elif b.startswith("|"):
        items.append(("table", b))''',
 '''    elif re.match(r"^!\\[(.+?)\\]\\((.+?)\\)$", b):
        m2 = re.match(r"^!\\[(.+?)\\]\\((.+?)\\)$", b)
        items.append(("figure", (m2.group(1), m2.group(2))))
    elif b.startswith("|"):
        items.append(("table", b))'''),

# c. 装配阶段处理 figure
('''    if kind == "caption":
        pending_caption = content.strip("*").strip()
        continue''',
 '''    if kind == "figure":
        caption, rel = content
        img_path = BASE / rel
        b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
        if state == "chapter":
            cur["parts"].append(
                f'<figure class="paper-figure"><img src="data:image/png;base64,{b64}" '
                f'width="567" alt="{esc(caption)}" /><figcaption>{esc(caption)}</figcaption></figure>'
            )
        continue
    if kind == "caption":
        pending_caption = content.strip("*").strip()
        continue'''),

# d. CSS
('''  /* References & Acknowledgements */''',
 '''  /* Figures */
  .paper-figure { text-align: center; margin-top: var(--sp-block); margin-bottom: var(--sp-block); }
  .paper-figure img { max-width: 100%; }
  .paper-figure figcaption {
    font-family: var(--ff-body); font-size: var(--fs-small); color: var(--color-text);
    text-align: center; text-indent: 0; margin-top: var(--sp-mini); margin-bottom: var(--sp-para);
  }

  /* References & Acknowledgements */'''),
]

ok = 0
for old, new in REPS:
    c = s.count(old)
    if c == 1:
        s = s.replace(old, new); ok += 1
    else:
        print(f"WARN count={c}: {old[:60]!r}")
p.write_text(s, encoding="utf-8")
print("patched:", ok, "/", len(REPS))
