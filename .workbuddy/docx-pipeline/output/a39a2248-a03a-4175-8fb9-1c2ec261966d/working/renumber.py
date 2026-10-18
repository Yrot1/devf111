# -*- coding: utf-8 -*-
"""按首次引用顺序重排 final_draft.md 中的文献编号（GB/T 7714 顺序编码制）。"""
import re
import shutil
from pathlib import Path

base = Path(r"G:\Java_713\JavaWeb\DevFlow-AI\.workbuddy\docx-pipeline\output\a39a2248-a03a-4175-8fb9-1c2ec261966d")
path = base / "stage1" / "final_draft.md"

# 备份
shutil.copy(path, base / "working" / "final_draft_pre_renumber.md")

text = path.read_text(encoding="utf-8")

marker_refs = "## 参考文献"
marker_ack = "## 致谢"
idx_refs = text.index(marker_refs)
idx_ack = text.index(marker_ack)
body = text[:idx_refs]
refs_part = text[idx_refs:idx_ack]
tail = text[idx_ack:]

# 旧编号 -> 新编号（按正文首次出现顺序）
mapping = {5: 1, 6: 2, 19: 3, 21: 4, 22: 5, 7: 6, 9: 7, 8: 8, 11: 9, 10: 10,
           13: 11, 12: 12, 14: 13, 15: 14, 16: 15, 17: 16, 1: 17, 2: 18,
           3: 19, 4: 20, 18: 21, 20: 22}

found = set()

def repl(m):
    n = int(m.group(1))
    found.add(n)
    if n not in mapping:
        raise ValueError(f"未映射的引用编号: [{n}]")
    return f"[{mapping[n]}]"

body_new = re.sub(r"\[(\d+)\]", repl, body)
print(f"正文引用编号出现集合: {sorted(found)}")

# 解析原文献条目
entries = {}
for line in refs_part.splitlines():
    m = re.match(r"^\[(\d+)\]\s+(.+)$", line.strip())
    if m:
        entries[int(m.group(1))] = m.group(2).strip()
assert len(entries) == 22, f"文献条目数量异常: {len(entries)}"

# 新顺序（旧的 5,6,19,21,22,7,9,8,11,10,13,12,14,15,16,17,1,2,3,4,18,20）
new_order = [5, 6, 19, 21, 22, 7, 9, 8, 11, 10, 13, 12, 14, 15, 16, 17, 1, 2, 3, 4, 18, 20]
lines = [marker_refs, ""]
for new_num, old_num in enumerate(new_order, start=1):
    lines.append(f"[{new_num}] {entries[old_num]}")
    lines.append("")
refs_new = "\n".join(lines).rstrip() + "\n\n"

out = body_new + refs_new + tail
path.write_text(out, encoding="utf-8")

# 校验
check = path.read_text(encoding="utf-8")
inbody = check[:check.index(marker_refs)]
used = sorted({int(x) for x in re.findall(r"\[(\d+)\]", inbody)})
print(f"重排后正文引用集合: {used}")
print(f"是否连续覆盖 1-22: {used == list(range(1, 23))}")
# 首次出现顺序校验
order = []
for m in re.finditer(r"\[(\d+)\]", inbody):
    n = int(m.group(1))
    if n not in order:
        order.append(n)
print(f"首次出现顺序: {order}")
print(f"顺序是否正确: {order == list(range(1, 23))}")
print("DONE")
