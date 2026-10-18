# -*- coding: utf-8 -*-
"""patch_md2html2.py — 把 figure 元素改为两个独立 <p>（图片段 + 题注段），确保分段落排版。"""
from pathlib import Path

BASE = Path(r"G:\Java_713\JavaWeb\DevFlow-AI\.workbuddy\docx-pipeline\output\a39a2248-a03a-4175-8fb9-1c2ec261966d")
p = BASE / "working" / "md2html.py"
s = p.read_text(encoding="utf-8")

REPS = [
("""        if state == "chapter":
            cur["parts"].append(
                f'<figure class="paper-figure"><img src="data:image/png;base64,{b64}" '
                f'width="567" alt="{esc(caption)}" /><figcaption>{esc(caption)}</figcaption></figure>'
            )
        continue""",
 """        if state == "chapter":
            cur["parts"].append(
                f'<p class="fig-img" style="text-align: center; text-indent: 0;">'
                f'<img src="data:image/png;base64,{b64}" width="567" alt="{esc(caption)}" /></p>'
                f'<p class="fig-cap" style="text-align: center; text-indent: 0;">{esc(caption)}</p>'
            )
        continue"""),
("""  /* Figures */
  .paper-figure { text-align: center; margin-top: var(--sp-block); margin-bottom: var(--sp-block); }
  .paper-figure img { max-width: 100%; }
  .paper-figure figcaption {
    font-family: var(--ff-body); font-size: var(--fs-small); color: var(--color-text);
    text-align: center; text-indent: 0; margin-top: var(--sp-mini); margin-bottom: var(--sp-para);
  }""",
 """  /* Figures */
  .fig-img { text-align: center; text-indent: 0; margin-top: var(--sp-block); margin-bottom: var(--sp-mini); }
  .fig-img img { max-width: 100%; }
  .fig-cap {
    font-family: var(--ff-body); font-size: var(--fs-small); color: var(--color-text);
    text-align: center; text-indent: 0; margin-top: 0; margin-bottom: var(--sp-block);
  }"""),
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

# 顺带看看转换器的图片宽度上限逻辑
conv = Path(r"C:\Users\14268\.workbuddy\plugins\cache\workbuddy-builtin\tencent-docx\5.5.6-wb.38337834.g5f969292.h4918b5ced607\skills\html-to-docx\scripts\html_to_docx\converter.py")
cs = conv.read_text(encoding="utf-8")
import re
for m in re.finditer(r".*max_width.*", cs):
    print("converter:", m.group(0).strip()[:110])
