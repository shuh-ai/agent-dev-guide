# CLI Agentic Coding 工程实践：从单Agent到多Agent协作

> **一句话定位**：2026年，终端成了 AI 编程的主战场。不再是"IDE 侧边栏给建议"，而是"终端里跑一个能自主工作几小时的编程 Agent"。

---

## 一、范式转变：从建议到委托

### 1.1 IDE 助手 vs CLI Agent

| 维度 | IDE 助手（2024） | CLI Agent（2026） |
|------|----------------|------------------|
| 交互模式 | 逐行建议 → 人工确认 | 任务委托 → 自主执行 |
| 工作范围 | 单文件、当前光标位置 | 跨文件、整个代码库 |
| 自主程度 | 每个修改都需要人批准 | 可以自主工作数小时 |
| 工作方式 | 你编程，它辅助 | 它编程，你审查 |
| 典型工具 | GitHub Copilot 侧边栏 | Claude Code、Codex CLI |

**Anthropic 的总结**：你和 IDE 助手是结对编程（pair programming），你和 CLI Agent 是委托编程（delegation programming）。

### 1.2 2026年 CLI Agent 生态全景

| 工具 | 提供商 | 模型 | 定位 |
|------|--------|------|------|
| **Claude Code** | Anthropic | Claude Opus 4.7 | 终端优先，深度代码理解 |
| **Codex CLI** | OpenAI | GPT-5.5 | 云端异步，并行任务 |
| **OpenCode** | 开源 | 多模型 | 提供商无关，灵活切换 |
| **Gemini CLI** | Google | Gemini 3.1 | 免费，1M token 上下文 |
| **GitHub Copilot CLI** | GitHub/Microsoft | 多模型 | 深度集成 GitHub 工作流 |
| **Aider** | 开源 | 多模型 | 轻量级，git 感知 |
| **Cursor** | Cursor | 多模型 | AI 原生 IDE |

---

## 二、核心工具深度对比

### 2.1 Claude Code

**定位**：终端优先的 Agentic 编程工具

**核心能力**：
- 读取整个代码库，理解项目结构
- 编辑文件、执行命令、管理 git 工作流
- 子Agent系统：并行派出多个探索Agent
- Computer Use：可以操作浏览器、截图

**架构特点**：
- **检查点系统**：每次编辑前快照文件，所有修改可回滚
- **CLAUDE.md**：项目级配置文件，定义约定和上下文
- **MCP 集成**：通过 MCP 连接外部工具（浏览器、数据库等）

**实际案例**：
- Rakuten：在 1250 万行代码的 vLLM 库中，7 小时自主完成激活向量提取方法实现，数值精度 99.9%
- Augment Code：企业客户用 Claude Code 将预计 4-8 个月的项目在 2 周内完成

**定价**：Claude Max 订阅（$100-200/月），或 API 按量计费

### 2.2 Codex CLI

**定位**：云端异步编程 Agent

**核心能力**：
- 云端执行，不占本地资源
- 支持并行运行多个任务
- OS 级沙箱（Landlock/seccomp on Linux，AppContainer on Windows）

**架构特点**：
- **异步模型**：提交任务后去做别的事，完成后通知
- **exec 子命令**：可以链式调用多个 Codex 运行
- **安全沙箱**：限制文件系统和网络访问

**和 Claude Code 的关键区别**：

| 维度 | Claude Code | Codex CLI |
|------|------------|-----------|
| 执行位置 | 本地终端 | 云端 |
| 交互模式 | 实时交互 | 异步提交 |
| 上下文大小 | 大（支持 Computer Use） | 中等 |
| 并行能力 | 子Agent并行 | 多任务并行 |
| 最佳场景 | 复杂代码库、架构设计 | 明确任务、批量执行 |

### 2.3 OpenCode + 生态

**定位**：开源、提供商无关的 CLI Agent

**核心优势**：
- 不绑定任何模型提供商
- 社区插件生态（Oh-My-OpenCode）
- 支持 ultrawork 模式（高效后台任务）

**Oh-My-OpenCode 插件**：
- 子Agent系统：自动为文件分析、上下文收集等任务派出子Agent
- 与 Claude Code 的 Superpowers 插件竞争

---

## 三、多Agent协作架构

### 3.1 为什么需要多Agent

单Agent的天花板：
- **上下文窗口限制**：有效上下文一直卡在 80-120K token，不管宣称多大
- **串行瓶颈**：一个Agent一次只能做一件事
- **视角单一**：一个Agent容易陷入局部最优

### 3.2 主流多Agent模式

**模式一：Orchestrator + Subagents（编排者 + 子Agent）**

```
主Agent（编排者）
    ├── 子Agent 1：分析代码结构
    ├── 子Agent 2：搜索相关文件
    ├── 子Agent 3：运行测试
    └── 子Agent 4：检查文档
         │
         ▼
    主Agent 综合结果 → 输出
```

- 代表：Claude Code、OpenCode + Oh-My-OpenCode
- 优点：分工明确，并行执行
- 缺点：子Agent之间不通信

**模式二：三探索者 + 评审者（3+1 模式）**

```
编排者
    ├── 探索者 A：方案一（独立上下文）
    ├── 探索者 B：方案二（独立上下文）
    ├── 探索者 C：方案三（独立上下文）
    └── 评审者：评估三个方案 → 选最优
```

- 代表：Claude Code Ultra Plan
- 优点：多视角避免局部最优
- 缺点：成本 x4

**模式三：数据库协调（大规模并行）**

```
数据库（协调层）
    ├── Agent 1：子任务 A
    ├── Agent 2：子任务 B
    ├── ...
    └── Agent N：子任务 N
```

- 代表：Blitzy 的企业级系统
- 优点：可扩展到数万个并行Agent
- 缺点：架构复杂度高

### 3.3 AGENTS.md：Agent 的"全局样式表"

2026年的一个重要约定：**AGENTS.md** 文件。

```
项目根目录/
├── AGENTS.md          ← 所有Agent共享的项目约定
├── CLAUDE.md          ← Claude Code 特定配置
├── .cursorrules       ← Cursor 特定配置
└── ...
```

**AGENTS.md 的作用**：
- 定义构建命令、代码规范、文件结构
- 所有子Agent自动继承
- Vercel 的评测显示：AGENTS.md 在构建/检查/测试任务中达到 100% 通过率，而 Skills 方案最高 79%

**类比**：就像 CSS 的全局样式会级联到每个元素，AGENTS.md 的规则会级联到每个子Agent。

---

## 四、工程实践

### 4.1 开发工作流

**日常开发流程**：

```bash
# 1. 启动 Claude Code
claude

# 2. 描述任务
> 给 UserService 添加缓存层，使用 Redis，需要支持 TTL 和手动失效

# 3. Claude Code 自动：
#    - 分析现有代码结构
#    - 设计缓存方案
#    - 编写实现代码
#    - 添加单元测试
#    - 更新文档
#    - 创建 git commit

# 4. 你审查结果
> 看起来不错，但 TTL 默认值改成 300 秒

# 5. Claude Code 修改
```

**复杂任务的多Agent流程**：

```bash
# 启动 planning 模式
> /plan 重构支付模块，支持多种支付方式

# Claude Code 派出多个子Agent并行探索：
#   子Agent 1：分析现有支付代码
#   子Agent 2：调研支付接口规范
#   子Agent 3：检查测试覆盖

# 主Agent 综合结果，生成重构计划
# 你确认后，主Agent 开始执行
```

### 4.2 插件与 Skills

**Superpowers（Claude Code 插件）**：
- 显著提升 Planning 模式的表现
- 更智能的问题提问
- 自动派出子Agent收集上下文
- 集成测试套件验证代码质量

**Skills（技能文件）**：
- Markdown 格式的指令文件
- 注入系统提示中
- 定义特定任务的工作流
- 示例：代码审查 Skill、测试生成 Skill、文档编写 Skill

### 4.3 安全实践

**沙箱配置**：

```bash
# Claude Code：检查点系统（自动快照，可回滚）
# 所有文件编辑前自动备份

# Codex CLI：OS 级沙箱
codex --sandbox landlock  # Linux
codex --sandbox appcontainer  # Windows
```

**最佳实践**：
- 明确任务边界，不要给 Agent 过大的权限
- 使用 git 分支隔离 Agent 的修改
- 关键操作（删除文件、修改配置）需要人工确认
- 定期审查 Agent 的工作记录

---

## 五、和现有内容的关系

本文聚焦**工具选型和工程实践**。关于更深层的架构设计思想（如 Harness Engineering——如何设计让 Agent 写代码的运行时环境），请参考本仓库的 Harness Engineering 系列文章：

- [Harness基础概念与核心架构](../01-核心能力专题/Harness%20Engineering/01-Harness基础概念与核心架构.md)
- [Harness四大支柱详解](../01-核心能力专题/Harness%20Engineering/02-Harness四大支柱详解.md)
- [Harness行业案例与平台对比](../01-核心能力专题/Harness%20Engineering/03-Harness行业案例与平台对比.md)

**区别**：
- Harness Engineering 讲的是"怎么设计环境让 Agent 更好地写代码"
- 本文讲的是"2026年有哪些 CLI Agent 工具，怎么用，怎么协作"

---

## 六、趋势展望

### 6.1 终端成为主战场

2026年所有大厂都在 CLI Agent 上发力：
- VS Code 2026年2月更新：支持在编辑器中直接运行 Claude 和 Codex Agent
- Anthropic 发布《2026 Agentic Coding Trends Report》
- 多Agent开发成为 VS Code 的一等公民

### 6.2 从"写代码"到"完成任务"

CLI Agent 的能力边界在扩展：
- 不只是写代码，还能做研究、分析数据、写文档
- Claude Code 的 Computer Use 让它可以操作浏览器
- 非技术用户也开始用 CLI Agent（内容营销、金融分析、学术研究）

### 6.3 Agent 驱动的商业

The New Stack 提出了一个有趣的趋势：**Agent-Driven Commerce**。

当 Agent 需要调用付费服务时（比如用更贵的模型、调用第三方 API），谁来付费？这催生了"机器对机器经济"的需求——Agent 自主决定何时花钱、花多少钱。

### 6.4 可靠性和安全成为焦点

随着 Agent 权限越来越大：
- 可靠性：长任务中保持稳定、从错误中恢复
- 安全性：保护数据、抵抗提示注入、避免不可逆操作
- 人工审批：关键决策需要人工确认的机制

---

## 参考资料

- [Anthropic: 2026 Agentic Coding Trends Report](https://resources.anthropic.com/hubfs/2026%20Agentic%20Coding%20Trends%20Report.pdf)
- [Best AI Coding Agents in 2026, Ranked](https://mightybot.ai/blog/coding-ai-agents-for-accelerating-engineering-workflows)
- [Codex vs Claude Code: Which AI Coding Agent](https://www.mindstudio.ai/blog/codex-vs-claude-code-2026)
- [The best way to do agentic development in 2026](https://dev.to/chand1012/the-best-way-to-do-agentic-development-in-2026-14mn)
- [Orchestrating AI Agents: A Subagent Architecture](https://clouatre.ca/posts/orchestrating-ai-agents-subagent-architecture)
- [VS Code: Your Home for Multi-Agent Development](https://code.visualstudio.com/blogs/2026/02/05/multi-agent-development)（2026.2）
- [5 Key Trends Shaping Agentic Development in 2026](https://thenewstack.io/5-key-trends-shaping-agentic-development-in-2026)
- [Top 13 Agentic AI Trends to Watch in 2026](https://www.firecrawl.dev/blog/agentic-ai-trends)
