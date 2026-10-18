# -*- coding: utf-8 -*-
"""patch_figs.py — 修 gen_figures.py 中浮点坐标导致的 PIL 报错（统一 int 取整）。"""
from pathlib import Path

BASE = Path(r"G:\Java_713\JavaWeb\DevFlow-AI\.workbuddy\docx-pipeline\output\a39a2248-a03a-4175-8fb9-1c2ec261966d")
p = BASE / "working" / "gen_figures.py"
s = p.read_text(encoding="utf-8")

REPS = [
("    d.text((cx * S, (y0 + i * lh + lh / 2) * S), ln, font=f, fill=fill, anchor='mm')",
 "    d.text((int(cx * S), int((y0 + i * lh + lh / 2) * S)), ln, font=f, fill=fill, anchor='mm')"),
("    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=r * S,\n                        fill=fill, outline=outline, width=ow * S)",
 "    d.rounded_rectangle([int(x * S), int(y * S), int((x + w) * S), int((y + h) * S)],\n                        radius=int(r * S), fill=fill, outline=outline,\n                        width=max(1, int(ow * S)))"),
("                d.line([((x1 + (x2 - x1) * t0) * S, (y1 + (y2 - y1) * t0) * S),\n                        ((x1 + (x2 - x1) * t1) * S, (y1 + (y2 - y1) * t1) * S)],\n                       fill=color, width=max(1, int(w * S)))",
 "                d.line([(int((x1 + (x2 - x1) * t0) * S), int((y1 + (y2 - y1) * t0) * S)),\n                        (int((x1 + (x2 - x1) * t1) * S), int((y1 + (y2 - y1) * t1) * S))],\n                       fill=color, width=max(1, int(w * S)))"),
("            d.line([(x1 * S, y1 * S), (x2 * S, y2 * S)], fill=color, width=max(1, int(w * S)))",
 "            d.line([(int(x1 * S), int(y1 * S)), (int(x2 * S), int(y2 * S))], fill=color, width=max(1, int(w * S)))"),
("    p1 = (x2 * S, y2 * S)\n    p2 = ((x2 - head * math.cos(ang - 0.36)) * S, (y2 - head * math.sin(ang - 0.36)) * S)\n    p3 = ((x2 - head * math.cos(ang + 0.36)) * S, (y2 - head * math.sin(ang + 0.36)) * S)",
 "    p1 = (int(x2 * S), int(y2 * S))\n    p2 = (int((x2 - head * math.cos(ang - 0.36)) * S), int((y2 - head * math.sin(ang - 0.36)) * S))\n    p3 = (int((x2 - head * math.cos(ang + 0.36)) * S), int((y2 - head * math.sin(ang + 0.36)) * S))"),
("    pts = [(cx * S, (cy - h / 2) * S), ((cx + w / 2) * S, cy * S),\n           (cx * S, (cy + h / 2) * S), ((cx - w / 2) * S, cy * S)]",
 "    pts = [(int(cx * S), int((cy - h / 2) * S)), (int((cx + w / 2) * S), int(cy * S)),\n           (int(cx * S), int((cy + h / 2) * S)), (int((cx - w / 2) * S), int(cy * S))]"),
("    d.text((x * S, y * S), text, font=F(size, bold), fill=fill, anchor=anchor)",
 "    d.text((int(x * S), int(y * S)), text, font=F(size, bold), fill=fill, anchor=anchor)"),
("        d.rectangle([cur * S, y * S, (cur + w) * S, (y + hgt) * S], fill=color, outline='white', width=3 * S)",
 "        d.rectangle([int(cur * S), int(y * S), int((cur + w) * S), int((y + hgt) * S)], fill=color, outline='white', width=3 * S)"),
("        d.text(((cur + w / 2) * S), (y - 34) * S, f\"{int(frac*100)}%\", font=F(17, True), fill=MUTED, anchor='mm')",
 "        d.text((int((cur + w / 2) * S), int((y - 34) * S)), f\"{int(frac*100)}%\", font=F(17, True), fill=MUTED, anchor='mm')"),
]

ok = 0
for old, new in REPS:
    c = s.count(old)
    if c == 1:
        s = s.replace(old, new); ok += 1
    else:
        print(f"WARN count={c}: {old[:60]}")
p.write_text(s, encoding="utf-8")
print("patched:", ok, "/", len(REPS))
