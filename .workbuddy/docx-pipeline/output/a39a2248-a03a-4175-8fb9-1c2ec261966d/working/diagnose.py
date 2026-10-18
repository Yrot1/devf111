# -*- coding: utf-8 -*-
"""诊断脚本：找出 final_draft.md 中会被 html-review 门禁标记的位置。"""
import re
from pathlib import Path

p = Path(r"G:\Java_713\JavaWeb\DevFlow-AI\.workbuddy\docx-pipeline\output\a39a2248-a03a-4175-8fb9-1c2ec261966d\stage1\final_draft.md")
text = p.read_text(encoding="utf-8")
blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]

def kind(b):
    if b.startswith("#### "): return "h4"
    if b.startswith("### "): return "h3"
    if b.startswith("## "): return "h2"
    if b.startswith("# "): return "h1"
    if b.startswith("|"): return "table"
    return "p"

kinds = [kind(b) for b in blocks]

print("========== TQ-03: 相邻标题（无正文） ==========")
for i in range(1, len(blocks)):
    if kinds[i] in ("h2","h3","h4") and kinds[i-1] in ("h2","h3","h4"):
        # h1->h2 豁免
        if kinds[i-1] == "h1" and kinds[i] == "h2":
            continue
        print(f"[{i}] {kinds[i-1]} -> {kinds[i]}")
        print(f"     前: {blocks[i-1][:60]}")
        print(f"     后: {blocks[i][:60]}")

print()
print("========== TQ-01: 超长段落 (>500 chars) ==========")
cnt = 0
for i, b in enumerate(blocks):
    if kinds[i] == "p":
        n = len(b)
        if n > 500:
            cnt += 1
            print(f"[{i}] len={n} :: {b[:50]}...")
print(f"共 {cnt} 段超长")
