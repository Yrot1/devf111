## 第6章 系统测试与效果评估

本章介绍系统的测试与评估工作，包括测试环境与策略、功能测试、集成与自动化测试以及基于 RAGAS 的回答质量评估。

### 6.1 测试环境与策略

系统的测试环境由容器化基础设施与本地应用进程组成，主要测试环境配置如表6-1所示。

**表6-1 测试环境配置**

| 项目 | 配置 |
|------|------|
| 操作系统 | Windows 11（开发与测试主机） |
| 运行时 | Python 3.13、Node.js 22 |
| 数据库 | PostgreSQL 16（pgvector 扩展），Docker 容器，映射端口 5434 |
| 向量数据库 | Milvus 2.5（含 etcd 与 MinIO 依赖），Docker 容器，端口 19530 |
| 后端服务 | FastAPI + Uvicorn，端口 8000 |
| 前端服务 | Next.js 开发/构建服务器，端口 3000 |
| 模型服务 | 大语言模型与嵌入、重排模型，经 OpenAI 兼容接口调用 |

测试策略分为四个层次：单元与集成测试采用 pytest 框架编写并自动执行，覆盖数据同步、智能体循环、工作流编排、检索链路、上下文压缩等关键模块；接口测试通过 FastAPI 测试客户端与真实后台任务执行验证端到端行为；功能测试以实际部署环境中的页面操作为主，验证用户视角的完整功能；效果评估采用固定评测集与 RAGAS 指标，对回答质量进行量化度量与回归对比。目前系统共有二十八个测试模块，覆盖后端主要功能链路。

### 6.2 功能测试

功能测试围绕核心用户场景设计测试用例，表6-2列出了具有代表性的测试用例及其结果。

**表6-2 功能测试用例与结果**

| 编号 | 测试场景 | 测试方法 | 预期结果 | 测试结果 |
|------|---------|---------|---------|---------|
| T1 | 仓库接入与同步 | 接入测试仓库并执行同步，分别测试默认取样、设置数量上限与全量三种模式 | 数据正确落库，响应报告各数据源覆盖范围与状态 | 符合预期 |
| T2 | 同步容错 | 在部分数据源接口异常的情况下执行同步 | 状态为 partial，已成功数据保留，未更新最近成功同步时间，错误原因可查 | 符合预期 |
| T3 | 仓库健康检查 | 对空数据、未完整同步与超过 24 小时未同步的仓库分别执行健康检查 | 分别给出数据为空、同步不完整与数据陈旧提示；数据不足时阻断可推进结论 | 符合预期 |
| T4 | 缺陷智能分诊 | 选取真实缺陷执行分析 | 输出分类、优先级、复杂度、负责人建议与行动项结构完整、格式可解析 | 符合预期 |
| T5 | 合并请求审查 | 选取含高风险路径改动的合并请求执行审查 | 输出摘要、风险点、检查清单与明确的合入建议 | 符合预期 |
| T6 | 构建失败排障 | 选取失败运行记录执行排障分析 | 提取关键错误块，给出失败类型、原因分析与排查步骤 | 符合预期 |
| T7 | 多智能体工作流 | 提出“检查缺陷、合并请求与失败构建，判断版本能否发布”问题并确认计划 | 生成计划，按依赖并行执行各任务，输出观察发现与汇总结论，全过程可回放 | 符合预期 |
| T8 | 检索问答与引用 | 在已上传知识库上执行问答并核对引用 | 回答带编号引用，引用可展开并对应原文；无证据时明确提示而非编造 | 符合预期 |
| T9 | 召回测试 | 对典型查询执行召回测试 | 返回各候选块各阶段分数与排名明细 | 符合预期 |
| T10 | 安全草稿 | 在对话中触发“对合并请求发表评论”意图 | 生成待确认草稿且不直接执行；确认后执行并写入审计日志 | 符合预期 |
| T11 | 长会话压缩 | 连续进行超过上下文预算的长对话 | 自动触发压缩，会话继续可用，压缩事件可诊断 | 符合预期 |
| T12 | 候选记忆批准 | 封存会话后审查候选记忆 | 候选条目待审批状态，批准后方参与后续召回 | 符合预期 |

上述测试覆盖了数据接入、分析能力、协作决策、检索问答与安全机制五类核心场景，各功能的输入输出均符合第3章提出的需求定义。

### 6.3 集成与自动化测试

系统的自动化测试覆盖主要后端链路，代表性测试模块及其验证要点如表6-3所示。

**表6-3 代表性自动化测试模块**

| 测试模块 | 验证要点 |
|---------|---------|
| 仓库同步集成测试 | 真实本地 HTTP 分页、数据库写入、故障处理、健康问答与旧数据库升级兼容 |
| 仓库连接与删除测试 | 仓库接入参数校验、令牌处理与级联删除清理 |
| 对话智能体测试 | 工具选择、循环停止条件、重复调用限制与回答组织 |
| 工作流编排测试 | 任务依赖调度、并行执行、失败跳过、观察发现与重规划收敛 |
| 缺陷、合并请求与构建排障智能体测试 | 各专用智能体的输出结构与关键判断逻辑 |
| 检索链路测试 | 切分、混合召回、融合、重排与分数阈值行为 |
| 项目隔离测试 | 跨仓库检索不可越界，隔离字段强制生效 |
| 上下文压缩测试 | 各级压缩触发条件、保留策略与失败降级 |
| 技能注册测试 | 技能发现、激活条件校验与工具白名单约束 |
| 评测运行测试 | 评测提交、后台执行、进度上报与结果落库 |

自动化测试通过 pytest 统一执行，测试环境中对模型调用进行了可控替身注入，保证在无外部模型服务时也可验证流程逻辑；涉及行为一致性的用例（如同步集成测试）则运行真实 HTTP 分页与数据库，避免“假测试”。

### 6.4 基于 RAGAS 的回答质量评估

本小节介绍基于 RAGAS 的评估体系设计，包括评估流程、指标与验收门禁，以及回归对比与失败诊断机制。

#### 6.4.1 评估体系设计

功能测试验证的是“功能是否可用”，评测体系回答的是“回答是否变好”。系统建立了基于固定评测集的自动评估流程：评测在隔离会话中真实运行生产对话智能体与完整工具集，先收集预检索证据，再由智能体循环执行二次检索，最后统一收集回答、证据与工具轨迹，交由 RAGAS 框架[12]计算质量指标。评测结果持久化评测集哈希、阈值配置、逐题工具轨迹、检索证据、硬规则检查与失败诊断信息，使两次评测之间具备严格可比性。

#### 6.4.2 评估指标与验收门禁

评测指标分为语义质量指标与执行行为指标两组，各项指标及验收阈值如表6-4所示（阈值可在配置中调整，表中为默认值）。

**表6-4 评测指标与验收阈值**

| 指标 | 含义 | 默认阈值 |
|------|------|---------|
| 上下文精确率（Context Precision） | 检索到的证据中相关内容的占比 | ≥ 0.75 |
| 上下文召回率（Context Recall） | 标准答案所需证据被检索到的比例 | ≥ 0.80 |
| 忠实度（Faithfulness） | 回答内容忠实于检索证据、无编造的比例 | ≥ 0.90 |
| 答案相关性（Answer Relevancy） | 回答与问题的相关程度 | ≥ 0.80 |
| 智能体目标达成度（Agent Goal Accuracy） | 回答是否达成题目定义的预期目标 | ≥ 0.80 |
| 工具调用准确率（Tool Call Accuracy） | 工具调用行为与期望工具使用的一致性 | ≥ 0.90 |
| 工具调用 F1（Tool Call F1） | 工具调用行为的查准与查全综合值 | ≥ 0.90 |

整体通过要求“硬规则全部满足”且“五项语义指标均达到阈值”。硬规则检查确定性行为（如引用是否完整、输出结构是否合法、是否出现禁止内容），语义指标由模型裁判（Judge）评分。评测页面将“执行状态”与“质量状态”分离展示：低分是质量失败；裁判调用失败或指标缺失则属于评测不完整，不能伪装为质量结论，这一区分保证了评测结论本身的可靠性。

#### 6.4.3 回归对比与失败诊断

评测体系服务于持续迭代，具体设计了四条闭环路径：

（1）回归对比。用户可选择两个“评测集哈希、裁判配置与 Top-K 一致”的历史评测结果进行对比，页面逐题展示两次运行的指标变化与证据差异，回答“改动是否带来真实提升”。

（2）失败诊断。评测失败后可直接展开问题用例，查看实际回答、参考答案、检索来源、工具轨迹与可执行诊断建议，定位失败环节（检索未命中、工具选择错误、综合表述偏差等）。

（3）评测到工单的闭环。对确认由系统缺陷导致的失败用例，可一键生成“创建缺陷”类型的操作草稿，把失败用例、证据与建议带入人工确认流程，且不会直接写入平台——评测发现的问题以安全草稿方式进入改进流程，形成“评测—诊断—工单—修复—回归”的完整闭环。

（4）评分重试。裁判服务超时或个别指标缺失时，页面支持“仅重试异常评分”，复用已保存的回答与证据重新评分，不需要重跑对话智能体，节约重复推理成本。

### 6.5 本章小结

本章介绍了系统的测试与评估工作：说明了容器化测试环境的配置与四层测试策略；通过十二个代表性功能用例验证了数据接入、分析能力、协作决策、检索问答与安全机制等核心场景；介绍了覆盖主要后端链路的自动化测试体系；最后详细说明了基于 RAGAS 的回答质量评估设计，包括指标定义、验收阈值、回归对比、失败诊断与评测闭环。测试与评估结果表明，系统各功能实现符合需求定义，且具备可量化、可回归的质量保障能力。

## 第7章 总结与展望

本章对全文工作进行总结，并分析系统现存的不足与后续的改进方向。

### 7.1 全文总结

本文针对研发协作中“信息分散、证据收集成本高、复杂判断依赖资深经验”的现实问题，设计并实现了一个基于多智能体协作的研发协作系统。论文完成的主要工作如下：

（1）完成了系统需求分析与总体设计。在分析可行性、功能需求与非功能需求的基础上，提出了证据驱动、分层解耦、人机协同、安全可控、可观测与可评测五项设计原则，完成了五层总体架构、八个功能模块、数据库域划分与接口协议的设计。

（2）实现了研发数据接入与同步模块。支持五类研发数据的分页同步与覆盖范围报告，通过五种同步状态区分完整、为空、部分、失败与跳过情形，并实现部分失败的保留策略与定时同步，为系统提供可靠的数据底座。

（3）实现了基于原生工具调用的对话智能体。通过状态图组织“决策—工具执行—结果观察”循环，实现了最大步数、重复调用检测、八类工具错误分类处理与上下文溢出恢复等执行约束，保证智能体在可控边界内完成任务。

（4）实现了“规划—调度—观察—综合”多智能体工作流。通过依赖驱动的并行调度、失败跳过、结构化观察检查与有限重规划机制，支撑跨领域工程决策问题的系统化分析，并实现工作流级与任务级的完整运行轨迹持久化。

（5）实现了工程化检索增强生成链路。通过研发数据分流策略区分当前代码、实时状态与历史知识三类数据的访问方式；实现结构感知切分、向量与关键词双路召回、加权融合、重排、编号引用、按仓库隔离、召回测试与答案门禁。

（6）实现了上下文与记忆、安全执行与评测体系。包括分层上下文预算与分级压缩、会话封存与候选记忆人工批准、安全草稿生命周期与审计留痕，以及基于固定评测集与 RAGAS 指标的量化评估、回归对比与失败诊断闭环。

系统测试与评估表明，各功能模块实现符合设计预期，关键链路具备自动化验证与量化度量能力。本文的工作完整覆盖了“数据接入—知识检索—智能体协作—安全执行—效果评测”五个环节，对同类大语言模型应用系统的工程化落地具有参考价值。

### 7.2 不足与展望

受时间与条件限制，本系统仍存在以下不足，也是后续改进的方向：

（1）评测规模有限。当前固定评测集侧重研发问答的核心场景，题目数量与场景覆盖度仍有提升空间；后续可扩展多类型、多难度的评测集，并引入更细粒度的过程指标（如检索命中位置、多轮工具调用效率）。

（2）模型能力依赖。系统的分析质量与所接入模型的能力强相关，不同模型在工具调用稳定性与长上下文处理上差异明显；后续可研究模型路由与多模型协同策略，按任务类型选择适配模型，并加强弱模型下的降级路径设计。

（3）写操作自动化程度保守。安全草稿机制保证了安全性，但也使操作链路包含人工确认环节；后续可在风险分级基础上设计“低风险白名单自动执行 + 高风险人工确认”的差异化策略，在安全与效率间取得更好的平衡。

（4）多用户与权限体系较简单。当前系统的角色模型以满足演示与单团队使用为主；后续可完善多租户隔离、细粒度权限与团队协作能力。

（5）增量同步与数据规模。当前同步以分页全量拉取为主，随着仓库规模增长，可引入基于时间戳与变更事件的增量同步机制，并结合平台 Webhook 实现近实时更新。

总体而言，本文验证了多智能体架构在研发协作场景中的可行性，也展示了“证据驱动、人机协同、安全可控、可评测”这一设计思路的工程价值。随着大语言模型能力的持续演进，此类系统有望在研发效能提升中发挥越来越重要的作用。

## 参考文献

[1] Yao S, Zhao J, Yu D, et al. ReAct: Synergizing reasoning and acting in language models[C]//International Conference on Learning Representations (ICLR). 2023.

[2] Schick T, Dwivedi-Yu J, Dessì R, et al. Toolformer: Language models can teach themselves to use tools[C]//Advances in Neural Information Processing Systems (NeurIPS). 2023.

[3] Mialon G, Dessì R, Lomeli M, et al. Augmented language models: A survey[J]. arXiv preprint arXiv:2302.07842, 2023.

[4] Chase H. LangChain: Building applications with LLMs through composability[CP/OL]. https://github.com/langchain-ai/langchain, 2022.

[5] LangChain Inc. LangGraph: Build resilient language agents as graphs[CP/OL]. https://github.com/langchain-ai/langgraph, 2024.

[6] Lewis P, Perez E, Piktus A, et al. Retrieval-augmented generation for knowledge-intensive NLP tasks[C]//Advances in Neural Information Processing Systems (NeurIPS). 2020: 9459-9474.

[7] Robertson S, Zaragoza H. The probabilistic relevance framework: BM25 and beyond[J]. Foundations and Trends in Information Retrieval, 2009, 3(4): 333-389.

[8] Karpukhin V, Oğuz B, Min S, et al. Dense passage retrieval for open-domain question answering[C]//Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP). 2020: 6769-6781.

[9] Cormack G V, Clarke C L A, Buettcher S. Reciprocal rank fusion outperforms Condorcet and individual rank learning methods[C]//Proceedings of the 32nd International ACM SIGIR Conference on Research and Development in Information Retrieval. 2009: 758-759.

[10] Nogueira R, Cho K. Passage re-ranking with BERT[J]. arXiv preprint arXiv:1901.04085, 2019.

[11] Gao Y, Xiong Y, Gao X, et al. Retrieval-augmented generation for large language models: A survey[J]. arXiv preprint arXiv:2312.10997, 2023.

[12] Es S, James J, Espinosa-Anke L, et al. RAGAS: Automated evaluation of retrieval augmented generation[J]. arXiv preprint arXiv:2309.15217, 2023.

[13] Park J S, O'Brien J C, Cai C J, et al. Generative agents: Interactive simulacra of human behavior[C]//Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology (UIST). 2023.

[14] Wu Q, Bansal G, Zhang J, et al. AutoGen: Enabling next-gen LLM applications via multi-agent conversation[J]. arXiv preprint arXiv:2308.08155, 2023.

[15] Hong S, Zhuge M, Chen J, et al. MetaGPT: Meta programming for a multi-agent collaborative framework[C]//International Conference on Learning Representations (ICLR). 2024.

[16] Qian C, Liu W, Liu H, et al. ChatDev: Communicative agents for software development[C]//Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL). 2024: 15174-15186.

[17] Vaswani A, Shazeer N, Parmar N, et al. Attention is all you need[C]//Advances in Neural Information Processing Systems (NeurIPS). 2017: 5998-6008.

[18] Brown T B, Mann B, Ryder N, et al. Language models are few-shot learners[C]//Advances in Neural Information Processing Systems (NeurIPS). 2020: 1877-1901.

[19] Ouyang L, Wu J, Jiang X, et al. Training language models to follow instructions with human feedback[C]//Advances in Neural Information Processing Systems (NeurIPS). 2022: 27730-27744.

[20] Wei J, Wang X, Schuurmans D, et al. Chain-of-thought prompting elicits reasoning in large language models[C]//Advances in Neural Information Processing Systems (NeurIPS). 2022: 24824-24837.

[21] Wang J, Yi X, Guo R, et al. Milvus: A purpose-built vector data management system[C]//Proceedings of the 2021 International Conference on Management of Data (SIGMOD). 2021: 2614-2627.

[22] Liu N F, Lin K, Hewitt J, et al. Lost in the middle: How language models use long contexts[J]. Transactions of the Association for Computational Linguistics, 2024, 12: 157-173.

## 致谢

本论文的完成离不开许多人的帮助与支持，在此致以诚挚的感谢。

首先感谢我的指导教师。从论文选题、系统设计到论文撰写的各个环节，老师都给予了悉心的指导与耐心的审阅，提出了许多宝贵的修改意见，使本文的结构与内容得以不断完善。老师严谨的治学态度与务实的工作作风，也让我在专业学习之外受益良多。

感谢院系各位老师在大学期间传授的专业知识，正是这些课程所打下的编程、数据库与软件工程基础，使我能够完成本系统的设计与实现。感谢一起学习与讨论的同学，与你们的交流让我在很多技术细节上豁然开朗。

感谢在系统开发过程中提供帮助的开源社区及技术资料的作者们，你们的分享是本项目得以顺利进行的重要基础。

最后，感谢我的家人在求学期间给予我的理解与支持，你们的鼓励是我前行路上最坚实的后盾。

由于本人水平有限，论文中难免存在不足之处，恳请各位老师批评指正。
