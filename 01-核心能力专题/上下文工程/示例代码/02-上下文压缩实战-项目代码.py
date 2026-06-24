"""
上下文压缩实战 — 完整实现
============================

对应文章: 02-上下文压缩实战

核心功能:
1. 对话历史压缩（摘要式、滑动窗口、分层保留）
2. 工具输出压缩（JSON裁剪、字段提取）
3. 代码上下文压缩（AST摘要、diff压缩）
4. 压缩触发策略（auto-compact 阈值触发）
5. 压缩质量评估（信息保留率）

依赖: 仅标准库（可选 openai 用于 LLM 摘要）
"""

from __future__ import annotations

import json
import re
import hashlib
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


# ============================================================
# 基础数据结构
# ============================================================

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class Message:
    """对话消息"""
    role: Role
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def estimate_tokens(self) -> int:
        """粗略估算 token 数（中文约 1.5 字/token，英文约 4 字符/token）"""
        if self.token_count > 0:
            return self.token_count
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', self.content))
        other_chars = len(self.content) - chinese_chars
        self.token_count = int(chinese_chars * 1.5 + other_chars / 4)
        return self.token_count


@dataclass
class CompressionResult:
    """压缩结果"""
    compressed_messages: list[Message]
    original_tokens: int
    compressed_tokens: int
    strategy: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def compression_ratio(self) -> float:
        if self.original_tokens == 0:
            return 1.0
        return self.compressed_tokens / self.original_tokens

    @property
    def saved_tokens(self) -> int:
        return self.original_tokens - self.compressed_tokens


# ============================================================
# 压缩策略抽象基类
# ============================================================

class CompressionStrategy(ABC):
    """压缩策略抽象基类"""

    @abstractmethod
    def compress(self, messages: list[Message], budget: int) -> CompressionResult:
        """
        压缩消息列表到指定 token 预算内。

        Args:
            messages: 原始消息列表
            budget: 目标 token 预算
        Returns:
            CompressionResult
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str: ...


# ============================================================
# 1. 对话历史压缩
# ============================================================

class SlidingWindowCompression(CompressionStrategy):
    """
    滑动窗口压缩 — 保留最近 N 轮对话，丢弃更早的消息。

    适用场景: 长对话中旧上下文已不重要。
    """

    def __init__(self, keep_recent: int = 10, system_always: bool = True):
        self.keep_recent = keep_recent
        self.system_always = system_always

    @property
    def name(self) -> str:
        return "sliding_window"

    def compress(self, messages: list[Message], budget: int) -> CompressionResult:
        original_tokens = sum(m.estimate_tokens() for m in messages)

        # 始终保留 system 消息
        system_msgs = [m for m in messages if m.role == Role.SYSTEM] if self.system_always else []
        non_system = [m for m in messages if m.role != Role.SYSTEM or not self.system_always]

        # 保留最近 N 条
        kept = non_system[-self.keep_recent:] if len(non_system) > self.keep_recent else non_system

        # 如果超出预算，继续缩减
        result = system_msgs + kept
        while sum(m.estimate_tokens() for m in result) > budget and len(kept) > 2:
            kept = kept[2:]  # 每次移除最早的一轮（user+assistant）
            result = system_msgs + kept

        # 添加压缩标记
        if len(non_system) > len(kept):
            dropped = len(non_system) - len(kept)
            summary = Message(
                role=Role.SYSTEM,
                content=f"[已压缩] 前 {dropped} 条消息已通过滑动窗口策略移除。",
                metadata={"compression_marker": True}
            )
            result = [summary] + result

        compressed_tokens = sum(m.estimate_tokens() for m in result)
        return CompressionResult(
            compressed_messages=result,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy=self.name,
            metadata={"dropped_count": len(non_system) - len(kept)}
        )


class SummaryCompression(CompressionStrategy):
    """
    摘要式压缩 — 将旧消息聚合为摘要，保留最近消息原文。

    适用场景: 需要保留旧上下文的关键信息。
    """

    def __init__(self, keep_recent: int = 6, summarizer: Optional[Callable[[list[Message]], str]] = None):
        self.keep_recent = keep_recent
        self.summarizer = summarizer or self._default_summarizer

    @property
    def name(self) -> str:
        return "summary"

    @staticmethod
    def _default_summarizer(messages: list[Message]) -> str:
        """默认摘要提取: 取每条消息的前 100 字符"""
        parts = []
        for m in messages:
            prefix = {"user": "用户", "assistant": "助手", "tool": "工具", "system": "系统"}[m.role.value]
            text = m.content[:100].replace("\n", " ")
            parts.append(f"- {prefix}: {text}...")
        return "## 历史对话摘要\n" + "\n".join(parts)

    def compress(self, messages: list[Message], budget: int) -> CompressionResult:
        original_tokens = sum(m.estimate_tokens() for m in messages)

        system_msgs = [m for m in messages if m.role == Role.SYSTEM]
        non_system = [m for m in messages if m.role != Role.SYSTEM]

        if len(non_system) <= self.keep_recent:
            return CompressionResult(
                compressed_messages=messages,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                strategy=self.name,
            )

        old_messages = non_system[:-self.keep_recent]
        recent_messages = non_system[-self.keep_recent:]

        summary_text = self.summarizer(old_messages)
        summary_msg = Message(
            role=Role.SYSTEM,
            content=summary_text,
            metadata={"compression_marker": True, "summarized_count": len(old_messages)}
        )

        result = system_msgs + [summary_msg] + recent_messages
        compressed_tokens = sum(m.estimate_tokens() for m in result)

        return CompressionResult(
            compressed_messages=result,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy=self.name,
            metadata={"summarized_count": len(old_messages)}
        )


class HierarchicalCompression(CompressionStrategy):
    """
    分层保留压缩 — 按重要性分层保留:

    Layer 0: system prompt（始终保留）
    Layer 1: 最近 3 轮（完整保留）
    Layer 2: 之前 7 轮（只保留 user 消息 + assistant 关键句）
    Layer 3: 更早的消息（仅保留摘要）

    适用场景: 长对话中需要平衡信息量与上下文长度。
    """

    def __init__(self, layer1: int = 6, layer2: int = 14):
        self.layer1 = layer1  # 完整保留的消息数
        self.layer2 = layer2  # 部分保留的消息数

    @property
    def name(self) -> str:
        return "hierarchical"

    @staticmethod
    def _extract_key_sentences(text: str, max_chars: int = 200) -> str:
        """提取关键句子（简化版：取前 max_chars 字符 + 最后一句）"""
        sentences = re.split(r'[。！？\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return text[:max_chars]
        first = sentences[0][:100]
        last = sentences[-1][:100] if len(sentences) > 1 else ""
        return f"{first}{'...' if len(sentences[0]) > 100 else ''}" + \
               (f"\n...{last}" if last and last != first else "")

    def compress(self, messages: list[Message], budget: int) -> CompressionResult:
        original_tokens = sum(m.estimate_tokens() for m in messages)

        system_msgs = [m for m in messages if m.role == Role.SYSTEM]
        non_system = [m for m in messages if m.role != Role.SYSTEM]

        if len(non_system) <= self.layer1:
            return CompressionResult(
                compressed_messages=messages,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                strategy=self.name,
            )

        # Layer 1: 完整保留
        layer1_msgs = non_system[-self.layer1:]
        remaining = non_system[:-self.layer1]

        # Layer 2: 压缩保留
        layer2_boundary = max(0, len(remaining) - self.layer2)
        layer2_original = remaining[layer2_boundary:]
        layer3_original = remaining[:layer2_boundary]

        layer2_compressed = []
        for msg in layer2_original:
            if msg.role == Role.USER:
                layer2_compressed.append(msg)  # 用户消息完整保留
            else:
                compressed_text = self._extract_key_sentences(msg.content)
                layer2_compressed.append(Message(
                    role=msg.role,
                    content=compressed_text,
                    metadata={**msg.metadata, "layer": 2, "compressed": True}
                ))

        # Layer 3: 摘要
        result = system_msgs[:]
        if layer3_original:
            topics = []
            for m in layer3_original:
                if m.role == Role.USER:
                    topics.append(m.content[:50])
            if topics:
                summary = Message(
                    role=Role.SYSTEM,
                    content=f"[更早的对话涉及以下话题: {'; '.join(topics[:5])}...]",
                    metadata={"compression_marker": True, "layer": 3}
                )
                result.append(summary)

        result.extend(layer2_compressed)
        result.extend(layer1_msgs)

        compressed_tokens = sum(m.estimate_tokens() for m in result)
        return CompressionResult(
            compressed_messages=result,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            strategy=self.name,
            metadata={"layer1": len(layer1_msgs), "layer2": len(layer2_compressed), "layer3": len(layer3_original)}
        )


# ============================================================
# 2. 工具输出压缩
# ============================================================

class ToolOutputCompressor:
    """
    工具输出压缩器 — 处理 JSON 裁剪和字段提取。

    典型场景: API 返回大段 JSON，但 LLM 只需其中几个字段。
    """

    def __init__(self):
        self.field_rules: dict[str, list[str]] = {}  # tool_name -> keep_fields

    def register_fields(self, tool_name: str, keep_fields: list[str]) -> None:
        """注册工具的保留字段规则"""
        self.field_rules[tool_name] = keep_fields

    def compress_json(self, data: Any, max_depth: int = 3, max_items: int = 10) -> Any:
        """
        递归压缩 JSON 数据。

        - 截断数组到 max_items
        - 限制嵌套深度到 max_depth
        - 移除 null 值
        """
        return self._compress_recursive(data, max_depth, max_items, current_depth=0)

    def _compress_recursive(self, data: Any, max_depth: int, max_items: int, current_depth: int) -> Any:
        if current_depth >= max_depth:
            if isinstance(data, (dict, list)):
                return f"[... truncated: {type(data).__name__} with {len(data)} items ...]"
            return data

        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                if v is None:
                    continue
                result[k] = self._compress_recursive(v, max_depth, max_items, current_depth + 1)
            return result
        elif isinstance(data, list):
            compressed = []
            for i, item in enumerate(data[:max_items]):
                compressed.append(self._compress_recursive(item, max_depth, max_items, current_depth + 1))
            if len(data) > max_items:
                compressed.append(f"[... {len(data) - max_items} more items ...]")
            return compressed
        else:
            return data

    def extract_fields(self, data: dict, tool_name: str) -> dict:
        """按注册规则提取字段"""
        fields = self.field_rules.get(tool_name)
        if not fields:
            return data

        result = {}
        for f in fields:
            if f in data:
                result[f] = data[f]
        # 保留 _metadata 等系统字段
        for key in ("_metadata", "_status", "_error"):
            if key in data:
                result[key] = data[key]
        return result

    def compress_tool_output(self, message: Message, tool_name: str = "") -> Message:
        """压缩工具输出消息"""
        try:
            data = json.loads(message.content)
        except (json.JSONDecodeError, TypeError):
            # 非 JSON 内容，截断
            if len(message.content) > 2000:
                return Message(
                    role=message.role,
                    content=message.content[:1000] + "\n...[truncated]...\n" + message.content[-500:],
                    metadata={**message.metadata, "compressed": True}
                )
            return message

        # 先提取字段
        if tool_name and tool_name in self.field_rules:
            data = self.extract_fields(data, tool_name)

        # 再压缩结构
        compressed_data = self.compress_json(data, max_depth=3, max_items=5)
        compressed_text = json.dumps(compressed_data, ensure_ascii=False, indent=2)

        return Message(
            role=message.role,
            content=compressed_text,
            metadata={**message.metadata, "compressed": True, "original_tool": tool_name}
        )


# ============================================================
# 3. 代码上下文压缩
# ============================================================

class CodeContextCompressor:
    """
    代码上下文压缩器 — AST 摘要和 diff 压缩。

    由于不依赖 ast 模块解析特定语言，使用正则实现简化版。
    """

    @staticmethod
    def extract_python_signatures(code: str) -> str:
        """
        从 Python 代码中提取类和函数签名（AST 摘要）。

        输出: 仅保留 class/def 行 + docstring 首行
        """
        lines = code.split('\n')
        result = []
        indent_stack = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            # 类定义
            if re.match(r'^class\s+', stripped):
                result.append(line)
                indent_stack.append(len(line) - len(line.lstrip()))
            # 函数/方法定义
            elif re.match(r'^(async\s+)?def\s+', stripped):
                # 检查签名是否跨多行
                sig = line
                if ')' not in stripped:
                    for j in range(i + 1, min(i + 10, len(lines))):
                        sig += ' ' + lines[j].strip()
                        if ')' in lines[j]:
                            break
                result.append(sig)
                indent_stack.append(len(line) - len(line.lstrip()))
            # docstring 首行
            elif stripped.startswith('"""') or stripped.startswith("'''"):
                if len(stripped) > 6:
                    result.append(f"    {stripped[:80]}")
            # import 语句
            elif stripped.startswith('import ') or stripped.startswith('from '):
                result.append(line)

        return '\n'.join(result)

    @staticmethod
    def compress_diff(diff_text: str, context_lines: int = 2) -> str:
        """
        压缩 diff 输出 — 只保留变更行及少量上下文。

        Args:
            diff_text: unified diff 格式文本
            context_lines: 保留的上下文行数
        """
        lines = diff_text.split('\n')
        result = []
        kept_hunks = set()

        for i, line in enumerate(lines):
            # 始终保留文件头
            if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
                result.append(line)
                continue

            # 保留变更行（+/-）
            if line.startswith('+') or line.startswith('-'):
                # 添加上下文
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                for j in range(start, end):
                    if j not in kept_hunks:
                        kept_hunks.add(j)
                        if not lines[j].startswith('+') and not lines[j].startswith('-'):
                            result.append(lines[j])
                if i not in kept_hunks:
                    kept_hunks.add(i)
                    result.append(line)

        return '\n'.join(result)

    @staticmethod
    def compress_code_block(code: str, max_lines: int = 50) -> str:
        """压缩代码块 — 保留签名 + 前 N 行 + 末尾"""
        lines = code.split('\n')
        if len(lines) <= max_lines:
            return code

        signatures = CodeContextCompressor.extract_python_signatures(code)
        head = '\n'.join(lines[:max_lines // 2])
        tail = '\n'.join(lines[-(max_lines // 4):])

        return f"{signatures}\n\n# === 代码正文（前 {max_lines//2} 行） ===\n{head}\n\n# === ... 省略 {len(lines) - max_lines} 行 ... ===\n\n# === 末尾 ===\n{tail}"


# ============================================================
# 4. 压缩触发策略 (Auto-Compact)
# ============================================================

@dataclass
class AutoCompactConfig:
    """自动压缩配置"""
    token_threshold: int = 80000       # 触发压缩的 token 阈值
    target_ratio: float = 0.6          # 压缩目标比例（压缩到原来的 60%）
    min_messages_to_compress: int = 10  # 最少消息数才触发压缩
    cooldown_turns: int = 3            # 压缩后冷却轮数
    preferred_strategy: str = "hierarchical"  # 首选策略


class AutoCompactManager:
    """
    自动压缩管理器 — 根据上下文长度自动触发压缩。

    决策逻辑:
    1. 估算当前 token 总量
    2. 超过阈值 → 选择合适的压缩策略
    3. 执行压缩 → 返回压缩后的消息
    4. 进入冷却期
    """

    def __init__(self, config: Optional[AutoCompactConfig] = None):
        self.config = config or AutoCompactConfig()
        self.strategies: dict[str, CompressionStrategy] = {
            "sliding_window": SlidingWindowCompression(),
            "summary": SummaryCompression(),
            "hierarchical": HierarchicalCompression(),
        }
        self.cooldown_remaining = 0
        self.compaction_history: list[dict] = []

    def register_strategy(self, name: str, strategy: CompressionStrategy) -> None:
        self.strategies[name] = strategy

    def estimate_tokens(self, messages: list[Message]) -> int:
        return sum(m.estimate_tokens() for m in messages)

    def should_compact(self, messages: list[Message]) -> bool:
        """判断是否应该触发压缩"""
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1
            return False
        if len(messages) < self.config.min_messages_to_compress:
            return False
        total_tokens = self.estimate_tokens(messages)
        return total_tokens > self.config.token_threshold

    def select_strategy(self, messages: list[Message]) -> str:
        """
        根据消息特征选择压缩策略。

        - 消息数 < 50 → hierarchical
        - 消息数 50-200 → summary
        - 消息数 > 200 → sliding_window（激进压缩）
        """
        n = len(messages)
        if n < 50:
            return "hierarchical"
        elif n < 200:
            return "summary"
        else:
            return "sliding_window"

    def compact(self, messages: list[Message], strategy_name: Optional[str] = None) -> CompressionResult:
        """执行压缩"""
        total_tokens = self.estimate_tokens(messages)
        budget = int(total_tokens * self.config.target_ratio)

        strategy_key = strategy_name or self.select_strategy(messages)
        strategy = self.strategies[strategy_key]

        result = strategy.compress(messages, budget)

        self.cooldown_remaining = self.config.cooldown_turns
        self.compaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy_key,
            "original_tokens": result.original_tokens,
            "compressed_tokens": result.compressed_tokens,
            "ratio": result.compression_ratio,
        })

        return result

    def maybe_compact(self, messages: list[Message]) -> list[Message]:
        """入口方法: 检查并可能执行压缩"""
        if self.should_compact(messages):
            result = self.compact(messages)
            return result.compressed_messages
        return messages


# ============================================================
# 5. 压缩质量评估
# ============================================================

class CompressionQualityEvaluator:
    """
    压缩质量评估器 — 衡量压缩后的信息保留率。

    评估维度:
    1. 关键信息覆盖率（关键词命中率）
    2. 结构完整性（system/user/assistant 角色是否齐全）
    3. 连续性（最近对话是否完整）
    """

    @staticmethod
    def keyword_retention_rate(original: list[Message], compressed: list[Message]) -> float:
        """计算关键词保留率"""
        def extract_keywords(messages: list[Message]) -> set[str]:
            words = set()
            for m in messages:
                # 简单分词: 按空格和标点拆分，取长度 > 2 的词
                tokens = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', m.content)
                words.update(tokens)
            return words

        orig_kw = extract_keywords(original)
        comp_kw = extract_keywords(compressed)

        if not orig_kw:
            return 1.0
        return len(orig_kw & comp_kw) / len(orig_kw)

    @staticmethod
    def structural_integrity(original: list[Message], compressed: list[Message]) -> dict[str, Any]:
        """检查结构完整性"""
        def role_distribution(messages: list[Message]) -> dict[str, int]:
            dist: dict[str, int] = {}
            for m in messages:
                dist[m.role.value] = dist.get(m.role.value, 0) + 1
            return dist

        orig_roles = role_distribution(original)
        comp_roles = role_distribution(compressed)

        # 检查角色是否都存在
        missing_roles = set(orig_roles.keys()) - set(comp_roles.keys())

        return {
            "original_roles": orig_roles,
            "compressed_roles": comp_roles,
            "missing_roles": list(missing_roles),
            "is_complete": len(missing_roles) == 0,
        }

    @staticmethod
    def recent_completeness(compressed: list[Message], keep_recent: int = 6) -> bool:
        """检查最近对话是否完整保留（无压缩标记）"""
        non_system = [m for m in compressed if m.role != Role.SYSTEM]
        recent = non_system[-keep_recent:]
        for m in recent:
            if m.metadata.get("compressed") or m.metadata.get("compression_marker"):
                return False
        return True

    def evaluate(self, original: list[Message], compressed: list[Message]) -> dict[str, Any]:
        """综合评估"""
        kw_rate = self.keyword_retention_rate(original, compressed)
        structure = self.structural_integrity(original, compressed)
        recent_ok = self.recent_completeness(compressed)

        overall_score = (
            kw_rate * 0.5 +
            (1.0 if structure["is_complete"] else 0.5) * 0.3 +
            (1.0 if recent_ok else 0.3) * 0.2
        )

        return {
            "keyword_retention_rate": round(kw_rate, 3),
            "structural_integrity": structure,
            "recent_completeness": recent_ok,
            "overall_score": round(overall_score, 3),
            "verdict": "PASS" if overall_score >= 0.7 else "WARN" if overall_score >= 0.5 else "FAIL",
        }


# ============================================================
# 组合使用示例
# ============================================================

def demo_conversation_compression():
    """演示: 对话历史压缩"""
    print("=" * 60)
    print("演示 1: 对话历史压缩")
    print("=" * 60)

    # 构造模拟对话
    messages = [
        Message(Role.SYSTEM, "你是一个编程助手，帮助用户解决 Python 问题。"),
    ]
    topics = [
        ("如何用 requests 发送 POST 请求？", "使用 requests.post(url, json=data) 即可。"),
        ("Python 的列表和元组有什么区别？", "列表可变，元组不可变。元组可作为字典键。"),
        ("怎么实现一个装饰器？", "使用 @wraps 装饰内层函数，返回 wrapper。"),
        ("asyncio 怎么用？", "使用 async def 定义协程，await 等待异步结果。"),
        ("什么是上下文管理器？", "实现 __enter__ 和 __exit__ 方法，或用 contextlib。"),
        ("怎么处理异常？", "使用 try/except/else/finally 结构。"),
        ("如何优化数据库查询？", "添加索引、使用 EXPLAIN 分析、避免 N+1 查询。"),
        ("什么是闭包？", "内部函数引用了外部函数的变量，形成闭包。"),
        ("如何实现单例模式？", "使用模块级变量、__new__ 方法或装饰器。"),
        ("Python 的 GIL 是什么？", "全局解释器锁，限制同一时刻只有一个线程执行字节码。"),
        ("怎么用 pathlib 操作文件路径？", "Path('dir') / 'file.txt' 拼接路径。"),
        ("如何写单元测试？", "使用 unittest 或 pytest，assert 断言结果。"),
        ("介绍一下上下文工程", "上下文工程是管理 LLM 输入上下文的系统化方法。"),
        ("现在帮我写一个排序算法", "下面是快速排序的实现: ..."),
    ]

    for user_q, assistant_a in topics:
        messages.append(Message(Role.USER, user_q))
        messages.append(Message(Role.ASSISTANT, assistant_a))

    total_tokens = sum(m.estimate_tokens() for m in messages)
    print(f"原始消息数: {len(messages)}, 估算 token: {total_tokens}")

    # 滑动窗口
    sw = SlidingWindowCompression(keep_recent=6)
    r1 = sw.compress(messages, budget=500)
    print(f"\n[滑动窗口] 压缩后: {len(r1.compressed_messages)} 条, "
          f"token: {r1.compressed_tokens}, 比例: {r1.compression_ratio:.2%}")

    # 摘要式
    sm = SummaryCompression(keep_recent=6)
    r2 = sm.compress(messages, budget=500)
    print(f"[摘要式]   压缩后: {len(r2.compressed_messages)} 条, "
          f"token: {r2.compressed_tokens}, 比例: {r2.compression_ratio:.2%}")

    # 分层保留
    hc = HierarchicalCompression(layer1=6, layer2=10)
    r3 = hc.compress(messages, budget=500)
    print(f"[分层保留] 压缩后: {len(r3.compressed_messages)} 条, "
          f"token: {r3.compressed_tokens}, 比例: {r3.compression_ratio:.2%}")


def demo_tool_output_compression():
    """演示: 工具输出压缩"""
    print("\n" + "=" * 60)
    print("演示 2: 工具输出压缩")
    print("=" * 60)

    # 模拟一个大的 API 返回
    api_response = {
        "status": "success",
        "data": {
            "users": [
                {"id": i, "name": f"User_{i}", "email": f"user{i}@example.com",
                 "profile": {"bio": f"Bio of user {i}" * 10, "avatar": f"https://avatar.example.com/{i}"}}
                for i in range(20)
            ],
            "pagination": {"page": 1, "total_pages": 50, "total_items": 1000}
        },
        "metadata": {"request_id": "abc-123", "latency_ms": 142}
    }

    original = Message(Role.TOOL, json.dumps(api_response, ensure_ascii=False))
    print(f"原始工具输出大小: {len(original.content)} 字符")

    compressor = ToolOutputCompressor()
    compressor.register_fields("get_users", ["status", "data.pagination", "metadata"])

    compressed = compressor.compress_tool_output(original, tool_name="get_users")
    print(f"压缩后大小: {len(compressed.content)} 字符")
    print(f"压缩率: {len(compressed.content) / len(original.content):.1%}")
    print(f"\n压缩后内容:\n{compressed.content[:500]}...")


def demo_code_compression():
    """演示: 代码上下文压缩"""
    print("\n" + "=" * 60)
    print("演示 3: 代码上下文压缩")
    print("=" * 60)

    sample_code = '''
import os
import json
from typing import Any, Optional
from dataclasses import dataclass

@dataclass
class Config:
    """应用配置"""
    name: str
    version: str = "1.0.0"
    debug: bool = False

class Application:
    """主应用类"""

    def __init__(self, config: Config):
        """初始化应用"""
        self.config = config
        self.plugins: list[Any] = []
        self._running = False

    def register_plugin(self, plugin: Any) -> None:
        """注册插件"""
        self.plugins.append(plugin)
        if hasattr(plugin, 'on_register'):
            plugin.on_register(self)

    def run(self) -> None:
        """运行应用"""
        self._running = True
        print(f"Starting {self.config.name} v{self.config.version}")
        for plugin in self.plugins:
            if hasattr(plugin, 'on_start'):
                plugin.on_start()
        # ... many more lines of actual logic ...
        results = []
        for i in range(100):
            result = self._process_item(i)
            results.append(result)
            if i % 10 == 0:
                print(f"Processed {i} items")
        self._running = False

    def _process_item(self, item_id: int) -> dict:
        """处理单个条目"""
        return {"id": item_id, "status": "done"}
'''

    signatures = CodeContextCompressor.extract_python_signatures(sample_code)
    print("提取的签名:")
    print(signatures)

    compressed = CodeContextCompressor.compress_code_block(sample_code, max_lines=20)
    print(f"\n压缩后代码 ({len(compressed.split(chr(10)))} 行):")
    print(compressed[:500])


def demo_auto_compact():
    """演示: 自动压缩触发"""
    print("\n" + "=" * 60)
    print("演示 4: 自动压缩触发 (Auto-Compact)")
    print("=" * 60)

    config = AutoCompactConfig(
        token_threshold=500,  # 故意设低用于演示
        target_ratio=0.5,
        min_messages_to_compress=4,
        cooldown_turns=2,
    )
    manager = AutoCompactManager(config)

    # 构造足够多的消息
    messages = [Message(Role.SYSTEM, "你是一个助手。")]
    for i in range(15):
        messages.append(Message(Role.USER, f"问题 {i}: " + "这是一段较长的问题内容 " * 5))
        messages.append(Message(Role.ASSISTANT, f"回答 {i}: " + "这是一段较长的回答内容 " * 8))

    total = sum(m.estimate_tokens() for m in messages)
    print(f"消息数: {len(messages)}, 总 token: {total}")
    print(f"是否触发压缩: {manager.should_compact(messages)}")

    if manager.should_compact(messages):
        result = manager.compact(messages)
        print(f"压缩结果: {result.original_tokens} → {result.compressed_tokens} tokens")
        print(f"压缩比例: {result.compression_ratio:.2%}")
        print(f"策略: {result.strategy}")

    # 冷却期内不会再次压缩
    print(f"\n冷却期剩余: {manager.cooldown_remaining}")
    print(f"是否再次触发: {manager.should_compact(result.compressed_messages)}")


def demo_quality_evaluation():
    """演示: 压缩质量评估"""
    print("\n" + "=" * 60)
    print("演示 5: 压缩质量评估")
    print("=" * 60)

    original = [
        Message(Role.SYSTEM, "你是一个 Python 专家。"),
        Message(Role.USER, "如何使用 asyncio 实现并发 HTTP 请求？"),
        Message(Role.ASSISTANT, "使用 aiohttp 库配合 asyncio.gather() 可以实现并发请求。"),
        Message(Role.USER, "能给个代码示例吗？"),
        Message(Role.ASSISTANT, "当然。import aiohttp, asyncio。async def fetch(url): ..."),
        Message(Role.USER, "怎么处理超时？"),
        Message(Role.ASSISTANT, "使用 asyncio.wait_for(coro, timeout=10) 设置超时。"),
        Message(Role.USER, "还有其他方式吗？"),
        Message(Role.ASSISTANT, "也可以用 aiohttp.ClientTimeout(total=30) 在 session 级别设置。"),
    ]

    # 模拟压缩结果
    compressed = [
        Message(Role.SYSTEM, "你是一个 Python 专家。", metadata={"compression_marker": True}),
        Message(Role.SYSTEM, "[摘要] 用户询问了 asyncio 并发 HTTP 请求的方法。", metadata={"compression_marker": True}),
        Message(Role.USER, "怎么处理超时？"),
        Message(Role.ASSISTANT, "使用 asyncio.wait_for(coro, timeout=10) 设置超时。"),
        Message(Role.USER, "还有其他方式吗？"),
        Message(Role.ASSISTANT, "也可以用 aiohttp.ClientTimeout(total=30) 在 session 级别设置。"),
    ]

    evaluator = CompressionQualityEvaluator()
    report = evaluator.evaluate(original, compressed)

    print(f"关键词保留率: {report['keyword_retention_rate']:.1%}")
    print(f"结构完整性: {report['structural_integrity']['is_complete']}")
    print(f"最近对话完整: {report['recent_completeness']}")
    print(f"综合评分: {report['overall_score']:.3f}")
    print(f"评估结论: {report['verdict']}")


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    demo_conversation_compression()
    demo_tool_output_compression()
    demo_code_compression()
    demo_auto_compact()
    demo_quality_evaluation()
    print("\n✅ 所有演示完成。")
