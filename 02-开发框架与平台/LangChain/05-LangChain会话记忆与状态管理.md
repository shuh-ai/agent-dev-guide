# LangChain 会话记忆与状态管理（Memory）

> **适用版本**：LangChain 1.3.x / LangGraph 1.2.x / langchain-core 1.4.x 

---

## 1. 为什么需要记忆？

LLM 本质是**无状态**的——每次 API 调用都是独立事件，模型不会自动保留任何历史信息。具体表现：

- 用户说"我叫小明"，下一轮再问"我叫什么？"，模型答不上来
- Agent 执行多步任务时，前序步骤的结果直接丢失
- 代词指代（"它"、"刚才那个"）在长对话中完全失效

💡 **Memory 的职责**：为无状态的 LLM 补上上下文连续性，让它能跨轮次感知对话历史。

```mermaid
graph LR
    subgraph "无记忆"
        A1[用户: 我叫小明] --> B1[LLM: 你好小明]
        A2[用户: 我叫什么?] --> B2[LLM: 我不知道你是谁]
    end

    subgraph "有记忆"
        C1[用户: 我叫小明] --> D1[LLM: 你好小明]
        C2[用户: 我叫什么?] --> D2[历史消息 + 当前问题] --> E2[LLM: 你叫小明]
    end

    style B2 fill:#FDECEA,stroke:#E74C3C
    style E2 fill:#E8F5E9,stroke:#67B168
```

---

## 2. 记忆的分类

智能体的记忆通常分为两大类：

- **短期记忆（Short-Term Memory）**：当前任务或会话的上下文信息
- **长期记忆（Long-Term Memory）**：跨任务、跨会话的经验与知识

| **维度** | **短期记忆** | **长期记忆** |
|----------|-------------|-------------|
| **定义** | 当前任务或会话的上下文（Working / Session Memory） | 跨任务、跨会话的经验与知识（Persistent Memory） |
| **生命周期** | 当前会话（短暂） | 跨任务、跨会话（持久） |
| **存储内容** | 对话历史、查询结果、任务状态 | 知识、经验、用户偏好 |
| **是否跨会话** | 否 | 是 |
| **存储介质** | 内存 / Redis / 数据库 | 向量数据库 / 持久化存储 |

**示例**：一个公司数据分析 Agent 场景：

1. 用户提出需求："帮我写 Q1 的销售分析报告"
2. **短期记忆**：当前对话历史、查询到的 Q1 销售数据、任务目标与执行状态
3. **长期记忆**：公司的 KPI 计算方式、用户偏好的报告风格

⚠️ 别被字面意思误导。"短期"不等于"断电就丢"，"长期"也不等于"持久化存储"。两者的本质区别在于**作用域**——短期记忆服务于当前会话，长期记忆跨越多个会话和任务。这个概念在传统后端开发里不太常见，初次接触 Agent 记忆体系时容易混淆。

---

## 3. 现代记忆管理架构

LangChain 1.x 把旧版的 `ConversationBufferMemory`、`ConversationChain` 等 API 全部废弃了。如果你是从旧版迁移过来的，旧代码基本要重写。（LangChain 的 API 稳定性嘛……你懂的。）当前推荐的两种现代方案：

```mermaid
graph TB
    subgraph "方案一：LCEL 轻量级记忆"
        A1[RunnableWithMessageHistory] --> B1[BaseChatMessageHistory]
        B1 --> C1[InMemoryChatMessageHistory / SQLite]
    end

    subgraph "方案二：LangGraph 状态级记忆"
        A2[create_agent] --> B2[LangGraph Runtime]
        B2 --> C2[State: messages 列表]
        B2 --> D2[Checkpointer]
        D2 --> E2[InMemorySaver / SqliteSaver / PostgresSaver]
    end

    F[你的应用] --> A1
    F --> A2

    style A1 fill:#4A90D9,stroke:#2C5F8A,color:#fff
    style A2 fill:#67B168,stroke:#3D7A3E,color:#fff
    style D2 fill:#F5A623,stroke:#C17D0E,color:#fff
```

| **方案** | **适用场景** | **核心机制** | **复杂度** |
|----------|-------------|-------------|-----------|
| **LCEL 轻量级记忆** | 简单对话链、独立模型调用 | `RunnableWithMessageHistory` + `BaseChatMessageHistory` | 低 |
| **LangGraph 状态级记忆** | Agent 系统、多步推理、生产级应用 | Checkpointer + State + `thread_id` | 中高 |

> **选型建议**：用 `create_agent` 构建 Agent 的话，直接用方案二——Checkpointer 已内嵌在运行时中。如果只是给独立的 LLM 调用加记忆，方案一更轻量，没必要上重型方案。

---

## 4. 🛠️ LangGraph Checkpointer：Agent 级记忆管理

这是 LangChain 1.x 中最核心的记忆管理方案。`create_agent` 底层基于 LangGraph 运行时，天然支持通过 **Checkpointer** 机制实现会话记忆。

### 4.1 核心机制

```mermaid
sequenceDiagram
    participant U as 用户
    participant A as Agent
    participant LLM as 大模型
    participant CP as Checkpointer

    U->>A: 第 1 轮消息 + thread_id
    A->>CP: 保存快照 (checkpoint)
    A->>LLM: 用户消息
    LLM-->>A: AI 回复
    A->>CP: 保存快照
    A-->>U: 返回回复

    U->>A: 第 2 轮消息 + thread_id
    A->>CP: 加载同一 thread_id 的历史
    CP-->>A: 返回历史消息列表
    A->>LLM: [历史消息...] + 当前消息
    LLM-->>A: AI 回复
    A->>CP: 保存新快照
    A-->>U: 返回回复
```

**核心概念**：

1. **AgentState**：Agent 的运行状态，其中 `messages` 列表记录了完整的对话历史
2. **Checkpointer**：持久化引擎，负责在每一轮交互后保存状态快照
3. **thread_id**：会话唯一标识，同一 `thread_id` 的消息属于同一会话

### 4.2 快速上手：InMemorySaver

`InMemorySaver` 是基于内存的 Checkpointer，适合开发和测试阶段。

**完整示例**：

```python
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

# Step 1: 创建 Checkpointer
checkpointer = InMemorySaver()

# Step 2: 创建 Agent 并绑定 Checkpointer
agent = create_agent(
    model="deepseek:deepseek-chat",
    checkpointer=checkpointer,
    system_prompt="你是一个友好的智能助手。",
)

# Step 3: 定义会话配置（通过 thread_id 标识会话）
config = {"configurable": {"thread_id": "user-001"}}

# Step 4: 第一轮对话——用户自我介绍
response = agent.invoke(
    {"messages": [HumanMessage(content="你好，我叫一木，我最喜欢小狗。")]},
    config,
)
for msg in response["messages"]:
    msg.pretty_print()
```

输出：

```
================================ Human Message =================================

你好，我叫一木，我最喜欢小狗。
================================== Ai Message ==================================

你好一木！很高兴认识你！🐶 小狗确实是很可爱的动物，你有养小狗吗？最喜欢什么品种呢？
```

```python
# Step 5: 第二轮对话——同一 thread_id，Agent 自动携带历史消息
response = agent.invoke(
    {"messages": [HumanMessage(content="我最喜欢的动物是什么？")]},
    config,
)
for msg in response["messages"]:
    msg.pretty_print()
```

输出：

```
================================ Human Message =================================

我最喜欢的动物是什么？
================================== Ai Message ==================================

你最喜欢的动物是小狗呀！🐶 你之前提到过自己叫一木，还说最喜欢小狗了。
```

**关键点**：两轮对话使用相同的 `thread_id`，Agent 自动从 Checkpointer 加载历史消息，模型据此准确回忆用户信息。

**切换会话**：使用不同的 `thread_id` 即可开启全新会话：

```python
# 新会话——Agent 不会记住之前的信息
new_config = {"configurable": {"thread_id": "user-002"}}
response = agent.invoke(
    {"messages": [HumanMessage(content="我叫什么名字？")]},
    new_config,
)
# 模型无法回答，因为它属于全新的会话
```

> **注意**：`InMemorySaver` 仅在程序运行期间有效，进程重启后记忆即丢失。生产环境请使用持久化方案。

---

## 5. 持久化存储方案

LangGraph 提供了多种持久化 Checkpointer 实现，适配不同的存储后端：

| **实现** | **存储后端** | **适用场景** |
|----------|-------------|-------------|
| `InMemorySaver` | 内存 | 开发调试、单元测试 |
| `SqliteSaver` | SQLite | 本地持久化、小型应用 |
| `PostgresSaver` | PostgreSQL | 生产环境、分布式部署 |
| `CosmosDBSaver` | Azure Cosmos DB | Azure 云生态 |
| `RedisSaver` | Redis | 高性能缓存型持久化 |

> 完整清单参见官方文档：[Checkpointer Libraries](https://docs.langchain.com/oss/python/langgraph/persistence#checkpointer-libraries)

### 5.1 SQLite 持久化

**安装依赖**：

```bash
uv add langgraph-checkpoint-sqlite
```

**初始化并使用**：

```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

# 创建 SQLite Checkpointer
conn = sqlite3.connect("checkpoint.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
checkpointer.setup()  # 自动建表

# 创建 Agent
agent = create_agent(
    model="deepseek:deepseek-chat",
    checkpointer=checkpointer,
)

# 使用方式与 InMemorySaver 完全一致
config = {"configurable": {"thread_id": "session-001"}}

response = agent.invoke(
    {"messages": [HumanMessage(content="记住，我的项目代号是 Phoenix。")]},
    config,
)

# 重启程序后，只要连接同一个 checkpoint.db，记忆依然存在
response = agent.invoke(
    {"messages": [HumanMessage(content="我的项目代号是什么？")]},
    config,
)
# 模型回答：你的项目代号是 Phoenix。
```

### 5.2 PostgreSQL 持久化

适用于生产级部署，支持多实例共享状态：

```bash
uv add langgraph-checkpoint-postgres
```

```python
from langgraph.checkpoint.postgres import PostgresSaver

# 使用 PostgreSQL 连接串
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/langgraph_db"
)
checkpointer.setup()

agent = create_agent(
    model="deepseek:deepseek-chat",
    checkpointer=checkpointer,
)
```

---

## 6. 📐 记忆管理策略：上下文窗口优化

会话记忆的核心挑战在于：**上下文窗口是有限的**。当会话历史超出模型的 token 上限时，会出现：

- 上下文截断，导致模型"失忆"
- 模型"注意力分散"，响应质量和速度严重下降

```mermaid
graph LR
    A[长会话历史] --> B{超出 Token 上限?}
    B -->|否| C[正常推理]
    B -->|是| D[选择优化策略]
    D --> E[修剪消息]
    D --> F[删除消息]
    D --> G[消息摘要]

    style B fill:#FFF3E0,stroke:#F5A623
    style E fill:#E8F4FD,stroke:#4A90D9
    style F fill:#FDECEA,stroke:#E74C3C
    style G fill:#E8F5E9,stroke:#67B168
```

LangChain 通过**中间件（Middleware）** 机制提供三种策略：

### 6.1 修剪消息（Trim Messages）

**修剪并非删除**——State 中的消息列表依然完整，只是在发送给模型前截取其中一部分。

| **特性** | **说明** |
|----------|---------|
| State 中是否保留 | 完整保留 |
| 是否发送给模型 | 只发送子集 |
| 信息损失 | 低（可按 token / 条数 / 时间窗口截取） |
| 适用场景 | 对话历史较长但近期消息更重要的场景 |

### 6.2 删除消息（Delete Messages）

直接从 State 中移除消息，**需谨慎使用**。

| **操作** | **State 中是否保留** | **是否发送给模型** |
|----------|---------------------|-------------------|
| 修剪消息 | 保留完整列表 | 只发送子集 |
| 删除消息 | 从 State 中移除 | 不再存在 |

> ⚠️ 删除操作不可逆，建议仅在明确不需要的历史消息（如中间调试信息）上使用。

### 6.3 消息摘要（Summarize Messages）

最智能的策略——利用大模型对历史消息生成摘要，既控制上下文长度，又最大程度保留关键信息。

```mermaid
graph LR
    subgraph "摘要前"
        M1[用户: 你好] --> M2[AI: 你好] --> M3[用户: 我喜欢编程] --> M4[AI: 很好呀] --> M5[用户: 我在学 Python] --> M6[AI: Python 很棒]
    end

    subgraph "摘要后"
        S1[摘要: 用户喜欢编程，正在学习 Python]
        S2[用户: 我在学 Python]
        S3[AI: Python 很棒]
    end

    M6 --> S1

    style S1 fill:#E8F5E9,stroke:#67B168
```

#### 使用 SummarizationMiddleware

LangChain 通过 `SummarizationMiddleware` 提供了开箱即用的消息摘要能力。

**参数说明**：

| **参数** | **选项** | **说明** |
|----------|---------|---------|
| `model` | — | 执行摘要时使用的大模型 |
| `max_tokens` | int | Token 上限阈值 |
| `keep_recent` | int | 保留最近 N 条消息 |
| `trigger` | `fraction` / `tokens` / `messages` | 触发摘要的条件 |
| `keep` | `fraction` / `tokens` / `messages` | 摘要后保留的消息量 |

**完整示例**：

```python
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.middleware import SummarizationMiddleware
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

# 初始化中间件
middleware = SummarizationMiddleware(
    model="deepseek:deepseek-chat",
    trigger=("messages", 3),   # 消息数量超过 3 条时触发摘要
    keep=("messages", 1)       # 摘要后保留 1 条最新消息
)

# 创建 Agent
checkpointer = InMemorySaver()
agent = create_agent(
    model="deepseek:deepseek-chat",
    middleware=[middleware],
    checkpointer=checkpointer,
)

# 模拟长会话
config: RunnableConfig = {"configurable": {"thread_id": "session-001"}}

agent.invoke({"messages": [HumanMessage(content="你好，我是一木。")]}, config)
agent.invoke({"messages": [HumanMessage(content="我最喜欢的游戏是英雄联盟")]}, config)
agent.invoke({"messages": [HumanMessage(content="我最喜欢的动物是小狗。")]}, config)

# 第 4 轮——触发摘要
final_response = agent.invoke(
    {"messages": [HumanMessage(content="你还记得我吗？")]},
    config,
)

for message in final_response["messages"]:
    message.pretty_print()
```

**输出结果**：

```
================================ Human Message =================================

Here is a summary of the conversation to date:
用户名为"一木"。最喜欢的游戏是英雄联盟。最喜欢的动物是小狗。
AI已向用户打招呼，并询问了用户在英雄联盟中最常玩的位置和段位。
AI也已询问用户目前是否有自己养小狗，或者最喜欢什么品种的小狗。
用户尚未回复关于游戏和动物的后续细节。
================================ Human Message =================================

你还记得我吗？
================================== Ai Message ==================================

当然记得，一木！你最喜欢的游戏是英雄联盟，最喜欢的动物是小狗。
之前还在问你平时打联盟喜欢走哪条路，以及有没有自己养一只可爱的小狗呢？
今天想聊点关于游戏的事，还是聊聊狗狗？😄
```

即使会话历史被摘要压缩，Agent 依然准确记住了用户名、爱好等关键信息，并自然地延续了对话。

---

## 7. LCEL 轻量级记忆方案

对于不使用 `create_agent` 的简单场景（如独立的 LLM 链），可以使用 LCEL 的 `RunnableWithMessageHistory` 实现记忆管理。

### 7.1 核心组件

```mermaid
graph TB
    A[用户输入] --> B[RunnableWithMessageHistory]
    B --> C[加载历史消息]
    C --> D[拼接: 历史 + 当前输入]
    D --> E[调用 LLM]
    E --> F[保存回复到历史]
    F --> G[返回结果]

    H[BaseChatMessageHistory] -.-> C
    F -.-> H

    style B fill:#4A90D9,stroke:#2C5F8A,color:#fff
    style H fill:#F5A623,stroke:#C17D0E,color:#fff
```

- **`BaseChatMessageHistory`**：消息历史的抽象接口，内置实现包括 `InMemoryChatMessageHistory`、`SQLChatMessageHistory` 等
- **`RunnableWithMessageHistory`**：包装器，自动在每次调用前加载历史、调用后保存消息

### 7.2 完整示例

```python
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()

# Step 1: 初始化模型
model = init_chat_model(model="deepseek:deepseek-chat")

# Step 2: 创建消息历史存储
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# Step 3: 用 RunnableWithMessageHistory 包装模型
model_with_memory = RunnableWithMessageHistory(
    model,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# Step 4: 调用（通过 session_id 区分会话）
config = {"configurable": {"session_id": "user-001"}}

response = model_with_memory.invoke(
    {"input": "你好，我叫一木，我最喜欢小狗。"},
    config=config,
)
print(response.content)

response = model_with_memory.invoke(
    {"input": "我最喜欢的动物是什么？"},
    config=config,
)
print(response.content)
# 输出: 你最喜欢的动物是小狗呀！🐶
```

> **适用场景**：简单的多轮对话链、不需要 Agent 能力的纯 LLM 交互。如果使用 `create_agent`，请直接使用 Checkpointer 方案。

---

## 8. ✅ 小结

| **知识点** | **关键要点** |
|-----------|-------------|
| **记忆的本质** | 为无状态 LLM 补上上下文连续性 |
| **短期记忆** | 当前会话上下文，通过 Checkpointer + `thread_id` 管理 |
| **长期记忆** | 跨会话知识，依赖持久化存储（向量数据库等） |
| **LangGraph Checkpointer** | Agent 级记忆管理的核心机制，`create_agent` 内置支持 |
| **InMemorySaver** | 基于内存，适合开发调试，重启后丢失 |
| **SqliteSaver** | 基于 SQLite 的本地持久化方案 |
| **PostgresSaver** | 生产级持久化方案，支持多实例共享 |
| **消息修剪** | 截取发送给模型的内容，State 中保留完整 |
| **消息删除** | 直接从 State 中移除，谨慎使用 |
| **消息摘要** | 用 LLM 总结历史，兼顾上下文长度和记忆完整性 |
| **LCEL 记忆方案** | `RunnableWithMessageHistory` + `BaseChatMessageHistory`，适用于简单对话链 |

**选择指南**：

- 使用 `create_agent` → 直接用 **Checkpointer**（推荐）
- 简单 LLM 链 → 用 **RunnableWithMessageHistory**
- 生产环境 → 用 **SqliteSaver / PostgresSaver** 持久化
- 长对话 → 搭配 **SummarizationMiddleware** 压缩历史

## 全套公开课课件领取：

![display](./images/display.png)

## DXZY.AI

DXZY.AI - 专注于 AI、RAG、Agent、MCP
![DXZY.AI Logo](./images/logo.png)

- GitHub: https://github.com/dxzyai/agent-dev-guide
- 官网: https://dxzy.ai
  ![DXZY.AI 服务](./images/service-qrcode.png)
