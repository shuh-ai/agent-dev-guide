"""
RAG 到上下文注入全链路 — 完整实现
====================================

对应文章: 03-RAG到上下文注入全链路

核心功能:
1. 检索结果排序（相关度、MMR 多样性、时间衰减）
2. 检索结果裁剪（token 预算分配、置信度阈值）
3. 注入格式化（XML 标签、Markdown 分隔）
4. 多源信息融合（RAG + 记忆 + 工具输出的优先级仲裁）
5. 完整的注入流水线

依赖: 仅标准库
"""

from __future__ import annotations

import json
import math
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional


# ============================================================
# 基础数据结构
# ============================================================

class SourceType(str, Enum):
    RAG = "rag"
    MEMORY = "memory"
    TOOL_OUTPUT = "tool_output"
    KNOWLEDGE_BASE = "knowledge_base"


class InjectionFormat(str, Enum):
    XML = "xml"
    MARKDOWN = "markdown"
    PLAIN = "plain"
    JSON = "json"


@dataclass
class RetrievedChunk:
    """检索到的文本块"""
    chunk_id: str
    content: str
    source: SourceType
    score: float                          # 检索相关度分数
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    token_count: int = 0

    def estimate_tokens(self) -> int:
        if self.token_count > 0:
            return self.token_count
        chinese_chars = sum(1 for c in self.content if '\u4e00' <= c <= '\u9fff')
        other_chars = len(self.content) - chinese_chars
        self.token_count = int(chinese_chars * 1.5 + other_chars / 4)
        return self.token_count


@dataclass
class InjectionContext:
    """注入上下文: 最终要注入到 prompt 中的内容"""
    sections: list[dict[str, Any]]         # 分区列表
    total_tokens: int
    sources_used: dict[str, int]           # 各来源使用数量
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================
# 1. 检索结果排序
# ============================================================

class RankingStrategy(ABC):
    """排序策略抽象基类"""

    @abstractmethod
    def rank(self, chunks: list[RetrievedChunk], query: str = "") -> list[RetrievedChunk]:
        ...


class RelevanceRanker(RankingStrategy):
    """按相关度分数排序（默认降序）"""

    def rank(self, chunks: list[RetrievedChunk], query: str = "") -> list[RetrievedChunk]:
        return sorted(chunks, key=lambda c: c.score, reverse=True)


class MMRRanker(RankingStrategy):
    """
    MMR (Maximal Marginal Relevance) 排序 — 兼顾相关度和多样性。

    在每一步选择与已选集合最不相似、且相关度较高的文档。
    lambda_param: 1.0 = 纯相关度排序, 0.0 = 纯多样性排序
    """

    def __init__(self, lambda_param: float = 0.7):
        self.lambda_param = lambda_param

    @staticmethod
    def _jaccard_similarity(a: str, b: str) -> float:
        """Jaccard 相似度（简化版，用字符 n-gram）"""
        def ngrams(text: str, n: int = 3) -> set[str]:
            return {text[i:i + n] for i in range(max(0, len(text) - n + 1))}

        set_a = ngrams(a.lower())
        set_b = ngrams(b.lower())
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    def rank(self, chunks: list[RetrievedChunk], query: str = "") -> list[RetrievedChunk]:
        if not chunks:
            return []

        selected: list[RetrievedChunk] = []
        remaining = list(chunks)

        while remaining:
            best_idx = -1
            best_score = -float('inf')

            for i, chunk in enumerate(remaining):
                relevance = chunk.score
                # 与已选集合的最大相似度
                max_sim = 0.0
                for s in selected:
                    sim = self._jaccard_similarity(chunk.content, s.content)
                    max_sim = max(max_sim, sim)

                mmr_score = self.lambda_param * relevance - (1 - self.lambda_param) * max_sim
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            if best_idx >= 0:
                selected.append(remaining.pop(best_idx))

        return selected


class TimeDecayRanker(RankingStrategy):
    """
    时间衰减排序 — 对检索结果施加时间衰减权重。

    final_score = score * exp(-decay_rate * age_hours)
    """

    def __init__(self, decay_rate: float = 0.01, now: Optional[datetime] = None):
        self.decay_rate = decay_rate
        self.now = now or datetime.now()

    def rank(self, chunks: list[RetrievedChunk], query: str = "") -> list[RetrievedChunk]:
        def time_adjusted_score(chunk: RetrievedChunk) -> float:
            age_hours = (self.now - chunk.created_at).total_seconds() / 3600
            decay = math.exp(-self.decay_rate * max(0, age_hours))
            return chunk.score * decay

        return sorted(chunks, key=time_adjusted_score, reverse=True)


class CompositeRanker(RankingStrategy):
    """
    组合排序器 — 串联多个排序策略。

    流程: relevance → MMR → time_decay
    """

    def __init__(self, strategies: Optional[list[RankingStrategy]] = None):
        self.strategies = strategies or [
            RelevanceRanker(),
            MMRRanker(lambda_param=0.7),
            TimeDecayRanker(decay_rate=0.005),
        ]

    def rank(self, chunks: list[RetrievedChunk], query: str = "") -> list[RetrievedChunk]:
        result = list(chunks)
        for strategy in self.strategies:
            result = strategy.rank(result, query)
        return result


# ============================================================
# 2. 检索结果裁剪
# ============================================================

@dataclass
class TrimmingConfig:
    """裁剪配置"""
    total_budget: int = 4000              # 总 token 预算
    source_allocation: dict[str, float] = field(default_factory=lambda: {
        "rag": 0.5,
        "memory": 0.2,
        "tool_output": 0.2,
        "knowledge_base": 0.1,
    })
    min_confidence: float = 0.3           # 最低置信度阈值
    max_chunks_per_source: int = 10       # 每来源最多块数
    overlap_threshold: float = 0.8        # 内容重叠阈值（去重）


class ChunkTrimmer:
    """
    检索结果裁剪器 — 按预算分配和质量阈值过滤。

    处理步骤:
    1. 置信度过滤（移除低于阈值的结果）
    2. 内容去重（移除高度重叠的结果）
    3. 按来源分配 token 预算
    4. 在预算内选择结果
    """

    def __init__(self, config: Optional[TrimmingConfig] = None):
        self.config = config or TrimmingConfig()

    def filter_confidence(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """过滤低置信度结果"""
        return [c for c in chunks if c.score >= self.config.min_confidence]

    def deduplicate(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """内容去重 — 基于内容哈希和相似度"""
        seen_hashes: set[str] = set()
        result: list[RetrievedChunk] = []

        for chunk in chunks:
            content_hash = hashlib.md5(chunk.content.encode()).hexdigest()[:16]
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)
            result.append(chunk)

        return result

    def allocate_budget(self) -> dict[str, int]:
        """按配置分配各来源的 token 预算"""
        allocation = {}
        for source, ratio in self.config.source_allocation.items():
            allocation[source] = int(self.config.total_budget * ratio)
        return allocation

    def trim(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """执行裁剪"""
        # Step 1: 置信度过滤
        filtered = self.filter_confidence(chunks)

        # Step 2: 去重
        deduped = self.deduplicate(filtered)

        # Step 3: 按来源分组
        by_source: dict[str, list[RetrievedChunk]] = {}
        for chunk in deduped:
            key = chunk.source.value
            by_source.setdefault(key, []).append(chunk)

        # Step 4: 按预算裁剪
        budget = self.allocate_budget()
        result: list[RetrievedChunk] = []

        for source_key, source_chunks in by_source.items():
            source_budget = budget.get(source_key, self.config.total_budget // 4)
            accumulated = 0
            count = 0

            for chunk in source_chunks:
                chunk_tokens = chunk.estimate_tokens()
                if accumulated + chunk_tokens > source_budget:
                    break
                if count >= self.config.max_chunks_per_source:
                    break
                result.append(chunk)
                accumulated += chunk_tokens
                count += 1

        return result


# ============================================================
# 3. 注入格式化
# ============================================================

class InjectionFormatter(ABC):
    """注入格式化器抽象基类"""

    @abstractmethod
    def format(self, chunks: list[RetrievedChunk], query: str = "") -> str: ...


class XMLFormatter(InjectionFormatter):
    """
    XML 标签格式化 — 用结构化标签组织检索结果。

    适合: Claude 等对 XML 标签敏感的模型。
    """

    def format(self, chunks: list[RetrievedChunk], query: str = "") -> str:
        sections: list[str] = []

        if query:
            sections.append(f"<query>\n{query}\n</query>")

        # 按来源分组
        by_source: dict[str, list[RetrievedChunk]] = {}
        for chunk in chunks:
            by_source.setdefault(chunk.source.value, []).append(chunk)

        source_labels = {
            "rag": "检索结果",
            "memory": "记忆上下文",
            "tool_output": "工具输出",
            "knowledge_base": "知识库",
        }

        sections.append("<context>")
        for source_key, source_chunks in by_source.items():
            label = source_labels.get(source_key, source_key)
            sections.append(f'  <source type="{source_key}" label="{label}">')
            for i, chunk in enumerate(source_chunks):
                sections.append(f'    <chunk id="{chunk.chunk_id}" score="{chunk.score:.3f}">')
                sections.append(f"      {chunk.content}")
                sections.append("    </chunk>")
            sections.append("  </source>")
        sections.append("</context>")

        return "\n".join(sections)


class MarkdownFormatter(InjectionFormatter):
    """
    Markdown 分隔格式化 — 用 Markdown 语法组织检索结果。

    适合: GPT 系列模型。
    """

    def format(self, chunks: list[RetrievedChunk], query: str = "") -> str:
        sections: list[str] = []

        if query:
            sections.append(f"## 查询\n{query}\n")

        by_source: dict[str, list[RetrievedChunk]] = {}
        for chunk in chunks:
            by_source.setdefault(chunk.source.value, []).append(chunk)

        source_labels = {
            "rag": "📚 检索结果",
            "memory": "🧠 记忆上下文",
            "tool_output": "🔧 工具输出",
            "knowledge_base": "📖 知识库",
        }

        sections.append("---\n## 上下文信息\n")

        for source_key, source_chunks in by_source.items():
            label = source_labels.get(source_key, source_key)
            sections.append(f"### {label}")
            for i, chunk in enumerate(source_chunks, 1):
                sections.append(f"\n**[{i}]** (相关度: {chunk.score:.2f})")
                sections.append(f"```\n{chunk.content}\n```\n")
            sections.append("---")

        return "\n".join(sections)


class PlainFormatter(InjectionFormatter):
    """纯文本格式化 — 无标记，适合简单场景"""

    def format(self, chunks: list[RetrievedChunk], query: str = "") -> str:
        parts: list[str] = []
        if query:
            parts.append(f"查询: {query}\n")

        for i, chunk in enumerate(chunks, 1):
            parts.append(f"[参考 {i}] (来源: {chunk.source.value}, 分数: {chunk.score:.2f})")
            parts.append(chunk.content)
            parts.append("")

        return "\n".join(parts)


# ============================================================
# 4. 多源信息融合
# ============================================================

@dataclass
class FusionRule:
    """融合规则"""
    source: SourceType
    priority: int                     # 数值越小优先级越高
    max_tokens: int                   # 该来源最大 token 数
    required: bool = False            # 是否必须包含


class MultiSourceFusion:
    """
    多源信息融合器 — 按优先级仲裁不同来源的检索结果。

    优先级策略:
    1. 工具输出（实时数据，最高优先级）
    2. RAG 检索结果（外部知识）
    3. 知识库（结构化知识）
    4. 记忆（历史上下文，最低优先级）
    """

    def __init__(self, rules: Optional[list[FusionRule]] = None, total_budget: int = 4000):
        self.rules = rules or [
            FusionRule(SourceType.TOOL_OUTPUT, priority=1, max_tokens=1000, required=True),
            FusionRule(SourceType.RAG, priority=2, max_tokens=2000),
            FusionRule(SourceType.KNOWLEDGE_BASE, priority=3, max_tokens=800),
            FusionRule(SourceType.MEMORY, priority=4, max_tokens=500),
        ]
        self.total_budget = total_budget

    def fuse(self, all_chunks: dict[str, list[RetrievedChunk]]) -> list[RetrievedChunk]:
        """
        融合多来源结果。

        Args:
            all_chunks: {source_type: [chunks]}
        Returns:
            按优先级排序的融合结果
        """
        sorted_rules = sorted(self.rules, key=lambda r: r.priority)
        result: list[RetrievedChunk] = []
        used_tokens = 0

        for rule in sorted_rules:
            source_chunks = all_chunks.get(rule.source.value, [])
            if not source_chunks:
                if rule.required:
                    # 必需来源缺失，添加占位提示
                    result.append(RetrievedChunk(
                        chunk_id=f"missing_{rule.source.value}",
                        content=f"[注意: {rule.source.value} 来源无可用数据]",
                        source=rule.source,
                        score=0.0,
                    ))
                continue

            source_tokens = 0
            for chunk in source_chunks:
                chunk_tokens = chunk.estimate_tokens()
                if used_tokens + chunk_tokens > self.total_budget:
                    break
                if source_tokens + chunk_tokens > rule.max_tokens:
                    break
                result.append(chunk)
                source_tokens += chunk_tokens
                used_tokens += chunk_tokens

        return result


# ============================================================
# 5. 完整注入流水线
# ============================================================

@dataclass
class PipelineConfig:
    """注入流水线配置"""
    total_budget: int = 4000
    min_confidence: float = 0.3
    format_type: InjectionFormat = InjectionFormat.XML
    enable_mmr: bool = True
    mmr_lambda: float = 0.7
    enable_time_decay: bool = True
    time_decay_rate: float = 0.005


class RAGInjectionPipeline:
    """
    RAG 注入全链路流水线

    流程:
    1. 接收多来源检索结果
    2. 多源融合（优先级仲裁）
    3. 排序（相关度 + MMR + 时间衰减）
    4. 裁剪（预算分配 + 置信度过滤 + 去重）
    5. 格式化注入文本
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()

        # 初始化排序器
        ranking_strategies: list[RankingStrategy] = [RelevanceRanker()]
        if self.config.enable_mmr:
            ranking_strategies.append(MMRRanker(lambda_param=self.config.mmr_lambda))
        if self.config.enable_time_decay:
            ranking_strategies.append(TimeDecayRanker(decay_rate=self.config.time_decay_rate))
        self.ranker = CompositeRanker(strategies=ranking_strategies)

        # 初始化裁剪器
        trim_config = TrimmingConfig(
            total_budget=self.config.total_budget,
            min_confidence=self.config.min_confidence,
        )
        self.trimmer = ChunkTrimmer(config=trim_config)

        # 初始化融合器
        self.fuser = MultiSourceFusion(total_budget=self.config.total_budget)

        # 初始化格式化器
        formatters = {
            InjectionFormat.XML: XMLFormatter(),
            InjectionFormat.MARKDOWN: MarkdownFormatter(),
            InjectionFormat.PLAIN: PlainFormatter(),
        }
        self.formatter = formatters[self.config.format_type]

    def run(self, raw_chunks: dict[str, list[RetrievedChunk]], query: str = "") -> InjectionContext:
        """
        执行完整的注入流水线。

        Args:
            raw_chunks: {source_type: [RetrievedChunk, ...]}
            query: 用户查询
        Returns:
            InjectionContext 包含格式化后的注入文本
        """
        # Step 1: 多源融合
        fused = self.fuser.fuse(raw_chunks)

        # Step 2: 排序
        ranked = self.ranker.rank(fused, query)

        # Step 3: 裁剪
        trimmed = self.trimmer.trim(ranked)

        # Step 4: 格式化
        formatted = self.formatter.format(trimmed, query)

        # 统计
        total_tokens = sum(c.estimate_tokens() for c in trimmed)
        sources_used: dict[str, int] = {}
        for c in trimmed:
            sources_used[c.source.value] = sources_used.get(c.source.value, 0) + 1

        return InjectionContext(
            sections=[
                {"type": "formatted_context", "content": formatted},
                {"type": "raw_chunks", "chunks": trimmed},
            ],
            total_tokens=total_tokens,
            sources_used=sources_used,
            metadata={
                "query": query,
                "format": self.config.format_type.value,
                "pipeline_stages": ["fusion", "ranking", "trimming", "formatting"],
            },
        )


# ============================================================
# 使用示例
# ============================================================

def demo_ranking():
    """演示: 检索结果排序"""
    print("=" * 60)
    print("演示 1: 检索结果排序")
    print("=" * 60)

    now = datetime.now()
    chunks = [
        RetrievedChunk("c1", "Python 是一种解释型编程语言", SourceType.RAG, 0.85,
                        created_at=now - timedelta(hours=1)),
        RetrievedChunk("c2", "Python 支持多种编程范式", SourceType.RAG, 0.90,
                        created_at=now - timedelta(hours=24)),
        RetrievedChunk("c3", "JavaScript 是前端开发的主流语言", SourceType.RAG, 0.75,
                        created_at=now - timedelta(hours=2)),
        RetrievedChunk("c4", "Python 的 GIL 限制了多线程性能", SourceType.RAG, 0.80,
                        created_at=now - timedelta(hours=6)),
        RetrievedChunk("c5", "Rust 以内存安全著称", SourceType.RAG, 0.70,
                        created_at=now - timedelta(hours=12)),
    ]

    print("原始顺序:")
    for c in chunks:
        print(f"  {c.chunk_id}: score={c.score:.2f}")

    # 相关度排序
    relevance = RelevanceRanker()
    r1 = relevance.rank(chunks)
    print("\n相关度排序:")
    for c in r1:
        print(f"  {c.chunk_id}: score={c.score:.2f}")

    # MMR 排序
    mmr = MMRRanker(lambda_param=0.6)
    r2 = mmr.rank(chunks)
    print("\nMMR 排序 (λ=0.6):")
    for c in r2:
        print(f"  {c.chunk_id}: score={c.score:.2f} | {c.content[:20]}...")

    # 时间衰减排序
    time_ranker = TimeDecayRanker(decay_rate=0.02, now=now)
    r3 = time_ranker.rank(chunks)
    print("\n时间衰减排序:")
    for c in r3:
        age_h = (now - c.created_at).total_seconds() / 3600
        decayed = c.score * math.exp(-0.02 * age_h)
        print(f"  {c.chunk_id}: original={c.score:.2f}, decayed={decayed:.2f}, age={age_h:.0f}h")


def demo_trimming():
    """演示: 检索结果裁剪"""
    print("\n" + "=" * 60)
    print("演示 2: 检索结果裁剪")
    print("=" * 60)

    chunks = [
        RetrievedChunk("c1", "Python 基础教程内容 " * 50, SourceType.RAG, 0.9),
        RetrievedChunk("c2", "Python 进阶技巧 " * 30, SourceType.RAG, 0.85),
        RetrievedChunk("c3", "低质量内容 " * 10, SourceType.RAG, 0.15),
        RetrievedChunk("c4", "用户之前的对话记忆 " * 20, SourceType.MEMORY, 0.7),
        RetrievedChunk("c5", "API 返回的实时数据 " * 40, SourceType.TOOL_OUTPUT, 0.95),
        RetrievedChunk("c6", "Python 基础教程内容 " * 50, SourceType.RAG, 0.88),  # 重复
    ]

    print(f"原始块数: {len(chunks)}")
    trimmer = ChunkTrimmer(TrimmingConfig(
        total_budget=2000,
        min_confidence=0.3,
    ))

    # 逐步演示
    filtered = trimmer.filter_confidence(chunks)
    print(f"置信度过滤后: {len(filtered)} (移除 score < 0.3)")

    deduped = trimmer.deduplicate(filtered)
    print(f"去重后: {len(deduped)}")

    trimmed = trimmer.trim(chunks)
    print(f"预算裁剪后: {len(trimmed)}")
    for c in trimmed:
        print(f"  {c.chunk_id}: source={c.source.value}, tokens≈{c.estimate_tokens()}")


def demo_formatting():
    """演示: 注入格式化"""
    print("\n" + "=" * 60)
    print("演示 3: 注入格式化")
    print("=" * 60)

    chunks = [
        RetrievedChunk("c1", "Python 是一种高级编程语言，广泛用于 AI 开发。", SourceType.RAG, 0.9),
        RetrievedChunk("c2", "用户询问过关于 asyncio 的问题。", SourceType.MEMORY, 0.7),
        RetrievedChunk("c3", '{"status": "ok", "latest_version": "3.12"}', SourceType.TOOL_OUTPUT, 0.95),
    ]

    # XML 格式
    xml_fmt = XMLFormatter()
    print("【XML 格式】")
    print(xml_fmt.format(chunks, query="Python 最新版本是什么？"))

    # Markdown 格式
    md_fmt = MarkdownFormatter()
    print("\n【Markdown 格式】")
    print(md_fmt.format(chunks, query="Python 最新版本是什么？"))

    # 纯文本格式
    plain_fmt = PlainFormatter()
    print("\n【纯文本格式】")
    print(plain_fmt.format(chunks, query="Python 最新版本是什么？"))


def demo_multi_source_fusion():
    """演示: 多源信息融合"""
    print("\n" + "=" * 60)
    print("演示 4: 多源信息融合")
    print("=" * 60)

    now = datetime.now()
    all_chunks: dict[str, list[RetrievedChunk]] = {
        "rag": [
            RetrievedChunk("r1", "RAG 文档片段 1: Python 语法基础", SourceType.RAG, 0.85),
            RetrievedChunk("r2", "RAG 文档片段 2: Python 高级特性", SourceType.RAG, 0.80),
        ],
        "memory": [
            RetrievedChunk("m1", "用户之前问过装饰器的用法", SourceType.MEMORY, 0.6),
        ],
        "tool_output": [
            RetrievedChunk("t1", '{"version": "3.12", "release_date": "2024-10-07"}',
                           SourceType.TOOL_OUTPUT, 0.95),
        ],
    }

    fuser = MultiSourceFusion(total_budget=3000)
    fused = fuser.fuse(all_chunks)

    print("融合结果（按优先级排序）:")
    for c in fused:
        print(f"  [{c.source.value:12}] {c.chunk_id}: {c.content[:40]}...")


def demo_full_pipeline():
    """演示: 完整注入流水线"""
    print("\n" + "=" * 60)
    print("演示 5: 完整 RAG 注入流水线")
    print("=" * 60)

    now = datetime.now()

    # 模拟多来源检索结果
    raw_chunks: dict[str, list[RetrievedChunk]] = {
        "rag": [
            RetrievedChunk("r1", "Python 3.12 引入了新的类型参数语法，简化了泛型编程。",
                           SourceType.RAG, 0.92, created_at=now - timedelta(days=1)),
            RetrievedChunk("r2", "Python 的 asyncio 模块提供了异步 I/O 支持。",
                           SourceType.RAG, 0.85, created_at=now - timedelta(days=3)),
            RetrievedChunk("r3", "Python 社区使用 PEP 流程来管理语言演进。",
                           SourceType.RAG, 0.70, created_at=now - timedelta(days=7)),
            RetrievedChunk("r4", "低置信度结果，应该被过滤掉。",
                           SourceType.RAG, 0.20, created_at=now - timedelta(days=1)),
        ],
        "memory": [
            RetrievedChunk("m1", "用户上次询问了 Python 装饰器的用法，已给出示例代码。",
                           SourceType.MEMORY, 0.75, created_at=now - timedelta(hours=2)),
        ],
        "tool_output": [
            RetrievedChunk("t1", json.dumps({
                "current_version": "3.12.3",
                "release_date": "2024-04-09",
                "download_url": "https://python.org/downloads"
            }, ensure_ascii=False),
                SourceType.TOOL_OUTPUT, 0.98, created_at=now),
        ],
        "knowledge_base": [
            RetrievedChunk("k1", "Python 之禅: 优美胜于丑陋，明了胜于晦涩。",
                           SourceType.KNOWLEDGE_BASE, 0.65, created_at=now - timedelta(days=30)),
        ],
    }

    # XML 格式流水线
    pipeline_xml = RAGInjectionPipeline(PipelineConfig(
        total_budget=3000,
        min_confidence=0.3,
        format_type=InjectionFormat.XML,
        enable_mmr=True,
        mmr_lambda=0.7,
    ))

    result = pipeline_xml.run(raw_chunks, query="Python 3.12 有什么新特性？")

    print("流水线执行结果:")
    print(f"  总 token: {result.total_tokens}")
    print(f"  来源使用: {result.sources_used}")
    print(f"  元数据: {json.dumps(result.metadata, ensure_ascii=False, indent=2)}")
    print(f"\n格式化输出:\n{result.sections[0]['content']}")

    # Markdown 格式流水线
    pipeline_md = RAGInjectionPipeline(PipelineConfig(
        total_budget=3000,
        format_type=InjectionFormat.MARKDOWN,
    ))

    result_md = pipeline_md.run(raw_chunks, query="Python 3.12 有什么新特性？")
    print(f"\n{'='*40}")
    print(f"Markdown 格式输出:\n{result_md.sections[0]['content'][:800]}...")


if __name__ == "__main__":
    demo_ranking()
    demo_trimming()
    demo_formatting()
    demo_multi_source_fusion()
    demo_full_pipeline()
    print("\n✅ 所有演示完成。")
