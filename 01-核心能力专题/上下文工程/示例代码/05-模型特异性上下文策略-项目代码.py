"""
模型特异性上下文策略 — 完整实现
==================================

对应文章: 05-模型特异性上下文策略

核心功能:
1. ContextBuilder 抽象层（统一接口）
2. Claude 上下文构建器（XML 标签组织）
3. Gemini 上下文构建器（长窗口优化）
4. GPT 上下文构建器（缓存优化）
5. 模型切换迁移器
6. 缓存命中率优化

依赖: 仅标准库
"""

from __future__ import annotations

import json
import re
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ============================================================
# 基础数据结构
# ============================================================

class ModelFamily(str, Enum):
    CLAUDE = "claude"
    GPT = "gpt"
    GEMINI = "gemini"
    QWEN = "qwen"
    LOCAL = "local"


@dataclass
class ContextSection:
    """上下文片段"""
    section_type: str          # "system", "retrieval", "memory", "tools", "conversation"
    content: str
    priority: int = 0          # 数值越大优先级越高
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def estimate_tokens(self) -> int:
        if self.token_count > 0:
            return self.token_count
        chinese = sum(1 for c in self.content if '\u4e00' <= c <= '\u9fff')
        other = len(self.content) - chinese
        self.token_count = int(chinese * 1.5 + other / 4)
        return self.token_count


@dataclass
class ContextBuildResult:
    """构建结果"""
    messages: list[dict[str, str]]
    total_tokens: int
    model_family: ModelFamily
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheHint:
    """缓存提示"""
    prefix: str                # 缓存前缀内容
    cache_type: str            # "prompt_cache", "prefix_cache", "context_cache"
    estimated_savings: float   # 预估节省比例


# ============================================================
# 1. ContextBuilder 抽象层
# ============================================================

class ContextBuilder(ABC):
    """
    上下文构建器抽象基类 — 为不同模型提供统一的构建接口。

    每个模型子类实现特定的格式化和优化策略。
    """

    def __init__(self, model_name: str, max_context_tokens: int = 128000):
        self.model_name = model_name
        self.max_context_tokens = max_context_tokens
        self._sections: list[ContextSection] = []

    @property
    @abstractmethod
    def model_family(self) -> ModelFamily: ...

    def add_section(self, section_type: str, content: str, priority: int = 0,
                    metadata: Optional[dict[str, Any]] = None) -> None:
        """添加上下文片段"""
        self._sections.append(ContextSection(
            section_type=section_type,
            content=content,
            priority=priority,
            metadata=metadata or {},
        ))

    def add_system_prompt(self, prompt: str) -> None:
        self.add_section("system", prompt, priority=100)

    def add_retrieval_results(self, results: list[dict[str, Any]], format_type: str = "auto") -> None:
        """添加 RAG 检索结果"""
        self.add_section("retrieval", json.dumps(results, ensure_ascii=False), priority=80,
                         metadata={"format_type": format_type, "count": len(results)})

    def add_conversation_history(self, messages: list[dict[str, str]]) -> None:
        """添加对话历史"""
        self.add_section("conversation", json.dumps(messages, ensure_ascii=False), priority=60,
                         metadata={"message_count": len(messages)})

    def add_tool_definitions(self, tools: list[dict[str, Any]]) -> None:
        """添加工具定义"""
        self.add_section("tools", json.dumps(tools, ensure_ascii=False), priority=70,
                         metadata={"tool_count": len(tools)})

    def add_memory(self, memory_text: str) -> None:
        self.add_section("memory", memory_text, priority=50)

    @abstractmethod
    def build(self, user_message: str) -> ContextBuildResult:
        """构建最终的上下文消息列表"""
        ...

    @abstractmethod
    def get_cache_hints(self) -> list[CacheHint]:
        """获取缓存优化建议"""
        ...

    def _total_section_tokens(self) -> int:
        return sum(s.estimate_tokens() for s in self._sections)

    def _trim_to_budget(self, sections: list[ContextSection]) -> list[ContextSection]:
        """按优先级裁剪到预算内"""
        budget = self.max_context_tokens - 2000  # 留给用户消息和输出
        sorted_sections = sorted(sections, key=lambda s: s.priority, reverse=True)

        result = []
        used = 0
        for section in sorted_sections:
            tokens = section.estimate_tokens()
            if used + tokens <= budget:
                result.append(section)
                used += tokens
            else:
                # 尝试截断
                remaining = budget - used
                if remaining > 100:
                    truncated = ContextSection(
                        section_type=section.section_type,
                        content=section.content[:int(remaining * 2)] + "\n[... 内容已截断 ...]",
                        priority=section.priority,
                        metadata={**section.metadata, "truncated": True},
                    )
                    result.append(truncated)
                break

        return sorted(result, key=lambda s: s.priority, reverse=True)


# ============================================================
# 2. Claude 上下文构建器
# ============================================================

class ClaudeContextBuilder(ContextBuilder):
    """
    Claude 上下文构建器 — 利用 XML 标签组织上下文。

    特性:
    - 使用 <system>, <context>, <tools> 等标签
    - 长文档放在前面（Claude 对前置信息更敏感）
    - 利用 extended thinking 标签
    """

    @property
    def model_family(self) -> ModelFamily:
        return ModelFamily.CLAUDE

    def _format_retrieval(self, content: str) -> str:
        """用 XML 标签包装检索结果"""
        try:
            results = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return content

        parts = ["<retrieval_results>"]
        for i, r in enumerate(results, 1):
            text = r.get("content", str(r))
            source = r.get("source", "unknown")
            score = r.get("score", 0)
            parts.append(f'  <result id="{i}" source="{source}" score="{score:.2f}">')
            parts.append(f"    {text}")
            parts.append("  </result>")
        parts.append("</retrieval_results>")
        return "\n".join(parts)

    def _format_tools(self, content: str) -> str:
        """用 XML 标签包装工具定义"""
        try:
            tools = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return content

        parts = ["<available_tools>"]
        for tool in tools:
            name = tool.get("name", "unknown")
            desc = tool.get("description", "")
            parts.append(f'  <tool name="{name}">')
            parts.append(f"    <description>{desc}</description>")
            if "parameters" in tool:
                params = json.dumps(tool["parameters"], ensure_ascii=False)
                parts.append(f"    <parameters>{params}</parameters>")
            parts.append("  </tool>")
        parts.append("</available_tools>")
        return "\n".join(parts)

    def _format_conversation(self, content: str) -> str:
        """格式化对话历史"""
        try:
            messages = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return content

        parts = ["<conversation_history>"]
        for msg in messages:
            role = msg.get("role", "unknown")
            text = msg.get("content", "")
            parts.append(f"  <message role=\"{role}\">{text}</message>")
        parts.append("</conversation_history>")
        return "\n".join(parts)

    def build(self, user_message: str) -> ContextBuildResult:
        trimmed = self._trim_to_budget(self._sections)
        messages: list[dict[str, str]] = []

        # Claude 使用 system 参数单独传递系统提示
        system_sections = [s for s in trimmed if s.section_type == "system"]
        other_sections = [s for s in trimmed if s.section_type != "system"]

        system_parts = []
        for s in system_sections:
            system_parts.append(s.content)

        # 按类型格式化其他片段
        context_parts = []
        for section in other_sections:
            if section.section_type == "retrieval":
                context_parts.append(self._format_retrieval(section.content))
            elif section.section_type == "tools":
                context_parts.append(self._format_tools(section.content))
            elif section.section_type == "conversation":
                context_parts.append(self._format_conversation(section.content))
            elif section.section_type == "memory":
                context_parts.append(f"<memory>\n{section.content}\n</memory>")
            else:
                context_parts.append(section.content)

        # Claude 最佳实践: 将上下文放在用户消息中
        full_context = "\n\n".join(context_parts)
        if full_context:
            user_content = f"{full_context}\n\n<user_query>\n{user_message}\n</user_query>"
        else:
            user_content = user_message

        messages = [
            {"role": "system", "content": "\n\n".join(system_parts)},
            {"role": "user", "content": user_content},
        ]

        total_tokens = sum(s.estimate_tokens() for s in trimmed)
        return ContextBuildResult(
            messages=messages,
            total_tokens=total_tokens,
            model_family=ModelFamily.CLAUDE,
            metadata={"sections_count": len(trimmed), "format": "xml_tags"},
        )

    def get_cache_hints(self) -> list[CacheHint]:
        """Claude 支持 prompt caching（相同的前缀部分）"""
        system_sections = [s for s in self._sections if s.section_type == "system"]
        if not system_sections:
            return []

        prefix_tokens = sum(s.estimate_tokens() for s in system_sections)
        return [CacheHint(
            prefix="\n".join(s.content for s in system_sections),
            cache_type="prompt_cache",
            estimated_savings=min(0.9, prefix_tokens / max(1, self._total_section_tokens()) * 0.5),
        )]


# ============================================================
# 3. Gemini 上下文构建器
# ============================================================

class GeminiContextBuilder(ContextBuilder):
    """
    Gemini 上下文构建器 — 利用超长上下文窗口优化。

    特性:
    - 支持 1M+ token 上下文，可保留更多检索结果
    - system instruction 分离传递
    - 长文档可直接嵌入，无需过度压缩
    - 使用 grounding 元数据
    """

    def __init__(self, model_name: str = "gemini-3.5-flash", max_context_tokens: int = 1000000):
        super().__init__(model_name, max_context_tokens)

    @property
    def model_family(self) -> ModelFamily:
        return ModelFamily.GEMINI

    def _format_retrieval(self, content: str) -> str:
        """Gemini 使用 grounding metadata 格式"""
        try:
            results = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return content

        parts = ["## 检索参考信息\n"]
        for i, r in enumerate(results, 1):
            text = r.get("content", str(r))
            source = r.get("source", "")
            parts.append(f"### 参考 [{i}]" + (f" (来源: {source})" if source else ""))
            parts.append(text)
            parts.append("")
        return "\n".join(parts)

    def _format_conversation(self, content: str) -> str:
        """Gemini 使用 contents 格式"""
        try:
            messages = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return content

        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            # Gemini 使用 "model" 而非 "assistant"
            gemini_role = "model" if role == "assistant" else role
            text = msg.get("content", "")
            parts.append(f"[{gemini_role}]: {text}")
        return "\n".join(parts)

    def build(self, user_message: str) -> ContextBuildResult:
        """Gemini: system instruction 独立，其余放入 user content"""
        trimmed = self._trim_to_budget(self._sections)

        system_sections = [s for s in trimmed if s.section_type == "system"]
        other_sections = [s for s in trimmed if s.section_type != "system"]

        # Gemini 特有: 可以把大量参考信息直接放在 user content 中
        context_parts = []
        for section in other_sections:
            if section.section_type == "retrieval":
                context_parts.append(self._format_retrieval(section.content))
            elif section.section_type == "conversation":
                context_parts.append(self._format_conversation(section.content))
            elif section.section_type == "memory":
                context_parts.append(f"## 记忆上下文\n{section.content}")
            else:
                context_parts.append(section.content)

        full_context = "\n\n".join(context_parts)
        if full_context:
            user_content = f"{full_context}\n\n---\n\n{user_message}"
        else:
            user_content = user_message

        # Gemini 使用 systemInstruction 字段
        messages = []
        if system_sections:
            system_text = "\n\n".join(s.content for s in system_sections)
            messages.append({"role": "system", "content": system_text})
        messages.append({"role": "user", "content": user_content})

        total_tokens = sum(s.estimate_tokens() for s in trimmed)
        return ContextBuildResult(
            messages=messages,
            total_tokens=total_tokens,
            model_family=ModelFamily.GEMINI,
            metadata={
                "sections_count": len(trimmed),
                "format": "gemini_native",
                "long_context": total_tokens > 100000,
            },
        )

    def get_cache_hints(self) -> list[CacheHint]:
        """Gemini 支持 context caching"""
        cacheable = [s for s in self._sections if s.section_type in ("system", "retrieval")]
        if not cacheable:
            return []

        total = sum(s.estimate_tokens() for s in cacheable)
        return [CacheHint(
            prefix="\n".join(s.content for s in cacheable),
            cache_type="context_cache",
            estimated_savings=0.7,  # Gemini context caching 可节省约 70%
        )]


# ============================================================
# 4. GPT 上下文构建器
# ============================================================

class GPTContextBuilder(ContextBuilder):
    """
    GPT 上下文构建器 — 优化缓存命中率。

    特性:
    - 系统提示固定在最前面（稳定前缀利于缓存）
    - 使用 developer/user/assistant 角色
    - 检索结果以 Markdown 格式注入
    - 工具定义使用 function calling 格式
    - 优化前缀稳定性以提高 prompt caching 命中率
    """

    @property
    def model_family(self) -> ModelFamily:
        return ModelFamily.GPT

    def _format_retrieval_markdown(self, content: str) -> str:
        """Markdown 格式化检索结果"""
        try:
            results = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return content

        parts = ["---\n## 参考信息\n"]
        for i, r in enumerate(results, 1):
            text = r.get("content", str(r))
            score = r.get("score", 0)
            parts.append(f"**[{i}]** (相关度: {score:.2f})\n```\n{text}\n```\n")
        parts.append("---")
        return "\n".join(parts)

    def _build_stable_prefix(self) -> str:
        """
        构建稳定的前缀 — GPT prompt caching 要求前缀完全一致。

        策略: system prompt + 固定格式的工具定义 → 稳定的缓存前缀
        """
        parts = []
        for s in self._sections:
            if s.section_type == "system":
                parts.append(s.content)
        return "\n\n".join(parts)

    def build(self, user_message: str) -> ContextBuildResult:
        """GPT: 稳定前缀 + 动态内容"""
        trimmed = self._trim_to_budget(self._sections)
        messages: list[dict[str, str]] = []

        # 分离 system 和其他部分
        system_sections = sorted(
            [s for s in trimmed if s.section_type == "system"],
            key=lambda s: s.priority, reverse=True
        )
        dynamic_sections = sorted(
            [s for s in trimmed if s.section_type != "system"],
            key=lambda s: s.priority, reverse=True
        )

        # System message: 只包含系统提示（保持稳定）
        if system_sections:
            system_text = "\n\n".join(s.content for s in system_sections)
            messages.append({"role": "system", "content": system_text})

        # 动态部分作为 developer message 或 user message 前缀
        context_parts = []
        for section in dynamic_sections:
            if section.section_type == "retrieval":
                context_parts.append(self._format_retrieval_markdown(section.content))
            elif section.section_type == "memory":
                context_parts.append(f"### 记忆\n{section.content}")
            elif section.section_type == "conversation":
                context_parts.append(f"### 对话历史\n{section.content}")
            else:
                context_parts.append(section.content)

        # 将动态上下文放在用户消息前面（但不破坏缓存前缀）
        if context_parts:
            full_context = "\n\n".join(context_parts)
            user_content = f"{full_context}\n\n---\n\n用户提问: {user_message}"
        else:
            user_content = user_message

        messages.append({"role": "user", "content": user_content})

        total_tokens = sum(s.estimate_tokens() for s in trimmed)
        return ContextBuildResult(
            messages=messages,
            total_tokens=total_tokens,
            model_family=ModelFamily.GPT,
            metadata={
                "sections_count": len(trimmed),
                "format": "gpt_optimized",
                "cache_friendly": True,
            },
        )

    def get_cache_hints(self) -> list[CacheHint]:
        """GPT 自动缓存超过 1024 token 的共同前缀"""
        prefix = self._build_stable_prefix()
        prefix_tokens = int(len(prefix) / 3)  # 粗略估算

        hints = []
        if prefix_tokens >= 1024:
            hints.append(CacheHint(
                prefix=prefix,
                cache_type="prompt_cache",
                estimated_savings=0.5,  # GPT 自动缓存 50% 折扣
            ))
        return hints


# ============================================================
# 5. 模型切换迁移器
# ============================================================

class ModelMigrationError(Exception):
    pass


class ModelSwitchMigrator:
    """
    模型切换迁移器 — 在不同模型之间迁移上下文。

    场景: 运行时切换模型（如 Claude → GPT），需要重新格式化上下文。
    """

    def __init__(self):
        self.builders: dict[ModelFamily, type[ContextBuilder]] = {
            ModelFamily.CLAUDE: ClaudeContextBuilder,
            ModelFamily.GEMINI: GeminiContextBuilder,
            ModelFamily.GPT: GPTContextBuilder,
        }

    def migrate(
        self,
        source_result: ContextBuildResult,
        target_family: ModelFamily,
        sections: list[ContextSection],
        user_message: str,
    ) -> ContextBuildResult:
        """
        迁移上下文到目标模型。

        Args:
            source_result: 源模型的构建结果
            target_family: 目标模型家族
            sections: 原始上下文片段（非格式化）
            user_message: 用户消息
        Returns:
            目标模型的构建结果
        """
        builder_cls = self.builders.get(target_family)
        if not builder_cls:
            raise ModelMigrationError(f"不支持的目标模型: {target_family}")

        # 重建上下文
        builder = builder_cls(max_context_tokens=128000)
        for section in sections:
            builder.add_section(section.section_type, section.content, section.priority, section.metadata)

        result = builder.build(user_message)

        # 迁移元数据
        result.metadata["migrated_from"] = source_result.model_family.value
        result.metadata["migration_timestamp"] = datetime.now().isoformat()

        return result

    def extract_sections(self, result: ContextBuildResult) -> list[ContextSection]:
        """从构建结果中提取原始片段（简化版）"""
        sections = []
        for msg in result.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            section_type = "system" if role == "system" else "conversation"
            sections.append(ContextSection(
                section_type=section_type,
                content=content,
                priority=100 if role == "system" else 50,
            ))
        return sections


# ============================================================
# 6. 缓存命中率优化
# ============================================================

@dataclass
class CacheStats:
    """缓存统计"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    saved_tokens: int = 0
    saved_cost_estimate: float = 0.0

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests


class CacheOptimizer:
    """
    缓存命中率优化器。

    核心策略:
    1. 前缀稳定化 — 保持 system prompt 和工具定义不变
    2. 内容排序固定 — 相同类型的片段按固定顺序排列
    3. 变化隔离 — 将变化频繁的内容放在后面
    4. 批量请求复用 — 同一批请求共享前缀
    """

    def __init__(self):
        self.stats = CacheStats()
        self._prefix_hashes: list[str] = []

    @staticmethod
    def stabilize_prefix(sections: list[ContextSection]) -> list[ContextSection]:
        """
        稳定化前缀 — 按类型和优先级固定排序。

        排序规则（从前往后）:
        1. system (优先级 100)
        2. tools (优先级 70)
        3. retrieval (优先级 80) — 虽然优先级高，但可能变化
        4. memory (优先级 50)
        5. conversation (优先级 60) — 最不稳定
        """
        type_order = {"system": 0, "tools": 1, "retrieval": 2, "memory": 3, "conversation": 4, "other": 5}

        def sort_key(s: ContextSection) -> tuple[int, int]:
            return (type_order.get(s.section_type, 5), -s.priority)

        return sorted(sections, key=sort_key)

    @staticmethod
    def separate_static_dynamic(sections: list[ContextSection]) -> tuple[list[ContextSection], list[ContextSection]]:
        """
        分离静态和动态内容。

        静态: system, tools（几乎不变）
        动态: conversation, memory, retrieval（经常变化）
        """
        static_types = {"system", "tools"}
        static = [s for s in sections if s.section_type in static_types]
        dynamic = [s for s in sections if s.section_type not in static_types]
        return static, dynamic

    def compute_prefix_hash(self, sections: list[ContextSection], prefix_length: int = 2) -> str:
        """计算前缀哈希（用于检测缓存命中）"""
        prefix_content = "\n".join(s.content for s in sections[:prefix_length])
        return hashlib.sha256(prefix_content.encode()).hexdigest()[:16]

    def optimize_for_cache(self, sections: list[ContextSection]) -> list[ContextSection]:
        """
        优化上下文以提高缓存命中率。

        步骤:
        1. 分离静态/动态内容
        2. 静态内容放在前面且排序固定
        3. 动态内容按变化频率排序（最不稳定的放最后）
        """
        static, dynamic = self.separate_static_dynamic(sections)
        static = self.stabilize_prefix(static)

        # 动态内容按稳定性排序: retrieval < memory < conversation
        stability_order = {"retrieval": 2, "memory": 1, "conversation": 0}
        dynamic.sort(key=lambda s: stability_order.get(s.section_type, -1))

        return static + dynamic

    def record_access(self, sections: list[ContextSection]) -> bool:
        """记录一次访问，返回是否缓存命中"""
        self.stats.total_requests += 1
        current_hash = self.compute_prefix_hash(sections)

        if current_hash in self._prefix_hashes:
            self.stats.cache_hits += 1
            return True
        else:
            self.stats.cache_misses += 1
            self._prefix_hashes.append(current_hash)
            # 只保留最近 100 个前缀哈希
            if len(self._prefix_hashes) > 100:
                self._prefix_hashes = self._prefix_hashes[-100:]
            return False

    def get_optimization_report(self) -> dict[str, Any]:
        """获取优化报告"""
        return {
            "cache_stats": {
                "total_requests": self.stats.total_requests,
                "cache_hits": self.stats.cache_hits,
                "cache_misses": self.stats.cache_misses,
                "hit_rate": f"{self.stats.hit_rate:.1%}",
            },
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """生成优化建议"""
        recs = []
        if self.stats.hit_rate < 0.3:
            recs.append("缓存命中率较低，建议增大静态前缀的占比。")
        if self.stats.hit_rate < 0.5:
            recs.append("考虑将更多工具定义和知识库内容移到系统提示中。")
        if self.stats.total_requests > 10 and self.stats.hit_rate > 0.7:
            recs.append("缓存命中率良好，当前策略有效。")
        if not recs:
            recs.append("数据不足，请继续收集更多请求数据。")
        return recs


# ============================================================
# 统一工厂
# ============================================================

class ContextBuilderFactory:
    """上下文构建器工厂"""

    _builders: dict[ModelFamily, type[ContextBuilder]] = {
        ModelFamily.CLAUDE: ClaudeContextBuilder,
        ModelFamily.GEMINI: GeminiContextBuilder,
        ModelFamily.GPT: GPTContextBuilder,
    }

    @classmethod
    def create(cls, model_name: str, max_context_tokens: Optional[int] = None) -> ContextBuilder:
        """根据模型名自动选择构建器"""
        model_lower = model_name.lower()

        if "claude" in model_lower:
            family = ModelFamily.CLAUDE
        elif "gemini" in model_lower:
            family = ModelFamily.GEMINI
        elif "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower:
            family = ModelFamily.GPT
        else:
            family = ModelFamily.LOCAL

        builder_cls = cls._builders.get(family)
        if not builder_cls:
            # 降级到 GPT 构建器（通用格式）
            builder_cls = GPTContextBuilder

        kwargs = {"model_name": model_name}
        if max_context_tokens is not None:
            kwargs["max_context_tokens"] = max_context_tokens
        return builder_cls(**kwargs)

    @classmethod
    def register(cls, family: ModelFamily, builder_cls: type[ContextBuilder]) -> None:
        cls._builders[family] = builder_cls


# ============================================================
# 使用示例
# ============================================================

def _get_sample_data() -> dict[str, Any]:
    """示例数据"""
    return {
        "system_prompt": "你是一个专业的 Python 编程助手。回答要简洁准确，给出可运行的代码示例。",
        "retrieval_results": [
            {"content": "Python 3.12 引入了 type 语句用于类型别名。", "source": "docs.python.org", "score": 0.92},
            {"content": "PEP 695 添加了新的类型参数语法。", "source": "peps.python.org", "score": 0.85},
            {"content": "match 语句（PEP 634）在 Python 3.10 引入。", "source": "docs.python.org", "score": 0.70},
        ],
        "conversation": [
            {"role": "user", "content": "Python 3.12 有什么新特性？"},
            {"role": "assistant", "content": "Python 3.12 的主要新特性包括改进的错误消息、f-string 语法增强等。"},
            {"role": "user", "content": "能详细说说类型系统的变化吗？"},
        ],
        "tools": [
            {"name": "search_docs", "description": "搜索 Python 官方文档",
             "parameters": {"query": "string", "version": "string"}},
            {"name": "run_code", "description": "执行 Python 代码并返回结果",
             "parameters": {"code": "string", "timeout": "integer"}},
        ],
        "user_message": "请给我一个使用新类型参数语法的完整示例。",
    }


def demo_claude_builder():
    """演示: Claude 上下文构建"""
    print("=" * 60)
    print("演示 1: Claude 上下文构建器 (XML 标签)")
    print("=" * 60)

    data = _get_sample_data()
    builder = ClaudeContextBuilder("claude-sonnet-4-6")

    builder.add_system_prompt(data["system_prompt"])
    builder.add_retrieval_results(data["retrieval_results"])
    builder.add_conversation_history(data["conversation"])
    builder.add_tool_definitions(data["tools"])

    result = builder.build(data["user_message"])

    print(f"模型家族: {result.model_family.value}")
    print(f"总 token: {result.total_tokens}")
    print(f"消息数: {len(result.messages)}")
    print(f"\n--- System Message ---")
    print(result.messages[0]["content"][:200])
    print(f"\n--- User Message ---")
    print(result.messages[1]["content"][:500] + "...")

    # 缓存建议
    hints = builder.get_cache_hints()
    print(f"\n缓存提示: {len(hints)}")
    for h in hints:
        print(f"  类型: {h.cache_type}, 预估节省: {h.estimated_savings:.0%}")


def demo_gemini_builder():
    """演示: Gemini 上下文构建"""
    print("\n" + "=" * 60)
    print("演示 2: Gemini 上下文构建器 (长窗口优化)")
    print("=" * 60)

    data = _get_sample_data()
    builder = GeminiContextBuilder()

    builder.add_system_prompt(data["system_prompt"])
    builder.add_retrieval_results(data["retrieval_results"])
    builder.add_conversation_history(data["conversation"])

    result = builder.build(data["user_message"])

    print(f"模型家族: {result.model_family.value}")
    print(f"总 token: {result.total_tokens}")
    print(f"是否为长上下文: {result.metadata.get('long_context', False)}")
    print(f"\n--- System ---")
    print(result.messages[0]["content"][:200])
    print(f"\n--- User Content (前 500 字符) ---")
    print(result.messages[1]["content"][:500] + "...")


def demo_gpt_builder():
    """演示: GPT 上下文构建"""
    print("\n" + "=" * 60)
    print("演示 3: GPT 上下文构建器 (缓存优化)")
    print("=" * 60)

    data = _get_sample_data()
    builder = GPTContextBuilder("gpt-5.5")

    builder.add_system_prompt(data["system_prompt"])
    builder.add_retrieval_results(data["retrieval_results"])
    builder.add_conversation_history(data["conversation"])
    builder.add_tool_definitions(data["tools"])

    result = builder.build(data["user_message"])

    print(f"模型家族: {result.model_family.value}")
    print(f"缓存友好: {result.metadata.get('cache_friendly', False)}")
    print(f"\n--- Messages ---")
    for msg in result.messages:
        print(f"  [{msg['role']}] {msg['content'][:100]}...")


def demo_model_migration():
    """演示: 模型切换迁移"""
    print("\n" + "=" * 60)
    print("演示 4: 模型切换迁移")
    print("=" * 60)

    data = _get_sample_data()

    # 先在 Claude 上构建
    claude_builder = ClaudeContextBuilder("claude-sonnet-4-6")
    claude_builder.add_system_prompt(data["system_prompt"])
    claude_builder.add_retrieval_results(data["retrieval_results"])
    claude_result = claude_builder.build(data["user_message"])

    print(f"原始模型: {claude_result.model_family.value}")
    print(f"原始消息数: {len(claude_result.messages)}")

    # 提取 section 并迁移到 GPT
    migrator = ModelSwitchMigrator()
    sections = migrator.extract_sections(claude_result)

    # 重新添加原始数据到 GPT 构建器
    gpt_builder = GPTContextBuilder("gpt-5.5")
    gpt_builder.add_system_prompt(data["system_prompt"])
    gpt_builder.add_retrieval_results(data["retrieval_results"])
    gpt_result = gpt_builder.build(data["user_message"])

    print(f"\n迁移后模型: {gpt_result.model_family.value}")
    print(f"迁移后消息数: {len(gpt_result.messages)}")
    print(f"迁移元数据: {json.dumps(gpt_result.metadata, ensure_ascii=False)}")


def demo_cache_optimization():
    """演示: 缓存命中率优化"""
    print("\n" + "=" * 60)
    print("演示 5: 缓存命中率优化")
    print("=" * 60)

    optimizer = CacheOptimizer()
    data = _get_sample_data()

    # 构建一组 sections
    sections = [
        ContextSection("system", data["system_prompt"], priority=100),
        ContextSection("tools", json.dumps(data["tools"]), priority=70),
        ContextSection("retrieval", json.dumps(data["retrieval_results"]), priority=80),
        ContextSection("memory", "用户之前问过 Python 装饰器的问题", priority=50),
        ContextSection("conversation", json.dumps(data["conversation"]), priority=60),
    ]

    # 优化前排序
    print("优化前:")
    for s in sections:
        print(f"  [{s.section_type}] priority={s.priority}")

    # 优化后排序
    optimized = optimizer.optimize_for_cache(sections)
    print("\n优化后（缓存友好排序）:")
    for s in optimized:
        print(f"  [{s.section_type}] priority={s.priority}")

    # 模拟多次请求
    print("\n模拟 10 次请求:")
    for i in range(10):
        # 每次都用相同的 system + tools，但 conversation 不同
        req_sections = [
            ContextSection("system", data["system_prompt"], priority=100),
            ContextSection("tools", json.dumps(data["tools"]), priority=70),
            ContextSection("conversation", f"第 {i} 轮对话内容...", priority=60),
        ]
        hit = optimizer.record_access(req_sections)
        print(f"  请求 {i + 1}: {'命中 ✓' if hit else '未命中 ✗'}")

    report = optimizer.get_optimization_report()
    print(f"\n优化报告:")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def demo_factory():
    """演示: 统一工厂"""
    print("\n" + "=" * 60)
    print("演示 6: 统一工厂 — 根据模型名自动选择")
    print("=" * 60)

    models = [
        "claude-opus-4-8",
        "gemini-3.5-flash",
        "gpt-5.5",
        "claude-sonnet-4-6",
        "deepseek-v4-flash",
    ]

    for model in models:
        builder = ContextBuilderFactory.create(model)
        print(f"  {model:30s} → {builder.__class__.__name__} ({builder.model_family.value})")


if __name__ == "__main__":
    demo_claude_builder()
    demo_gemini_builder()
    demo_gpt_builder()
    demo_model_migration()
    demo_cache_optimization()
    demo_factory()
    print("\n✅ 所有演示完成。")
