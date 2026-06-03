# Part 5. Agentic RAG 架构的基本原理与应用入门

> 本文是笃行智元 AI 大模型技术社区「RAG 检索增强生成」系列的第 5 篇。
>
> 从 RAG 基础回顾出发，逐步拆解 AI Agent 核心架构（规划/记忆/工具/行动）、Chain-of-Thought 推理、ReAct 循环模式，再引入 LangGraph 构建完整 ReAct Agent，最终将 Agent 与 RAG 融合实现 Agentic RAG。
>
> 前置阅读：[Part 1. RAG 技术体系全景](./Part1-RAG技术体系全景.md) | [Part 2. 从零到一快速搭建多模态 RAG 引擎](./Part2-从零到一快速搭建多模态RAG引擎.md)

---

## 一、RAG 基础回顾

### 1.1 RAG 解决了什么问题

大模型有两个根本性限制：

1. **上下文窗口有限**：任何大模型都有最大输入 Token 限制（如 GPT-4o 128K、Claude 200K、Gemini 3 Pro 1M），将整篇文档甚至整个文件系统直接作为 Prompt 是不现实的，必须精准选择最相关的片段
2. **知识时效性不足**：大模型在预训练/微调阶段获取知识，训练截止日期之后的信息无法回答。例如，如果模型的训练数据截止到 2025 年，就无法回答"今天的天气怎么样？"

大量实验证明：当为大模型提供一定的上下文信息后，其输出会变得更稳定。RAG 的解决思路就是**先从外部知识库检索最相关的文档片段，再将其作为上下文注入 Prompt**，让 LLM 基于这些信息生成回答。

> 这样做的好处是三重的：① 充分利用大模型在内容生成上的能力；② 通过引入的上下文信息显著约束大模型的输出范围和结果；③ 实现将私有数据融入大模型中。

### 1.2 RAG 核心流程

从技术实现上看，RAG 分为两个阶段：

- **检索阶段（Retrieval）**：从知识库中找出与问题最相关的知识。具体流程：用户查询 → Embedding 模型将查询文本向量化 → 在向量数据库中执行语义相似度搜索 → 返回 Top-K 最相关的文档片段
- **生成阶段（Generation）**：将检索到的知识内容与用户问题一起输入 LLM，生成的答案不仅考虑了问题的语义信息，还参考了相关私有数据

![RAG 架构总览](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/rag/_images/rag-high-level-architecture.svg)

RAG 构建的关键组件：**检索组件（Embedding 模型 + 向量数据库）和生成组件（LLM）**。在推理时，用户查询用于对索引文档运行相似性搜索，检索最相似的文档作为额外上下文。

**分块策略（Chunking）** 是 RAG 质量的关键变量：

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| 固定大小分块 | 按字符数切分（如 1000 字符），相邻块有重叠 | 通用文本 |
| 递归字符分割 | 先按段落 → 再按换行 → 最后按字符切分 | **大多数场景的默认选择** |
| 语义分块 | 按语义边界（句子/段落）切分，相似度低于阈值时断开 | 高质量需求 |
| 文档结构分块 | 按 Markdown 标题、HTML 标签等结构切分 | 结构化文档 |

在实现 RAG 系统时，主要有三种方式：手动实现、框架实现和手动+框架结合。通常，企业中不会选择完全手动实现，因为工作量大且维护复杂。**手动+框架结合的方式是 90% 以上开发者的首选**。

### 1.3 Native RAG 的局限

传统 RAG（也称 Native RAG）有两个关键限制：

1. **仅考虑单一外部知识源**：实际场景往往需要多个知识源（多个向量库、Web 搜索、外部 API），甚至需要在不同知识源之间做出选择决策
2. **一次性检索，无质量验证**：上下文被检索一次后直接使用，没有对检索到的上下文质量进行推理或验证，更没有"如果检索结果不够好就重新检索"的能力

**RAG 在整个架构中占据的比例实际上非常小**——我们主要依赖大模型结合背景信息进行推理的能力，而检索策略的作用更为重要。此外，RAG 的实际应用场景相对有限，无论是哪种形式的问答系统，都还未能达到通用人工智能（AGI）的水平。

这两个限制恰好是 AI Agent 擅长解决的——Agent 的核心能力正是**集成外部工具、自主规划步骤、评估中间结果并动态调整策略**。

---

## 二、RAG 实战：LangChain + Milvus + Ollama

在深入 Agentic RAG 之前，先用一个完整的 RAG 实现建立基础。

### 2.1 文档加载与切分

首先从 PDF 中提取文本，用 LangChain 的 `RecursiveCharacterTextSplitter` 按语义边界切分。

```python
from PyPDF2 import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 读取 PDF
def pdf_read(pdf_paths):
    text = ""
    for pdf in pdf_paths:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

content = pdf_read(['./01_大模型应用发展及Agent前沿技术趋势.pdf'])

# 封装为 LangChain Document 格式
documents = [Document(page_content=content)]

# 切分文本
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,       # 每个块 1000 字符
    chunk_overlap=300      # 相邻块重叠 300 字符，保持语义连贯
)
splits = text_splitter.split_documents(documents)
print(f"切分为 {len(splits)} 个文本块")
```

> `RecursiveCharacterTextSplitter` 会先按段落（`\n\n`）切分，再按换行（`\n`）切分，最后按字符切分——这样能最大程度保留语义完整性。`chunk_overlap=300` 确保相邻块之间有重叠区域，避免语义在边界处断裂。

### 2.2 加载 Embedding 模型

LangChain 提供了与不同 Embedding 的接入方式。这里使用 Ollama 接入开源模型 `bge-m3`（1024 维，中英文支持优秀）。

```python
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    base_url="http://localhost:11434",  # 替换为自己本地启动的 Ollama endpoint
    model="bge-m3",
)

# 测试：将文本转为向量
text = "大模型  AI Agent 开发实战"
vector = embeddings.embed_query(text)
print(f"向量维度: {len(vector)}")  # 输出 1024
print(str(vector)[:100])            # 查看前 100 个字符的向量表示
```

> **Embedding 模型选型建议**（2026 年）：中文场景首选 `bge-m3`（BAAI）或 `text-embedding-v3`（阿里云）；英文场景可选 `text-embedding-3-small`（OpenAI）或 `voyage-3`（Voyage AI）。

### 2.3 存入向量数据库（Milvus）

将切分后的文档向量化后存入向量数据库。这里使用 Milvus（云端 Zilliz 免费实例）。

```python
from langchain_milvus import Milvus

vectorstore = Milvus.from_documents(
    documents=splits,
    collection_name="rag_demo",
    embedding=embeddings,
    connection_args={
        "uri": "https://in03-xxx.serverless.gcp-us-west1.cloud.zilliz.com",
        "user": "db_xxx",
        "password": "your_password",
    }
)
```

> **操作步骤**：访问 [Zilliz Cloud](https://cloud.zilliz.com) → 注册登录 → 创建索引 → 选择 Free 实例 → 保存用户名和密码 → 等待创建完成后获取连接信息。

**向量数据库选型对比**（2026 年）：

| 数据库 | 特点 | 适用场景 | 参考价格 |
|--------|------|----------|----------|
| **Milvus / Zilliz** | 开源+云，支持十亿级向量 | 企业级大规模部署 | Zilliz Cloud $100+/月 |
| **Qdrant** | 开源+云，性能优秀，Rust 实现 | 成本敏感的中小规模 | Cloud $30+/月 |
| **Chroma** | 开源，开发者友好 | 原型开发、学习 | 免费 |
| **Pinecone** | 全托管，开箱即用 | 快速上线 | $70-200/月（10M 向量） |
| **Weaviate** | 开源+云，内置向量化 | 需要端到端方案 | Cloud $25+/月 |

### 2.4 接入生成模型并构建问答链

```python
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 加载 LLM —— 使用 Ollama 接入 QWQ 推理模型
llm = ChatOllama(
    base_url="http://localhost:11434",
    model="qwq:latest",  # 也可替换为 qwen3、deepseek-v3 等
)

# 定义 Prompt 模板
prompt = PromptTemplate(
    template="""You are an assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Use three sentences maximum and keep the answer concise:

    Question: {question}
    Context: {context}
    Answer:""",
    input_variables=["question", "context"],
)

# 构建 RAG Chain：Prompt → LLM → 输出解析
rag_chain = prompt | llm | StrOutputParser()

# 执行检索 + 问答
question = "请问什么是 AI Agent？"
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})  # 检索 Top-3
docs = retriever.invoke(question)

answer = rag_chain.invoke({"context": docs, "question": question})
print(answer)
```

以上是通过手动+框架快速构建一个 RAG 问答流程的完整代码。相较于全手动实现，其效率和便捷性对开发者非常友好。

**这个 RAG 应用有两个关键限制：**

1. **仅考虑一个外部知识源**：某些场景可能需要两个外部知识源，或者需要调用外部工具和 API（如 Web 搜索）
2. **一次性检索，无质量验证**：上下文被检索一次，没有对检索到的上下文质量进行推理或验证

这两个限制正是 AI Agent 架构要解决的核心问题。

---

## 三、AI Agent 架构详解

### 3.1 什么是 AI Agent

AI Agent（人工智能代理）是一个能够**感知环境、处理信息并采取行动以实现特定目标**的软件系统。

与严格遵守设定脚本的传统自动化系统不同，AI Agent 具有感知、解释、学习和适应的能力。将它们视为数字助理——不仅执行任务，还不断评估周围环境，从不同的交互中学习，并做出决策以实现特定目标。

**从 AGI 的视角理解 AI Agent：**

人工智能技术迄今为止唯一成功开发的类型是狭义人工智能（ANI），也称弱人工智能——在执行特定任务或一组相关任务的系统（如图像识别、NLP、推荐引擎、自动驾驶等）。而我们期望做到的通用人工智能（AGI），是指具有相当于或超越人类能力的人工智能，涵盖跨不同领域学习、理解和应用知识的能力。

现阶段大模型本质上只是在做"预测"——通过大量数据训练以生成准确响应，但缺乏目标、身份或主动决策的概念。它们是复杂的文本生成器，没有目的或方向感。

**人类解决问题的方式** 是：不断吸收信息 → 做出决定 → 采取行动 → 观察变化 → 做出下一个决定。整个生活是一个永无休止的观察、思想和行动的链条。通用人工智能的核心理念就是将这个概念转移到大模型上——**让大模型不断做出新的决策，从而逐步接近更复杂问题的解决方案。**

AI Agent 就是这条路径上的核心载体——它把单一的大模型作为"大脑"，而不是全部。如果在 Agent 构建流程中添加语音转文本模型、图像理解模型，就可以构建自己的 Jarvis（钢铁侠的私人虚拟助理）。

### 3.2 Agent 经典四组件架构

AI Agent 的经典架构包含四个关键组件：

![AI Agent 架构总览](https://lilianweng.github.io/posts/2023-06-23-agent/agent-overview.png)

> ▲ LLM 驱动的 AI Agent 经典架构：Planning + Memory + Tool Use + Action（来源：Lilian Weng, "LLM Powered Autonomous Agents", 2023）

**四个组件详解：**

| 组件 | 功能 | 具体内容 |
|------|------|----------|
| **规划（Planning）** | 将大任务拆分为子任务，制定执行策略 | 面对"对比三家 AI 芯片公司的融资情况"，Agent 会先规划：① 检索公司 A 融资信息 ② 检索公司 B 融资信息 ③ 检索公司 C 融资信息 ④ 调用计算工具对比 ⑤ 生成报告 |
| **记忆（Memory）** | 存储历史交互和中间结果，支持上下文推理 | 短期记忆：当前对话的上下文（LLM 的 context window）；长期记忆：跨会话的知识积累（向量数据库、外部存储）。Agent 能"回忆"之前检索到的信息，避免重复查询 |
| **工具（Tools）** | 调用外部 API、数据库、搜索引擎等 | 搜索引擎（Serper API）、向量检索器（Milvus）、Python 代码解释器、邮件/日历 API……工具让 Agent 的能力超出单纯的语言处理 |
| **行动（Action）** | 执行具体操作，将决策转化为输出 | 发送 API 请求、调用函数、生成文本回答、发送邮件、操作数据库 |

### 3.3 Agent 与环境的交互模型

从更细粒度看，AI Agent 的交互模型可以拆解为四层：

**1. 环境（Environment）**

AI Agent 接收来自周围环境的信息。环境可以是网站、数据库、API 服务或任何其他类型的系统。环境是 Agent 获取信息和执行操作的目标对象。

**2. 感知（Perception）——即输入**

AI Agent 通过多种方式感知环境：
- 视觉（图像）：通过视觉模型理解图片、截图
- 听觉（声音）：通过语音识别模型理解音频
- 文本（文字信息）：通过 LLM 理解自然语言指令
- 其他传感器输入（位置、温度等）

这些输入帮助 Agent 理解当前的环境状态和用户意图。

**3. 大脑（Brain）**

大脑是 Agent 的核心处理单元，包含两个关键子层：

- **存储（Storage）**：
  - **记忆（Memory）**：存储先前的经验和数据，类似于人类的记忆。包括对话历史、中间检索结果、过去的操作记录
  - **知识（Knowledge）**：包括事实、信息和 Agent 用于决策的程序性知识

- **决策制定（Decision Making）**：
  - **总结（Summary）**：对检索到的信息进行压缩和提炼
  - **回忆（Recall）**：在需要时回顾和利用存储的知识
  - **学习（Learn）**：从交互反馈中更新策略
  - **检索（Retrieve）**：从外部数据源获取信息
  - **规划/推理（Planning/Reasoning）**：基于当前输入和存储的知识，制定行动计划

**4. 行动（Action）**

Agent 基于其感知和决策过程产生响应或行动。这可以是物理动作、发送 API 请求、生成文本、操作数据库或任何其他形式的输出。

整个过程是一个**动态循环**：Agent 不断从环境中学习，通过行动影响环境，然后根据反馈继续调整行动和策略。这种模式特别适用于需要理解和生成自然语言的应用场景，如聊天机器人、自动翻译系统或其他形式的自动化客户支持。

### 3.4 Chain-of-Thought（CoT）推理

在引入 ReAct 之前，需要先理解 CoT（Chain-of-Thought，思维链）。

CoT 是一种提示工程技术，首次在 2022 年的论文 *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*（Google Research）中提出。其核心思想是：**通过将复杂问题分解为多个逻辑思维步骤，帮助 LLM 执行推理并解决复杂问题**。

CoT 的两个关键机制：

- **分解问题**：当面对复杂任务时，不是通过单个步骤解决，而是将任务分解为更小的步骤，每个步骤解决不同方面的问题
- **顺序思维**：思维链中的每一步都建立在上一步的结果之上，这样模型就能从头到尾构造出一条完整的逻辑推理链

![Chain-of-Thought Prompting](https://ar5iv.labs.arxiv.org/html/2210.03629/x1.png)

> ▲ CoT 推理示意：将多步问题分解为中间推理步骤（来源：Wei et al., 2022）

**示例：** 一家商店以 100 元的价格出售产品。如果商店降价 20%，然后加价 10%，最终价格是多少？

```
Step 1 — 计算降价 20% 后的价格：
  原价 100 元，降价 20%
  100 × (1 - 0.2) = 80 元

Step 2 — 计算涨价 10% 后的价格：
  降价后价格 80 元，涨价 10%
  80 × (1 + 0.1) = 88 元

结论：先降价后加价，最终售价为 88 元
```

用 LLM 验证 CoT 效果：

```python
from langchain_ollama import ChatOllama

llm = ChatOllama(base_url="http://localhost:11434", model="qwq:latest")

response = llm.invoke(
    "罗杰有 5 个网球，他又买了 2 罐网球，每罐有 3 个网球，他现在有多少个网球？"
)
print(response.content)
```

LLM 输出：

```
罗杰原来有 5 个网球。
他买了 2 罐，每罐 3 个，所以 3 × 2 = 6 个网球。
原来 5 个 + 新买的 6 个 = 11 个网球。
所以罗杰现在有 11 个网球。

检查：5 + 6 = 11 ✓

最终答案: 11
```

可以看到，LLM 自动将问题分解为多个推理步骤，逐步得出结论。但 CoT 的问题在于：**它仅在推理层面工作，不与外部环境交互**——推理的中间结果无法被验证，仍然可能产生幻觉。

### 3.5 ReAct 模式——CoT 的进化

**ReAct**（Reasoning + Acting）在 2022 年 10 月的论文 *ReAct: Synergizing Reasoning and Acting in Language Models*（Google DeepMind / Princeton）中首次引入，于 2023 年 3 月修订。该框架的目的是**协同 LLM 中的推理和行动**，使它们更加强大、通用和可解释。

ReAct 的核心思想：**思想-行动-观察循环**（Thought-Action-Observation Loop）。

![ReAct Agent 循环](https://miro.medium.com/v2/resize:fit:1400/0*GNbgKmyAmyhQarx4)

> ▲ ReAct 代理的 Thought → Action → Observation 循环

```
用户提问："OpenAI 最近有什么大动作？"

  Thought 1: 这个问题需要实时信息，我无法从知识库中回答
  Action 1:  调用 web_search 工具，搜索 "OpenAI recent announcements"
  Observation 1: 返回了 3 条相关新闻链接和摘要

  Thought 2: 信息足够了，可以整合回答
  Action 2:  基于搜索结果为用户生成最终回答
  → "OpenAI 最近发布了 canvas 功能、ChatGPT search、新 Embedding 模型……"
```

**ReAct 框架的两个组成部分：**

- **Reason（推理）**：基于 CoT 技术，将输入分解为多个逻辑思维步骤。通过推理跟踪（Reasoning Trace）记录整个过程经历的步骤以得出结论
- **Act（行动）**：与外部环境实时交互（搜索引擎、API 等），获取反馈。行动不是盲目的，而是由推理结果驱动的

**ReAct 循环中的四个要素：**

| 要素 | 含义 | 示例 |
|------|------|------|
| **Question** | 用户请求的任务或需要解决的问题 | "OpenAI 最近有什么新闻？" |
| **Thought** | 确定要采取的行动，创建/维护/调整行动计划 | "需要实时信息，应该调用搜索工具" |
| **Action Input** | 让 LLM 与外部环境进行实时交互，包括调用具有预定义范围的 API | 调用 `web_search("OpenAI recent news")` |
| **Observation** | 观察执行操作结果的输出 | 返回了 3 条搜索结果的 JSON |

整个过程重复此循环直至任务完成。ReAct 有效缓解了纯 CoT 的幻觉问题——**每一步推理都通过外部工具的实际执行结果来验证和修正**。

**CoT vs ReAct 对比：**

| 维度 | CoT | ReAct |
|------|-----|-------|
| 核心能力 | 推理（Reason） | 推理 + 行动（Reason + Act） |
| 外部交互 | 无，纯靠 LLM 内部知识 | 可调用工具、API、搜索引擎获取实时信息 |
| 幻觉控制 | 弱（推理中间步骤可能出错且无法验证） | 强（每步推理都有外部反馈验证） |
| 适用任务 | 数学推理、逻辑题、文本分析 | 需要外部信息的复杂任务、多步决策 |
| 可解释性 | 中（展示推理链路） | 高（展示推理 + 行动 + 观察的完整链路） |

### 3.6 Agent 的迭代执行——AgentExecutor

AI Agent 能够连续执行正确的工具、不断观察结果、然后决定下一步需要哪种工具。这种函数的迭代执行是由 **AgentExecutor**（代理运行时）驱动的。

AgentExecutor 的核心职责：
1. 接收用户输入
2. 调用 LLM 决定下一步行动
3. 如果 LLM 决定使用工具 → 执行工具 → 将结果返回 LLM
4. 重复步骤 2-3，直到 LLM 认为信息足够，直接生成最终回答
5. 达到预定义的终止条件时结束

随着企业认识到 AI Agent 的重要性，解决方案提供商纷纷涌现，提供从无代码、低代码到完整 Python 库的各种工具。但最根本的区别在于基于 Agent 经典框架的扩展及不同的 AgentExecutor 构建理念。

**主流 Agent 框架对比**（2026 年）：

| 框架 | 定位 | GitHub Stars | 特点 |
|------|------|-------------|------|
| **LangGraph** | 有向图工作流编排 | 15K+ | 以 LangChain 为基础，状态图驱动，适合复杂流程 |
| **CrewAI** | 角色型多 Agent 协作 | 45K+ | v1.10.1，内置 MCP 集成，角色分工明确 |
| **AutoGen** | 多 Agent 对话 | 40K+ | 微软出品，Agent 间对话驱动 |
| **LlamaIndex Workflows** | 文档检索 Agent | 38K+ | 适合 RAG 场景，维护性好 |

> 导航网站 https://e2b.dev/ai-agents/open-source 提供了 AI Agent 工具的完整分类整理。

---

## 四、LangGraph 实现 ReAct Agent

### 4.1 LangGraph 简介

![LangGraph 工作流](https://www.ibm.com/adobe/dynamicmedia/deliver/dm-aid--56f5a126-236c-4ce8-a103-086a55edf80e/langgraph.png?preferwebp=true)

> ▲ LangGraph 有向图工作流：节点代表处理步骤，边代表流转关系

LangGraph 是以 LangChain 表达式语言为基础构建的 AI Agent 开发框架。它将 Agent 的工作流定义为**有向图**（Directed Graph），每个节点代表一个处理步骤（LLM 调用、工具执行等），边代表步骤间的流转。

**为什么选择 LangGraph：**

- 以 LangChain 为基础，大模型接入、工具定义等方面的优势可自然迁移
- 有向图结构天然适合表达 ReAct 的"思考→行动→观察"循环
- 支持条件边（Conditional Edges）——根据 LLM 输出动态决定走哪条路径
- 内置状态管理（State），支持多轮对话和复杂流程
- 最新版本 v1.0.10（2026 年 3 月 PyPI 发布）

与 RAG 的构建方法一样，Agent 开发也可以选择手动实现、框架实现或手动+框架结合。**手动+框架结合依然是最高效的方法**。

### 4.2 定义 State

```python
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Agent 的状态定义"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
```

`AgentState` 定义了 Agent 在整个执行过程中的状态结构。`add_messages` 注解确保新消息追加到已有消息列表，而非覆盖——这是实现多轮对话的关键。

### 4.3 定义工具——联网搜索

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import requests, json

class SearchQuery(BaseModel):
    query: str = Field(description="搜索查询内容")

@tool(args_schema=SearchQuery)
def web_search(query: str) -> str:
    """实时联网搜索，获取最新信息"""
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "num": 3})
    headers = {
        "X-API-KEY": "your_serper_api_key",  # 替换为自己的 Serper API Key
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, data=payload)
    data = response.json()
    if "organic" in data:
        return json.dumps(data["organic"], ensure_ascii=False)
    return json.dumps({"error": "No results found"})

# 验证工具有效性
result = web_search("什么是 AI Agent？")
print(result)
```

> **工具定义要点**：① 使用 `@tool` 装饰器注册函数为可调用工具；② 通过 `args_schema` 定义参数结构，LLM 会根据 schema 生成正确的调用参数；③ 函数的 docstring 会被 LLM 用来理解工具的功能，务必写清楚。

### 4.4 构建 Agent 图

```python
from langchain_core.messages import ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END

# 绑定工具到模型
tools = [web_search]
model = llm.bind_tools(tools)
tools_by_name = {tool.name: tool for tool in tools}

# 工具执行节点
def tool_node(state: AgentState):
    """执行 Agent 请求的工具调用"""
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
        outputs.append(ToolMessage(
            content=json.dumps(tool_result),
            name=tool_call["name"],
            tool_call_id=tool_call["id"],
        ))
    return {"messages": outputs}

# LLM 调用节点
def call_model(state: AgentState):
    """LLM 分析当前状态，决定下一步行动"""
    system_prompt = SystemMessage(
        content="You are a helpful AI assistant. "
                "Respond to the user's query to the best of your ability!"
    )
    response = model.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

# 路由判断——是否需要继续调用工具
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return "end"       # LLM 没有请求工具调用 → 结束，生成最终回答
    return "continue"       # LLM 请求了工具调用 → 继续，执行工具

# 构建有向图
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)     # LLM 思考节点
workflow.add_node("tools", tool_node)      # 工具执行节点
workflow.set_entry_point("agent")          # 入口：先让 LLM 思考

workflow.add_conditional_edges("agent", should_continue, {
    "continue": "tools",    # 需要工具 → 执行工具
    "end": END,             # 不需要工具 → 结束
})
workflow.add_edge("tools", "agent")        # 工具执行后回到 Agent 继续思考

agent = workflow.compile()
```

**图结构说明：**

```
START → agent ──┬── 需要工具 → tools ──→ agent（循环：思考→行动→观察→再思考）
                │
                └── 不需要工具 → END
```

![LangGraph ReAct Agent 工作流](https://dylancastillo.co/posts/react-agent-langgraph_files/figure-html/cell-9-output-1.png)

> ▲ LangGraph 构建的 ReAct Agent 图结构：agent ↔ tools 循环

### 4.5 运行测试

```python
def print_stream(stream):
    for s in stream:
        message = s["messages"][-1]
        if not isinstance(message, tuple):
            message.pretty_print()

# 测试 1：简单问题（无需工具，LLM 直接回答）
inputs = {"messages": [("user", "你好，请你介绍一下你自己？")]}
print_stream(agent.stream(inputs, stream_mode="values"))
```

输出：

```
================================ Human Message =================================
你好，请你介绍一下你自己？
================================== Ai Message ==================================
作为一个AI助手，我的主要功能是帮助用户回答问题、提供信息和进行对话。
```

```python
# 测试 2：实时问题（Agent 自动调用 web_search 工具）
inputs = {"messages": [("user", "OpenAI 最近在互联网上有什么大动作？")]}
print_stream(agent.stream(inputs, stream_mode="values"))
```

输出：

```
================================ Human Message =================================
OpenAI 最近在互联网上有什么大动作？
================================== Ai Message ==================================
Tool Calls:
  fetch_real_time_info (call_id: xxx)
  Args:
    query: What are the recent announcements and updates from OpenAI?
================================ Tool Message =================================
Name: fetch_real_time_info
[{"title": "News | OpenAI", "link": "https://openai.com/news/", ...}, ...]
================================== Ai Message ==================================
OpenAI 最近在互联网上有不少动态：
1. 新产品发布：canvas 功能，可用来编写和编码与 ChatGPT 的交互
2. ChatGPT Search：在 ChatGPT 中集成了搜索功能
3. API 更新：新的 Embedding 模型、Assistants API 改进……
```

整个过程中，Agent 自动完成"判断是否需要工具 → 选择哪个工具 → 调用工具 → 观察结果 → 生成回答"的全流程，**无需人工干预**。

---

## 五、Agentic RAG：Agent + RAG 的融合

### 5.1 什么是 Agentic RAG

**Agentic RAG**（Agent-based Retrieval-Augmented Generation）是在传统 RAG 框架中引入 Agent 作为核心编排组件。

与传统 RAG 的"检索→生成"线性流程不同，Agentic RAG 中的 Agent 可以：

- **自主选择**使用哪个检索工具（向量搜索、Web 搜索、API 调用）
- **多轮检索**：根据初步结果判断是否需要更多信息，自动发起新一轮检索
- **质量评估**：评估检索结果的质量，不满足时重写查询或切换数据源
- **结果融合**：将不同来源的结果整合后生成最终回答

![Agentic RAG 架构](https://deepchecks.com/wp-content/uploads/2024/12/img-the-architecture-agentic.jpg)

> ▲ Agentic RAG 架构：Agent 作为编排中心，协调多个检索工具和数据源

**Agentic RAG 的核心思想：** 将 AI 代理合并到 RAG 管道中，以编排其组件并执行简单信息检索和生成之外的其他操作，以克服非代理管道的限制。通过使用可访问不同检索器工具的检索代理，包括：

- 矢量搜索引擎（典型 RAG 管道中的向量相似度搜索）
- Web 搜索（实时联网获取最新信息）
- 任何以编程方式访问的 API（邮件、聊天、数据库等）

### 5.2 完整实现

在已有 ReAct Agent 基础上，添加向量知识库检索工具：

```python
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

@tool
def vec_kg(question: str) -> str:
    """个人知识库检索，存储 AI Agent 相关概念和文档"""
    prompt = PromptTemplate(
        template="""You are an assistant for question-answering tasks.
        Use the following context to answer. If unknown, say so. Max 3 sentences:

        Question: {question}
        Context: {context}
        Answer:""",
        input_variables=["question", "context"],
    )

    rag_chain = prompt | llm | StrOutputParser()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
    docs = retriever.invoke(question)

    return rag_chain.invoke({"context": docs, "question": question})

# 合并工具列表：Web 搜索 + 知识库检索
tools = [web_search, vec_kg]
model = llm.bind_tools(tools)
tools_by_name = {tool.name: tool for tool in tools}

# 重新编译 Agent（图结构不变，工具列表更新）
agent_with_rag = workflow.compile()
```

现在 Agent 拥有两个工具：
- `vec_kg`：向量知识库检索（私有数据）
- `web_search`：实时联网搜索（公开信息）

Agent 会根据问题类型**自动判断**使用哪个工具——知识库能回答的就用 `vec_kg`，需要实时信息的就用 `web_search`。

**测试：知识库检索**

```python
inputs = {"messages": [
    ("user", "请检索我的知识库并总结一下什么是 AI Agent，注意，请使用中文回复。")
]}
print_stream(agent_with_rag.stream(inputs, stream_mode="values"))
```

输出：

```
================================ Human Message =================================
请检索我的知识库并总结一下什么是 AI Agent
================================== Ai Message ==================================
Tool Calls:
  vec_kg (call_id: xxx)
  Args:
    question: 什么是AI Agent？
================================ Tool Message =================================
Name: vec_kg
AI Agent是一种人工智能系统，能够与环境互动、感知输入并做出决策……
================================== Ai Message ==================================
根据知识库的回复，AI Agent是一种人工智能系统，能够与环境互动、感知输入并做出决策。
它通过收集信息、分析和学习来适应不同的任务和情境。
```

**测试：多工具协同**

```python
inputs = {"messages": [
    ("user", "请检索我的知识库，并实时联网检索，结合两部分信息总结：什么是 AI Agent？注意，请使用中文回复。")
]}
print_stream(agent_with_rag.stream(inputs, stream_mode="values"))
```

输出：

```
================================ Human Message =================================
请检索我的知识库，并实时联网检索，结合两部分信息总结：什么是 AI Agent？
================================== Ai Message ==================================
Tool Calls:
  vec_kg (call_id: xxx)        ← 同时调用知识库
  Args: question: "什么是 AI Agent？"
  fetch_real_time_info (call_id: yyy)  ← 同时调用 Web 搜索
  Args: query: "什么是 AI Agent？"
================================ Tool Message =================================
（两个工具的结果都返回）
================================== Ai Message ==================================
综合知识库和网络搜索的信息：
AI Agent 是一种能够自主执行任务、与环境互动并根据反馈调整行为的人工智能系统……
```

> **注意**：LLM 可能存在以下问题——① 推理模型仅做步骤拆解但不触发工具调用；② 产生幻觉，说自己"无法访问知识库"。这些是 Agent 开发中常见的优化点，需要通过调整 System Prompt、工具描述、Few-shot 示例等方式解决。

### 5.3 Agentic RAG vs Native RAG

| 维度 | Native RAG | Agentic RAG |
|------|-----------|-------------|
| 检索方式 | 固定流程：一次检索一次生成 | Agent 自主决策：多轮、多源、可重试 |
| 工具数量 | 单一检索器（向量搜索） | 多工具（向量搜索 + Web + API + ……） |
| 质量验证 | 无（检索到什么用什么） | Agent 评估结果质量，必要时重写查询重试 |
| 可扩展性 | 更换检索器需要改代码 | 新增工具只需注册到 tools 列表 |
| 适用场景 | 简单知识库问答 | 复杂多源信息查询、需要推理和决策的任务 |
| 自主性 | 低（固定 pipeline） | 高（Agent 自主规划和执行） |

### 5.4 开发方式选择

| 方式 | 描述 | 推荐度 |
|------|------|--------|
| 手动实现 | 完全自己写循环逻辑和工具调用 | ⭐ 仅学习用 |
| 框架实现 | 用 LangGraph / CrewAI 等全自动 | ⭐⭐⭐ 快速原型 |
| **手动 + 框架** | 框架提供基础能力 + 手动定制关键流程 | **⭐⭐⭐⭐⭐ 最高效** |

90% 以上的开发者选择手动+框架结合的方式，因为它在灵活性和开发效率之间取得了最佳平衡。

---

## 六、进阶方向

### 6.1 多 Agent 协作

使用 CrewAI（v1.10.1, 2026 年 3 月发布）编排多个专职 Agent：
- **检索 Agent**：负责从不同数据源检索信息
- **分析 Agent**：负责对检索到的信息进行分析和对比
- **写作 Agent**：负责将分析结果组织成结构化回答

每个 Agent 有自己的角色定义、目标和工具集，通过消息传递协作完成任务。

### 6.2 记忆增强

引入长期记忆组件，跨会话保持上下文：
- **短期记忆**：当前对话的上下文（LLM context window）
- **长期记忆**：向量数据库存储的历史交互和知识
- **共享记忆**：多 Agent 之间共享的中间状态

### 6.3 Human-in-the-loop

在关键决策点介入人工审批，确保安全可控。LangGraph 原生支持在图的特定节点插入人工审核步骤。

### 6.4 Self-RAG

Agent 自我评估检索质量和回答可靠性，自主决定是否重新检索。核心思想：LLM 在生成回答时，同时输出一个"是否需要检索"的判断信号。

### 6.5 最新模型推荐

2026 年 RAG 场景推荐模型：

| 模型 | 类型 | 特点 |
|------|------|------|
| Gemini 3 Pro Preview | 闭源 | MMLU-Pro 89.8%，1M context window |
| Claude Opus | 闭源 | 长文本理解顶级，200K context |
| DeepSeek V3 | 开源 | 性价比高，MoE 架构 |
| Qwen3 | 开源 | 阿里出品，中文场景优秀 |
| GLM-5.1 | 开源 | 智谱 AI，专为 Agent 工程设计 |
