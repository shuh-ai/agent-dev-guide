# Hermes Agent Skills

## 一、简介

**技能（Skill）** 是 Hermes 最独特的功能——代表**程序化记忆（Procedural Memory）**。与预置的"工具"不同，技能是 Hermes 在完成任务后自主创建的可复用工作流。

技能采用**渐进披露（Progressive Disclosure）** 模式：技能内容不会时刻占用上下文窗口，仅在名称被引用或匹配到相关任务时才加载完整内容。这意味着你可以安装大量技能而几乎不增加基础 Token 消耗。

### 技能存储位置

```powershell
# Windows
%LOCALAPPDATA%\hermes\skills\

# Linux / macOS
~/.hermes/skills/
```

每个技能对应一个子目录，内含 `SKILL.md`（主文件）和可选的 `references/`、`templates/`、`scripts/` 等附属文件。内置技能按类别分组存放。

**Windows：** `%LOCALAPPDATA%\hermes\skills\`
**Linux / macOS：** `~/.hermes/skills/`

```
skills/
├── autonomous-ai-agents/
│   ├── hermes-agent/SKILL.md
│   ├── hermes-agent/references/
│   ├── claude-code/SKILL.md
│   └── codex/SKILL.md
├── creative/
│   ├── ascii-art/SKILL.md
│   ├── ascii-art/templates/
│   ├── excalidraw/SKILL.md
│   └── pixel-art/SKILL.md
├── devops/
│   └── kanban-orchestrator/SKILL.md
├── mlops/
│   └── llama-cpp/SKILL.md
├── github/
│   └── github-pr-workflow/SKILL.md
└── ...
```

| 对比 | 工具（Tool） | 技能（Skill） |
|------|------------|-------------|
| 来源 | 系统预置，不可更改 | Agent 自主创建，持续优化 |
| 内容 | 单核能力（如搜索、读文件） | 多步骤工作流，组合多个工具 |
| 进化 | 固定不变 | 使用中自我改进 |
| 加载策略 | 全部注入上下文 | 渐进披露，按需加载，最小化 Token |
| 生命周期 | 随版本更新 | 创建→优化→复用→共享 |

**典型流程：** 完成复杂任务 → Hermes 自动生成技能 → 下次类似任务直接调用 → 越用越省、越用越强。

---

## 二、常用操作

| 类别 | 命令/操作 | 描述 |
|------|----------|------|
| 浏览 | `hermes skills list` | 列出所有已安装的技能（builtin-自带的，local-本地的，自主生成的） |
| 浏览 | `hermes skills browse` | 在 Skills Hub 中浏览可安装的技能 |
| 浏览 | `/skills`（会话内） | 查看当前会话可用的技能 |
| 搜索 | `hermes skills search QUERY` | 在 Skills Hub 中搜索技能 |
| 安装 | `hermes skills install ID` | 安装技能（支持 Hub ID 或直接 SKILL.md URL） |
| 安装 | `hermes skills inspect ID` | 预览技能内容，不安装 |
| 调用 | `/<skill-name>`（会话内） | 直接调用已安装的技能 |
| 调用 | `hermes -s skill1,skill2` | 启动时预加载指定技能 |
| 发布 | `hermes skills publish PATH` | 将本地技能发布到 Skills Hub |
| 管理 | `hermes skills config` | 按消息平台启用/禁用技能 |
| 管理 | `hermes skills check` | 检查技能是否有更新 |
| 管理 | `hermes skills update` | 更新过期的技能 |
| 管理 | `hermes skills uninstall NAME` | 卸载技能 |
| 加载 | `/skill <name>`（会话内） | 向当前会话加载一个技能 |
| 加载 | `/reload-skills`（会话内） | 重新扫描技能目录，识别新增/删除的技能 |

---

## 三、使用技能

### 3.1 启动时预加载

```bash
# 加载一个或多个技能
hermes -s "code-review,deployment"

# 单次查询加载技能
hermes chat -q "Review this PR" -s "code-review"
```

### 3.2 会话中调用

```
# 进入对话后，直接输入
/code-review
```

Hermes 会自动加载技能内容，按照技能定义的工作流执行。

### 3.3 自动触发

完成重复性任务后，Hermes 可能会主动询问是否创建技能。同意后自动生成，后续相同任务自动调用。

---

## 四、管理技能

### 查看已安装技能

```bash
hermes skills list
```

列出本地所有技能的名称、描述和版本。

### 安装新技能

```bash
# 从 Skills Hub 安装
hermes skills install code-review

# 从 URL 安装
hermes skills install https://example.com/path/to/SKILL.md --name my-skill
```

### 按平台控制技能

```bash
hermes skills config
```

某些技能只在特定平台可用（如 Telegram 上的图片处理技能），在此配置。

### 发布技能

```bash
hermes skills publish ./my-skill/
```

兼容 `agentskills.io` 开放标准，技能可在社区间共享。

### 卸载技能

```bash
hermes skills uninstall code-review
```

### 添加自定义技能源

```bash
hermes skills tap add https://github.com/username/skills-repo
```

从 GitHub 仓库添加技能源，扩展可安装的技能库。
