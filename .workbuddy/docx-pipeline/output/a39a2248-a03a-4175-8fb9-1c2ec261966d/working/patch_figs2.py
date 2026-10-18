# -*- coding: utf-8 -*-
"""patch_figs2.py — 修正第一版图上的细节问题。"""
from pathlib import Path

BASE = Path(r"G:\Java_713\JavaWeb\DevFlow-AI\.workbuddy\docx-pipeline\output\a39a2248-a03a-4175-8fb9-1c2ec261966d")
p = BASE / "working" / "gen_figures.py"
s = p.read_text(encoding="utf-8")

REPS = [
# 图4-1：层名块加宽，避免换行
('        rbox(d, 40, y, 150, band_h, name, fill=color, outline=color, size=22, bold=True,\n             tc=\'white\', r=10, ow=1, maxw=120*0.8)',
 '        rbox(d, 40, y, 180, band_h, name, fill=color, outline=color, size=21, bold=True,\n             tc=\'white\', r=10, ow=1, maxw=166)'),
('        cx0, cx1 = 215, 1460', '        cx0, cx1 = 252, 1460'),
# 图4-2：HTTP 标签下移，避开转角
('    note(d, 262, 380, "HTTP", size=15)', '    note(d, 262, 434, "HTTP", size=15)'),
# 图5-2：右侧回路标签改为单行、右侧对齐；H 加高；补第三条脚注
('    W, H = 1500, 900\n    img, d = canvas(W, H)\n    cx = 730', '    W, H = 1500, 936\n    img, d = canvas(W, H)\n    cx = 730'),
('    note(d, 1348, 420, "有限次重规划\\n（计划未变化或达到上限即停止）", size=15, fill=PRI2, anchor=\'lm\')',
 '    note(d, 1322, 228, "有限次重规划", size=15, fill=PRI2, anchor=\'rm\')'),
('    note(d, 60, 862, "工作流运行与任务运行均持久化运行轨迹，支撑页面回放与问题排查。", size=16)',
 '    note(d, 60, 862, "工作流运行与任务运行均持久化运行轨迹，支撑页面回放与问题排查。", size=16)\n    note(d, 60, 894, "重规划设有次数上限；若新旧任务图无变化则提前停止，达到上限后进入综合环节。", size=16)'),
# 图5-3：下标字符换普通写法
('"关键词召回\\nBM25（k₁ = 1.5，b = 0.75；单字 + Bigram）"', '"关键词召回\\nBM25（k1 = 1.5，b = 0.75；单字 + Bigram）"'),
# 图5-6：图例移到右下角
('    # 图例\n    d.line([(1090 * S, 120 * S), (1130 * S, 120 * S)], fill=INK, width=int(2.4 * S))\n    note(d, 1140, 120, "请求与调度", size=14, anchor=\'lm\')\n    d.line([(1270 * S, 120 * S), (1310 * S, 120 * S)], fill=PRI2, width=int(2.4 * S))\n    note(d, 1320, 120, "SSE 事件", size=14, anchor=\'lm\')',
 '    # 图例（右下角）\n    d.line([(1080 * S, 990 * S), (1125 * S, 990 * S)], fill=INK, width=int(2.4 * S))\n    note(d, 1135, 990, "请求与调度", size=14, anchor=\'lm\')\n    d.line([(1290 * S, 990 * S), (1335 * S, 990 * S)], fill=PRI2, width=int(2.4 * S))\n    note(d, 1345, 990, "SSE 事件", size=14, anchor=\'lm\')'),
]

ok = 0
for old, new in REPS:
    c = s.count(old)
    if c == 1:
        s = s.replace(old, new); ok += 1
    else:
        print(f"WARN count={c}: {old[:70]!r}")
p.write_text(s, encoding="utf-8")
print("patched:", ok, "/", len(REPS))
