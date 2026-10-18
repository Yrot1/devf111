# 基于多智能体协作的研发协作系统设计与实现

## 摘要

在团队软件研发过程中，判断一次代码改动能否合入、定位一次持续集成失败的根因、评估一个缺陷的优先级，往往需要同时查阅代码变更、缺陷描述、评审评论、构建日志和项目文档。这些研发信息分散在代码仓库、项目管理平台、持续集成系统和团队知识库中，工程师需要先花费大量时间收集与整理上下文，才能进入真正的分析决策环节。大语言模型具备较强的语言理解与推理能力，但直接使用通用对话模型处理研发协作问题，仍存在证据来源不权威、上下文组织困难、复杂问题分析深度不足、涉及写操作时安全风险高等问题。

针对上述问题，本文设计并实现了一个面向研发协作场景的多智能体系统。系统采用 Python 智能体后端与 Next.js 前端的全栈架构，自下而上划分为数据基础层、知识与工具层、智能协作层、应用服务层和用户层五层结构。本文的主要工作包括：第一，构建研发数据接入与同步模块，实现代码仓库中缺陷、合并请求、持续集成运行记录、代码文件与评审评论等数据的同步、分页覆盖范围报告与状态管理；第二，设计基于原生工具调用机制的对话智能体，通过状态图组织"决策—工具执行—结果观察"循环，并实现最大步数、重复调用检测、工具错误分类处理等执行约束；第三，设计"规划—调度—观察—综合"多智能体工作流，由规划智能体拆解任务并声明依赖关系，调度器按依赖就绪情况并行执行任务，观察智能体检查证据缺口与结论冲突，综合智能体汇总形成统一建议，同时支持有限次数的重规划；第四，实现工程化的检索增强生成链路，包括文档结构感知切分、向量与关键词双路混合召回、加权融合、重排、编号引用、按仓库隔离检索与召回测试；第五，设计分层上下文预算与跨会话记忆机制、安全草稿与人工确认机制，以及基于 RAGAS 的回答质量评测与回归验证体系。此外，系统采用"研发数据分流"策略：当前代码通过工作区工具读取，实时状态通过数据库或接口查询，历史非结构化知识进入检索增强生成链路，避免将过期信息当作事实。

系统在本地容器化环境中完成部署，功能测试与集成测试覆盖数据同步、智能体循环、工作流编排、检索链路、上下文压缩、项目隔离与安全确认等关键链路；基于固定评测集与 RAGAS 指标的评测体系能够对回答质量进行量化，并支持同一基线的回归对比与失败诊断。结果表明，该设计能够为缺陷分诊、合并请求审查、持续集成排障与版本发布检查等场景提供带证据的分析建议，并以安全草稿方式承接外部写操作，为研发协作类智能体系统的工程设计提供了一种可行方案。

**关键词：** 大语言模型；智能体；多智能体协作；检索增强生成；研发协作

## Abstract

In team software development, deciding whether a code change can be merged, diagnosing the root cause of a CI failure, or evaluating the priority of an issue usually requires reviewing code changes, issue descriptions, review comments, build logs and project documents at the same time. Such information is scattered across code repositories, project management platforms, CI systems and team knowledge bases, so engineers must spend considerable time collecting and organizing context before reaching the analysis and decision stage. Large language models (LLMs) have strong language understanding and reasoning capabilities, but directly applying a general-purpose chat model to development collaboration tasks still suffers from unauthoritative evidence, difficult context organization, insufficient depth for complex problems, and security risks in write operations.

To address these problems, this thesis designs and implements a multi-agent system for development collaboration scenarios. The system adopts a full-stack architecture with a Python agent backend and a Next.js frontend, and is organized into five layers: the data foundation layer, the knowledge and tool layer, the intelligent collaboration layer, the application service layer and the user layer. The main work of this thesis includes: first, a repository data ingestion and synchronization module that synchronizes issues, pull requests, CI runs, code files and review comments with pagination coverage reporting and status management; second, a conversational agent based on native tool calling, whose "decision–execution–observation" loop is organized as a state graph with execution constraints such as a maximum step limit, repeated-call detection and categorized tool error handling; third, a "plan–orchestrate–observe–synthesize" multi-agent workflow, in which the planner decomposes tasks and declares dependencies, the orchestrator executes ready tasks in parallel, the observer inspects evidence gaps and conflicting conclusions, and the synthesizer produces a unified recommendation, with bounded replanning; fourth, an engineered Retrieval-Augmented Generation (RAG) pipeline featuring structure-aware chunking, hybrid retrieval combining dense vectors and keyword search, weighted fusion, reranking, numbered citations, per-repository isolation and retrieval testing; fifth, a layered context budget and cross-session memory mechanism, a safety draft mechanism with human confirmation, and a RAGAS-based answer quality evaluation and regression verification system. In addition, the system adopts a "development data triage" strategy: current code is read through workspace tools, real-time status is queried from the database or APIs, and historical unstructured knowledge enters the RAG pipeline, avoiding treating outdated information as facts.

The system is deployed in a local containerized environment. Functional and integration tests cover key paths such as data synchronization, the agent loop, workflow orchestration, the retrieval pipeline, context compression, project isolation and safety confirmation. The evaluation system based on a fixed test suite and RAGAS metrics can quantify answer quality and support regression comparison and failure diagnosis against the same baseline. The results show that the design can provide evidence-backed analysis suggestions for issue triage, pull request review, CI debugging and release readiness checking, and can carry out external write operations through safety drafts, offering a feasible engineering approach for development collaboration agent systems.

**Key words:** large language model; agent; multi-agent collaboration; retrieval-augmented generation; development collaboration

## 第1章 绪论

### 1.1 研究背景与意义

随着软件系统规模不断扩大与团队协作方式持续演进，软件研发活动已经高度平台化、分布式化。一个中等规模的研发团队，日常需要同时维护代码仓库、缺陷跟踪系统、合并请求（Pull Request，PR）评审流程、持续集成（Continuous Integration，CI）流水线和团队知识库等多个平台。研发协作中大量高频问题的答案并非来自单一数据源，而是需要跨平台交叉验证。例如，判断一次代码改动能否合入，需要先确认合并请求改写的内容，再查阅关联缺陷中的需求背景、评审者留下的讨论意见以及自动化检查的运行结果；排查一次构建失败，需要从失败任务日志中提取关键错误，再结合当前代码状态与历史文档判断原因。这些信息分散且数量庞大，仅"找齐背景与证据"这一步就会消耗工程师大量时间，对不熟悉项目的新成员而言尤其困难。

大语言模型（Large Language Model，LLM）的出现为解决上述问题提供了新的技术路径。以 Transformer 架构为基础的预训练语言模型经过大规模语料训练与指令微调后，具备了强大的自然语言理解、生成与推理能力，能够胜任摘要、分类、问答等多种任务。然而，在研发协作这一专业场景中，直接使用通用对话模型存在明显不足：其一，模型的参数化知识无法覆盖特定项目的最新代码与实时状态，容易产生与事实不符的"幻觉"；其二，研发问题往往涉及多源证据的收集与比对，单轮问答难以完成系统性的信息整合；其三，简单地堆砌对话历史会迅速耗尽模型的上下文窗口，影响长会话的可用性；其四，模型若被赋予直接操作外部系统的能力，误操作可能对真实仓库造成不可逆的影响。

智能体（Agent）范式的提出为解决这些不足提供了新的思路。智能体将大语言模型从"文本生成器"升级为"任务执行者"：模型通过工具调用（Tool Calling）与外部世界交互，通过"推理—行动—观察"的循环逐步收集证据、修正判断，最终完成任务。当任务复杂度进一步提高、需要跨领域综合分析时，单智能体又面临职责边界模糊、分析深度不足的问题，多智能体协作（Multi-Agent Collaboration）随之成为研究与工程实践的热点——由多个职责明确的专用智能体分工完成子任务，再由更高层的规划与汇总机制形成整体结论。

本文正是在上述背景下开展研究与设计的。本文设计并实现了一个面向研发协作场景的多智能体系统，它连接代码仓库数据，能够分析缺陷、审查合并请求、排查持续集成失败、检索项目知识，并在多智能体协作模式下回答"版本能否发布"这类跨领域工程决策问题。本课题的研究意义体现在两个方面。在工程实践层面，系统完整覆盖了数据接入、知识检索、智能体协作、安全执行与效果评测五个环节，探索了大语言模型应用从"演示可用"走向"工程可靠"所需的关键设计，包括证据溯源、执行约束、人机协同与量化评测等。在技术学习层面，本文对智能体循环、检索增强生成、多智能体任务调度、上下文管理、安全草稿与评测工程等当前大模型应用领域的前沿课题进行了系统性的梳理与实现验证，对理解新一代 AI 应用架构具有参考价值。

### 1.2 国内外研究现状

#### 1.2.1 大语言模型与智能体技术

智能体技术的核心是让语言模型具备与外部环境交互的能力。Yao 等人提出的 ReAct 范式[5]将推理（Reasoning）与行动（Acting）交织进行，模型在每一步先生成思考轨迹，再决定调用何种工具并观察返回结果，从而在知识密集型任务中显著优于只做推理或只做行动的方法。Schick 等人提出的 Toolformer[6]进一步验证了语言模型可以通过自监督方式学会在合适的位置调用外部工具接口。Mialon 等人对增强语言模型进行了系统综述[19]，将"推理、工具、记忆"归纳为语言模型增强的三条主线。在工程实践层面，基于原生工具调用的智能体框架（如 LangChain[21]与 LangGraph[22]）被广泛采用，前者统一了模型、工具与消息的抽象，后者以状态图（State Graph）方式显式建模智能体的执行流程、分支与停止条件，使多轮工具调用具备可控的执行边界。

#### 1.2.2 检索增强生成技术

检索增强生成（Retrieval-Augmented Generation，RAG）由 Lewis 等人系统提出[7]，其核心思想是在生成回答前先检索外部知识，将检索到的证据与问题一同交给模型，从而缓解幻觉并提升回答的可溯源性与时效性。检索环节的技术演进经历了从稀疏检索到稠密检索、再到混合检索的过程：BM25 作为经典的稀疏检索算法，基于词项频率与文档长度归一化计算相关性[9]；Karpukhin 等人提出的稠密段落检索（DPR）[8]使用双塔结构将问题与文档映射到同一向量空间，通过语义相似度召回候选。Cormack 等人提出的倒数排名融合（Reciprocal Rank Fusion，RRF）[11]为不同召回路径的结果融合提供了简单而有效的方法。在召回之后，Nogueira 等人采用交叉编码器对候选段落进行重排[10]，进一步提升排序质量。Gao 等人的综述[13]将 RAG 的发展归纳为朴素 RAG、高级 RAG 与模块化 RAG 三个阶段，并指出工程化 RAG 系统需要在切分策略、检索策略、重排与评测等环节进行系统设计。评测方面，Es 等人提出的 RAGAS 框架[12]从上下文精确率、上下文召回率、答案忠实度与答案相关性等维度对 RAG 系统进行自动化评估，已成为该领域被广泛采用的评测工具。

#### 1.2.3 多智能体协作技术

多智能体协作将复杂任务拆解给多个职责明确的智能体。Park 等人提出的生成式智能体[14]通过记忆、反思与规划机制的组合，让多个智能体在开放环境中产生可信的协作行为，验证了多智能体架构在复杂任务中的潜力。Wu 等人提出的 AutoGen[15]以"可对话智能体"为核心抽象，支持多智能体通过对话协同完成代码生成与执行等任务，并允许人类以参与者身份介入。面向软件开发场景，Hong 等人提出的 MetaGPT[16]与 Qian 等人提出的 ChatDev[17]将软件公司中的角色分工（产品经理、架构师、程序员、测试员等）映射为智能体角色，通过标准化的中间产物（如需求文档、设计文档）在角色之间传递信息，展示了多智能体在软件工程流程中的可行性。总体来看，现有多智能体研究多聚焦于任务生成与流程模拟，而面向真实研发数据（仓库代码、缺陷、合并请求、构建日志）的协作分析系统，以及配套的证据校验、冲突检查与安全控制机制，仍存在较大的工程探索空间。

#### 1.2.4 现有研发协作工具的不足

当前研发协作领域已有若干工具化实践：代码托管平台内置了静态检查与自动评审能力，集成开发环境中的编程助手可以补全代码、解释片段。但这类工具多聚焦于"代码本身"，对研发协作中"跨平台信息收集与判断"这一关键环节的支持仍然有限：缺陷、评审讨论、构建日志与项目文档之间的关联关系没有被有效利用；分析结论往往缺少可核查的证据链；面对"该不该合入""该不该发布"这类需要综合多源信息的决策问题，缺乏系统性的多智能体分工协作机制；此外，赋予工具自动执行写操作的能力时，缺乏草稿确认、权限校验与审计留痕等安全设计。上述不足正是本文工作试图填补的空间——面向研发协作场景，构建一个证据驱动、人机协同、安全可控的多智能体分析系统。

### 1.3 主要研究内容

围绕上述目标，本文的主要研究内容包括以下五个方面：

（1）研发数据接入与同步。设计并实现代码仓库数据的连接、分页同步与状态管理机制，将分散在代码托管平台各处的缺陷、合并请求、变更文件、评审评论、持续集成运行记录与日志等数据统一落库，并设计同步覆盖范围的报告机制与仓库健康检查，为后续分析提供可靠的数据底座。

（2）对话智能体与工具调用循环。基于原生工具调用机制设计对话智能体，通过状态图组织"决策—工具执行—结果观察"的多轮循环；设计工具注册与结构化参数校验、最大步数与重复调用限制、工具错误分类与重试等执行约束，保证智能体在可控边界内完成任务。

（3）多智能体协作工作流。设计"规划—调度—观察—综合"四角色协作架构：规划智能体负责任务拆解、依赖声明与验收标准定义；调度器按任务依赖就绪情况并行调度并处理失败跳过；观察智能体负责合并门禁检查、跨智能体结论冲突检测与证据缺口识别；综合智能体负责汇总形成统一建议；同时设计有限重规划机制，避免工作流陷入无效循环。

（4）工程化检索增强生成链路。设计研发数据分流策略与文档处理流水线，实现结构感知切分、向量与关键词混合召回、加权融合、重排、编号引用、按仓库隔离与召回测试，并处理"证据不足时拒答"的答案门禁问题。

（5）上下文管理、安全执行与效果评测。设计分层上下文预算与压缩机制、跨会话记忆的沉淀与人工批准机制、写操作的安全草稿与审计机制，以及基于固定评测集与 RAGAS 指标的量化评测与回归对比体系。

### 1.4 论文组织结构

本文共分为七章，各章内容安排如下：

第1章为绪论，介绍课题的研究背景与意义、国内外研究现状、主要研究内容与论文组织结构。

第2章为相关技术基础，介绍大语言模型与提示工程、工具调用与智能体循环、LangChain 与 LangGraph 编排框架、检索增强生成、混合检索与重排以及系统开发与部署所涉及的关键技术。

第3章为系统需求分析，对系统进行可行性分析，从功能与非功能两个维度梳理系统需求。

第4章为系统总体设计，阐述系统设计目标与原则、总体架构、功能模块划分、数据库设计、接口设计与部署架构设计。

第5章为系统详细设计与实现，逐模块介绍研发数据同步、对话智能体、多智能体工作流、检索增强生成、上下文与记忆、安全机制、流式推送与运行轨迹、能力扩展以及前端交互的详细设计与实现过程。

第6章为系统测试与效果评估，介绍测试环境与策略、功能测试、集成测试以及基于 RAGAS 的回答质量评估体系。

第7章为总结与展望，总结全文工作并分析不足与后续改进方向。

## 第2章 相关技术基础

### 2.1 大语言模型与提示工程

#### 2.1.1 大语言模型基本原理

本文所依托的大语言模型以 Transformer 架构[1]为基础。Transformer 抛弃了循环神经网络（Recurrent Neural Network，RNN）的序列递推结构，完全基于自注意力机制（Self-Attention）建模序列中任意两个位置之间的依赖关系，具备良好的并行训练能力与长距离依赖建模能力。其核心计算如式（2-1）所示：

Attention(Q, K, V) = softmax(QKᵀ / √d_k)V　　（2-1）

其中 Q、K、V 分别表示查询矩阵、键矩阵与值矩阵，d_k 为键向量的维度。多头注意力机制将上述计算在多个子空间中并行执行再拼接，使模型能够从不同表示子空间捕捉语义信息。

大语言模型的训练通常分为两个阶段：第一阶段为预训练，模型在海量文本上以自回归方式学习下一个词的预测，获得通用的语言能力与世界知识[2]；第二阶段为指令微调与基于人类反馈的强化学习（Reinforcement Learning from Human Feedback，RLHF）[3]，通过人工标注的指令数据与偏好数据对模型进行对齐，使其输出更符合人类指令意图。经过两个阶段训练后的模型具备零样本与少样本学习能力，能够按照自然语言指令完成分类、摘要、抽取、推理等多种任务，这是构建智能体系统的能力基础。

#### 2.1.2 提示工程与结构化输出

提示工程（Prompt Engineering）指通过精心设计输入提示来引导模型产生期望输出的方法。Wei 等人提出的思维链（Chain-of-Thought）提示[4]表明，在提示中引导模型先给出推理过程再给出结论，可以显著提升模型在数学与逻辑推理任务上的表现，这一思想后续被广泛吸收进智能体的推理循环设计中。

在工程系统中，模型输出不仅是给人阅读的文本，还需要被程序消费。本文系统采用结构化输出（Structured Output）方案：通过 Pydantic 模型定义输出 Schema，要求模型以 JSON 格式返回分析结果，并在运行时对返回内容进行类型校验与约束检查。相比自由文本，结构化输出使分析结果可直接入库、渲染与二次加工，同时当模型输出不符合 Schema 时可以触发重试或降级，提高了系统的鲁棒性。

### 2.2 工具调用与智能体循环

工具调用（Tool Calling）是模型与外部系统交互的标准化接口。系统在请求中向模型声明一组可用工具及其参数 Schema，模型根据当前任务决定是否调用工具、调用哪个工具以及传入什么参数；系统执行工具后将结果回传给模型，模型继续决定下一步动作，直至任务完成或触发停止条件。

这一"决策—执行—观察"的循环被称为智能体循环（Agent Loop），其概念源头可追溯到 ReAct 范式[5]。一个健壮的 Agent Loop 需要解决以下工程问题：第一，循环停止条件，包括任务完成、达到最大步数上限、重复调用检测等，防止无界循环；第二，工具错误处理，工具可能因网络、权限、数据缺失等原因失败，系统需要对错误分类并决定重试、降级或终止；第三，观测结果的组织，工具返回结果可能非常长，需要截断、摘要或结构化压缩后再回传给模型；第四，安全性，敏感工具（如写操作）需要权限校验与人工确认。本文第5章介绍的对话智能体正是围绕上述问题展开设计的。

### 2.3 LangChain 与 LangGraph 编排框架

LangChain[21]是当前应用最广泛的大语言模型应用开发框架之一，它提供了模型（Chat Model）、消息（Message）、工具（Tool）等核心抽象，统一了不同模型厂商接口的调用方式，并将工具的参数校验、调用执行封装为可复用的组件。本文系统的对话智能体基于 LangChain 的工具抽象注册工具集，通过 OpenAI 兼容接口接入大语言模型服务。

LangGraph[22]在 LangChain 基础上进一步提供基于状态图（State Graph）的编排能力。开发者将智能体的执行过程建模为若干节点（Node）与边（Edge）：节点表示一个计算步骤（如模型决策、工具执行），边表示步骤之间的流转条件。相较于线性链式调用，状态图的优势在于：流程分支与循环显式可查；执行状态（消息、中间结果、计数器等）统一管理；支持中断、恢复与可视化。本文系统的对话智能体以状态图组织执行循环，将"模型推理""工具执行"等步骤定义为节点，并根据模型是否产生工具调用决定下一步流向，使多轮循环的停止条件具备显式、可控的结构。

### 2.4 检索增强生成

检索增强生成（RAG）由 Lewis 等人提出[7]，其基本流程可概括为三个阶段：

（1）索引阶段。将外部知识文档进行解析与切分，得到若干文本块（Chunk），通过嵌入模型将文本块映射为语义向量并存入向量数据库，同时对文档块附加来源、时间等元数据。

（2）检索阶段。将用户问题同样映射为向量，在向量数据库中检索语义相近的文本块；为提高召回质量，工程系统通常同时执行关键词检索，并对多路结果进行融合与重排。

（3）生成阶段。将检索到的证据片段与用户问题一同组织进提示词，引导模型"基于给定证据"生成回答，并在回答中标注引用来源。

RAG 在本文系统中的定位是"历史与非结构化知识的语义召回通道"，与工作区代码检索、数据库结构化查询共同构成三类证据来源，其详细设计见第5.4节。

### 2.5 混合检索与重排技术

单一检索路径存在固有局限：稀疏检索（如 BM25）依赖词项匹配，擅长捕获专有名词、错误码等精确匹配信号，但无法理解语义改写；稠密检索基于语义向量，擅长同义表达与模糊语义，但对罕见词的区分度较低。工程实践因此普遍采用混合检索（Hybrid Retrieval）。

BM25 评分函数如式（2-2）所示：

Score(q, d) = Σ IDF(q_i) · (f(q_i, d) · (k₁ + 1)) / (f(q_i, d) + k₁ · (1 − b + b · |d| / avgdl))　　（2-2）

其中 f(q_i, d) 为词项 q_i 在文档 d 中的出现频次，|d| 为文档长度，avgdl 为平均文档长度，k₁ 与 b 为可调参数，分别控制词频饱和程度与长度归一化强度[9]。

多路召回结果的融合方法中，倒数排名融合（RRF）[11]仅依赖各路的排名位置而非原始分数，避免了不同打分体系不可比的问题，其公式如式（2-3）所示：

RRF(d) = Σ 1 / (k + rank_i(d))　　（2-3）

其中 rank_i(d) 为文档 d 在第 i 路召回中的排名，k 为平滑常数。在本文系统的实现中，考虑到两类召回分数的可比性，融合环节同时引入了带权重的分数融合与双路命中奖励策略（详见第5.4.4节）。

重排（Rerank）阶段使用交叉编码器（Cross-Encoder）模型对候选段落与问题做联合编码打分[10]。与双塔结构中问题与文档独立编码不同，交叉编码器能够建模问题与文档之间的细粒度交互，排序精度更高，但计算开销大，因此通常只对召回阶段的 Top-N 候选（如几十条）进行重排，从中筛选最终的 Top-K 证据。

### 2.6 系统开发与部署技术

本文系统的后端采用 Python 语言，Web 框架为 FastAPI，其基于类型注解的依赖注入与 Pydantic 数据校验模型能够显著降低接口层与模型层的开发成本；数据访问层使用 SQLAlchemy ORM，数据库为 PostgreSQL 16（配合 pgvector 扩展）。向量检索使用 Milvus 分布式向量数据库[18]，其支持亿级向量的相似性检索，并通过分区与标量过滤满足多租户隔离需求。前后端之间的实时进度推送采用服务器发送事件（Server-Sent Events，SSE）协议，相比轮询具备更低的延迟与更小的服务端开销。

前端采用 Next.js 15 与 React 19 框架，使用 TypeScript 作为开发语言，样式方案为 Tailwind CSS，数据获取与缓存采用 TanStack React Query，并配合 React Markdown 渲染模型输出的富文本内容。整个系统通过 Docker Compose 编排部署，将 PostgreSQL、Milvus、etcd、MinIO 等基础服务容器化，后端与前端以本地进程方式运行，配置项通过环境变量文件统一管理。

### 2.7 本章小结

本章介绍了本文所涉及的关键技术基础，包括大语言模型与提示工程的基本原理、工具调用与智能体循环的工作机制、LangChain 与 LangGraph 编排框架的设计思想、检索增强生成的流程、混合检索与重排算法的技术要点，以及系统开发与部署所用的主流技术栈。上述技术构成了后续章节系统设计与实现的技术依据。
