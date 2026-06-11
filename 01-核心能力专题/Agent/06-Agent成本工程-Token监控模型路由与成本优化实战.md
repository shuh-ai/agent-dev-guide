# Agent 成本工程：Token 监控、模型路由与成本优化实战

> 本文整合 2026 年最新的 LLM 成本优化策略，覆盖 Token 监控、模型路由、缓存机制、Prompt 优化等核心主题，帮助开发者将 Agent 运行成本降低 50-80%。

![LLM 成本优化策略](./images/llm-cost-optimization.png)

---

## 一、Agent 成本危机：为什么成本控制是生产化的关键

### 1.1 成本问题的严重性

一个生产级 Agent 每月的 Token 消耗可能达到数百万甚至上千万。以 GPT-4o 为例：

| 场景 | 日均请求 | 平均 Token/请求 | 月成本（估算） |
|------|----------|----------------|---------------|
| 客服 Agent（小规模） | 1,000 | 2,000 | ~$180 |
| 客服 Agent（中规模） | 10,000 | 2,000 | ~$1,800 |
| 企业知识库 Agent | 5,000 | 5,000 | ~$2,250 |
| 代码生成 Agent | 2,000 | 8,000 | ~$4,320 |

**大白话解释：** 如果你不做任何成本优化，一个中等规模的 Agent 每月可能烧掉几千美元。而通过合理的优化策略，这个成本可以降低 50-80%。

### 1.2 成本的两大驱动因素

| 驱动因素 | 说明 | 影响 |
|----------|------|------|
| **Token 消耗** | 输入 + 输出的 Token 总量 | 直接决定费用 |
| **模型选择** | 不同模型价格差异巨大 | GPT-4o 比 GPT-4o-mini 贵 20-30 倍 |

**关键洞察：** 80% 的 Agent 任务可以用更便宜的模型完成，只有 20% 的复杂任务需要顶级模型。

---

## 二、2026 年主流模型价格对比

### 2.1 模型价格速查表（2026年6月更新）

| 模型 | 输入价格（/百万Token） | 输出价格（/百万Token） | 适用场景 |
|------|----------------------|----------------------|----------|
| **GPT-5.5** | $5.00 | $30.00 | 旗舰通用、复杂推理 |
| **GPT-5.4** | $2.50 | $15.00 | 生产主力、性价比之选 |
| **GPT-4.1 Nano** | $0.10 | $0.40 | 最低成本、简单任务 |
| **o4-mini** | $0.55 | $2.20 | 推理任务、低成本 |
| **Claude Opus 4.8** | $5.00 | $25.00 | 最强能力、复杂任务 |
| **Claude Sonnet 4.6** | $3.00 | $15.00 | 代码生成、平衡性能 |
| **Claude Haiku 4.5** | $0.25 | $1.25 | 快速响应、简单任务 |
| **DeepSeek V3** | ¥0.1~0.3 | ¥0.2~0.5 | 国内低成本之选 |

> **价格说明：** 以上价格为 2026 年 6 月最新数据，来自 OpenAI 和 Anthropic 官方定价页面。GPT-5.5 于 2026 年 4 月 24 日发布，Claude Opus 4.8 于 2026 年 5 月 28 日发布。

### 2.2 成本差异可视化

```
模型成本对比（每百万 Token 输入价格）

GPT-5.5           ████████████████████████████████████████  $5.00
Claude Opus 4.8   ████████████████████████████████████████  $5.00
Claude Sonnet 4.6 █████████████████████████  $3.00
GPT-5.4           ████████████████████  $2.50
o4-mini           ████  $0.55
Claude Haiku 4.5  ██  $0.25
GPT-4.1 Nano      █  $0.10
DeepSeek V3       █  ¥0.1~0.3
```

**关键结论：** GPT-5.5 和 GPT-4.1 Nano 的价格差距高达 **50 倍**。如果 80% 的任务可以用 GPT-4.1 Nano 完成，整体成本可降低 **90%**。

---

## 三、模型路由：用对模型省大钱

### 3.1 什么是模型路由

模型路由（Model Routing）是根据任务的复杂度自动选择最合适模型的策略。

**核心思想：** 简单任务用便宜模型，复杂任务用贵模型。

### 3.2 任务复杂度分级

| 复杂度 | 任务类型 | 推荐模型 | 成本 |
|--------|----------|----------|------|
| **低** | 问候、简单问答、格式转换 | GPT-4.1 Nano / Claude Haiku 4.5 | $0.10-0.25/M |
| **中** | 信息检索、文本摘要、翻译 | GPT-5.4 / Claude Sonnet 4.6 | $2.50-3.00/M |
| **高** | 代码生成、复杂推理、多步分析 | GPT-5.5 / Claude Opus 4.8 | $5.00/M |
| **极高** | 数学证明、复杂架构设计 | GPT-5.5 Pro | $30.00/M |

### 3.3 模型路由实现

```python
from openai import OpenAI
import re

client = OpenAI()

def classify_task_complexity(user_input: str) -> str:
    """基于规则的任务复杂度分类"""
    
    # 低复杂度模式
    low_patterns = [
        r'^(你好|hi|hello|hey)',
        r'^(谢谢|thanks|thank you)',
        r'^(再见|bye|goodbye)',
        r'格式化|转换|翻译.*短',
    ]
    
    # 高复杂度模式
    high_patterns = [
        r'代码|实现|编写|重构|debug',
        r'分析.*原因|为什么.*导致',
        r'设计.*架构|系统设计',
        r'数学|证明|算法',
        r'多步|分步骤|详细.*步骤',
    ]
    
    for pattern in low_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            return "low"
    
    for pattern in high_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            return "high"
    
    return "medium"


def route_to_model(complexity: str) -> str:
    """根据复杂度选择模型"""
    routing = {
        "low": "gpt-4.1-nano",      # 最低成本
        "medium": "gpt-5.4",         # 生产主力
        "high": "gpt-5.5",           # 旗舰通用
    }
    return routing.get(complexity, "gpt-4.1-nano")


def smart_chat(user_input: str) -> str:
    """智能路由的聊天函数"""
    complexity = classify_task_complexity(user_input)
    model = route_to_model(complexity)
    
    print(f"任务复杂度: {complexity}, 使用模型: {model}")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_input}]
    )
    
    return response.choices[0].message.content
```

### 3.4 LLM-based 分类器

对于更精确的分类，可以用一个小模型来做任务分类：

```python
def classify_with_llm(user_input: str) -> str:
    """用 LLM 对任务复杂度进行分类"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 用最便宜的模型做分类
        messages=[
            {
                "role": "system",
                "content": """你是一个任务复杂度分类器。根据用户输入判断任务复杂度。
返回 JSON: {"complexity": "low|medium|high", "reason": "原因"}

分类标准：
- low: 简单问候、是/否问题、格式转换、简短翻译
- medium: 信息检索、文本摘要、一般问答
- high: 代码生成、复杂推理、多步分析、数学问题"""
            },
            {"role": "user", "content": user_input}
        ],
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return result["complexity"]
```

---

## 四、缓存机制：避免重复计算

### 4.1 缓存的三个层次

| 层次 | 原理 | 节省比例 | 实现复杂度 |
|------|------|----------|-----------|
| **精确缓存** | 完全相同的输入直接返回缓存结果 | 90%+ | 低 |
| **语义缓存** | 语义相似的输入返回缓存结果 | 60-80% | 中 |
| **前缀缓存** | 共享 System Prompt 的前缀部分 | 50-90% | 低 |

### 4.2 精确缓存实现

```python
import hashlib
import json
from typing import Optional

class LLMCache:
    """简单的 LLM 响应缓存"""
    
    def __init__(self, ttl: int = 3600):
        self.cache = {}
        self.ttl = ttl
    
    def _make_key(self, model: str, messages: list) -> str:
        """生成缓存键"""
        content = json.dumps({"model": model, "messages": messages}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, model: str, messages: list) -> Optional[str]:
        """获取缓存"""
        key = self._make_key(model, messages)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                print("✅ 缓存命中")
                return entry["response"]
        return None
    
    def set(self, model: str, messages: list, response: str):
        """设置缓存"""
        key = self._make_key(model, messages)
        self.cache[key] = {
            "response": response,
            "timestamp": time.time()
        }


# 使用示例
cache = LLMCache(ttl=3600)

def cached_chat(model: str, messages: list) -> str:
    """带缓存的聊天"""
    # 检查缓存
    cached = cache.get(model, messages)
    if cached:
        return cached
    
    # 调用 API
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    result = response.choices[0].message.content
    
    # 存入缓存
    cache.set(model, messages, result)
    return result
```

### 4.3 语义缓存

语义缓存可以识别"意思相同但表述不同"的查询：

```python
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticCache:
    """基于语义相似度的缓存"""
    
    def __init__(self, similarity_threshold: float = 0.95):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.cache = []
        self.threshold = similarity_threshold
    
    def _get_embedding(self, text: str) -> np.ndarray:
        return self.model.encode(text)
    
    def search(self, query: str) -> Optional[str]:
        """搜索语义相似的缓存"""
        query_embedding = self._get_embedding(query)
        
        for entry in self.cache:
            similarity = np.dot(query_embedding, entry["embedding"]) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(entry["embedding"])
            )
            if similarity >= self.threshold:
                print(f"✅ 语义缓存命中 (相似度: {similarity:.2f})")
                return entry["response"]
        
        return None
    
    def add(self, query: str, response: str):
        """添加缓存"""
        self.cache.append({
            "query": query,
            "response": response,
            "embedding": self._get_embedding(query)
        })
```

### 4.4 OpenAI Prompt Caching

OpenAI 在 2024 年底推出了 Prompt Caching 功能，可以自动缓存共享前缀：

```python
# OpenAI 的 Prompt Caching 是自动的
# 当多个请求共享相同的前缀时，缓存部分只计费一次
# 节省比例：输入 Token 费用降低 50%

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        # 这个长 System Prompt 会被缓存
        {"role": "system", "content": "你是一个专业的客服助手..." + very_long_context},
        # 只有这部分是新输入
        {"role": "user", "content": "我的订单状态是什么？"}
    ]
)

# 第一次请求：全额计费
# 后续请求：缓存的前缀部分只收 50% 费用
```

---

## 五、Prompt 优化：减少 Token 消耗

### 5.1 Prompt 瘦身策略

| 策略 | 方法 | 节省比例 |
|------|------|----------|
| **精简指令** | 删除冗余描述，保留核心指令 | 20-30% |
| **使用缩写** | 用关键词替代完整句子 | 10-20% |
| **动态上下文** | 只注入相关上下文，而非全部 | 30-50% |
| **压缩历史** | 对话历史摘要而非完整保留 | 40-60% |

### 5.2 动态上下文注入

```python
def build_optimized_prompt(user_query: str, context_docs: list) -> str:
    """优化的 Prompt 构建，只注入相关上下文"""
    
    # 1. 检索最相关的文档（而非全部）
    relevant_docs = retrieve_relevant_docs(user_query, context_docs, top_k=3)
    
    # 2. 压缩文档内容
    compressed_docs = [compress_doc(doc) for doc in relevant_docs]
    
    # 3. 构建精简 Prompt
    context = "\n---\n".join(compressed_docs)
    
    return f"""基于以下信息回答问题。如果信息不足，说"我不确定"。

<context>
{context}
</context>

问题：{user_query}"""
```

### 5.3 对话历史压缩

```python
def compress_conversation_history(messages: list, max_tokens: int = 2000) -> list:
    """压缩对话历史，保留关键信息"""
    
    if estimate_tokens(messages) <= max_tokens:
        return messages  # 不需要压缩
    
    # 保留系统消息
    system_messages = [m for m in messages if m["role"] == "system"]
    user_messages = [m for m in messages if m["role"] != "system"]
    
    # 保留最近 N 条消息
    recent_messages = user_messages[-6:]
    
    # 对较早的消息进行摘要
    older_messages = user_messages[:-6]
    if older_messages:
        summary = summarize_messages(older_messages)
        summary_message = {
            "role": "system",
            "content": f"之前的对话摘要：{summary}"
        }
        return system_messages + [summary_message] + recent_messages
    
    return system_messages + recent_messages
```

---

## 六、Token 监控与预算管理

### 6.1 Token 监控系统

```python
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict

@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    model: str
    timestamp: float
    cost: float

class TokenMonitor:
    """Token 使用监控"""
    
    def __init__(self):
        self.usage_log: list[TokenUsage] = []
        self.daily_budget: float = 100.0  # 每日预算（美元）
        self.alert_threshold: float = 0.8  # 80% 时告警
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算费用（2026年6月最新价格）"""
        pricing = {
            # OpenAI 模型
            "gpt-5.5": {"input": 5.00, "output": 30.00},
            "gpt-5.4": {"input": 2.50, "output": 15.00},
            "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
            "o4-mini": {"input": 0.55, "output": 2.20},
            # Anthropic 模型
            "claude-opus-4-8": {"input": 5.00, "output": 25.00},
            "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
            "claude-haiku-4-5": {"input": 0.25, "output": 1.25},
            # 其他
            "deepseek-v3": {"input": 0.15, "output": 0.30},
        }
        
        if model not in pricing:
            return 0.0
        
        prices = pricing[model]
        input_cost = (input_tokens / 1_000_000) * prices["input"]
        output_cost = (output_tokens / 1_000_000) * prices["output"]
        
        return input_cost + output_cost
    
    def log_usage(self, model: str, input_tokens: int, output_tokens: int):
        """记录使用量"""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            timestamp=time.time(),
            cost=cost
        )
        self.usage_log.append(usage)
        
        # 检查预算
        self._check_budget()
        
        return cost
    
    def _check_budget(self):
        """检查是否超出预算"""
        today_start = time.time() - (time.time() % 86400)
        today_usage = sum(
            u.cost for u in self.usage_log
            if u.timestamp >= today_start
        )
        
        usage_ratio = today_usage / self.daily_budget
        
        if usage_ratio >= 1.0:
            print(f"🚨 警告：已超出每日预算！已花费 ${today_usage:.2f} / ${self.daily_budget:.2f}")
        elif usage_ratio >= self.alert_threshold:
            print(f"⚠️ 注意：已使用 {usage_ratio*100:.0f}% 的每日预算 (${today_usage:.2f} / ${self.daily_budget:.2f})")
    
    def get_stats(self) -> Dict:
        """获取统计数据"""
        today_start = time.time() - (time.time() % 86400)
        today_usage = [u for u in self.usage_log if u.timestamp >= today_start]
        
        return {
            "total_requests": len(today_usage),
            "total_cost": sum(u.cost for u in today_usage),
            "total_input_tokens": sum(u.input_tokens for u in today_usage),
            "total_output_tokens": sum(u.output_tokens for u in today_usage),
            "by_model": self._group_by_model(today_usage)
        }
    
    def _group_by_model(self, usage: list) -> Dict:
        """按模型分组统计"""
        stats = defaultdict(lambda: {"requests": 0, "cost": 0, "tokens": 0})
        for u in usage:
            stats[u.model]["requests"] += 1
            stats[u.model]["cost"] += u.cost
            stats[u.model]["tokens"] += u.input_tokens + u.output_tokens
        return dict(stats)
```

### 6.2 成本监控仪表盘

```python
def print_cost_dashboard(monitor: TokenMonitor):
    """打印成本监控仪表盘"""
    stats = monitor.get_stats()
    
    print("=" * 60)
    print("📊 Agent 成本监控仪表盘")
    print("=" * 60)
    print(f"今日请求数: {stats['total_requests']}")
    print(f"今日总费用: ${stats['total_cost']:.4f}")
    print(f"今日输入 Token: {stats['total_input_tokens']:,}")
    print(f"今日输出 Token: {stats['total_output_tokens']:,}")
    print()
    print("按模型统计:")
    for model, data in stats['by_model'].items():
        print(f"  {model}:")
        print(f"    请求数: {data['requests']}")
        print(f"    费用: ${data['cost']:.4f}")
        print(f"    Token: {data['tokens']:,}")
    print("=" * 60)
```

---

## 七、批处理与异步优化

### 7.1 OpenAI Batch API

对于非实时任务，使用 Batch API 可以节省 **50%** 的费用：

```python
import json

def batch_process_with_openai(tasks: list) -> str:
    """使用 OpenAI Batch API 批量处理任务"""
    
    # 1. 准备批次文件
    batch_file = []
    for i, task in enumerate(tasks):
        batch_file.append({
            "custom_id": f"task-{i}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": task}
                ]
            }
        })
    
    # 2. 上传文件
    with open("batch_input.jsonl", "w") as f:
        for item in batch_file:
            f.write(json.dumps(item) + "\n")
    
    # 3. 创建批次任务
    client = OpenAI()
    batch_file_obj = client.files.create(
        file=open("batch_input.jsonl", "rb"),
        purpose="batch"
    )
    
    batch = client.batches.create(
        input_file_id=batch_file_obj.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    
    return batch.id

# Batch API 价格对比：
# - 标准 API: $0.15 / 1M input tokens (GPT-4o-mini)
# - Batch API: $0.075 / 1M input tokens (GPT-4o-mini)
# - 节省: 50%
```

### 7.2 请求合并

将多个小请求合并为一个大请求：

```python
def batch_classify(texts: list[str]) -> list[str]:
    """批量分类，而非逐个调用"""
    
    # 将多个文本合并到一个请求中
    combined_text = "\n---\n".join([f"[{i}] {text}" for i, text in enumerate(texts)])
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "对以下每个文本进行分类，返回 JSON 数组，每个元素包含 index 和 category。"
            },
            {"role": "user", "content": combined_text}
        ],
        response_format={"type": "json_object"}
    )
    
    results = json.loads(response.choices[0].message.content)
    return [r["category"] for r in results["texts"]]

# 10 个分类任务：
# - 逐个调用: 10 次 API 调用，10 次网络往返
# - 批量调用: 1 次 API 调用，1 次网络往返
# - 节省: 约 70% 的延迟和 90% 的网络开销
```

---

## 八、成本优化最佳实践

### 8.1 优化清单

| 优化项 | 实施难度 | 预期节省 | 优先级 |
|--------|----------|----------|--------|
| **模型路由** | 中 | 50-75% | ⭐⭐⭐⭐⭐ |
| **精确缓存** | 低 | 30-90% | ⭐⭐⭐⭐⭐ |
| **Prompt 瘦身** | 低 | 20-30% | ⭐⭐⭐⭐ |
| **语义缓存** | 中 | 60-80% | ⭐⭐⭐⭐ |
| **批处理** | 中 | 50% | ⭐⭐⭐ |
| **对话历史压缩** | 中 | 40-60% | ⭐⭐⭐ |
| **前缀缓存** | 低 | 50-90% | ⭐⭐⭐ |

### 8.2 成本优化决策树

```
收到用户请求
    │
    ├── 是否为重复/相似查询？
    │   ├── 是 → 返回缓存结果（节省 100%）
    │   └── 否 → 继续
    │
    ├── 任务复杂度如何？
    │   ├── 低 → 使用 gpt-4o-mini（节省 90%）
    │   ├── 中 → 使用 gpt-4o-mini（节省 90%）
    │   └── 高 → 继续
    │
    ├── 是否为实时任务？
    │   ├── 否 → 使用 Batch API（节省 50%）
    │   └── 是 → 继续
    │
    └── 使用 gpt-4o / Claude Sonnet
```

---

## 九、真实案例：从每月 $3000 到 $800

### 9.1 案例背景

某企业的客服 Agent 月均 Token 消耗：
- 日均请求：5,000 次
- 平均 Token/请求：3,000（输入 2,000 + 输出 1,000）
- 使用模型：GPT-5.5
- 月成本：~$3,000

### 9.2 优化措施

| 措施 | 实施方式 | 节省 |
|------|----------|------|
| 模型路由 | 80% 请求改用 GPT-4.1 Nano | $2,400 |
| 精确缓存 | 缓存常见问题的回答 | $200 |
| Prompt 优化 | 精简系统提示，减少 500 Token | $150 |
| 对话历史压缩 | 只保留最近 3 轮对话 | $100 |

### 9.3 优化结果

| 指标 | 优化前 | 优化后 | 变化 |
|------|--------|--------|------|
| 月成本 | $3,000 | $600 | **-80%** |
| 平均延迟 | 2.5s | 1.8s | -28% |
| 用户满意度 | 4.2/5 | 4.3/5 | +2% |

**关键洞察：** 用户满意度没有下降，因为 80% 的客服问题用 GPT-4.1 Nano 就能很好回答。

---

## 十、成本监控工具推荐

| 工具 | 类型 | 特点 |
|------|------|------|
| **LangSmith** | 平台内置 | LangChain 官方，Trace + 成本追踪 |
| **Maxim AI** | 专业工具 | 实时监控、告警、多模型对比 |
| **Helicone** | 代理层 | 零代码接入，自动记录所有请求 |
| **Portkey** | 网关层 | 多 Provider 路由 + 成本优化 |
| **自建监控** | 自定义 | 使用本文的 TokenMonitor 类 |

---

## 十一、落地路线图

### 第一阶段：立即生效（0-1周）

- [ ] 接入 Token 监控，了解当前成本分布
- [ ] 实现精确缓存，缓存高频查询
- [ ] 精简 System Prompt，删除冗余内容

### 第二阶段：快速见效（1-4周）

- [ ] 实现模型路由，简单任务用 mini
- [ ] 对话历史压缩
- [ ] 设置预算告警

### 第三阶段：深度优化（1-3个月）

- [ ] 语义缓存
- [ ] 批处理非实时任务
- [ ] 多 Provider 路由（对比价格）

---

## 参考资料

| 资源 | 链接 | 说明 |
|------|------|------|
| OpenAI Pricing | [openai.com/api/pricing](https://openai.com/api/pricing/) | 官方价格表（2026年6月） |
| Anthropic Pricing | [anthropic.com/pricing](https://www.anthropic.com/pricing) | Claude 价格表（2026年6月） |
| GPT-5.5 发布公告 | [openai.com/blog](https://openai.com/blog/gpt-5-5) | GPT-5.5 新特性介绍 |
| Claude Opus 4.8 发布 | [anthropic.com/blog](https://www.anthropic.com/blog/claude-opus-4-8) | Claude Opus 4.8 新特性 |
| Prompt Caching Guide | [platform.openai.com](https://platform.openai.com/docs/guides/prompt-caching) | OpenAI Prompt Caching 文档 |
| LangSmith | [smith.langchain.com](https://smith.langchain.com/) | LangChain 监控平台 |
| GPTCache | [github.com/zilliztech/GPTCache](https://github.com/zilliztech/GPTCache) | 语义缓存框架 |
| Price Per Token | [pricepertoken.com](https://pricepertoken.com/) | 模型价格对比工具 |
