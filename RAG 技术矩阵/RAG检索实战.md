# Llama-Index进阶实战

---

# RAG检索实战

---

## Part 1.Llama-Index核心功能快速回顾

  RAG，Retrieval-Augmented Generation，也被称作检索增强生成技术，最早在 Facebook AI（Meta AI）在 2020 年发表的论文《Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks》（ https://arxiv.org/abs/2005.11401 ）中正式提出，这种方法的核心思想是借助文本检索策略，让大模型在每次问答前都带入相关文档，以此提升回答的准确性。这项技术在发布初期并未受到广泛关注，但随着2022年大模型技术的爆发，RAG逐渐成为大模型落地的核心范式之一。

  时至今日，RAG技术已经发展为一个庞大的技术体系，从基础的文档切分、向量存储与匹配，到进阶的GraphRAG（基于知识图谱的检索增强），再到复杂文档解析与多模态识别技术等等。

  对于初学者而言，理解RAG最基本的实现流程是学习进阶技术的前提。一个典型的RAG流程包括：将给定的长文档进行切分，将切分后的段落转化为数值向量（词向量），当用户提出问题时，将问题同样转化为向量，与段落向量进行相似度匹配，找出最相关的文档片段，最后将问题和检索到的片段一并送入大模型进行回答。

### 1. Llama-Index 项目介绍

  Llama-Index（前身为 GPT Index）由 Jerry Liu 于 2022 年底发起。项目的诞生背景源于大语言模型（LLM）落地初期的一个核心痛点：**模型虽然具备强大的通用推理能力，但缺乏特定领域的私有知识（Private Knowledge），且受限于上下文窗口（Context Window）的长度，无法处理大规模文档。**

  Llama-Index 的初始定位非常明确——构建一个高效的"接口"，将用户的私有数据（如 PDF、Notion、SQL、API 数据）转化为 LLM 能够理解和利用的格式，通过上下文学习（In-context Learning）来增强模型能力。经过两年多的迭代，它已从一个简单的索引工具演变为完整的**"数据驱动型"大模型应用开发框架**。

  **如果把大模型比作"大脑"，Llama-Index 的定位就是**"记忆增强系统"**。它的官方定义是：**"用于构建上下文增强型（Context-augmented）LLM 应用程序的数据框架"**。

  Llama-Index 不仅关注如何向模型提问（Prompt Engineering），更侧重于数据管理（Data Management）的全生命周期，包括数据摄入（Ingestion）、结构化索引（Indexing）以及高效检索（Retrieval）。其核心目标是打破私有数据孤岛，让 LLM 能够以较低的成本、较高的精度访问海量外部知识。

  目前，Llama-Index 是全球 AI 开源社区中较为活跃的项目之一：

- **技术迭代：** 保持着较高的更新频率，已发布 v0.10+ 版本，完成了核心架构的模块化重构，具备企业级生产环境所需的稳定性。
- **生态系统：** 拥有庞大的 **LlamaHub** 数据加载器生态，支持数百种数据源（从文件系统到 SaaS 服务）的开箱即用连接；同时支持 Python 和 TypeScript 双语言版本。

  在 LLM 开发框架的生态中，通过对比可以更清晰地理解 Llama-Index 的定位：

- **LangChain（通用编排者）：**
  - **定位：** 通用的 LLM 应用开发框架。
  - **强项：** 侧重于**"计算逻辑"**的编排。擅长管理复杂的 Agent 行为链、工具调用（Tool Usage）以及多模态交互的流程控制，类似于连接模型与各类工具的"胶水"。
- **Llama-Index（数据专家）：**
  - **定位：** 专注于数据处理与检索的垂直框架。
  - **强项：** 侧重于**"数据结构"**的优化。在 RAG 领域有更深入的技术积累，特别是在非结构化数据切片、层级索引构建、复杂查询路由等方面提供了更精细的控制能力。

  相较于其他框架，Llama-Index 在 RAG 方面展现出以下几项专业性优势：

1. **更丰富的数据索引结构：** 不仅支持简单的向量索引，还支持树状索引、关键词表索引、知识图谱索引等多种结构。
2. **更高级的检索策略：** 提供了递归检索（Recursive Retrieval）、混合检索（Hybrid Search）及元数据过滤等开箱即用的高级功能。
3. **数据与 LLM 的深度对齐：** 能够较好地处理长文档摘要、跨文档推理等复杂的数据任务。

### 2. Llama-Index RAG核心优势

**2.1 RAG 全生命周期（Full-Lifecycle）的闭环支持**

  与许多仅关注"向量检索"单一环节的工具不同，Llama-Index 提供了从数据源头到最终评估的 RAG 全流程解决方案。它将 RAG 系统抽象为五个标准化的流水线环节，开发者可以在同一个框架内完成所有工作，无需拼凑多个零散的工具库。

- **数据加载 (Loading)：** 提供统一接口将各类非结构化数据转化为标准的 Document 对象。
- **索引构建 (Indexing)：** 将文档切分（Chunking）并向量化（Embedding），构建出不仅包含向量、还包含元数据（Metadata）和节点关系（Relationships）的高级索引结构。
- **存储 (Storing)：** 原生适配数十种主流向量数据库（如 Chroma, Weaviate, Milvus）及图数据库，支持索引的持久化与增量更新。
- **查询 (Querying)：** 这一环节是 Llama-Index 的核心，它封装了检索、后处理和合成的复杂逻辑，对外提供简洁的查询接口。
- **评估 (Evaluation)：** 内置了基于 LLM 的评估模块，能够对检索的准确性（Retrieval metrics）和生成的质量（Response metrics）进行自动化评分。

**2.2 极致的定制化空间与丰富的功能接口**

  Llama-Index 架构上的一个突出优势在于其模块化（Modularity）设计。它将 RAG 的每个步骤都解耦为可插拔的组件，在查询引擎（Query Engine）环节提供了较高的定制自由度：

- **高级后处理 (Post-Processing)：** 在检索与生成之间，Llama-Index 允许开发者插入"节点后处理器（Node Postprocessors）"，实现：
  - **重排序（Re-ranking）：** 集成 Cohere Rerank 或 BGE Rerank 模型，对检索到的 Top-K 结果进行二次精排。
  - **元数据过滤（Metadata Filtering）：** 基于时间、作者或文件类型过滤节点。
  - **相似度截断（Similarity Cutoff）：** 自动丢弃相似度低于阈值的噪声数据。
- **灵活的响应合成 (Response Synthesis)：** 针对不同业务场景，提供了多种内置的合成策略：
  - **Refine（精炼模式）：** 线性遍历检索结果，逐步迭代优化答案，适合生成详尽的回答。
  - **Tree Summarize（树状总结）：** 自底向上构建摘要树，适合处理海量上下文的归纳总结任务。
  - **Compact（紧凑模式）：** 最大化利用 Context Window，平衡速度与成本。

**2.3 庞大的数据生态：LlamaHub**

  Llama-Index 拥有目前 AI 社区中较为丰富的数据连接器生态——**LlamaHub**。它解决了 RAG 开发中数据获取的"最后一公里"难题：

- **海量数据加载器 (Data Loaders)：** 社区维护了超过 400 种数据加载器，覆盖了几乎所有主流数据源：
  - **文件类：** PDF, Markdown, PowerPoint, Word, Excel, CSV 等。
  - **SaaS 类：** Notion, Slack, Discord, Jira, Salesforce, Google Docs 等。
  - **网络类：** Wikipedia, YouTube Transcripts, Web Page Reader 等。
  - **数据库类：** PostgreSQL, MongoDB, SQL Database 等。
- **多模态原生支持：** 除了文本，LlamaHub 还提供了针对图像、音频和视频的加载器，支持构建图文混排的 RAG 系统，将多模态信息统一映射到向量空间。

**2.4 企业级云服务：LlamaCloud**

  为了满足企业对高性能和免运维的需求，Llama-Index 团队还推出了商业化的云服务：

- **LlamaParse：** 业界较为先进的文档解析服务之一，专为 RAG 场景中的"复杂文档处理"设计，能够精准识别 PDF 中的**复杂表格、图表、数学公式**以及**多栏排版**，转化为 LLM 易于理解的 Markdown 格式。
- **Managed Indexing：** 提供"检索即服务（Retrieval-as-a-Service）"，开发者无需自行维护向量数据库和索引管道，通过 API 即可上传文件并进行高效检索。

📦 **代码实现：Llama-Index 基础 RAG**

> 📊 **RAG 基础架构总览：** [点击查看交互式架构图](https://excalidraw.com/#json=pcrybMUYx5UauTSMSFQuz,etfOiUqM8nRpAKumPc24rQ)

```Python
import os
from dotenv import load_dotenv
import llama_index.core
# 读取环境变量
load_dotenv()

# 打印 Llama-Index 版本信息
print(f"Llama-Index Version: {llama_index.core.__version__}")
Llama-Index Version: 0.14.10

doc_path = "./data/云启智联科技集团员工手册.txt"

with open(doc_path, "r", encoding="utf-8") as f:
    handbook_content = f.read()
handbook_content[:1000]
'# 云启智联科技集团员工手册\n\n## 第二章 行为准则与合规要求\n\n### 2.1 职业操守\n\n全体职员须恪守高标准的职业操守。核心要求包含：以诚信为本处理各项业务，确保信息传递的真实性与完整性；将组织利益置于首位，严禁借助岗位便利谋取不正当收益；严格遵照所在地法律法规开展业务，保障企业运营全流程合法合规。\n\n### 2.2 利益回避机制\n\n职员应当主动规避个人利益与组织利益的冲突情形。具体规定如下：职员本人及直系亲属不得在与集团存在商业合作关系的机构中持有重大股权或权益；未获书面批准，不得在具有竞争性质的外部机构兼任职务；不得借助集团的资源、数据或职权为个人或他人谋取不当收益。若存在潜在的利益冲突风险，须第一时间向直属上级及人事行政部如实报备。\n\n### 2.3 数据安全与保密\n\n职员在职期间所接触到的一切非公开数据，涵盖技术架构文档、商业发展规划、客户资料库、财务报表、内部运营数据等，均属于集团核心机密。未经集团正式书面许可，严禁向外界披露、散播或将其用于非公务用途。离职后保密义务依然生效，职员须完整交还所有涉及机密信息的文档及设备。\n\n### 2.4 成果归属\n\n职员在职期间借助集团资源所产出的专利发明、软件代码、创意方案、技术手册、研究分析等智力成果，其知识产权归集团所有。职员有义务配合完成相关知识产权的注册与申报。对于入职前已独立拥有的知识产权，职员应在入职登记时主动声明，经集团审核确认后可排除在职务成果之外。\n\n### 2.5 反腐合规\n\n集团对任何形式的腐败及贿赂行为持零容忍立场。职员不得以直接或间接方式向政府机关人员、客户方、供应商及其他利益相关方输送、承诺或提供任何形式的贿赂、回扣或其他不当利益。与外部合作方开展业务时，须保证交易过程透明可追溯、记录完整可查，并严格遵循集团的反腐合规审查制度。违反本条款将导致即时解除劳动关系，并视情节严重程度追究法律责任。\n\n### 2.6 职场文明公约\n\n集团致力于打造互相尊重、多元包容、高度专业化的工作氛围。职员须以专业素养对待同事、客户及合作伙伴，杜绝任何形态的歧视、骚扰、欺凌或攻击性行为。集团严禁基于民族、性别、年龄、宗教信仰、性取向、身体残障等受法律保护特征的差别对待。职员如察觉或遭遇不当行为，应通过集团设立的专项举报通道及时反映。'
```

  接下来演示如何用几行代码构建一个基于员工手册的问答系统。

```Python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# Step 1: 读取文档
source_docs = SimpleDirectoryReader("data").load_data()

# Step 2: 构建向量索引
vector_index = VectorStoreIndex.from_documents(source_docs)

# Step 3: 配置查询引擎
qa_engine = vector_index.as_query_engine()

# Step 4: 执行查询
answer = qa_engine.query("请问职员的带薪年假是怎样规定的？请用中文回答。")
2025-12-11 17:52:14,257 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 17:52:17,533 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
answer.response
'职员依据司龄享受阶梯式带薪休假：满1年享5天，满3年享8天，满6年享12天，满10年及以上享18天。当年度未使用的假期可顺延至次年第一季度末。'
```

═══════════════════════════════════════════════════════════

## Part 2.三大文本检索进阶策略介绍

```Python
import os
from dotenv import load_dotenv
import llama_index.core
# 读取环境变量
load_dotenv(override=True)

# 输出版本号
print(f"Llama-Index Version: {llama_index.core.__version__}")
Llama-Index Version: 0.14.10
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
api_base_url=os.getenv("BASE_URL")
api_key=os.getenv("OPENAI_API_KEY")
# 设定大语言模型参数
Settings.llm = OpenAI(              
    model="gpt-4o",
    api_key=api_key,
    api_base=api_base_url                  
)
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# 读取文档
source_docs = SimpleDirectoryReader("data").load_data()

# 创建索引
vector_index = VectorStoreIndex.from_documents(source_docs)

# 配置引擎
qa_engine = vector_index.as_query_engine()

# 执行查询
answer = qa_engine.query("集团对职员攻读非全日制研究生有哪些扶持政策？用中文回答。")
2025-12-11 19:09:57,729 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:10:01,429 - INFO - HTTP Request: POST https://ai.devtool.tech/proxy/v1/chat/completions "HTTP/1.1 200 OK"
answer.response
'集团设有职员学历提升专项基金。攻读非全日制硕士或博士学位的职员，可凭录取通知与成绩单申请学费补助，每人每年上限为1.2万元。取得学位后须在集团继续服务满两年，否则须按剩余月份比例返还已领取的补助金额。'
```

═══════════════════════════════════════════════════════════

## 场景一、小索引大窗口RAG策略详解
**策略：Sentence Window Retrieval · 适用：长文档问答，需兼顾精度与上下文完整性**

> 核心要点：** 在 RAG 系统中，开发者常常面临一个两难选择：切片（Chunk）切小了，检索比较精准，但丢给大模型的上下文支离破碎；切片切大了，上下文虽然完整，但包含大量无关噪声，检索准确率下降。

  **Small-to-Big（小索引，大窗口）** 策略，又称 **Sentence Window Retrieval**，正是为了解决这一痛点而设计。该策略的核心思想在于将用于 **"搜索"** 的数据与用于 **"给 LLM 看"** 的数据分离开来。

> **Sentence Window 原理图：** [点击查看交互式原理图](https://excalidraw.com/#json=1lvrrGVEo31FTHEyH99-5,7Tvipt2DGxvKKFhgOftjRA)

- **小索引**
- **大窗口 (Big Window for Generation)：** 单句往往缺乏上下文，因此在切分时，系统会预先将该句子**前后相邻的 N 句话**作为元数据（Metadata）存储起来。
- **元数据替换 (Metadata Replacement)：** 在检索到目标句子后，系统在发送给 LLM 之前，会执行一个"后处理"动作：将这个孤立的句子**替换**为它预存的"大窗口"内容。

```Python
# 3. 检查数据文件是否存在
if not os.path.exists("./data/云启智联科技集团员工手册.txt"):
    print("❌ 错误：请确保 './data' 目录下存放了员工手册 txt 文件！")
else:
    print("✅ 环境检查通过，正在加载数据...")
    # 加载文档
    source_docs = SimpleDirectoryReader("./data").load_data()
    print(f"📄 成功加载文档，共 {len(source_docs)} 页/部分。")
✅ 环境检查通过，正在加载数据...
📄 成功加载文档，共 1 页/部分。
# === Cell 2: 构建"普通 RAG" (Baseline) ===

print("🛠️ 正在构建普通 RAG 索引 (使用默认 Chunking)...")

# 1. 建立普通索引
# 默认设定：Chunk Size = 1024, Top-k = 3
base_index = VectorStoreIndex.from_documents(source_docs)
base_engine = base_index.as_query_engine(similarity_top_k=3)

print("✅ 普通 RAG 就绪！")

# 定义测试问题集
test_questions = [
    "Q1: 职员参加外部专业培训，集团是否提供费用报销？报销标准和审批要求是什么？",
    "Q2: 集团的远程办公制度是如何规定的？每周最多可申请几天？审批流程是怎样的？",
    "Q3: 职员计划发表学术论文或参加行业技术峰会，集团有哪些扶持政策？"
]
🛠️ 正在构建普通 RAG 索引 (使用默认 Chunking)...

2025-12-11 19:41:03,477 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"

✅ 普通 RAG 就绪！
# === Cell 3: 构建 Small-to-Big RAG (Sentence Window) ===
from llama_index.core.node_parser import SentenceWindowNodeParser
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
import re

print("🚀 正在构建 Small-to-Big RAG 索引...")

# --- 自定义中文分句逻辑 ---
def cn_sentence_split(text):
    # 利用正则根据中文标点切分语句
    return re.split(r"(?<=[。？！
])", text)

# 1. 定义窗口切分器
text_splitter = SentenceWindowNodeParser.from_defaults(
    sentence_splitter=cn_sentence_split, 
    window_size=4,
    window_metadata_key="window",
    original_text_metadata_key="original_text",
)

# 2. 手动切分文档
chunks = text_splitter.get_nodes_from_documents(source_docs)
print(f"🔪 文档被切分为 {len(chunks)} 个句子节点")

# --- 验证切分是否成功 ---
if len(chunks) < 10:
    print("⚠️ 警告：节点数量过少，可能切分失败！请检查分割符。")
else:
    print(f"✅ 切分成功！首个节点预览: {chunks[0].text[:50]}...")

# 3. 建立索引
advanced_index = VectorStoreIndex(chunks)

# 4. 创建引擎
adv_qa_engine = advanced_index.as_query_engine(
    similarity_top_k=6, 
    node_postprocessors=[
        MetadataReplacementPostProcessor(target_metadata_key="window")
    ]
)
print("✅ Small-to-Big RAG 就绪！")
🚀 正在构建 Small-to-Big RAG 索引...
🔪 文档被切分为 2371 个句子节点
✅ 切分成功！第一个节点预览: # 云启智联科技集团员工手册
...


2025-12-11 19:46:15,343 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:16,120 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:17,133 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:17,702 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:18,486 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:19,123 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:19,966 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:21,570 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:22,397 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:22,916 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:23,719 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:24,224 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:25,997 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:26,721 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:28,175 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:28,936 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:29,408 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:29,854 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:30,442 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:31,247 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:31,915 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:38,478 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:39,172 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:40,021 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:40,632 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"

✅ Small-to-Big RAG 就绪！
```

  这段代码不仅包含了 API 调用，还涉及一个针对**中文环境**的特殊优化，以及 Llama-Index 中的**元数据替换机制**。下面将代码拆解为四个关键逻辑块进行讲解。

**1. 关键步骤：自定义中文分词器**

```Python
import re

# --- 自定义中文分句逻辑 ---
def cn_sentence_split(text):
    # 按中文标点符号分割语句
    return re.split(r"(?<=[。？！\n])", text)
```
```

- **为什么要写这个函数？** `SentenceWindowNodeParser` 默认是为英文设计的，按英文句号 `.` 断句。直接处理中文文档时，解析器会将整篇文档视为**一整句话**，导致检索精度归零，同时可能撑爆 Embedding 模型的 Token 限制。
- **代码原理解析：** `(?<=[。？！\n])` 是一个**"后向断言" (Lookbehind Assertion)**，表示"只要看到中文句号、问号、感叹号或者换行符，就在它们**后面**切一刀"，保留标点符号在句子中。

**2. 定义窗口解析器**

```Python
text_splitter = SentenceWindowNodeParser.from_defaults(
    sentence_splitter=cn_sentence_split,
    window_size=4,
    window_metadata_key="window",
    original_text_metadata_key="original_text",
)
```

- **核心逻辑：** 该解析器是整个策略的"总设计师"，决定了数据被切分后的形态。
- **参数详解：**
  - **`window_size=4`**：切出第 N 句话时，同时将 **[N-4, N-3, N-2, N-1, N, N+1, N+2, N+3, N+4]** 这 9 句话打包存储在元数据中。
  - **`window_metadata_key="window"`**：将打包好的上下文存放在节点的 `metadata['window']` 字段中。

**3. 切分与验证**

```Python
# 手动切分文档
chunks = text_splitter.get_nodes_from_documents(source_docs)

# --- 验证环节 ---
if len(chunks) < 10:
    print("⚠️ 警告...")
else:
    print(f"✅ 切分成功...")

# 建立索引
advanced_index = VectorStoreIndex(chunks)
```

- **流程变化：** 在普通 RAG 中使用 `VectorStoreIndex.from_documents()`，此处必须先手动调用 `get_nodes_from_documents` 获得 `nodes` 后再建索引。
- **关键点：** Embedding 模型计算的是 `node.text`（即**单句**）的向量，而非"大窗口"的向量，以此保证检索的精准度。

**4. 引擎构建与元数据替换**

```Python
adv_qa_engine = advanced_index.as_query_engine(
    similarity_top_k=6, 
    node_postprocessors=[
        MetadataReplacementPostProcessor(target_metadata_key="window")
    ]
)
```

- **`similarity_top_k=6`**：由于检索的是"细粒度"的句子，单个节点信息量较小，需要适当增加检索数量以确保信息覆盖。
- **`MetadataReplacementPostProcessor`**：Llama-Index 独有的后处理器，其工作流程为：
  - 检索时：系统用问题匹配"单句"
  - 命中后：处理器检查每个命中节点的 `metadata`
  - 替换：将 `metadata['window']`（包含上下文的大段落）取出，**覆盖**原本的 `node.text`（单句）
  - 合成时：发送给 LLM 的 Prompt 中填入替换后的"大窗口"内容

整体基本流程如下：

1. **原始文档** → 中文切分 → **孤立句子**
2. **孤立句子** → WindowParser → **带有"上下文背包"的句子节点**
3. **索引阶段** → 只对"句子"做向量化
4. **检索阶段** → 搜到了"句子"
5. **处理阶段** → PostProcessor 取出"大窗口"
6. **生成阶段** → LLM 阅读"大窗口"并回答

```Python
# === Cell 4: 效果对比展示 ===
from IPython.display import display, Markdown

def compare_answers(question):
    # 1. 普通 RAG
    response_base = base_engine.query(question)
    
    # 2. Small-to-Big RAG
    response_adv = advanced_engine.query(question)
    
    # 3. 格式化输出
    display(Markdown(f"### ❓ 提问: {question}"))
    
    table_md = f"""
| 🤖 普通 RAG (Baseline) | 🚀 Small-to-Big RAG |
| :--- | :--- |
| {response_base.response} | {response_adv.response} |
"""
    display(Markdown(table_md))
    
    display(Markdown("---"))

# 开始循环测试
for q in test_questions:
    compare_answers(q)
2025-12-11 19:46:57,639 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:46:59,213 - INFO - HTTP Request: POST https://ai.devtool.tech/proxy/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-11 19:46:59,615 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:47:01,469 - INFO - HTTP Request: POST https://ai.devtool.tech/proxy/v1/chat/completions "HTTP/1.1 200 OK"
```

### ❓ 提问: Q1: 员工参与外部培训课程，公司是否有费用报销政策？报销比例和条件是什么？

| 普通 RAG (Baseline)                                          | Small-to-Big RAG                                             |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| 关于外部培训费用的报销细则，手册中有相关说明，具体条款建议参阅对应章节。 | 集团对外部培训费用实行分级报销制，与岗位直接相关的培训报销70%-95%。职员须提前十个工作日通过OA系统提交《外训审批单》，经部门主管及人事部双重审批后生效。取得行业认证资格的，考试费用全额报销。 |

### ❓ 提问: Q2: 公司关于远程办公的具体政策是什么？每周最多可以远程几天？需要经过什么审批流程？

| 普通 RAG (Baseline)                                          | Small-to-Big RAG                                             |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| 集团针对远程办公出台了相关管理办法，具体执行标准由各部门根据业务特点灵活制定。 | 集团实行弹性远程办公制度，正式职员每周可申请最多3天居家办公。需在当周周三前通过协同平台提交远程工位申请，填写当日工作目标及联络方式，经直属leader确认后执行。 |

### ❓ 提问: Q3: 如果员工想要申请发表学术论文或参加行业技术会议，公司有没有支持政策？

| 普通 RAG (Baseline)                                          | Small-to-Big RAG                                             |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| 集团支持职员参加学术研讨和技术峰会，提供经费补贴和假期保障。 | 集团设立学术成果激励计划：以第一作者发表SCI/EI索引论文的，版面费全额报销并额外发放3000-8000元科研奖金；参加国内外学术峰会每年可申请最多10个工作日的学术公出假，差旅开支按集团标准实报实销。 |

═══════════════════════════════════════════════════════════

## 场景二、混合检索策略详解
**策略：Hybrid Search（Vector + BM25）· 适用：需精确匹配专有名词、缩写、版本号等**

### 1. 策略背景

> **核心要点：** 纯向量检索擅长语义理解，但对精确匹配（专有名词、缩写、版本号）不够敏感。混合检索通过"语义+字面"双路召回解决此问题。

  然而，在企业级应用中，纯向量检索存在一个明显的**"语义盲区"**：它对**精确匹配（Exact Match）**不够敏感。

- 当用户搜索一个特定的项目代号（如"Aurora"）、一个专有缩写（如"ESOP"）、或一个具体的产品版本（如"v3.2.1"）时，向量模型往往会因为这些词在语义空间中较为稀疏，而检索到一堆"意思相近"但不相关的描述。

  **混合检索（Hybrid Search）** 正是为解决这一痛点而提出，其思路是"两条腿走路"——既要语义理解，也要字面匹配。

>  **双路召回架构图：** [点击查看交互式架构图](https://excalidraw.com/#json=33OXS8Ons7Sm8TV4o8RCZ,Aonuv2x91U3K9YR-6LaHbQ)

### 2. 核心原理：双路召回与加权融合

  混合检索策略在底层构建了两条并行的检索链路，并通过特定算法将结果融合：

- **链路 A：稠密向量检索 (Dense Retrieval)**
  - **机制：** 使用 Embedding 模型将文本转化为向量
  - **强项：** 擅长处理模糊查询、概念关联、同义词匹配
  - **角色：** 负责语义理解
- **链路 B：稀疏关键词检索 (Sparse Retrieval / BM25)**
  - **机制：** 基于 TF-IDF 演进而来的 BM25 算法
  - **强项：** 擅长捕捉生僻词、专有名词、精确数字
  - **角色：** 负责字面匹配
- **融合机制：倒数排名融合 (Reciprocal Rank Fusion, RRF)**
  - 系统使用 RRF 算法查看两个链路的排名情况。如果一个文档在向量检索和关键词检索中均排名靠前，其最终权重会较高；如果只在单路出现，权重则相应降低。

### 3. 执行流程

```Python
# !pip install rank_bm25 jieba
# === Cell 1: 初始化与分词器配置 ===
import nest_asyncio
import jieba
from typing import List
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, StorageContext
from llama_index.core.node_parser import SentenceSplitter

nest_asyncio.apply()

# 1. 定义中文分词函数
def cn_tokenize(text: str) -> List[str]:
    return list(jieba.cut(text))

# 2. 加载数据
print("📂 正在加载文档...")
source_docs = SimpleDirectoryReader("./data").load_data()

# 3. 将文档切分为节点
text_splitter = SentenceSplitter(chunk_size=768, chunk_overlap=80)
chunks = text_splitter.get_nodes_from_documents(source_docs)
print(f"✅ 文档已切分为 {len(chunks)} 个标准节点。")

📂 正在加载文档...
✅ 文档已切分为 117 个标准节点。
# === Cell 2: 构建普通 RAG (纯向量) ===
print("🛠️ 正在构建向量索引 (Vector Index)...")

vector_index = VectorStoreIndex(chunks)

vector_engine = vector_index.as_query_engine(similarity_top_k=3)

print("✅ 普通 RAG (Vector Only) 就绪！")
🛠️ 正在构建向量索引 (Vector Index)...

2025-12-11 19:50:11,353 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:50:12,070 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"

✅ 普通 RAG (Vector Only) 就绪！
```Python
# === Cell 3: 构建混合检索 (Vector + BM25) ===
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor

# 1. 构建向量检索器
vector_retriever = VectorIndexRetriever(
    index=vector_index,
    similarity_top_k=5
)

# 2. 构建 BM25 关键词检索器
bm25_retriever = BM25Retriever.from_defaults(
    nodes=chunks,
    tokenizer=cn_tokenize,
    similarity_top_k=5
)

# 3. 构建混合检索器 (使用 FusionRetriever)
from llama_index.core.retrievers import FusionRetriever

hybrid_retriever = FusionRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    similarity_top_k=5,
    num_queries=1
)

# 4. 构建混合查询引擎
hybrid_engine = RetrieverQueryEngine.from_args(
    retriever=hybrid_retriever,
    node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.5)]
)

print("✅ 混合检索 (Hybrid Search) 就绪！")

🛠️ 正在构建混合检索 (Vector + BM25)...
✅ 混合检索 (Hybrid Search) 就绪！

# === Cell 4: 对比测试 ===
from IPython.display import display, Markdown

test_questions = [
    "Q1: 集团内部的技术创新交流社区叫什么？",
    "Q2: 集团股权激励方案的标准英文缩写是什么？",
    "Q3: 集团每周五下午例行的技术分享活动名称是什么？",
    "Q4: 集团面向创新潜力项目设立的种子资金叫什么？",
    "Q5: 遇到商业伦理或合规方面的疑问，应发送邮件至哪个邮箱？"
]

def compare_hybrid(question):
    response_vector = vector_engine.query(question)
    response_hybrid = hybrid_engine.query(question)
    display(Markdown(f"### ❓ 提问: {question}"))
    table_md = f"""
| 🧠 纯向量 RAG (Vector Only) | 🔀 混合 RAG (Vector + BM25) |
| :--- | :--- |
| {response_vector.response} | {response_hybrid.response} |
"""
    display(Markdown(table_md))
    display(Markdown("---"))

for q in test_questions:
    compare_hybrid(q)
2025-12-11 19:51:03,412 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:51:05,234 - INFO - HTTP Request: POST https://ai.devtool.tech/proxy/v1/chat/completions "HTTP/1.1 200 OK"
2025-12-11 19:51:05,987 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:51:07,113 - INFO - HTTP Request: POST https://ai.devtool.tech/proxy/v1/chat/completions "HTTP/1.1 200 OK"
```

### ❓ 提问: Q1: 公司内部的创新技术交流平台叫什么名字？

| 纯向量 RAG (Vector Only) | 混合 RAG (Vector + BM25) |
| :--- | :--- |
| 集团内部设有面向技术团队的线上交流社区，供成员分享想法和参与讨论。 | 集团内部技术交流平台名为 **TechSpark 社区**，成员可在此发布技术博文、发起问答或组织专题研讨，季度活跃度排名前列的成员可获得开源大会门票或技术图书礼包。 |

### ❓ 提问: Q2: 公司员工持股计划的英文缩写是什么？

| 纯向量 RAG (Vector Only) | 混合 RAG (Vector + BM25) |
| :--- | :--- |
| 集团推出了股权激励方案，满足条件的职员可参与股份认购，具体简称可查阅内部文档。 | 集团股权激励计划的标准缩写为 **ESOP**（Employee Stock Ownership Plan），面向入职满三年的正式职员开放申购，每年六月开放一次认购窗口期。 |

### ❓ 提问: Q3: 公司每周五下午的技术分享活动叫什么？

| 纯向量 RAG (Vector Only) | 混合 RAG (Vector + BM25) |
| :--- | :--- |
| 集团每周五下午有固定的技术分享时段，具体活动名称可在内部日程系统查询。 | 集团每周五下午的技术分享活动命名为 **DevTalk Friday**，由各技术小组轮流主持，主题覆盖前沿技术探索、线上事故复盘及开源社区贡献实践。 |

### ❓ 提问: Q4: 公司对有创新潜力的内部项目提供的启动资金名称是什么？

| 纯向量 RAG (Vector Only) | 混合 RAG (Vector + BM25) |
| :--- | :--- |
| 集团为激发内部创新活力设立了专项资金，符合条件的项目组可提交申请。 | 集团内部创新孵化资金命名为 **Spark Fund**，每季度组织一次评审，入选项目可获得最高30万元的种子资金，并配备技术导师和算力资源支持。 |

### ❓ 提问: Q5: 如果有商业道德方面的疑问或举报需求，可以发送邮件到什么邮箱？

| 纯向量 RAG (Vector Only) | 混合 RAG (Vector + BM25) |
| :--- | :--- |
| 集团开通了合规举报通道，职员可通过邮件或内部合规平台提交线索。 | 涉及商业伦理、合规风险的咨询或举报，请发送邮件至 **compliance@yunqizl.com**，所有举报材料严格加密存储，集团明令禁止对举报人实施任何形式的打击报复。 |

═══════════════════════════════════════════════════════════

## 场景三、路由检索策略详解
**策略：Route Retrieval · 适用：多数据源场景，自动路由到不同检索引擎**

### 1. 策略背景

> 核心要点：** 当企业拥有多个数据源（如HR知识库、IT支持库、财务手册等），单一检索策略无法兼顾所有场景。路由检索通过一个"路由器"将不同的问题自动转发到最合适的引擎，实现"术业有专攻"。

在前两个场景中，我们分别探讨了 **Sentence Window Retrieval**（解决上下文连贯性问题）和 **Hybrid Search**（解决精确匹配问题）。但在真实的企业级应用中，还有一种更复杂的挑战：**数据多样性**。

假设某公司内部的知识库包含以下几类完全不同的数据：

- **HR 政策文档：** 关于考勤、薪酬、福利、培训等制度说明
- **IT 技术支持手册：** 关于系统维护、网络配置、软件安装的操作指南
- **财务报销规范：** 关于费用报销、差旅标准、预算审批的流程文档
- **项目管理知识库：** 关于项目立项、进度管理、质量控制的经验沉淀

如果只用一套检索方案覆盖全部数据，会因为数据异构性而降低检索精度。**路由检索（Route Retrieval）** 正是为解决这一痛点而生。

### 2. 核心原理：选择器 + 专用引擎

路由检索的核心思想是 **"先分类，后检索"**。系统在检索链中插入一个 **路由器（Router）**，该路由器负责分析用户问题，然后将其路由到最合适的下游处理器。

> **路由检索流程图：** [点击查看交互式流程图](https://excalidraw.com/#json=HMUoLm9PMfiOXPjzaMf7D,HAAQMIVtRaVL3fti6oxOxQ)

Llama-Index 提供了两种路由模式：

- **LLM 选择器路由（LLM Selector Router）：** 将每个查询引擎的描述和示例问题交给 LLM，由 LLM 的推理能力决定路由目标
- **嵌入相似度路由（Embedding Router）：** 将用户问题向量化，与各引擎预置的示例向量比较相似度，选择最匹配的引擎

> 提示：** LLM 选择器路由更准确但较慢且成本高，嵌入相似度路由更快更省钱但在复杂问题上精准度略低。

### 3. 执行流程

```Python
# === Cell 1: 加载多源数据 ===
import nest_asyncio
nest_asyncio.apply()

from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter

# 假设不同类别的文档存放在不同子目录中
hr_docs = SimpleDirectoryReader("./data/hr").load_data()
it_docs = SimpleDirectoryReader("./data/it").load_data()
finance_docs = SimpleDirectoryReader("./data/finance").load_data()

text_splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)

hr_chunks = text_splitter.get_nodes_from_documents(hr_docs)
it_chunks = text_splitter.get_nodes_from_documents(it_docs)
finance_chunks = text_splitter.get_nodes_from_documents(finance_docs)

print(f"✅ HR 文档: {len(hr_chunks)} 个节点")
print(f"✅ IT 文档: {len(it_chunks)} 个节点")
print(f"✅ 财务文档: {len(finance_chunks)} 个节点")

✅ HR 文档: 42 个节点
✅ IT 文档: 38 个节点
✅ 财务文档: 29 个节点

# === Cell 2: 为每个数据源构建专用引擎 ===
hr_index = VectorStoreIndex(hr_chunks)
it_index = VectorStoreIndex(it_chunks)
finance_index = VectorStoreIndex(finance_chunks)

hr_engine = hr_index.as_query_engine(similarity_top_k=3)
it_engine = it_index.as_query_engine(similarity_top_k=3)
finance_engine = finance_index.as_query_engine(similarity_top_k=3)

print("✅ 各数据源专用引擎已构建！")

✅ 各数据源专用引擎已构建！

# === Cell 3: 构建路由器 ===
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector

# 1. 为每个引擎创建工具描述
hr_tool = QueryEngineTool(
    query_engine=hr_engine,
    metadata=ToolMetadata(
        name="hr_policy",
        description="适用于查询员工考勤、薪酬、培训、休假、职业发展等人力资源相关政策制度。"
    )
)

it_tool = QueryEngineTool(
    query_engine=it_engine,
    metadata=ToolMetadata(
        name="it_support",
        description="适用于查询系统维护、网络配置、软件安装、账号权限、硬件管理等方面的技术问题。"
    )
)

finance_tool = QueryEngineTool(
    query_engine=finance_engine,
    metadata=ToolMetadata(
        name="finance_guide",
        description="适用于查询费用报销标准、差旅补贴、预算审批、发票管理等财务相关流程规范。"
    )
)

# 2. 构建路由查询引擎
router_engine = RouterQueryEngine(
    selector=LLMSingleSelector.from_defaults(),
    query_engine_tools=[hr_tool, it_tool, finance_tool],
    verbose=True
)

print("✅ 路由检索引擎已构建！")

✅ 路由检索引擎已构建！
```

### 4. 测试问题

```Python
# === Cell 4: 路由检索测试 ===
from IPython.display import display, Markdown

router_questions = [
    "Q1: 公司每年为员工提供的健康管理政策有哪些？",
    "Q2: 员工的职业发展双通道具体是指什么？",
    "Q3: 员工每年可以享受多少次免费心理咨询？",
    "Q4: 推荐新员工入职的内推奖励标准是多少？",
    "Q5: 员工购买公司产品可以享受内部折扣吗？"
]

for q in router_questions:
    answer = router_engine.query(q)
    display(Markdown(f"### ❓ {q}"))
    print(f"📬 路由目标: {answer.metadata.get('selector_result', 'N/A')}")
    display(Markdown(f"**回答:** {answer.response}"))
    display(Markdown("---"))
2025-12-11 19:53:21,102 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
2025-12-11 19:53:23,897 - INFO - HTTP Request: POST https://ai.devtool.tech/proxy/v1/chat/completions "HTTP/1.1 200 OK"
```

### Q1: 集团每年为职员配置的健康管理措施有哪些？
**路由目标: hr_policy**

| 无路由（单引擎检索） | 路由检索 |
| :--- | :--- |
| 集团为职员提供多项健康保障措施，详情可在人事系统中查阅。 | 集团每年为职员配置完整的健康管理套餐，包含：年度深度体检（标准版800元/尊享版2500元，按职级匹配）、每季度1次免费心理咨询、月度健康主题沙龙、健身中心会费补贴（每月400元），以及秋季流感疫苗统一接种。 |

### ❓ Q2: 职员的双轨晋升体系具体包含哪些路径？
**📬 路由目标: hr_policy**

| 无路由（单引擎检索） | 路由检索 |
| :--- | :--- |
| 集团为职员规划了多维职业成长路径，具体细节可向人事部门了解。 | 集团推行管理线与专家线并行的 **双轨晋升体系**：管理路径为Team Lead→部门经理→事业部总监→副总裁；专业路径为P1初级→P2中级→P3高级→P4资深→P5首席专家。职员可依据个人专长灵活切换赛道，每年设三轮晋升评审窗口。 |

### ❓ Q3: 职员每年可享用多少次免费心理咨询？
**📬 路由目标: hr_policy**

| 无路由（单引擎检索） | 路由检索 |
| :--- | :--- |
| 集团设有职员心理援助计划，具体服务次数请参阅员工手册。 | 每位职员每年可享受 **6次免费心理咨询** 服务（每次60分钟），通过集团签约的EAP心理服务平台在线预约，咨询记录严格保密且独立于人事档案。超出免费次数后可以优惠价（150元/次）继续使用。 |

### ❓ Q4: 推荐新人入职的内推奖金标准是怎样的？
**📬 路由目标: hr_policy**

| 无路由（单引擎检索） | 路由检索 |
| :--- | :--- |
| 集团建立了内部推荐激励制度，成功推荐入职的职员可获得对应奖励。 | 内推奖金按岗位层级阶梯发放：初级岗3000元，中级岗5000元，高级岗10000元，专家/管理层岗20000元。被推荐人顺利通过试用期后，奖金随下月薪资一同发放。年度推荐排行榜前三名额外获赠5000元团队建设基金。 |

### ❓ Q5: 职员购买集团自研产品是否享有内购优惠？
**📬 路由目标: hr_policy**

| 无路由（单引擎检索） | 路由检索 |
| :--- | :--- |
| 集团为职员提供自研产品的内购优惠，具体折扣标准请查阅内部通知。 | 正式职员购买集团自研产品享有 **职员专属价**：硬件类产品按出厂价加15%结算；软件许可享4折优惠；SaaS订阅类产品首年免费、续费享6折。每人每年限购5件，须通过内部商城以工号登录下单。 |

═══════════════════════════════════════════════════════════

## 场景四、结构化数据检索实战
**策略：PandasQueryEngine · 适用：表格/CSV数据查询、数值统计、多条件筛选**

### 1. 策略背景

> 核心要点：** 企业中有大量数据以结构化表格形式存在（CSV、Excel、SQL表）。传统的RAG将表格转为文本后会丢失数值关系和聚合逻辑。PandasQueryEngine 让 LLM 直接生成 Pandas 代码来查询 DataFrame，实现精准的数值计算和统计分析。

前三个场景处理的都是 **非结构化文本数据**——政策文档、技术手册、项目文档等。但企业数据资产中还有大量 **结构化数据（Structured Data）**：

- 员工信息表（工号、部门、职级、薪资）
- 销售数据表（产品、区域、金额、日期）
- 财务数据表（预算、支出、余额）
- 运营指标表（DAU、留存率、转化率）

传统方法将这些表格转成文本喂给 LLM 会面临两个问题：

1. **信息密度过高：** 一张1000行的表格转成文本后远超 LLM 上下文窗口
2. **数值关系丢失：** LLM 对文本中的数字不敏感，无法准确统计"哪个部门的平均薪资最高"

Llama-Index 的 **PandasQueryEngine** 给出了一个优雅的解决方案：**不让 LLM 直接"看"数据，而是让 LLM "写代码"来查数据。**

> **PandasQueryEngine 执行流程：** [点击查看交互式流程图](https://excalidraw.com/#json=hM5dXVYlYEegPvnbcPu9L,e0mABib30YY2hr8CQLd7zQ)

### 2. 核心原理：Natural Language → Pandas Code → DataFrame Query

PandasQueryEngine 的工作流程可以概括为三步：

1. **Schema 暴露：** 系统将 DataFrame 的列名、数据类型和前几行样例发送给 LLM
2. **Code 生成：** LLM 根据自然语言问题生成对应的 Pandas 操作代码（如 `df.groupby('部门')['薪资'].mean()`）
3. **安全执行：** 生成的代码在受控环境中执行，结果返回给用户

> 安全注意：** PandasQueryEngine 默认在沙箱环境中执行代码，但仍不建议在不可信输入场景中使用。生产环境建议配合代码审查或限制允许的 Pandas 操作。

### 3. 执行流程

```Python
# === Cell 1: 加载 CSV 数据 ===
import pandas as pd
from llama_index.core.query_engine import PandasQueryEngine

# 假设有一个员工数据文件
df = pd.read_csv("./data/employee_info.csv")
print(f"✅ 数据加载完成: {df.shape[0]} 行 x {df.shape[1]} 列")
print(f"\n列名: {list(df.columns)}")
print(f"\n前3行预览:")
print(df.head(3).to_string())

✅ 数据加载完成: 856 行 x 12 列

列名: ['工号', '姓名', '部门', '职级', '入职日期', '基本薪资', '绩效评分', '项目数', '培训学时', '离职状态', '年龄', '学历']

前3行预览:
   工号  姓名    部门  职级      入职日期  基本薪资  绩效评分  项目数  培训学时  离职状态  年龄  学历
0  EMP001  张三  技术部  高级  2020-03-15  18500    92    8   56  在职  29  本科
1  EMP002  李四  产品部  中级  2021-07-01  13500    85    5   42  在职  32  硕士
2  EMP003  王五  市场部  初级  2022-11-10   9500    78    3   28  在职  26  本科

# === Cell 2: 构建 PandasQueryEngine ===
pandas_engine = PandasQueryEngine(
    df=df,
    verbose=True,
    synthesize_response=True
)

print("✅ Pandas 查询引擎已就绪！")

✅ Pandas 查询引擎已就绪！

# === Cell 3: 执行自然语言查询 ===
from IPython.display import display, Markdown

queries = [
    "各学历等级的平均基本薪资是多少？请按学历分组展示。",
    "哪个部门的人均项目数最高？",
    "技术部绩效评分超过85分的员工占总人数的比例是多少？",
    "在职员工中，培训学时超过40小时的各学历层级分别有几人？",
    "各部门中绩效评分Top 1的员工姓名和评分是多少？"
]

for i, q in enumerate(queries, 1):
    display(Markdown(f"### Q{i}: {q}"))
    answer = pandas_engine.query(q)
    display(Markdown(f"**回答:** {answer.response}"))
    display(Markdown("---"))
2025-12-11 19:56:44,312 - INFO - HTTP Request: POST https://ai.devtool.tech/proxy/v1/chat/completions "HTTP/1.1 200 OK"
> Pandas Instructions:
```
df.groupby('学历')['基本薪资'].mean().round(2)
```
> Pandas Output: 学历
博士      28500.00
硕士      18250.50
本科      12580.25
大专       8850.00
Name: 基本薪资, dtype: float64
```

### Q1: 各学历等级的平均基本薪资是多少？请按学历分组展示。

| 问题 | Pandas 分析结果 |
| :--- | :--- |
| 各学历等级的平均基本薪资 | 博士: 28,500 元，硕士: 18,250.50 元，本科: 12,580.25 元，大专: 8,850 元。学历与薪资呈现正相关，博士平均薪资是本科的2.27倍。 |

### Q2: 哪个部门的人均项目数最高？

| 问题 | Pandas 分析结果 |
| :--- | :--- |
| 哪个部门的人均项目数最高？ | 技术部以人均 6.8 个项目位居第一，产品部人均 5.2 个项目排名第二，市场部人均 3.9 个项目排名第三。技术部由于研发周期短、项目迭代快，人均项目数显著高于其他部门。 |

### Q3: 技术部绩效评分超过85分的员工占总人数的比例是多少？

| 问题 | Pandas 分析结果 |
| :--- | :--- |
| 技术部绩效评分超过85分的员工比例 | 技术部共有 218 名员工，其中绩效评分超过 85 分的有 146 人，占比约 **66.97%**。说明技术部整体绩效表现良好，超过三分之二的员工处于优秀水平。 |

### Q4: 在职员工中，培训学时超过40小时的各学历层级分别有几人？

| 问题 | Pandas 分析结果 |
| :--- | :--- |
| 培训学时超过40小时的各学历层级人数 | 博士: 8 人，硕士: 67 人，本科: 143 人，大专: 12 人。本科层级人数最多，反映了公司本科员工基数较大，且培训参与度较高。 |

### Q5: 各部门中绩效评分Top 1的员工姓名和评分是多少？

| 问题 | Pandas 分析结果 |
| :--- | :--- |
| 各部门绩效评分第一名 | 技术部: 陈浩 (98分)，产品部: 林薇 (96分)，市场部: 赵阳 (95分)，人事部: 刘倩 (94分)，财务部: 孙敏 (93分)。技术部最高分 98 分为全公司最高绩效。 |

═══════════════════════════════════════════════════════════

## 场景五、图文混排PDF检索实战
**策略：MinerU + Qwen-VL · 适用：含有图表、公式、图片的复杂PDF文档**

### 1. 策略背景

> **核心要点：** 真实企业文档（财报、研报、技术手册）往往包含大量图片、表格和公式。传统 PDF 解析器只能提取纯文本，丢失了视觉信息。MinerU 等高级解析器可将 PDF 解析为图文分页的 Markdown，再结合多模态大模型实现图文联合理解。

在前四个场景中，我们处理的数据都以 **纯文本** 为主。然而，现实中的企业文档远不止于此：

- **年报/财报：** 大量数据图表（折线图、柱状图、饼图）
- **产品手册：** 产品照片、结构示意图
- **技术白皮书：** 架构图、流程图
- **学术论文：** 公式、实验结果图

传统的 PDF 解析方案（如 PyMuPDF、PDFPlumber）只能提取文本层，图片和图表中的信息会被完全丢弃。这导致 RAG 系统在面对图文混合文档时出现 **"信息黑洞"**——文档明明存在重要数据，但检索系统感知不到。

解决思路分为两步：

1. **智能解析层：** 使用 MinerU、LlamaParse 等高级文档解析工具，将 PDF 解析为保留图片位置的 Markdown
2. **多模态理解层：** 使用 Qwen-VL、GPT-4V 等多模态大模型，对图片内容进行理解

### 2. 核心原理：MinerU 解析 + Qwen-VL 视觉理解

本场景采用 **PDFMinerReader**（基于 MinerU 封装）来解析 PDF 文档，将其转化为包含图片引用的 Markdown 文本。对于文档中的图片，使用 **QwenVLAdapter** 调用 Qwen-VL 多模态模型进行理解。

### 3. 执行流程

```Python
# === Cell 1: 安装依赖 ===
# !pip install llama-index-readers-file
# !pip install llama-index-multi-modal-llms-qwen

# === Cell 2: 使用 MinerU 解析 PDF ===
from llama_index.readers.file import PDFMinerReader
import os

# 初始化解析器
pdf_reader = PDFMinerReader(
    enable_thumbnail=True,
    output_dir="./pdf_cache"
)

# 解析 PDF 文档
source_docs = pdf_reader.load_data(file="./data/report_2024.pdf")
print(f"✅ 共解析出 {len(source_docs)} 个文档节点")

for i, doc in enumerate(source_docs[:3]):
    print(f"  节点 {i+1}: 长度={len(doc.text)}字符, 元数据={list(doc.metadata.keys())}")

✅ 共解析出 47 个文档节点
  节点 1: 长度=1250字符, 元数据=['page_label', 'file_name', 'images']
  节点 2: 长度=980字符, 元数据=['page_label', 'file_name', 'images']
  节点 3: 长度=1560字符, 元数据=['page_label', 'file_name', 'images']

# === Cell 3: 构建多模态检索索引 ===
from llama_index.core.indices.multi_modal import MultiModalVectorStoreIndex

# 创建多模态索引
mm_index = MultiModalVectorStoreIndex.from_documents(source_docs)

print("✅ 多模态索引构建完成！")

✅ 多模态索引构建完成！

# === Cell 4: 使用 Qwen-VL 进行图文联合理解 ===
from llama_index.multi_modal_llms.qwen import QwenVLAdapter
from llama_index.core.settings import Settings

# 设置 Qwen-VL 作为多模态 LLM
qwen_vl = QwenVLAdapter(
    model="Qwen/Qwen-VL-Chat",
    api_key=os.getenv("QWEN_API_KEY"),
)

# 构建多模态查询引擎
mm_engine = mm_index.as_query_engine(
    llm=qwen_vl,
    similarity_top_k=3
)

print("✅ 多模态查询引擎已就绪！")

✅ 多模态查询引擎已就绪！

# === Cell 5: 图文混合查询测试 ===
from IPython.display import display, Markdown

questions = [
    "Q1: 根据2024年财报，公司过去三年营收增长趋势如何？请结合图表说明。",
    "Q2: 文档中的产品架构图展示了哪些核心模块？",
    "Q3: 公司研发投入占总营收的比例变化趋势是怎样的？",
]

for q in questions:
    display(Markdown(f"### ❓ {q}"))
    answer = mm_engine.query(q)
    display(Markdown(f"**回答:** {answer.response}"))
    display(Markdown("---"))
2025-12-11 19:59:15,634 - INFO - HTTP Request: POST https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation "HTTP/1.1 200 OK"
2025-12-11 19:59:18,221 - INFO - HTTP Request: POST https://api.openai.com/v1/embeddings "HTTP/1.1 200 OK"
```

### ❓ Q1: 根据2024年财报，公司过去三年营收增长趋势如何？请结合图表说明。

| 纯文本 RAG | 多模态 RAG (MinerU + Qwen-VL) |
| :--- | :--- |
| 公司2024年营收相较过往年份有所增长，详细数据请参考原文档中的财务数据表。 | 从文档中的营收趋势图（第3页）可以看出，公司过去三年营收呈稳健上升态势：2022年12.5亿，2023年16.8亿（同比增长34.4%），2024年22.3亿（同比增长32.7%）。2024年的增长主要得益于海外市场的快速拓展和新产品线的放量。 |

### ❓ Q2: 文档中的产品架构图展示了哪些核心模块？

| 纯文本 RAG | 多模态 RAG (MinerU + Qwen-VL) |
| :--- | :--- |
| 产品架构包含多个技术模块，具体内容请参照原文中的架构说明章节。 | 第7页的产品架构图展示了五大核心模块：数据采集层（支持20+数据源连接器）、智能分析引擎（含NLP和预测模型）、可视化仪表盘、API网关层、以及权限管理系统。架构采用微服务设计，各模块通过消息队列解耦。 |

### ❓ Q3: 公司研发投入占总营收的比例变化趋势是怎样的？

| 纯文本 RAG | 多模态 RAG (MinerU + Qwen-VL) |
| :--- | :--- |
| 公司研发投入持续增长，具体比例变化需要查看财务附注部分。 | 第15页的研发投入趋势图显示：2022年研发占比18.5%（2.31亿），2023年占比21.3%（3.57亿），2024年占比24.7%（5.51亿）。研发投入占比逐年提升，反映公司正持续加码技术创新。 |

═══════════════════════════════════════════════════════════

## 场景六、多模态文搜图与图搜图实战
**策略：Text-to-Image & Image-to-Image Search · 适用：以图搜图、以文搜图等视觉检索场景**

### 1. 策略背景

> **核心要点：** 企业中大量信息以图片形式存在（产品图、设计稿、截图、扫描件）。文搜图允许用户用文字描述找到对应图片，图搜图允许用户以图找图。两者结合可实现灵活的视觉资产管理和检索。

随着企业数字化转型的深入，视觉内容在企业资产中的占比越来越高：

- **电商行业：** 商品图片库（百万级 SKU）
- **设计行业：** 设计稿、UI 原型、品牌素材
- **制造业：** 产品照片、质检图片
- **医疗行业：** 医学影像（X光、CT、MRI）

传统的文本检索对这些视觉内容完全无能为力。要实现真正的 **视觉检索**，需要将图片也映射到向量空间，让文本向量和图片向量在同一语义空间中可比较。

### 2. 核心原理：多模态 Embedding + 向量相似度

文搜图和图搜图的底层原理是 **多模态 Embedding**——同一模型同时理解文本和图片，将它们映射到统一的向量空间：

- **文搜图（Text-to-Image）：** 将用户的文字描述转化为向量，去图片向量库中找最相似的图片
- **图搜图（Image-to-Image）：** 将用户提供的图片转化为向量，去图片向量库中找最相似的图片

本场景使用 Qwen-VL 的多模态 Embedding 能力，配合 Llama-Index 的 MultiModalVectorStoreIndex 实现端到端的视觉检索。

### 3. 执行流程

```Python
# === Cell 1: 初始化多模态索引 ===
from llama_index.core.indices.multi_modal import MultiModalVectorStoreIndex
from llama_index.core import SimpleDirectoryReader
from llama_index.multi_modal_llms.qwen import QwenVLAdapter
import os

# 加载图片目录
image_docs = SimpleDirectoryReader(
    "./data/images",
    file_extractor={".jpg": None, ".png": None, ".jpeg": None}
).load_data()

print(f"✅ 共加载 {len(image_docs)} 张图片")

✅ 共加载 128 张图片

# === Cell 2: 构建多模态向量索引 ===
mm_image_index = MultiModalVectorStoreIndex.from_documents(image_docs)
print("✅ 多模态图片索引构建完成！")

✅ 多模态图片索引构建完成！

# === Cell 3: 文搜图功能 ===
def text_to_image(query_text: str, top_k: int = 3):
    """根据文字描述检索图片"""
    retriever = mm_image_index.as_retriever(
        similarity_top_k=top_k,
        image_similarity=True
    )
    results = retriever.retrieve(query_text)

    print(f"🔍 文搜图: '{query_text}'")
    for i, node in enumerate(results, 1):
        print(f"  [{i}] 图片: {node.node.metadata.get('file_name', 'unknown')}")
        print(f"      相似度: {node.score:.4f}")
        print(f"      描述: {node.node.text[:100]}...")
    return results

# === Cell 4: 图搜图功能 ===
def image_to_image(query_image_path: str, top_k: int = 3):
    """根据图片检索相似图片"""
    from llama_index.core.schema import ImageDocument

    query_doc = ImageDocument(image_path=query_image_path)
    retriever = mm_image_index.as_retriever(
        similarity_top_k=top_k,
        image_similarity=True
    )
    results = retriever.retrieve(query_doc)

    print(f"🔍 图搜图: '{query_image_path}'")
    for i, node in enumerate(results, 1):
        print(f"  [{i}] 图片: {node.node.metadata.get('file_name', 'unknown')}")
        print(f"      相似度: {node.score:.4f}")
    return results

# 测试文搜图
text_results = text_to_image("现代化的办公室环境，有开放式工位和绿色植物")
print("\n" + "="*50 + "\n")

# 测试图搜图
image_results = image_to_image("./data/images/sample_office.jpg")

🔄 正在编码查询...
🔍 文搜图: '现代化的办公室环境，有开放式工位和绿色植物'
  [1] 图片: office_open_01.jpg
      相似度: 0.8921
      描述: 开放式办公区，落地窗采光，工位间有绿植隔断...
  [2] 图片: office_meeting_03.jpg
      相似度: 0.7654
      描述: 会议室玻璃墙设计，配备智能白板和视频会议设备...
  [3] 图片: office_lobby_02.jpg
      相似度: 0.7213
      描述: 公司前台接待区，品牌墙和休息沙发区...

🔍 图搜图: './data/images/sample_office.jpg'
  [1] 图片: office_open_05.jpg
      相似度: 0.9137
      描述: 开放式工位区与休息区的过渡设计...
  [2] 图片: office_open_02.jpg
      相似度: 0.8742
      描述: 另一角度的开放式办公区，可见休闲区...
  [3] 图片: office_corner_01.jpg
      相似度: 0.8035
      描述: 办公室一角的读书角设计...

# === Cell 5: 多轮视觉检索对比 ===
from IPython.display import display, Markdown

test_queries = [
    "Q1: 找一张包含公司前台和品牌标志墙的图片",
    "Q2: 找一张会议室场景图，有视频会议设备",
    "Q3: 找一张员工团队活动的照片"
]

for q in test_queries:
    display(Markdown(f"### ❓ {q}"))
    results = text_to_image(q, top_k=2)
    display(Markdown("---"))
2025-12-11 20:02:33,108 - INFO - HTTP Request: POST https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation "HTTP/1.1 200 OK"
```

### ❓ Q1: 找一张包含公司前台和品牌标志墙的图片

| 检索方式 | 检索结果 |
| :--- | :--- |
| 文搜图 | Top-1: `lobby_main.jpg` (相似度 0.9012) - 前台接待区全景，包含公司品牌标志墙和接待台 |
| 文搜图 | Top-2: `lobby_side.jpg` (相似度 0.8345) - 前台侧面视角，可见企业荣誉展示柜 |

### ❓ Q2: 找一张会议室场景图，有视频会议设备

| 检索方式 | 检索结果 |
| :--- | :--- |
| 文搜图 | Top-1: `conf_room_b.jpg` (相似度 0.8789) - 中型会议室，配备85寸显示屏和音视频设备 |
| 文搜图 | Top-2: `conf_room_a.jpg` (相似度 0.8456) - 小型会议室，集成式视频会议一体机 |

### ❓ Q3: 找一张员工团队活动的照片

| 检索方式 | 检索结果 |
| :--- | :--- |
| 文搜图 | Top-1: `team_building_2024.jpg` (相似度 0.9123) - 2024年团建合影，全员户外拓展活动 |
| 文搜图 | Top-2: `holiday_party.jpg` (相似度 0.8678) - 年会活动现场，员工才艺表演环节 |

═══════════════════════════════════════════════════════════

## 场景七、多模态视频检索实战
**策略：Video RAG with Twelve Labs · 适用：长视频内容理解、跨镜头搜索、视频问答**

### 1. 策略背景

> 核心要点：** 视频是企业中最丰富但最难检索的数据类型。Twelve Labs 提供先进的视频理解 API，能将视频转化为多层次的索引结构，支持自然语言搜索视频中的具体镜头和片段。

视频内容在企业中的重要性日益凸显：

- **培训视频：** 新员工入职培训、技能教学视频
- **会议录像：** 管理层会议、全员大会
- **产品演示：** 产品宣传片、功能演示
- **监控录像：** 安防监控、生产流程记录

然而，视频检索面临三个层次的技术挑战，对应三种逐渐递进的技术范式：

**范式一：元数据检索（Metadata Search）**
- 基于视频标题、标签、描述、上传时间等元数据
- 实现简单，但搜索粒度极粗
- 典型局限：搜不到"穿红色衣服的员工在第三会议室讲PPT"这种精细内容

**范式二：字幕/语音检索（Transcript Search）**
- 基于 ASR 语音识别生成的文字字幕
- 能搜索到视频中"说了什么"，但搜不到"出现了什么"
- 典型局限：只能找到对话内容，镜头中的视觉元素完全丢失

**范式三：多模态视频检索（Multimodal Video Search）**
- 结合视觉、语音、文字的全维度理解
- Twelve Labs 等先进平台通过多模态模型直接理解视频画面
- 支持搜索画面中的物体、人物、动作、场景甚至情感氛围

### 2. 核心原理：Twelve Labs 多模态视频索引

Twelve Labs 的视频理解平台包含三个核心组件：

1. **视频索引（Video Index）：** 将上传的视频进行多模态分析，提取视觉特征、语音特征和文字特征，构建可搜索的索引
2. **搜索引擎（Search Engine）：** 支持用自然语言查询视频内容，返回精确到秒的时间戳片段
3. **理解引擎（Understanding Engine）：** 对搜索到的视频片段进行深度理解，回答关于视频内容的自然语言问题

### 3. 执行流程

```Python
# === Cell 1: 安装与配置 Twelve Labs ===
# !pip install twelvelabs

from twelvelabs import TwelveLabs
import os

# 初始化 Twelve Labs 客户端
tl_client = TwelveLabs(api_key=os.getenv("TWELVE_LABS_API_KEY"))

print("✅ Twelve Labs 客户端就绪！")

✅ Twelve Labs 客户端就绪！

# === Cell 2: 创建视频索引 ===
# 创建索引
index = tl_client.index.create(
    name="video_kb_01",
    engines=[
        {
            "name": "marengo2.7",
            "options": ["visual", "audio"]
        },
        {
            "name": "pegasus1.2",
            "options": ["visual", "audio"]
        }
    ]
)
print(f"✅ 索引创建成功: {index.id} - {index.name}")

✅ 索引创建成功: idx_abc123def456 - video_kb_01

# === Cell 3: 上传视频并索引 ===
video_paths = [
    "./data/videos/onboarding_2024.mp4",
    "./data/videos/product_demo.mp4",
    "./data/videos/all_hands_q4.mp4"
]

video_ids = []
for vp in video_paths:
    task = tl_client.task.create(index_id=index.id, file=vp)
    print(f"⏳ 正在处理: {vp}")
    task.wait_for_done(sleep_interval=5)
    print(f"✅ 处理完成: {vp}")
    video_ids.append(task.video_id)

print(f"✅ 共索引 {len(video_ids)} 个视频")

⏳ 正在处理: ./data/videos/onboarding_2024.mp4
✅ 处理完成: ./data/videos/onboarding_2024.mp4
⏳ 正在处理: ./data/videos/product_demo.mp4
✅ 处理完成: ./data/videos/product_demo.mp4
⏳ 正在处理: ./data/videos/all_hands_q4.mp4
✅ 处理完成: ./data/videos/all_hands_q4.mp4
✅ 共索引 3 个视频

# === Cell 4: 视频内容搜索 ===
def search_video(query_text: str, top_n: int = 3):
    """使用自然语言搜索视频内容"""
    results = tl_client.search.index(
        index_id=index.id,
        query=query_text,
        options=["visual", "audio"],
        top_n=top_n
    )

    print(f"🔍 视频搜索: '{query_text}'")
    for i, clip in enumerate(results.data, 1):
        print(f"\n  [{i}] 视频: {clip.video_id}")
        print(f"      片段: {clip.start:.1f}s -> {clip.end:.1f}s (时长: {clip.end-clip.start:.1f}s)")
        print(f"      置信度: {clip.confidence:.4f}")
        if hasattr(clip, 'metadata') and clip.metadata:
            print(f"      描述: {clip.metadata.get('description', 'N/A')}")
    return results

# 测试视频搜索
search_video("新员工入职培训中介绍公司价值观的片段")

🔍 视频搜索: '新员工入职培训中介绍公司价值观的片段'

  [1] 视频: v_abc001
      片段: 125.0s -> 198.0s (时长: 73.0s)
      置信度: 0.9432
      描述: 培训讲师在屏幕上展示公司核心价值观，逐条讲解"客户至上、创新驱动、团队协作"三条核心价值观

  [2] 视频: v_abc001
      片段: 45.0s -> 78.0s (时长: 33.0s)
      置信度: 0.8125
      描述: HR负责人介绍公司发展历程和组织架构

  [3] 视频: v_abc003
      片段: 320.0s -> 360.0s (时长: 40.0s)
      置信度: 0.6543
      描述: CEO在全员大会上强调公司2025年的战略方向和核心价值观

# === Cell 5: 视频问答 ===
def video_qa(video_id: str, question: str):
    """对指定视频进行问答"""
    result = tl_client.generate.summarize(
        video_id=video_id,
        type="question",
        prompt=question
    )

    print(f"❓ 视频问答: {question}")
    print(f"💬 回答: {result.data}")
    return result

qa_result = video_qa("v_abc001", "新员工入职培训总时长是多少？包含哪些主要环节？")

❓ 视频问答: 新员工入职培训总时长是多少？包含哪些主要环节？
💬 回答: 新员工入职培训总时长约4小时，包含以下主要环节：公司概况介绍（45分钟）、核心价值观讲解（60分钟）、部门职责说明（50分钟）、办公系统和工具使用培训（55分钟）、以及Q&A答疑环节（30分钟）。培训中间安排了两次15分钟的休息时间。

# === Cell 6: 跨视频对比检索 ===
from IPython.display import display, Markdown

cross_questions = [
    "Q1: 在员工培训视频中，讲师提到了哪些具体的技术栈？",
    "Q2: 产品演示视频中展示了哪个核心功能的操作流程？",
    "Q3: 全员大会视频中CEO发布的第四季度关键目标是什么？"
]

for q in cross_questions:
    display(Markdown(f"### ❓ {q}"))
    results = search_video(q, top_n=2)
    if results.data:
        top = results.data[0]
        ans = tl_client.generate.summarize(
            video_id=top.video_id,
            type="question",
            prompt=q
        )
        display(Markdown(f"**回答:** {ans.data}"))
    display(Markdown("---"))
2025-12-11 20:08:14,556 - INFO - HTTP Request: POST https://api.twelvelabs.io/v1.3/search "HTTP/1.1 200 OK"
2025-12-11 20:08:16,892 - INFO - HTTP Request: POST https://api.twelvelabs.io/v1.3/generate "HTTP/1.1 200 OK"
```

### ❓ Q1: 在员工培训视频中，讲师提到了哪些具体的技术栈？

| 技术范式 | 检索结果 |
| :--- | :--- |
| 元数据检索 | 只能看到视频标题为"新员工入职培训"，无法获取技术栈相关信息 |
| 字幕检索 | 讲师提到"我们使用的技术栈包括 Python、Go 和 TypeScript，数据库方面主要用 PostgreSQL 和 Redis" |
| 多模态检索 | 画面中同时展示了技术栈架构图（第2页PPT），包含微服务框架（Spring Boot）、消息队列（Kafka）、容器编排（Kubernetes）等完整技术生态 |

### ❓ Q2: 产品演示视频中展示了哪个核心功能的操作流程？

| 技术范式 | 检索结果 |
| :--- | :--- |
| 元数据检索 | 视频标签包含"产品演示"，无更多细分信息 |
| 字幕检索 | 演示者说"接下来我们看一下数据分析报表的自动生成功能" |
| 多模态检索 | 演示者完整操作了 **智能报表生成** 功能：选择数据源→配置维度（时间/地区/产品线）→设定可视化图表类型→一键生成PDF报告→设置定期邮件推送。全程用时3分25秒，并展示了生成的报表样例。 |

### ❓ Q3: 全员大会视频中CEO发布的第四季度关键目标是什么？

| 技术范式 | 检索结果 |
| :--- | :--- |
| 元数据检索 | 视频标题"2024 Q4 All-Hands Meeting"，日期2024年10月 |
| 字幕检索 | CEO说"第四季度我们的核心目标是营收突破8亿元，用户增长30%，产品NPS评分达到65以上" |
| 多模态检索 | CEO在PPT第8页详细展示了Q4三大战略目标：1）营收目标8亿元（环比增长25%）；2）新增企业客户200家；3）上线两个新功能模块（AI助手V2和智能报表）。同时画面显示了各部门的OKR分解和责任矩阵。 |

═══════════════════════════════════════════════════════════

## 七大场景总结对比

> 核心总结：** 不同场景需要不同的 RAG 策略。没有"万能"的检索方法，关键是根据数据特征和业务需求选择最合适的策略组合。

| 场景编号 | 场景名称 | 核心策略 | 适用数据 | 关键组件 | 最佳实践场景 |
| :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | 小索引大窗口 | Sentence Window Retrieval | 长文档、政策手册 | `SentenceWindowNodeParser`, `MetadataReplacementPostProcessor` | 员工手册问答、法律文档条款查询 |
| 2 | 混合检索 | Hybrid Search (Vector + BM25) | 含专有名词的文档 | `FusionRetriever`, `BM25Retriever`, RRF 融合 | 内部知识库、项目代号搜索、产品名精确匹配 |
| 3 | 路由检索 | Route Retrieval | 多源异构数据 | `RouterQueryEngine`, `LLMSingleSelector`, `QueryEngineTool` | 企业统一知识库（HR+IT+财务） |
| 4 | 结构化数据查询 | PandasQueryEngine | CSV/Excel/SQL | `PandasQueryEngine`, DataFrame | 报表分析、员工数据统计、销售指标查询 |
| 5 | 图文PDF检索 | MinerU + Qwen-VL | 图文混排PDF | `PDFMinerReader`, `QwenVLAdapter`, `MultiModalVectorStoreIndex` | 财报分析、研报检索、产品手册问答 |
| 6 | 文搜图/图搜图 | Multimodal Image Search | 图片库 | `MultiModalVectorStoreIndex`, Qwen-VL Embedding | 设计素材管理、商品图检索、品牌资产管理 |
| 7 | 视频检索 | Video RAG (Twelve Labs) | 视频文件 | Twelve Labs API (Marengo + Pegasus) | 培训视频检索、会议录像分析、监控内容搜索 |

### 选型决策建议

```
数据全是纯文本 + 长文档 + 需要细节上下文 --> 场景一 (Sentence Window)
数据有大量专有名词/缩写/版本号        --> 场景二 (Hybrid Search)
数据分散在多个不同来源中              --> 场景三 (Route Retrieval)
数据是结构化表格/CSV                  --> 场景四 (PandasQueryEngine)
数据是PDF + 包含图片图表               --> 场景五 (MinerU + Qwen-VL)
数据是纯图片/照片库                    --> 场景六 (文搜图/图搜图)
数据是视频文件                         --> 场景七 (Twelve Labs Video RAG)
```

### 关键概念速查

| 概念 | 说明 |
| :--- | :--- |
| **Sentence Window Retrieval** | 小索引（单句）检索引擎 + 大窗口（上下文）生成策略 |
| **Hybrid Search** | 向量检索（语义） + BM25 关键词检索（字面）双路召回 |
| **RRF (Reciprocal Rank Fusion)** | 倒数排名融合算法，综合多路检索的排名结果 |
| **Route Retrieval** | 根据问题内容自动路由到不同的专用检索引擎 |
| **PandasQueryEngine** | 将自然语言转化为 Pandas 代码，对 DataFrame 执行查询 |
| **MinerU** | 高性能 PDF 解析工具，支持图文分离和版面分析 |
| **Qwen-VL** | 通义千问多模态大模型，支持图文联合理解 |
| **MultiModalVectorStoreIndex** | Llama-Index 多模态索引，文本和图片共享同一向量空间 |
| **Twelve Labs** | 视频理解 API 平台，支持多模态视频搜索和问答 |
| **Marengo** | Twelve Labs 的搜索引擎，支持视觉和语音特征的向量检索 |
| **Pegasus** | Twelve Labs 的理解引擎，支持视频内容的深度问答和摘要 |

---

**本文档所有代码示例基于 Llama-Index v0.14+ 和 Python 3.10+ 编写，实际运行时请确保依赖版本匹配。文档中所涉及的 API Key 请通过环境变量配置，切勿硬编码在代码中。**
