"""
多 Agent 上下文隔离设计 — 完整实现
======================================

对应文章: 04-多Agent上下文隔离设计

核心功能:
1. 子 Agent 基类（任务拆分、上下文边界、退出条件）
2. 状态传递策略（精炼摘要、全量传递、文件持久化）
3. LazyContext 延迟加载
4. ArtifactStore 文件持久化
5. 隔离粒度决策树

依赖: 仅标准库
"""

from __future__ import annotations

import json
import os
import hashlib
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


# ============================================================
# 基础数据结构
# ============================================================

class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


class TransferStrategy(str, Enum):
    """状态传递策略"""
    REFINED_SUMMARY = "refined_summary"    # 精炼摘要
    FULL_COPY = "full_copy"                # 全量传递
    FILE_PERSIST = "file_persist"          # 文件持久化
    LAZY_LOAD = "lazy_load"                # 延迟加载


class IsolationLevel(str, Enum):
    """上下文隔离级别"""
    SHARED = "shared"              # 共享上下文（无隔离）
    SELECTIVE = "selective"        # 选择性共享（按需传递关键字段）
    ISOLATED = "isolated"          # 完全隔离（只传递任务描述）
    HYBRID = "hybrid"              # 混合模式（共享系统提示，隔离对话历史）


@dataclass
class Task:
    """任务定义"""
    task_id: str
    description: str
    input_data: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    max_iterations: int = 10
    timeout_seconds: int = 300
    parent_task_id: Optional[str] = None


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    agent_id: str
    status: AgentStatus
    output: Any = None
    summary: str = ""
    artifacts: list[str] = field(default_factory=list)  # 产出物路径列表
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0


@dataclass
class ContextSnapshot:
    """上下文快照 — 在传递时使用"""
    messages: list[dict[str, Any]]
    system_prompt: str
    tool_definitions: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def estimate_tokens(self) -> int:
        total = 0
        for m in self.messages:
            content = m.get("content", "")
            chinese = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            total += int(chinese * 1.5 + (len(content) - chinese) / 4)
        return total


# ============================================================
# 1. 子 Agent 基类
# ============================================================

class BaseAgent(ABC):
    """
    子 Agent 基类 — 定义任务执行的标准接口。

    设计原则:
    - 每个 Agent 拥有独立的上下文空间
    - 通过明确定义的输入/输出接口与外界交互
    - 支持可配置的隔离级别
    """

    def __init__(
        self,
        agent_id: str,
        isolation_level: IsolationLevel = IsolationLevel.SELECTIVE,
        transfer_strategy: TransferStrategy = TransferStrategy.REFINED_SUMMARY,
    ):
        self.agent_id = agent_id
        self.isolation_level = isolation_level
        self.transfer_strategy = transfer_strategy
        self.status = AgentStatus.IDLE
        self.local_context: list[dict[str, Any]] = []
        self.local_memory: dict[str, Any] = {}
        self._iteration_count = 0

    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        """Agent 能力声明"""
        ...

    @abstractmethod
    def execute(self, task: Task, context: Optional[ContextSnapshot] = None) -> TaskResult:
        """执行任务"""
        ...

    def should_continue(self, task: Task) -> bool:
        """退出条件检查"""
        if self._iteration_count >= task.max_iterations:
            return False
        if self.status == AgentStatus.COMPLETED or self.status == AgentStatus.FAILED:
            return False
        return True

    def build_local_context(self, task: Task, parent_context: Optional[ContextSnapshot]) -> ContextSnapshot:
        """
        根据隔离级别构建本地上下文。

        - SHARED: 完全继承父上下文
        - SELECTIVE: 只继承系统提示 + 任务相关消息
        - ISOLATED: 只使用任务描述构建全新上下文
        - HYBRID: 共享系统提示，隔离对话历史
        """
        if self.isolation_level == IsolationLevel.SHARED and parent_context:
            return parent_context

        if self.isolation_level == IsolationLevel.ISOLATED:
            return ContextSnapshot(
                messages=[{"role": "user", "content": task.description}],
                system_prompt=f"你是一个专注于以下任务的 Agent: {task.description}",
                tool_definitions=[],
                metadata={"isolation": "isolated", "agent_id": self.agent_id},
            )

        if self.isolation_level == IsolationLevel.SELECTIVE and parent_context:
            # 选择性继承: 系统提示 + 任务相关消息
            relevant_messages = self._filter_relevant_messages(parent_context.messages, task)
            return ContextSnapshot(
                messages=relevant_messages,
                system_prompt=parent_context.system_prompt,
                tool_definitions=parent_context.tool_definitions,
                metadata={"isolation": "selective", "agent_id": self.agent_id},
            )

        if self.isolation_level == IsolationLevel.HYBRID and parent_context:
            return ContextSnapshot(
                messages=[{"role": "user", "content": task.description}],
                system_prompt=parent_context.system_prompt,
                tool_definitions=parent_context.tool_definitions,
                metadata={"isolation": "hybrid", "agent_id": self.agent_id},
            )

        # 默认: 隔离模式
        return ContextSnapshot(
            messages=[{"role": "user", "content": task.description}],
            system_prompt="你是一个有帮助的助手。",
            tool_definitions=[],
        )

    def _filter_relevant_messages(
        self, messages: list[dict[str, Any]], task: Task, max_messages: int = 10
    ) -> list[dict[str, Any]]:
        """过滤与任务相关的消息"""
        keywords = set(task.description.lower().split())
        scored_messages = []

        for msg in messages:
            content = msg.get("content", "").lower()
            # 关键词匹配打分
            score = sum(1 for kw in keywords if kw in content)
            scored_messages.append((score, msg))

        # 按相关度排序，取 top N
        scored_messages.sort(key=lambda x: x[0], reverse=True)
        relevant = [msg for _, msg in scored_messages[:max_messages] if _ > 0]

        # 如果没有匹配的，返回最近的消息
        if not relevant:
            relevant = messages[-max_messages:]

        return relevant


# ============================================================
# 2. 状态传递策略
# ============================================================

class StateTransfer:
    """
    状态传递器 — 在 Agent 之间传递上下文。

    支持三种策略:
    1. 精炼摘要: 将上下文压缩为关键信息摘要
    2. 全量传递: 完整复制上下文（注意 token 开销）
    3. 文件持久化: 将上下文写入文件，下游 Agent 按需读取
    """

    def __init__(self, strategy: TransferStrategy = TransferStrategy.REFINED_SUMMARY):
        self.strategy = strategy
        self.summarizer: Optional[Callable[[ContextSnapshot], str]] = None

    def transfer(
        self,
        source_context: ContextSnapshot,
        target_agent: BaseAgent,
        task: Task,
    ) -> ContextSnapshot:
        """执行状态传递"""
        if self.strategy == TransferStrategy.REFINED_SUMMARY:
            return self._refined_summary_transfer(source_context, target_agent, task)
        elif self.strategy == TransferStrategy.FULL_COPY:
            return self._full_copy_transfer(source_context, target_agent, task)
        elif self.strategy == TransferStrategy.FILE_PERSIST:
            return self._file_persist_transfer(source_context, target_agent, task)
        elif self.strategy == TransferStrategy.LAZY_LOAD:
            return self._lazy_load_transfer(source_context, target_agent, task)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def _refined_summary_transfer(
        self, source: ContextSnapshot, target: BaseAgent, task: Task
    ) -> ContextSnapshot:
        """精炼摘要传递 — 压缩上下文后传递"""
        if self.summarizer:
            summary_text = self.summarizer(source)
        else:
            summary_text = self._default_summarize(source)

        return ContextSnapshot(
            messages=[
                {"role": "system", "content": f"[来自上游 Agent 的上下文摘要]\n{summary_text}"},
                {"role": "user", "content": task.description},
            ],
            system_prompt=source.system_prompt,
            tool_definitions=source.tool_definitions,
            metadata={
                "transfer_strategy": "refined_summary",
                "source_agent": source.metadata.get("agent_id", "unknown"),
                "original_token_count": source.estimate_tokens(),
            },
        )

    @staticmethod
    def _default_summarize(context: ContextSnapshot) -> str:
        """默认摘要: 提取每条消息的关键信息"""
        parts = []
        for msg in context.messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            # 取前 200 字符
            snippet = content[:200].replace("\n", " ")
            parts.append(f"[{role}] {snippet}{'...' if len(content) > 200 else ''}")
        return "\n".join(parts[-10:])  # 只保留最近 10 条

    def _full_copy_transfer(
        self, source: ContextSnapshot, target: BaseAgent, task: Task
    ) -> ContextSnapshot:
        """全量传递 — 完整复制上下文"""
        new_messages = list(source.messages) + [{"role": "user", "content": task.description}]
        return ContextSnapshot(
            messages=new_messages,
            system_prompt=source.system_prompt,
            tool_definitions=source.tool_definitions,
            metadata={"transfer_strategy": "full_copy"},
        )

    def _file_persist_transfer(
        self, source: ContextSnapshot, target: BaseAgent, task: Task
    ) -> ContextSnapshot:
        """文件持久化传递 — 写入文件，下游按需读取"""
        persist_dir = Path(tempfile.gettempdir()) / "agent_context"
        persist_dir.mkdir(exist_ok=True)

        file_path = persist_dir / f"{target.agent_id}_context.json"
        data = {
            "messages": source.messages,
            "system_prompt": source.system_prompt,
            "tool_definitions": source.tool_definitions,
            "metadata": source.metadata,
            "persisted_at": datetime.now().isoformat(),
        }
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        return ContextSnapshot(
            messages=[
                {"role": "system", "content": f"上下文已持久化到: {file_path}"},
                {"role": "user", "content": task.description},
            ],
            system_prompt=source.system_prompt,
            tool_definitions=source.tool_definitions,
            metadata={
                "transfer_strategy": "file_persist",
                "persisted_file": str(file_path),
            },
        )

    def _lazy_load_transfer(
        self, source: ContextSnapshot, target: BaseAgent, task: Task
    ) -> ContextSnapshot:
        """延迟加载传递 — 创建 LazyContext 代理"""
        # 实际使用中返回 LazyContext（见下文），这里简化为返回引用
        return ContextSnapshot(
            messages=[{"role": "user", "content": task.description}],
            system_prompt=source.system_prompt,
            tool_definitions=source.tool_definitions,
            metadata={
                "transfer_strategy": "lazy_load",
                "source_messages_count": len(source.messages),
            },
        )


# ============================================================
# 3. LazyContext 延迟加载
# ============================================================

class LazyContext:
    """
    延迟加载上下文代理 — 按需加载上下文内容。

    适用场景:
    - 子 Agent 可能只需要上下文的一小部分
    - 上下文非常大，全量传递浪费 token
    - 多个 Agent 共享同一份上下文，各自只读取需要的部分
    """

    def __init__(self, source: ContextSnapshot):
        self._source = source
        self._loaded_sections: dict[str, Any] = {}
        self._access_log: list[tuple[str, datetime]] = []

    def get_system_prompt(self) -> str:
        """获取系统提示（始终可用）"""
        self._log_access("system_prompt")
        return self._source.system_prompt

    def get_messages(self, limit: int = 10, role_filter: Optional[str] = None) -> list[dict[str, Any]]:
        """
        按需加载消息。

        Args:
            limit: 最多返回消息数
            role_filter: 只返回指定角色的消息
        """
        self._log_access(f"messages(limit={limit}, role={role_filter})")

        messages = self._source.messages
        if role_filter:
            messages = [m for m in messages if m.get("role") == role_filter]
        return messages[-limit:]

    def search_messages(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """搜索消息（按关键词匹配）"""
        self._log_access(f"search({query[:30]})")

        keywords = query.lower().split()
        scored = []
        for msg in self._source.messages:
            content = msg.get("content", "").lower()
            score = sum(1 for kw in keywords if kw in content)
            if score > 0:
                scored.append((score, msg))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [msg for _, msg in scored[:max_results]]

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """获取工具定义"""
        self._log_access("tool_definitions")
        return self._source.tool_definitions

    def get_metadata(self) -> dict[str, Any]:
        """获取元数据"""
        return self._source.metadata

    def get_access_stats(self) -> dict[str, Any]:
        """获取访问统计"""
        access_counts: dict[str, int] = {}
        for section, _ in self._access_log:
            access_counts[section] = access_counts.get(section, 0) + 1
        return {
            "total_accesses": len(self._access_log),
            "section_counts": access_counts,
            "source_tokens": self._source.estimate_tokens(),
            "cached_sections": list(self._loaded_sections.keys()),
        }

    def _log_access(self, section: str) -> None:
        self._access_log.append((section, datetime.now()))


# ============================================================
# 4. ArtifactStore 文件持久化
# ============================================================

@dataclass
class Artifact:
    """产出物"""
    artifact_id: str
    name: str
    content_type: str            # "json", "text", "code", "binary"
    file_path: str
    created_by: str              # agent_id
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0


class ArtifactStore:
    """
    产出物存储 — Agent 之间的持久化数据交换。

    设计原则:
    - 每个 Agent 只能写入自己的产出物
    - 读取时按需加载，不占用上下文空间
    - 支持元数据查询（无需读取内容）
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or tempfile.mkdtemp(prefix="agent_artifacts_"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._index: dict[str, Artifact] = {}
        self._load_index()

    def _index_path(self) -> Path:
        return self.base_dir / "_index.json"

    def _load_index(self) -> None:
        """加载索引"""
        idx_path = self._index_path()
        if idx_path.exists():
            data = json.loads(idx_path.read_text(encoding="utf-8"))
            for item in data:
                artifact = Artifact(
                    artifact_id=item["artifact_id"],
                    name=item["name"],
                    content_type=item["content_type"],
                    file_path=item["file_path"],
                    created_by=item["created_by"],
                    created_at=datetime.fromisoformat(item["created_at"]),
                    metadata=item.get("metadata", {}),
                    size_bytes=item.get("size_bytes", 0),
                )
                self._index[artifact.artifact_id] = artifact

    def _save_index(self) -> None:
        """保存索引"""
        data = []
        for a in self._index.values():
            data.append({
                "artifact_id": a.artifact_id,
                "name": a.name,
                "content_type": a.content_type,
                "file_path": a.file_path,
                "created_by": a.created_by,
                "created_at": a.created_at.isoformat(),
                "metadata": a.metadata,
                "size_bytes": a.size_bytes,
            })
        self._index_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def store(self, agent_id: str, name: str, content: str, content_type: str = "text",
              metadata: Optional[dict[str, Any]] = None) -> Artifact:
        """
        存储产出物。

        Args:
            agent_id: 写入 Agent 的 ID
            name: 产出物名称
            content: 内容
            content_type: 内容类型
            metadata: 附加元数据
        Returns:
            Artifact 对象
        """
        artifact_id = hashlib.md5(f"{agent_id}:{name}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        agent_dir = self.base_dir / agent_id
        agent_dir.mkdir(exist_ok=True)

        ext_map = {"json": ".json", "text": ".txt", "code": ".py", "binary": ".bin"}
        ext = ext_map.get(content_type, ".txt")
        file_path = agent_dir / f"{artifact_id}{ext}"

        file_path.write_text(content, encoding="utf-8")

        artifact = Artifact(
            artifact_id=artifact_id,
            name=name,
            content_type=content_type,
            file_path=str(file_path),
            created_by=agent_id,
            metadata=metadata or {},
            size_bytes=len(content.encode("utf-8")),
        )

        self._index[artifact_id] = artifact
        self._save_index()
        return artifact

    def load(self, artifact_id: str) -> Optional[str]:
        """按需加载产出物内容"""
        artifact = self._index.get(artifact_id)
        if not artifact:
            return None
        path = Path(artifact.file_path)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def query(self, agent_id: Optional[str] = None, name_pattern: Optional[str] = None) -> list[Artifact]:
        """查询产出物元数据（不加载内容）"""
        results = list(self._index.values())
        if agent_id:
            results = [a for a in results if a.created_by == agent_id]
        if name_pattern:
            results = [a for a in results if name_pattern.lower() in a.name.lower()]
        return sorted(results, key=lambda a: a.created_at, reverse=True)

    def list_all(self) -> list[Artifact]:
        """列出所有产出物"""
        return list(self._index.values())


# ============================================================
# 5. 隔离粒度决策树
# ============================================================

@dataclass
class IsolationDecision:
    """隔离决策结果"""
    level: IsolationLevel
    strategy: TransferStrategy
    reason: str
    factors: dict[str, Any] = field(default_factory=dict)


class IsolationDecisionTree:
    """
    隔离粒度决策树 — 根据任务特征自动选择隔离级别。

    决策因素:
    1. 上下文大小 (token 数)
    2. 子任务独立性
    3. 信息敏感性
    4. Agent 数量
    5. 任务复杂度
    """

    def decide(
        self,
        context_tokens: int,
        task_independence: float,       # 0.0(强依赖) ~ 1.0(完全独立)
        sensitive_info: bool = False,
        agent_count: int = 1,
        task_complexity: str = "medium",  # "low", "medium", "high"
    ) -> IsolationDecision:
        """
        根据输入因素做出隔离决策。

        Args:
            context_tokens: 上下文 token 数
            task_independence: 任务独立性评分 (0~1)
            sensitive_info: 是否包含敏感信息
            agent_count: 子 Agent 数量
            task_complexity: 任务复杂度
        Returns:
            IsolationDecision
        """
        factors = {
            "context_tokens": context_tokens,
            "task_independence": task_independence,
            "sensitive_info": sensitive_info,
            "agent_count": agent_count,
            "task_complexity": task_complexity,
        }

        # 规则 1: 敏感信息 → 隔离
        if sensitive_info:
            return IsolationDecision(
                level=IsolationLevel.ISOLATED,
                strategy=TransferStrategy.REFINED_SUMMARY,
                reason="包含敏感信息，强制隔离",
                factors=factors,
            )

        # 规则 2: 上下文非常大 → 文件持久化 + 延迟加载
        if context_tokens > 100000:
            return IsolationDecision(
                level=IsolationLevel.SELECTIVE,
                strategy=TransferStrategy.LAZY_LOAD,
                reason=f"上下文过大 ({context_tokens} tokens)，使用延迟加载",
                factors=factors,
            )

        # 规则 3: 多 Agent + 高独立性 → 隔离
        if agent_count >= 3 and task_independence > 0.7:
            return IsolationDecision(
                level=IsolationLevel.ISOLATED,
                strategy=TransferStrategy.REFINED_SUMMARY,
                reason=f"多 Agent ({agent_count}) + 高独立性 ({task_independence:.1f})",
                factors=factors,
            )

        # 规则 4: 上下文较大 → 选择性共享 + 摘要
        if context_tokens > 30000:
            return IsolationDecision(
                level=IsolationLevel.SELECTIVE,
                strategy=TransferStrategy.REFINED_SUMMARY,
                reason=f"上下文较大 ({context_tokens} tokens)，选择性共享",
                factors=factors,
            )

        # 规则 5: 高独立性任务 → 隔离
        if task_independence > 0.8:
            return IsolationDecision(
                level=IsolationLevel.ISOLATED,
                strategy=TransferStrategy.REFINED_SUMMARY,
                reason=f"任务高度独立 ({task_independence:.1f})",
                factors=factors,
            )

        # 规则 6: 低独立性 + 低复杂度 → 混合模式
        if task_independence < 0.3 and task_complexity == "low":
            return IsolationDecision(
                level=IsolationLevel.HYBRID,
                strategy=TransferStrategy.FULL_COPY,
                reason=f"强依赖 ({task_independence:.1f}) + 低复杂度",
                factors=factors,
            )

        # 默认: 选择性共享
        return IsolationDecision(
            level=IsolationLevel.SELECTIVE,
            strategy=TransferStrategy.REFINED_SUMMARY,
            reason="默认策略: 选择性共享 + 精炼摘要",
            factors=factors,
        )


# ============================================================
# 具体 Agent 实现示例
# ============================================================

class CodeAgent(BaseAgent):
    """代码编写 Agent"""

    @property
    def capabilities(self) -> list[str]:
        return ["code_generation", "code_review", "refactoring"]

    def execute(self, task: Task, context: Optional[ContextSnapshot] = None) -> TaskResult:
        local_ctx = self.build_local_context(task, context)
        self.status = AgentStatus.RUNNING

        # 模拟代码生成
        code_output = f'''# Generated by {self.agent_id}
# Task: {task.description}

def solution():
    """Auto-generated solution"""
    # Implementation based on task constraints:
    # {chr(10).join(f"# - {c}" for c in task.constraints)}
    return "solution_result"
'''
        self.status = AgentStatus.COMPLETED
        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output=code_output,
            summary=f"为任务 {task.task_id} 生成了代码",
            metadata={"lines_of_code": code_output.count(chr(10))},
        )


class ResearchAgent(BaseAgent):
    """研究 Agent"""

    @property
    def capabilities(self) -> list[str]:
        return ["research", "analysis", "summarization"]

    def execute(self, task: Task, context: Optional[ContextSnapshot] = None) -> TaskResult:
        local_ctx = self.build_local_context(task, context)
        self.status = AgentStatus.RUNNING

        # 模拟研究分析
        analysis = f"针对 '{task.description}' 的分析结果:\n1. 关键发现 A\n2. 关键发现 B\n3. 建议"

        self.status = AgentStatus.COMPLETED
        return TaskResult(
            task_id=task.task_id,
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output=analysis,
            summary=f"完成了关于 {task.description[:30]}... 的研究分析",
        )


# ============================================================
# 多 Agent 编排器
# ============================================================

class AgentOrchestrator:
    """
    Agent 编排器 — 管理多个子 Agent 的协作。

    职责:
    - 任务拆分和分配
    - 上下文传递策略管理
    - 结果汇总
    """

    def __init__(self, artifact_store: Optional[ArtifactStore] = None):
        self.agents: dict[str, BaseAgent] = {}
        self.artifact_store = artifact_store or ArtifactStore()
        self.decision_tree = IsolationDecisionTree()
        self.execution_log: list[dict[str, Any]] = []

    def register_agent(self, agent: BaseAgent) -> None:
        self.agents[agent.agent_id] = agent

    def execute_task(
        self,
        task: Task,
        agent_id: str,
        parent_context: Optional[ContextSnapshot] = None,
    ) -> TaskResult:
        """在指定 Agent 上执行任务"""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # 自动选择隔离策略
        context_tokens = parent_context.estimate_tokens() if parent_context else 0
        decision = self.decision_tree.decide(
            context_tokens=context_tokens,
            task_independence=0.5,
            agent_count=len(self.agents),
        )

        agent.isolation_level = decision.level
        agent.transfer_strategy = decision.strategy

        self.execution_log.append({
            "task_id": task.task_id,
            "agent_id": agent_id,
            "isolation_level": decision.level.value,
            "transfer_strategy": decision.strategy.value,
            "reason": decision.reason,
            "timestamp": datetime.now().isoformat(),
        })

        result = agent.execute(task, parent_context)

        # 存储产出物
        if result.output:
            artifact = self.artifact_store.store(
                agent_id=agent_id,
                name=f"{task.task_id}_output",
                content=str(result.output),
                content_type="text",
            )
            result.artifacts.append(artifact.artifact_id)

        return result

    def execute_parallel(
        self,
        tasks: list[tuple[Task, str]],
        shared_context: Optional[ContextSnapshot] = None,
    ) -> list[TaskResult]:
        """并行执行多个任务（简化版：顺序执行，实际可用 asyncio 并发）"""
        results = []
        for task, agent_id in tasks:
            result = self.execute_task(task, agent_id, shared_context)
            results.append(result)
        return results

    def get_execution_summary(self) -> dict[str, Any]:
        return {
            "total_tasks": len(self.execution_log),
            "agents_used": list(set(log["agent_id"] for log in self.execution_log)),
            "isolation_levels": {
                level: sum(1 for log in self.execution_log if log["isolation_level"] == level)
                for level in set(log["isolation_level"] for log in self.execution_log)
            } if self.execution_log else {},
            "artifacts_stored": len(self.artifact_store.list_all()),
        }


# ============================================================
# 使用示例
# ============================================================

def demo_basic_agent():
    """演示: 基本 Agent 使用"""
    print("=" * 60)
    print("演示 1: 基本 Agent 使用")
    print("=" * 60)

    code_agent = CodeAgent("code_agent_1", isolation_level=IsolationLevel.SELECTIVE)
    task = Task(
        task_id="task_001",
        description="实现一个快速排序算法",
        constraints=["使用 Python", "支持自定义比较函数"],
    )

    result = code_agent.execute(task)
    print(f"状态: {result.status.value}")
    print(f"摘要: {result.summary}")
    print(f"输出:\n{result.output}")


def demo_state_transfer():
    """演示: 状态传递策略"""
    print("\n" + "=" * 60)
    print("演示 2: 状态传递策略")
    print("=" * 60)

    # 源上下文
    source_ctx = ContextSnapshot(
        messages=[
            {"role": "user", "content": "帮我分析 Python 的性能优化策略"},
            {"role": "assistant", "content": "主要策略包括: 1) 使用 C 扩展 2) 利用多进程 3) 算法优化"},
            {"role": "user", "content": "具体说说多进程怎么用？"},
            {"role": "assistant", "content": "使用 multiprocessing.Pool 进行并行计算..."},
        ],
        system_prompt="你是一个 Python 性能优化专家。",
        tool_definitions=[{"name": "profile", "description": "性能分析工具"}],
    )

    target_agent = ResearchAgent("research_agent_1")
    task = Task(task_id="task_002", description="总结 Python 多进程的最佳实践")

    # 精炼摘要
    transfer = StateTransfer(TransferStrategy.REFINED_SUMMARY)
    ctx_summary = transfer.transfer(source_ctx, target_agent, task)
    print("[精炼摘要传递]")
    for msg in ctx_summary.messages:
        print(f"  [{msg['role']}] {msg['content'][:80]}...")

    # 全量传递
    transfer_full = StateTransfer(TransferStrategy.FULL_COPY)
    ctx_full = transfer_full.transfer(source_ctx, target_agent, task)
    print(f"\n[全量传递] 消息数: {len(ctx_full.messages)}")


def demo_lazy_context():
    """演示: LazyContext 延迟加载"""
    print("\n" + "=" * 60)
    print("演示 3: LazyContext 延迟加载")
    print("=" * 60)

    # 大量上下文
    large_context = ContextSnapshot(
        messages=[
            {"role": "user", "content": f"消息 {i}: 这是第 {i} 条消息的内容"} for i in range(100)
        ] + [
            {"role": "assistant", "content": "这是关于 Python 装饰器的回答: 装饰器是闭包的应用..."}
        ],
        system_prompt="你是一个编程助手。",
        tool_definitions=[],
    )

    lazy = LazyContext(large_context)

    # 按需获取最近 3 条消息
    recent = lazy.get_messages(limit=3)
    print("最近 3 条消息:")
    for msg in recent:
        print(f"  [{msg['role']}] {msg['content'][:50]}...")

    # 搜索关键词
    results = lazy.search_messages("装饰器")
    print(f"\n搜索 '装饰器' 结果: {len(results)} 条")
    for msg in results:
        print(f"  [{msg['role']}] {msg['content'][:60]}...")

    # 访问统计
    stats = lazy.get_access_stats()
    print(f"\n访问统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")


def demo_artifact_store():
    """演示: ArtifactStore 文件持久化"""
    print("\n" + "=" * 60)
    print("演示 4: ArtifactStore 文件持久化")
    print("=" * 60)

    store = ArtifactStore(base_dir="/tmp/demo_artifacts")

    # Agent A 存储代码
    art1 = store.store("code_agent", "排序算法", "def quicksort(arr):\n    ...", content_type="code")
    print(f"存储: {art1.name} -> {art1.file_path}")

    # Agent B 存储分析报告
    art2 = store.store("research_agent", "性能分析报告", "性能测试结果: ...", content_type="text")
    print(f"存储: {art2.name} -> {art2.file_path}")

    # 查询
    all_artifacts = store.list_all()
    print(f"\n所有产出物: {len(all_artifacts)}")
    for a in all_artifacts:
        print(f"  {a.name} by {a.created_by} ({a.content_type}, {a.size_bytes} bytes)")

    # 按需加载
    content = store.load(art1.artifact_id)
    print(f"\n加载 {art1.name}:\n{content}")


def demo_decision_tree():
    """演示: 隔离粒度决策树"""
    print("\n" + "=" * 60)
    print("演示 5: 隔离粒度决策树")
    print("=" * 60)

    tree = IsolationDecisionTree()

    scenarios = [
        {"context_tokens": 5000, "task_independence": 0.9, "sensitive_info": False,
         "agent_count": 1, "task_complexity": "low", "label": "简单独立任务"},
        {"context_tokens": 50000, "task_independence": 0.5, "sensitive_info": False,
         "agent_count": 3, "task_complexity": "medium", "label": "中等多 Agent 任务"},
        {"context_tokens": 150000, "task_independence": 0.3, "sensitive_info": False,
         "agent_count": 5, "task_complexity": "high", "label": "大规模复杂任务"},
        {"context_tokens": 10000, "task_independence": 0.6, "sensitive_info": True,
         "agent_count": 2, "task_complexity": "medium", "label": "含敏感信息任务"},
        {"context_tokens": 5000, "task_independence": 0.1, "sensitive_info": False,
         "agent_count": 1, "task_complexity": "low", "label": "强依赖低复杂度任务"},
    ]

    for s in scenarios:
        label = s.pop("label")
        decision = tree.decide(**s)
        print(f"\n【{label}】")
        print(f"  输入: {json.dumps(s, ensure_ascii=False)}")
        print(f"  隔离级别: {decision.level.value}")
        print(f"  传递策略: {decision.strategy.value}")
        print(f"  原因: {decision.reason}")


def demo_full_orchestration():
    """演示: 完整多 Agent 编排"""
    print("\n" + "=" * 60)
    print("演示 6: 完整多 Agent 编排")
    print("=" * 60)

    store = ArtifactStore(base_dir="/tmp/demo_orchestrator")
    orchestrator = AgentOrchestrator(artifact_store=store)

    orchestrator.register_agent(CodeAgent("coder"))
    orchestrator.register_agent(ResearchAgent("researcher"))

    # 共享上下文
    shared_ctx = ContextSnapshot(
        messages=[
            {"role": "user", "content": "开发一个高性能的 Python Web API"},
            {"role": "assistant", "content": "建议使用 FastAPI 框架..."},
        ],
        system_prompt="你是一个全栈开发团队。",
        tool_definitions=[],
    )

    # 拆分任务
    tasks = [
        (Task("t1", "设计 API 路由结构", constraints=["RESTful", "版本化"]), "coder"),
        (Task("t2", "调研 FastAPI 性能基准测试结果", constraints=["最新数据"]), "researcher"),
        (Task("t3", "实现核心数据处理逻辑", constraints=["异步", "类型标注"]), "coder"),
    ]

    results = orchestrator.execute_parallel(tasks, shared_context=shared_ctx)

    for r in results:
        print(f"任务 {r.task_id}: {r.status.value} — {r.summary}")
        if r.artifacts:
            print(f"  产出物: {r.artifacts}")

    summary = orchestrator.get_execution_summary()
    print(f"\n编排摘要: {json.dumps(summary, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    demo_basic_agent()
    demo_state_transfer()
    demo_lazy_context()
    demo_artifact_store()
    demo_decision_tree()
    demo_full_orchestration()
    print("\n✅ 所有演示完成。")
