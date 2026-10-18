# DevFlow-AI 项目长期记忆

## 项目概况

- 用户项目：DevFlow-AI —— 面向 GitHub PR/Issue 研发协作的全栈 AI Agent 系统（小林coding 课程项目，用户用于毕业设计）。
- 技术栈：Python/FastAPI/LangChain/LangGraph 后端 + Next.js 15/React 19/TypeScript 前端；
  数据层 PostgreSQL(pgvector) + Milvus；Docker Compose 基础设施（postgres 端口 5434、milvus 19530）。
- 后端核心：backend/app/services/agents（13 个 Agent：Chat/Issue/PR/CI/Planner/Observer/Synthesis/Safety/Workflow 等），
  RAG 链路在 services/rag/，评测在 services/evals/（RAGAS），6 个 Skill 在 services/skills/。

## 重要约定

- **用户只读约束**：用户明确要求"只写论文，不可以修改代码，只能看代码"。涉及此项目的代码一律只读。
- 毕业设计论文已交付：`基于多智能体协作的研发协作系统设计与实现.docx`（项目根目录，2026-10-15 生成，约 4.4 万字）。
  后续论文相关修改（如填封面、改章节）应基于 `.workbuddy/docx-pipeline/output/a39a2248-a03a-4175-8fb9-1c2ec261966d/`
  中的 stage1 草稿或直接编辑 docx。

## 工具环境经验（本机）

- tencent-docx 插件 HTML→DOCX 转换环境：`C:\Users\14268\.venv-html-to-docx`（Python 3.12，已装齐依赖）。
  自建时注意：`setup-html-to-docx.sh` 在 Git Bash 下会因 POSIX 路径与 Windows uv 不兼容而静默失败，
  需手动用 Windows 路径执行 uv venv + uv pip install（详见 2026-10-15 日志）。
- 本机 Bash 工具存在 PATH 缺陷（ls/find 等不可用），命令行操作需先 export PortableGit 的 usr/bin 路径。

## 论文事实要点（写论文/答辩时用）

- 关键数字：ChatAgent max_steps=12、重复调用上限 2、工具错误 8 类；工作流任务超时 90s；
  上下文预算 24000 tokens、压缩阈值 20000/13000/8000/3000；RAG 融合权重 0.62/0.30 + 0.08 双路奖励；
  BM25(k1=1.5, b=0.75)；每父块最多 2 块；Milvus 集合 devflow_rag_qwen1024；
  RAGAS 阈值：precision 0.75 / recall 0.80 / faithfulness 0.90 / relevancy 0.80 / goal 0.80。
- 测试：28 个 pytest 测试模块；评测集 devflow-real-project-rag-baseline。


## 论文 DOCX 流水线（.workbuddy/docx-pipeline）关键经验
- 交付物：项目根目录《基于多智能体协作的研发协作系统设计与实现.docx》（终版含 8 图、约 2.6 万字）。
- 链路：stage1/final_draft.md → working/md2html.py → stage2/formatted-毕业设计论文.html（先过 skills/html-review 门禁，需 100 分）→ html_to_docx 转换（venv：C:/Users/14268/.venv-html-to-docx/Scripts/python.exe）。
- 必坑：Edit 工具批量并发会丢编辑（须用单进程脚本批量替换）；<figure> 需拆成独立 <p>；图片建议 width=567px（最终显示上限约 13.97cm，A4 页边距 3.0/2.5/3.0/2.5）。
