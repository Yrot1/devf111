# -*- coding: utf-8 -*-
"""gen_figures.py — 生成论文的 8 张架构图/流程图（Pillow，2x 超采样，微软雅黑）。"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(r"G:\Java_713\JavaWeb\DevFlow-AI\.workbuddy\docx-pipeline\output\a39a2248-a03a-4175-8fb9-1c2ec261966d")
OUT = BASE / "figures"
OUT.mkdir(exist_ok=True)

S = 2
INK = '#333333'; MUTED = '#5A6B7B'; PRI = '#1F4E79'; PRI2 = '#2E75B6'
BOR = '#8FAECB'; FILL = '#EAF2FA'; FILLX = '#F7FAFD'; GRAYF = '#F1F3F6'
GRAYB = '#C9D2DB'; WARM = '#C55A11'
FNT = {}

def F(size, bold=False):
    key = (size, bold)
    if key not in FNT:
        p = "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"
        FNT[key] = ImageFont.truetype(p, int(size * S))
    return FNT[key]

def wrap(text, font, maxw):
    lines = []
    for seg in text.split('\n'):
        cur = ''
        for ch in seg:
            if font.getlength(cur + ch) <= maxw:
                cur += ch
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        lines.append(cur)
    return lines

def blk(d, cx, cy, text, size, fill=INK, bold=False, maxw=10**6, lh=None):
    f = F(size, bold)
    lines = wrap(text, f, maxw)
    lh = lh or size * 1.5
    y0 = cy - len(lines) * lh / 2
    for i, ln in enumerate(lines):
        d.text((int(cx * S), int((y0 + i * lh + lh / 2) * S)), ln, font=f, fill=fill, anchor='mm')

def rbox(d, x, y, w, h, text, fill=FILL, outline=PRI2, size=18, bold=False,
         tc=INK, r=12, ow=2, maxw=None):
    d.rounded_rectangle([int(x * S), int(y * S), int((x + w) * S), int((y + h) * S)],
                        radius=int(r * S), fill=fill, outline=outline,
                        width=max(1, int(ow * S)))
    blk(d, x + w / 2, y + h / 2, text, size, fill=tc, bold=bold,
        maxw=(maxw or (w - 30)) * S)

def arrow(d, pts, color=INK, w=2.6, head=12, dashed=False):
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        if dashed:
            L = math.hypot(x2 - x1, y2 - y1)
            n = max(1, int(L // 16))
            for k in range(n):
                t0 = k / n; t1 = min((k + 0.55) / n, 1)
                d.line([(int((x1 + (x2 - x1) * t0) * S), int((y1 + (y2 - y1) * t0) * S)),
                        (int((x1 + (x2 - x1) * t1) * S), int((y1 + (y2 - y1) * t1) * S))],
                       fill=color, width=max(1, int(w * S)))
        else:
            d.line([(int(x1 * S), int(y1 * S)), (int(x2 * S), int(y2 * S))], fill=color, width=max(1, int(w * S)))
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    p1 = (int(x2 * S), int(y2 * S))
    p2 = (int((x2 - head * math.cos(ang - 0.36)) * S), int((y2 - head * math.sin(ang - 0.36)) * S))
    p3 = (int((x2 - head * math.cos(ang + 0.36)) * S), int((y2 - head * math.sin(ang + 0.36)) * S))
    d.polygon([p1, p2, p3], fill=color)

def diamond(d, cx, cy, w, h, text, fill=FILLX, outline=PRI2, size=18, maxw=None):
    pts = [(int(cx * S), int((cy - h / 2) * S)), (int((cx + w / 2) * S), int(cy * S)),
           (int(cx * S), int((cy + h / 2) * S)), (int((cx - w / 2) * S), int(cy * S))]
    d.polygon(pts, fill=fill, outline=outline, width=2 * S)
    blk(d, cx, cy, text, size, maxw=(maxw or w * 0.62) * S)

def note(d, x, y, text, size=16, fill=MUTED, anchor='lm', bold=False):
    d.text((int(x * S), int(y * S)), text, font=F(size, bold), fill=fill, anchor=anchor)

def canvas(w, h):
    img = Image.new('RGB', (w * S, h * S), 'white')
    return img, ImageDraw.Draw(img)

def save(img, w, h, name):
    img.resize((w, h), Image.LANCZOS).save(OUT / name, dpi=(96, 96))
    print('saved', name)

# ============================================================ 图4-1 总体架构
def fig_4_1():
    W, H = 1500, 1020
    img, d = canvas(W, H)
    layers = [
        ("用户层", PRI, [("智能对话", FILL), ("工作流回放", FILL), ("知识库管理", FILL), ("评测与报告", FILL)], ""),
        ("应用服务层", PRI, [("REST 接口", FILL), ("SSE 流式推送", FILL), ("上下文组装", FILL), ("鉴权与校验", FILL)], ""),
        ("智能协作层", PRI, [("对话智能体", FILL), ("规划智能体", FILL), ("任务调度器", FILL), ("观察智能体", FILL), ("综合智能体", FILL)],
         "专项智能体：缺陷分析 · 合并请求审查 · 构建排障 · 安全风险分类"),
        ("知识与工具层", PRI, [("代码工作区工具", FILL), ("平台接口工具", FILL), ("混合检索 RAG", FILL), ("记忆工具", FILL), ("MCP 与技能", FILL)], ""),
        ("数据基础层", PRI, [("PostgreSQL（结构化数据）", FILL), ("Milvus（向量索引）", FILL), ("Git 工作区（代码检出）", FILL)], ""),
    ]
    y = 40
    band_h = 170
    for idx, (name, color, chips, sub) in enumerate(layers):
        # 左侧层名
        rbox(d, 40, y, 180, band_h, name, fill=color, outline=color, size=21, bold=True,
             tc='white', r=10, ow=1, maxw=166)
        # 内容区
        cx0, cx1 = 252, 1460
        n = len(chips)
        gap = 16
        cw = (cx1 - cx0 - gap * (n - 1)) / n
        ch = 64
        cy = y + (band_h - ch) / 2 - (14 if sub else 0)
        for k, (t, fl) in enumerate(chips):
            x = cx0 + k * (cw + gap)
            rbox(d, x, cy, cw, ch, t, fill=fl, outline=BOR, size=17, r=10, ow=1.5)
        if sub:
            note(d, (cx0 + cx1) / 2, y + band_h - 26, sub, size=15, anchor='mm')
        y += band_h + 22
    # 层间箭头（向下）
    for k in range(4):
        ya = 40 + (band_h + 22) * k + band_h + 4
        arrow(d, [(820, ya), (820, ya + 15)], color=BOR, w=2, head=7)
    save(img, W, H, "fig4-1.png")

# ============================================================ 图4-2 部署架构
def fig_4_2():
    W, H = 1500, 840
    img, d = canvas(W, H)
    # 浏览器
    rbox(d, 60, 360, 190, 100, "浏览器\n（研发人员）", fill=GRAYF, outline=GRAYB, size=18)
    # 应用进程区
    d.rounded_rectangle([330 * S, 150 * S, 830 * S, 700 * S], radius=14 * S,
                        fill='#FBFCFE', outline=BOR, width=2 * S)
    note(d, 580, 178, "本地应用进程", size=18, fill=PRI, anchor='mm', bold=True)
    rbox(d, 400, 230, 360, 92, "Next.js 前端（端口 3000）", fill=FILL, outline=PRI2, size=17)
    rbox(d, 400, 480, 360, 92, "FastAPI 后端（端口 8000）\nUvicorn", fill=FILL, outline=PRI2, size=17)
    # 容器区
    d.rounded_rectangle([920 * S, 150 * S, 1420 * S, 700 * S], radius=14 * S,
                        fill='#FBFCFE', outline=BOR, width=2 * S)
    note(d, 1170, 178, "Docker Compose 基础设施", size=18, fill=PRI, anchor='mm', bold=True)
    cards = [("PostgreSQL 16\n:5434", ), ("Milvus 2.5\n:19530", ), ("etcd / MinIO\nMilvus 依赖", ),
             ("pgvector 扩展", ), ("Redis :6379\n（可选）", ), ("持久化数据卷", )]
    for k, (t,) in enumerate(cards):
        col = k % 2; row = k // 2
        x = 958 + col * 238
        yy = 215 + row * 160
        rbox(d, x, yy, 222, 120, t, fill=FILL, outline=BOR, size=16, r=10, ow=1.5)
    # LLM
    d.rounded_rectangle([1090 * S, 40 * S, 1440 * S, 128 * S], radius=12 * S,
                        fill='#FDF6EF', outline=WARM, width=2 * S)
    blk(d, 1265, 84, "大语言模型服务\n（OpenAI 兼容接口）", 17, maxw=320 * S)
    # 箭头
    arrow(d, [(250, 410), (300, 410), (300, 276), (398, 276)], color=INK, w=2.6)
    note(d, 262, 434, "HTTP", size=15)
    arrow(d, [(830, 526), (920, 526)], color=INK, w=2.6)
    note(d, 875, 505, "SQL / 向量 / 缓存", size=15, anchor='mm')
    arrow(d, [(760, 480), (760, 420), (880, 420), (880, 84), (1088, 84)], color=WARM, w=2.4, dashed=True)
    note(d, 892, 62, "模型调用（HTTPS）", size=15, fill=WARM)
    note(d, 750, 770, "配置通过根目录环境变量文件统一管理；演示环境可降级为本地嵌入与启发式重排。", size=16, anchor='mm')
    save(img, W, H, "fig4-2.png")

# ============================================================ 图5-1 Agent 循环
def fig_5_1():
    W, H = 1460, 920
    img, d = canvas(W, H)
    cx = 520
    bw = 520
    x = cx - bw / 2
    rbox(d, x, 56, bw, 80, "用户消息与运行上下文", fill=GRAYF, outline=GRAYB, size=18)
    rbox(d, x, 172, bw, 84, "上下文组装（分层预算：系统提示 · 记忆摘要 · 检索证据 · 近期对话）", fill=FILL, size=17)
    rbox(d, x, 292, bw, 84, "大语言模型决策（温度 0，输出文本或工具调用请求）", fill=FILL, size=17)
    diamond(d, cx, 470, 330, 120, "是否产生工具调用？", size=18)
    rbox(d, x, 564, bw, 84, "工具执行（参数校验 · 错误分类与重试 · 结果截断）", fill=FILL, size=17)
    rbox(d, x, 684, bw, 84, "观察结果追加到上下文", fill=FILL, size=17)
    rbox(d, 950, 420, 450, 120, "生成并输出最终回答与引用\n（SSE 流式推送）", fill='#F3F8F3', outline='#7FA87F', size=17)
    arrow(d, [(cx, 136), (cx, 172)], w=2.6)
    arrow(d, [(cx, 256), (cx, 292)], w=2.6)
    arrow(d, [(cx, 376), (cx, 410)], w=2.6)
    arrow(d, [(cx + 165, 470), (948, 470)], w=2.6)
    note(d, 880, 448, "否", size=17)
    arrow(d, [(cx, 530), (cx, 564)], w=2.6)
    note(d, cx + 34, 546, "是", size=17)
    arrow(d, [(cx, 648), (cx, 684)], w=2.6)
    arrow(d, [(x - 0, 726), (130, 726), (130, 334), (x - 2, 334)], color=PRI2, w=2.6)
    note(d, 148, 640, "继续循环", size=16, fill=PRI2)
    # 侧注
    note(d, 950, 590, "循环保护", size=18, fill=PRI, bold=True)
    for i, t in enumerate(["· 单次运行最多 12 步，达到上限强制收束",
                            "· 同一调用重复超过 2 次即终止",
                            "· 模型调用超时 60 秒，启用提示词缓存"]):
        note(d, 950, 632 + i * 34, t, size=16)
    save(img, W, H, "fig5-1.png")

# ============================================================ 图5-2 多智能体流程
def fig_5_2():
    W, H = 1500, 936
    img, d = canvas(W, H)
    cx = 730
    bw = 960
    x = cx - bw / 2
    rbox(d, x, 46, bw, 74, "用户目标（例如：检查缺陷、合并请求与失败构建，判断版本能否发布）", fill=GRAYF, outline=GRAYB, size=18)
    rbox(d, x, 156, bw, 92, "规划智能体（PlannerAgent）\n拆解任务 · 声明依赖 · 定义验收标准 → 输出工作流规格", fill=FILL, size=17)
    rbox(d, x, 284, bw, 76, "调度器（WorkflowOrchestrator）：依赖就绪的任务并行执行", fill=FILL, size=17)
    chipw, chiph, gap = 280, 62, 40
    x0 = cx - (3 * chipw + 2 * gap) / 2
    for k, t in enumerate(["分析任务 A", "分析任务 B", "分析任务 C"]):
        rbox(d, x0 + k * (chipw + gap), 388, chipw, chiph, t, fill=FILLX, outline=BOR, size=16, r=9, ow=1.5)
    rbox(d, x, 486, bw, 76, "观察智能体（ObserverAgent）：门禁 · 冲突 · 证据检查", fill=FILL, size=17)
    diamond(d, cx, 640, 330, 118, "需要重规划？", size=18)
    rbox(d, x, 716, bw, 90, "综合智能体（SynthesisAgent）：输出统一决策备忘录\n（结论 · 依据 · 风险 · 待确认事项）", fill=FILL, size=17)
    arrow(d, [(cx, 120), (cx, 156)], w=2.6)
    arrow(d, [(cx, 248), (cx, 284)], w=2.6)
    arrow(d, [(cx, 360), (cx, 375), (cx, 388 - 0)], w=2.6)
    arrow(d, [(cx, 450), (cx, 486)], w=2.6)
    arrow(d, [(cx, 562), (cx, 581)], w=2.6)
    arrow(d, [(cx, 699), (cx, 716)], w=2.6)
    note(d, cx + 30, 706, "否", size=16)
    # 右回路
    arrow(d, [(cx + 165, 640), (1330, 640), (1330, 202), (cx + bw / 2 + 2, 202)], color=PRI2, w=2.6)
    note(d, 1322, 228, "有限次重规划", size=15, fill=PRI2, anchor='rm')
    note(d, 60, 830, "任务失败 → 其全部下游任务标记为“跳过”（skipped）；单任务超时上限 90 秒。", size=16)
    note(d, 60, 862, "工作流运行与任务运行均持久化运行轨迹，支撑页面回放与问题排查。", size=16)
    note(d, 60, 894, "重规划设有次数上限；若新旧任务图无变化则提前停止，达到上限后进入综合环节。", size=16)
    save(img, W, H, "fig5-2.png")

# ============================================================ 图5-3 混合检索
def fig_5_3():
    W, H = 1500, 830
    img, d = canvas(W, H)
    cx = 750
    rbox(d, cx - 380, 40, 760, 66, "用户查询", fill=GRAYF, outline=GRAYB, size=18)
    rbox(d, cx - 380, 138, 760, 66, "查询预处理：改写 · 元数据过滤条件构建", fill=FILL, size=17)
    # 分叉
    arrow(d, [(cx, 204), (cx, 232)], w=2.4)
    d.line([(420 * S, 232 * S), (1080 * S, 232 * S)], fill=INK, width=int(2.4 * S))
    arrow(d, [(420, 232), (420, 268)], w=2.4)
    arrow(d, [(1080, 232), (1080, 268)], w=2.4)
    rbox(d, 230, 268, 380, 104, "向量召回\nMilvus 近邻检索（按仓库过滤）", fill=FILL, size=17)
    rbox(d, 890, 268, 380, 104, "关键词召回\nBM25（k1 = 1.5，b = 0.75；单字 + Bigram）", fill=FILL, size=16)
    # 汇合
    d.line([(420 * S, 404 * S), (420 * S, 436 * S)], fill=INK, width=int(2 * S))
    d.line([(1080 * S, 404 * S), (1080 * S, 436 * S)], fill=INK, width=int(2 * S))
    d.line([(420 * S, 436 * S), (1080 * S, 436 * S)], fill=INK, width=int(2.4 * S))
    rbox(d, 230, 468, 1040, 84, "加权融合：向量 0.62 + 关键词 0.30 + 双路命中奖励 0.08\n去冗余：同一父文档 ≤ 2 块 · Jaccard 近重复过滤（阈值 0.9）", fill=FILL, size=16)
    arrow(d, [(750, 436), (750, 468)], w=2.4)
    rbox(d, cx - 380, 586, 760, 64, "重排：交叉编码器打分（候选默认最多 24 条）", fill=FILL, size=17)
    arrow(d, [(750, 552), (750, 586)], w=2.4)
    rbox(d, cx - 380, 684, 760, 64, "Top-K 证据（默认 3 条）→ 编号引用注入提示词", fill=FILL, size=17)
    arrow(d, [(750, 650), (750, 684)], w=2.4)
    arrow(d, [(cx + 380, 716), (1230, 716)], w=2.4)
    rbox(d, 1232, 676, 228, 80, "证据不足：答案门禁\n直接拒答并提示", fill='#FDF6EF', outline=WARM, size=15)
    note(d, 60, 790, "融合权重、去重与阈值均可按知识库配置调整；两路召回均支持标签、状态、路径与时间范围等过滤。", size=15)
    save(img, W, H, "fig5-3.png")

# ============================================================ 图5-4 上下文预算
def fig_5_4():
    W, H = 1500, 620
    img, d = canvas(W, H)
    note(d, 750, 84, "输入预算 24,000 tokens（另预留 3,000 tokens 供模型响应）", size=19, fill=PRI, anchor='mm', bold=True)
    segs = [("系统提示", 0.12, "2,880", '#C9DCF0', INK),
            ("记忆摘要", 0.22, "5,280", '#A8C8E8', INK),
            ("检索证据", 0.34, "8,160", '#2E75B6', 'white'),
            ("近期对话", 0.22, "5,280", '#7FA8D0', 'white'),
            ("工具结果", 0.10, "2,400", '#DDE9F5', INK)]
    x0, x1 = 90, 1410
    total = x1 - x0
    y, hgt = 240, 108
    cur = x0
    for name, frac, toks, color, tc in segs:
        w = total * frac
        d.rectangle([int(cur * S), int(y * S), int((cur + w) * S), int((y + hgt) * S)], fill=color, outline='white', width=3 * S)
        d.text((int((cur + w / 2) * S), int((y - 34) * S)), f"{int(frac*100)}%", font=F(17, True), fill=MUTED, anchor='mm')
        blk(d, cur + w / 2, y + hgt / 2 - 16, name, 17, fill=tc, bold=True, maxw=(w - 26) * S)
        blk(d, cur + w / 2, y + hgt / 2 + 24, f"{toks} tokens", 14, fill=tc, maxw=(w - 26) * S)
        cur += w
    notes = ["· 按类别独立裁剪：证据按检索排名截断 · 工具结果按长度压缩 · 近期对话保留最近若干条",
             "· 任一类信息膨胀不会挤占其他类别的基本额度",
             "· 任务约束与证据等关键信息采用固定位置组织，缓解长上下文中部信息利用不足的问题"]
    for i, t in enumerate(notes):
        note(d, 90, 440 + i * 40, t, size=16)
    save(img, W, H, "fig5-4.png")

# ============================================================ 图5-5 安全确认
def fig_5_5():
    W, H = 1460, 860
    img, d = canvas(W, H)
    cx = 620
    bw = 760
    x = cx - bw / 2
    rbox(d, x, 44, bw, 72, "模型产生写操作意图（发表评论 · 创建缺陷 · 添加标签）", fill=GRAYF, outline=GRAYB, size=17)
    rbox(d, x, 146, bw, 66, "安全风险分类工具评估风险级别", fill=FILL, size=17)
    rbox(d, x, 242, bw, 92, "安全智能体生成操作草稿（ActionDraft）\n类型 · 目标 · 正文 · 风险级别 · 状态", fill=FILL, size=17)
    rbox(d, x, 364, bw, 66, "前端草稿卡片展示：待确认（pending_confirmation）", fill=FILL, size=17)
    diamond(d, cx, 530, 330, 118, "人工确认？", size=18)
    rbox(d, x, 616, bw, 92, "批准：后端执行写操作\n（角色-动作权限校验 → 记录审计日志 AuditLog）", fill='#F3F8F3', outline='#7FA87F', size=17)
    rbox(d, 1100, 486, 320, 88, "拒绝：退回智能体\n向用户说明并调整方案", fill='#FDF6EF', outline=WARM, size=16)
    arrow(d, [(cx, 116), (cx, 146)], w=2.6)
    arrow(d, [(cx, 212), (cx, 242)], w=2.6)
    arrow(d, [(cx, 334), (cx, 364)], w=2.6)
    arrow(d, [(cx, 430), (cx, 471)], w=2.6)
    arrow(d, [(cx, 589), (cx, 616)], w=2.6)
    note(d, cx + 34, 606, "批准", size=16)
    arrow(d, [(cx + 165, 530), (1100, 530)], color=WARM, w=2.4)
    note(d, 950, 508, "拒绝", size=16, fill=WARM)
    note(d, 60, 770, "所有写操作默认关闭、显式启用；审计日志记录操作者、目标对象、参数摘要、执行状态与结果。", size=16)
    note(d, 60, 806, "演示模式下不执行真实写操作，仅生成草稿供核对。", size=16)
    save(img, W, H, "fig5-5.png")

# ============================================================ 图5-6 时序图
def fig_5_6():
    W, H = 1520, 1030
    img, d = canvas(W, H)
    lanes = [(190, "浏览器前端"), (570, "API 服务"), (950, "工作流调度器"), (1330, "智能体与工具")]
    for lx, name in lanes:
        rbox(d, lx - 140, 40, 280, 64, name, fill=PRI, outline=PRI, tc='white', size=18, bold=True, r=10, ow=1)
        d.line([(lx * S, 104 * S), (lx * S, 952 * S)], fill='#9BB0C4', width=int(2 * S))
    # 虚线段感：加白色小段让虚线更柔和
    for lx, _ in lanes:
        yy = 104
        while yy < 952:
            d.line([(lx * S, yy * S), (lx * S, min(yy + 10, 952) * S)], fill='white', width=int(2 * S))
            yy += 26
    msgs = [
        (170, 0, 1, "提交分析请求", INK),
        (248, 1, 2, "创建 WorkflowRun，启动执行", INK),
        (326, 2, 1, "事件流：run.started · 任务计划", PRI2),
        (404, 1, 0, "SSE 推送：计划与执行进度", PRI2),
        (482, 2, 3, "按依赖调度 TaskRun", INK),
        (560, 3, 2, "增量输出 token / 工具调用记录", PRI2),
        (638, 2, 1, "事件流：task.updated · token 分片", PRI2),
        (716, 1, 0, "SSE 推送：边生成边展示", PRI2),
        (794, 2, 1, "事件流：run.completed · 最终报告", PRI2),
        (872, 1, 0, "SSE 推送：完成与统计", PRI2),
    ]
    for yy, a, b, text, color in msgs:
        xa, xb = lanes[a][0], lanes[b][0]
        arrow(d, [(xa, yy), (xb, yy)], color=color, w=2.4)
        mx = (xa + xb) / 2
        note(d, mx, yy - 20, text, size=15, fill=color, anchor='mm')
    note(d, 60, 990, "运行轨迹持久化：AgentRun（对话运行）· AgentWorkflowRun（工作流运行）· AgentTaskRun（任务运行）。", size=16)
    # 图例（右下角）
    d.line([(1080 * S, 990 * S), (1125 * S, 990 * S)], fill=INK, width=int(2.4 * S))
    note(d, 1135, 990, "请求与调度", size=14, anchor='lm')
    d.line([(1290 * S, 990 * S), (1335 * S, 990 * S)], fill=PRI2, width=int(2.4 * S))
    note(d, 1345, 990, "SSE 事件", size=14, anchor='lm')
    save(img, W, H, "fig5-6.png")

fig_4_1(); fig_4_2(); fig_5_1(); fig_5_2(); fig_5_3(); fig_5_4(); fig_5_5(); fig_5_6()
print("ALL DONE")
