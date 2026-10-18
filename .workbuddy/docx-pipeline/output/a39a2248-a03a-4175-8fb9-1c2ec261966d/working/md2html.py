# -*- coding: utf-8 -*-
"""md2html.py — 把 final_draft.md 转换为学术论文排版 HTML（academic-paper 模板 + design tokens）。"""
import base64
import html as htmlmod
import re
from pathlib import Path

BASE = Path(r"G:\Java_713\JavaWeb\DevFlow-AI\.workbuddy\docx-pipeline\output\a39a2248-a03a-4175-8fb9-1c2ec261966d")
md = (BASE / "stage1" / "final_draft.md").read_text(encoding="utf-8")
OUT = BASE / "stage2" / "formatted-毕业设计论文.html"

TITLE = "基于多智能体协作的研发协作系统设计与实现"


def esc(t: str) -> str:
    return htmlmod.escape(t, quote=False)


def inline(t: str) -> str:
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return t.replace("`", "")


def split_long(text: str, limit: int = 470, minimum: int = 160):
    """把超长段落按句末标点切分为多段（TQ-01 门禁要求单段 < 500 字）。"""
    if len(text) <= limit:
        return [text]
    sentences = re.findall(r"[^。！？]*[。！？]|[^。！？]+$", text)
    parts, buf = [], ""
    for s in sentences:
        if not s:
            continue
        if len(buf) + len(s) > limit and len(buf) >= minimum:
            parts.append(buf)
            buf = s
        else:
            buf += s
    if buf:
        parts.append(buf)
    # 二次：英文句号切分
    out = []
    for pt in parts:
        if len(pt) <= limit:
            out.append(pt)
            continue
        ss = re.split(r"(?<=[.!?])\s+", pt)
        buf2 = ""
        for s in ss:
            cand = (buf2 + " " + s) if buf2 else s
            if len(cand) > limit and len(buf2) >= minimum:
                out.append(buf2)
                buf2 = s
            else:
                buf2 = cand
        if buf2:
            out.append(buf2)
    # 兜底硬切
    final = []
    for pt in out:
        while len(pt) > limit:
            final.append(pt[:limit])
            pt = pt[limit:]
        if pt:
            final.append(pt)
    return final


# ---------------------------------------------------------------- 解析 blocks
blocks = [b.strip() for b in re.split(r"\n\s*\n", md) if b.strip()]

items = []
for b in blocks:
    if b.startswith("#### "):
        items.append(("h4", b[5:].strip()))
    elif b.startswith("### "):
        items.append(("h3", b[4:].strip()))
    elif b.startswith("## "):
        items.append(("h2", b[3:].strip()))
    elif b.startswith("# "):
        items.append(("h1", b[2:].strip()))
    elif re.match(r"^!\[(.+?)\]\((.+?)\)$", b):
        m2 = re.match(r"^!\[(.+?)\]\((.+?)\)$", b)
        items.append(("figure", (m2.group(1), m2.group(2))))
    elif b.startswith("|"):
        items.append(("table", b))
    elif re.match(r"^\*\*表[\d\-]+.*\*\*$", b):
        items.append(("caption", b))
    elif re.match(r"^\*\*关键词", b):
        items.append(("keywords_cn", b))
    elif re.match(r"^\*\*Key words", b):
        items.append(("keywords_en", b))
    else:
        items.append(("p", b))

# ---------------------------------------------------------------- 结构装配
abstract_cn, abstract_en = [], []
kw_cn, kw_en = "", ""
chapters, refs, ack = [], [], []
refs_id = ack_id = None
state = "init"
cur = None
pending_caption = None
ch_counter = 0


def add_p(target, text):
    for seg in split_long(text):
        target.append(f"<p>{inline(seg)}</p>")


def parse_table(block, caption):
    rows = block.split("\n")

    def cells(line):
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [c.strip() for c in line.split("|")]

    header = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    cap = f"<caption>{esc(caption)}</caption>" if caption else ""
    thead = "<thead><tr>" + "".join(f"<th>{inline(h)}</th>" for h in header) + "</tr></thead>"
    tbody = (
        "<tbody>"
        + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body)
        + "</tbody>"
    )
    return f'<table class="three-line-table">{cap}{thead}{tbody}</table>'


for kind, content in items:
    if kind == "h1":
        continue
    if kind == "h2":
        if content == "摘要":
            state = "abs_cn"
        elif content == "Abstract":
            state = "abs_en"
        elif content == "参考文献":
            state = "refs"
            ch_counter += 1
            refs_id = f"section-{ch_counter}"
        elif content == "致谢":
            state = "ack"
            ch_counter += 1
            ack_id = f"section-{ch_counter}"
        else:
            state = "chapter"
            ch_counter += 1
            cur = {"id": f"section-{ch_counter}", "title": content, "parts": [], "sections": []}
            chapters.append(cur)
            cur["parts"].append(f'<h2 id="{cur["id"]}">{esc(content)}</h2>')
        continue
    if kind == "h3" and state == "chapter":
        m = re.match(r"^(\d+)\.(\d+)", content)
        sid = f"s{m.group(1)}-{m.group(2)}" if m else f"s{ch_counter}-{len(cur['sections']) + 1}"
        cur["sections"].append({"id": sid, "title": content})
        cur["parts"].append(f'<h3 id="{sid}">{esc(content)}</h3>')
        continue
    if kind == "h4" and state == "chapter":
        cur["parts"].append(f"<h4>{esc(content)}</h4>")
        continue
    if kind == "figure":
        caption, rel = content
        img_path = BASE / rel
        b64 = base64.b64encode(img_path.read_bytes()).decode("ascii")
        if state == "chapter":
            cur["parts"].append(
                f'<p class="fig-img" style="text-align: center; text-indent: 0;">'
                f'<img src="data:image/png;base64,{b64}" width="567" alt="{esc(caption)}" /></p>'
                f'<p class="fig-cap" style="text-align: center; text-indent: 0;">{esc(caption)}</p>'
            )
        continue
    if kind == "caption":
        pending_caption = content.strip("*").strip()
        continue
    if kind == "table":
        html_tb = parse_table(content, pending_caption)
        pending_caption = None
        if state == "chapter":
            cur["parts"].append(html_tb)
        elif state == "refs":
            refs.append(html_tb)
        continue
    if kind in ("p", "keywords_cn", "keywords_en"):
        if state == "abs_cn":
            if kind == "keywords_cn":
                kw_cn = inline(content)
            else:
                abstract_cn.append(content)
        elif state == "abs_en":
            if kind == "keywords_en":
                kw_en = inline(content)
            else:
                abstract_en.append(content)
        elif state == "chapter":
            add_p(cur["parts"], content)
        elif state == "refs":
            refs.append(content)
        elif state == "ack":
            add_p(ack, content)
        continue

# ---------------------------------------------------------------- 以下为覆盖不到的校验（防呆）
assert kw_cn and kw_en, "keywords missing"
assert refs_id and ack_id, "refs/ack id missing"
assert len(chapters) == 7, f"chapters = {len(chapters)}"

# ---------------------------------------------------------------- 装配 HTML
toc_items = []
for ch in chapters:
    sub = ""
    if ch["sections"]:
        sub = "<ol>" + "".join(
            f'<li><a href="#{s["id"]}">{esc(s["title"])}</a></li>' for s in ch["sections"]
        ) + "</ol>"
    toc_items.append(f'<li><a href="#{ch["id"]}">{esc(ch["title"])}</a>{sub}</li>')
toc_items.append(f'<li><a href="#{refs_id}">参考文献</a></li>')
toc_items.append(f'<li><a href="#{ack_id}">致谢</a></li>')
toc_html = "\n".join(toc_items)

abs_cn_html = (
    '<div class="abstract" aria-label="摘要">'
    '<p class="abstract-heading">摘要</p>'
    + "".join(f'<p class="abstract-text">{inline(seg)}</p>' for seg in split_long("".join(abstract_cn)) if seg)
    + f'<p class="keywords">{kw_cn}</p>'
    "</div>"
)
# 摘要按原段落切分（保持分段结构），逐段再限长
abs_cn_html = (
    '<div class="abstract" aria-label="摘要">'
    '<p class="abstract-heading">摘要</p>'
    + "".join(f'<p class="abstract-text">{inline(seg)}</p>' for para in abstract_cn for seg in split_long(para))
    + f'<p class="keywords">{kw_cn}</p>'
    "</div>"
)
abs_en_html = (
    '<div class="abstract abstract-en" aria-label="Abstract">'
    '<p class="abstract-heading">Abstract</p>'
    + "".join(f'<p class="abstract-text">{inline(seg)}</p>' for para in abstract_en for seg in split_long(para))
    + f'<p class="keywords">{kw_en}</p>'
    "</div>"
)

refs_html = (
    f'<div class="references" aria-label="参考文献"><h2 id="{refs_id}">参考文献</h2>'
    + "".join(f'<p class="reference-item">{inline(r)}</p>' for r in refs)
    + "</div>"
)
ack_html = f'<div class="acknowledgements"><h2 id="{ack_id}">致谢</h2>' + "".join(ack) + "</div>"

body_inner = "\n".join(
    [abs_cn_html, abs_en_html, f'<nav class="doc-toc" aria-label="文档目录"><p class="toc-title">目录</p><ol class="toc-list">\n{toc_html}\n</ol></nav>']
    + ["<main class=\"paper-body\">\n" + "\n".join("".join(ch["parts"]) for ch in chapters) + "\n</main>"]
    + [refs_html, ack_html]
)

COVER = """  <section role="cover">
    <div class="cover-body" style="text-align: center;">
      <p class="cover-eyebrow" style="text-align: center;">本科毕业设计（论文）</p>
      <h1 class="cover-title" style="text-align: center;">基于多智能体协作的研发协作系统设计与实现</h1>
    </div>
    <div class="cover-meta" style="text-align: center;">
      <p class="cover-info" style="text-align: center;">学　　院：＿＿＿＿＿＿＿＿</p>
      <p class="cover-info" style="text-align: center;">专　　业：＿＿＿＿＿＿＿＿</p>
      <p class="cover-info" style="text-align: center;">年　　级：＿＿＿＿＿＿＿＿</p>
      <p class="cover-info" style="text-align: center;">学　　号：＿＿＿＿＿＿＿＿</p>
      <p class="cover-info" style="text-align: center;">学生姓名：＿＿＿＿＿＿＿＿</p>
      <p class="cover-info" style="text-align: center;">指导教师：＿＿＿＿＿＿＿＿</p>
      <p class="cover-date" style="text-align: center;">＿＿＿＿年＿＿月</p>
    </div>
  </section>"""

CSS = """
  @page { @bottom-center { content: counter(page); } }
  @page cover { @bottom-center { content: none; } }
  section[role="cover"] { page: cover; }

  :root {
    /* ---- design tokens: academic-paper ---- */
    --typography-fontFamily-heading: "黑体", SimHei, sans-serif;
    --typography-fontFamily-body: "宋体", SimSun, serif;
    --typography-fontFamily-bodyLatin: "Times New Roman", "宋体", SimSun, serif;
    --typography-fontFamily-code: "Courier New", Consolas, monospace;
    --typography-fontSize-title: 18pt;
    --typography-fontSize-h1: 15pt;
    --typography-fontSize-h2: 14pt;
    --typography-fontSize-h3: 12pt;
    --typography-fontSize-body: 12pt;
    --typography-fontSize-abstract: 11pt;
    --typography-fontSize-caption: 10.5pt;
    --typography-fontSize-footnote: 9pt;
    --typography-lineHeight-body: 1.5;
    --typography-lineHeight-heading: 1.5;
    --typography-fontWeight-bold: 700;
    --typography-fontWeight-normal: 400;
    --color-primary: #000000;
    --color-text: #000000;
    --color-muted: #444444;
    --color-border: #000000;
    --color-bg: #ffffff;
    --spacing-paragraph: 0.5em;
    --spacing-block: 1em;
    --spacing-sectionGap: 1.5em;
    --spacing-indent: 2em;
    --spacing-mini: 0.25em;
    --layout-marginTop: 3.0cm;
    --layout-marginBottom: 2.5cm;
    --layout-marginLeft: 3.0cm;
    --layout-marginRight: 2.5cm;

    /* ---- semantic aliases ---- */
    --fs-title: var(--typography-fontSize-title, 18pt);
    --fs-h1: var(--typography-fontSize-h1, 15pt);
    --fs-h2: var(--typography-fontSize-h2, 14pt);
    --fs-h3: var(--typography-fontSize-h3, 12pt);
    --fs-body: var(--typography-fontSize-body, 12pt);
    --fs-abstract: var(--typography-fontSize-abstract, 11pt);
    --fs-small: var(--typography-fontSize-caption, 10.5pt);
    --fs-cover-title: var(--typography-fontSize-title, 18pt);
    --fs-cover-meta: var(--typography-fontSize-h2, 14pt);
    --ff-heading: var(--typography-fontFamily-heading, "黑体", SimHei, sans-serif);
    --ff-body: var(--typography-fontFamily-bodyLatin, "Times New Roman", "宋体", SimSun, serif);
    --lh-body: var(--typography-lineHeight-body, 1.5);
    --lh-heading: var(--typography-lineHeight-heading, 1.5);
    --fw-bold: var(--typography-fontWeight-bold, 700);
    --fw-normal: var(--typography-fontWeight-normal, 400);
    --color-hl: var(--color-primary, #000000);
    --sp-para: var(--spacing-paragraph, 0.5em);
    --sp-block: var(--spacing-block, 1em);
    --sp-section: var(--spacing-sectionGap, 1.5em);
    --sp-indent: var(--spacing-indent, 2em);
    --sp-mini: var(--spacing-mini, 0.25em);
    --page-content-width: var(--layout-contentWidth, 15.5cm);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: var(--ff-body);
    font-size: var(--fs-body);
    line-height: var(--lh-body);
    color: var(--color-text);
    background: var(--color-bg);
    max-width: var(--page-content-width);
    margin-left: auto;
    margin-right: auto;
    padding: var(--sp-block) var(--sp-section);
  }

  h1 { font-family: var(--ff-heading); font-size: var(--fs-title); font-weight: var(--fw-bold); color: var(--color-text); text-align: center; }
  h2 {
    font-family: var(--ff-heading); font-size: var(--fs-h1); font-weight: var(--fw-bold);
    color: var(--color-text); text-align: center; line-height: var(--lh-heading);
    margin-top: var(--sp-section); margin-bottom: var(--sp-block);
  }
  h3 {
    font-family: var(--ff-heading); font-size: var(--fs-h2); font-weight: var(--fw-bold);
    color: var(--color-text); text-align: left; line-height: var(--lh-heading);
    margin-top: var(--sp-block); margin-bottom: var(--sp-para);
  }
  h4 {
    font-family: var(--ff-heading); font-size: var(--fs-h3); font-weight: var(--fw-bold);
    color: var(--color-text); text-align: left; line-height: var(--lh-heading);
    margin-top: var(--sp-block); margin-bottom: var(--sp-para);
  }

  p {
    font-family: var(--ff-body); font-size: var(--fs-body); color: var(--color-text);
    line-height: var(--lh-body); text-align: justify; text-indent: var(--sp-indent);
    margin-bottom: var(--sp-para);
  }

  /* Cover（每个块自行声明关键样式） */
  .cover-body { text-align: center; }
  .cover-eyebrow {
    font-family: var(--ff-heading); font-size: var(--fs-cover-meta); font-weight: var(--fw-normal);
    color: var(--color-text); text-align: center; text-indent: 0;
    margin-top: var(--sp-section); margin-bottom: var(--sp-block);
  }
  .cover-title {
    text-align: center; font-size: var(--fs-cover-title); font-weight: var(--fw-bold);
    font-family: var(--ff-heading); color: var(--color-text);
    margin-top: var(--sp-section); margin-bottom: var(--sp-section);
  }
  .cover-meta { text-align: center; margin-top: var(--sp-section); }
  .cover-info {
    text-align: center; text-indent: 0; font-family: var(--ff-body); font-size: var(--fs-body);
    color: var(--color-text); line-height: var(--lh-body); margin-bottom: var(--sp-mini);
  }
  .cover-date {
    text-align: center; text-indent: 0; font-family: var(--ff-body); font-size: var(--fs-body);
    color: var(--color-text); margin-top: var(--sp-section);
  }

  /* Abstract */
  .abstract { margin-top: var(--sp-section); margin-bottom: var(--sp-section); }
  .abstract-heading {
    font-family: var(--ff-heading); font-size: var(--fs-h1); font-weight: var(--fw-bold);
    color: var(--color-text); text-align: center; text-indent: 0;
    margin-bottom: var(--sp-para);
  }
  .abstract-text {
    font-family: var(--ff-body); font-size: var(--fs-abstract); color: var(--color-text);
    line-height: var(--lh-body); text-align: justify; text-indent: var(--sp-indent);
    margin-bottom: var(--sp-para);
  }
  .keywords {
    font-family: var(--ff-body); font-size: var(--fs-abstract); color: var(--color-text);
    text-align: justify; text-indent: 0; margin-top: var(--sp-para);
  }

  /* TOC */
  .doc-toc { margin-top: var(--sp-section); margin-bottom: var(--sp-section); }
  .toc-title {
    font-family: var(--ff-heading); font-size: var(--fs-h1); font-weight: var(--fw-bold);
    color: var(--color-text); text-align: center; text-indent: 0;
    margin-bottom: var(--sp-block);
  }
  .toc-list, .toc-list ol, .toc-list ul { list-style: none; list-style-type: none; padding-left: var(--sp-block); margin: 0; }
  .toc-list li {
    font-family: var(--ff-body); font-size: var(--fs-body); color: var(--color-text);
    line-height: var(--lh-body); text-indent: 0; margin-bottom: var(--sp-mini);
  }
  .toc-list a { color: var(--color-hl); text-decoration: none; }

  /* Three-line table */
  .three-line-table { border-collapse: collapse; width: 100%; margin-top: var(--sp-block); margin-bottom: var(--sp-block); }
  .three-line-table caption {
    font-family: var(--ff-body); font-size: var(--fs-small); color: var(--color-text);
    text-align: center; text-indent: 0; margin-bottom: var(--sp-mini);
  }
  .three-line-table thead tr:first-child { border-top: 2px solid var(--color-border); }
  .three-line-table thead tr:last-child { border-bottom: 1px solid var(--color-border); }
  .three-line-table tbody tr:last-child { border-bottom: 2px solid var(--color-border); }
  .three-line-table td, .three-line-table th {
    border-left: none; border-right: none; padding: var(--sp-mini) var(--sp-para);
    text-indent: 0; vertical-align: top;
    font-family: var(--ff-body); font-size: var(--fs-small); color: var(--color-text);
    line-height: var(--lh-body); text-align: left;
  }
  .three-line-table th { font-weight: var(--fw-bold); }

  /* Figures */
  .fig-img { text-align: center; text-indent: 0; margin-top: var(--sp-block); margin-bottom: var(--sp-mini); }
  .fig-img img { max-width: 100%; }
  .fig-cap {
    font-family: var(--ff-body); font-size: var(--fs-small); color: var(--color-text);
    text-align: center; text-indent: 0; margin-top: 0; margin-bottom: var(--sp-block);
  }

  /* References & Acknowledgements */
  .references { margin-top: var(--sp-section); }
  .reference-item {
    font-family: var(--ff-body); font-size: var(--fs-small); color: var(--color-text);
    text-align: left; text-indent: 0; margin-left: var(--sp-indent); margin-bottom: var(--sp-mini);
    line-height: var(--lh-body);
  }
  strong { font-weight: var(--fw-bold); }
"""

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="docx-page-size" content="A4">
  <title>{esc(TITLE)}</title>
  <style>{CSS}</style>
</head>
<body>
{COVER}
  <section role="body" data-page-restart="1">
{body_inner}
  </section>
</body>
</html>
"""

OUT.write_text(HTML, encoding="utf-8")
print("written:", OUT)
print("size:", len(HTML))
print("h2 count:", len(re.findall(r"<h2", HTML)))
print("h3 count:", len(re.findall(r"<h3", HTML)))
print("table count:", len(re.findall(r"<table", HTML)))
print("p count:", len(re.findall(r"<p[ >]", HTML)))
