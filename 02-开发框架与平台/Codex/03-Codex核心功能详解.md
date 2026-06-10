# Codex 桌面端核心功能详解

> 本文聚焦 Codex App 桌面端的核心功能，从 UI 交互角度介绍各项能力。

---

## 1. Chat 对话界面

桌面端以对话式交互为核心，用户通过聊天窗口与 AI 协作。

### 1.1 对话流程

| 阶段 | 说明 |
|------|------|
| 输入 | 底部输入框输入需求，支持多行文本、快捷键提交（Enter / ⌘+Enter） |
| 分析 | Codex 解析意图，自动读取项目上下文、AGENTS.md 配置 |
| 响应 | AI 给出方案说明并展示代码变更预览 |
| 确认 | 在 diff 视图中审阅，逐文件接受或拒绝修改 |
| 执行 | 确认后 Codex 自动写入文件并执行必要操作 |

### 1.2 上下文感知

桌面端自动感知当前项目上下文：

- **项目文件树**：自动加载并索引项目结构
- **打开的文件**：当前编辑器中打开的文件作为优先上下文
- **AGENTS.md**：自动读取项目指令文件中的技术栈和规范
- **历史对话**：同一会话中保持完整上下文连贯性

---

## 2. 项目与仓库管理

### 2.1 连接 GitHub 仓库

1. 在设置页面登录 GitHub 账号并授权
2. 点击「打开项目」→ 选择「Clone Repository」
3. 浏览或搜索已授权的仓库，一键克隆到本地
4. 克隆完成后自动在 Codex 中打开

### 2.2 打开本地项目

| 方式 | 操作 |
|------|------|
| 菜单 | 文件 → 打开文件夹 → 选择项目根目录 |
| 拖放 | 将项目文件夹直接拖入 Codex 窗口 |
| 最近项目 | 首页「最近项目」列表快速恢复 |

### 2.3 文件树浏览

桌面端左侧提供项目文件树面板：支持文件夹展开/折叠、点击文件预览、右键菜单操作，文件树同步反映 Codex 的文件修改。

---

## 3. 桌面端代码编辑

### 3.1 内联建议

对话中生成的代码变更以 diff 预览呈现：绿色高亮新增行、红色为删除行，点击「接受」写入文件，点击「拒绝」丢弃修改，支持逐文件部分接受。

### 3.2 多文件编辑

| 特性 | 说明 |
|------|------|
| 并行展示 | 所有修改文件在 diff 面板中以标签页形式展示 |
| 逐文件审阅 | 可按文件逐一审阅和接受变更 |
| 依赖感知 | 修改关联文件时自动保持接口一致性 |
| 回滚支持 | 接受后可通过内置历史记录回滚 |

### 3.3 Diff 视图模式

| 视图 | 用途 |
|------|------|
| 并排视图 | 左右对比原始代码与修改后代码 |
| 内联视图 | 同一面板中以内联方式展示增删 |
| 统一视图 | 类似 git diff 的统一格式输出 |

---

## 4. 图片与多模态输入

桌面端支持在对话中嵌入图片，实现视觉理解驱动的开发。

| 方式 | 操作 |
|------|------|
| 拖放 | 将图片文件直接拖入聊天输入框 |
| 粘贴 | 从剪贴板粘贴截图（⌘+V / Ctrl+V） |
| 附件 | 点击输入框旁的附件按钮，选择本地图片文件 |

**典型场景：** UI 还原（拖入设计稿生成页面代码）、Bug 分析（粘贴报错截图定位问题）、参考实现（提供界面截图生成组件）。支持 PNG、JPEG、GIF、WebP 格式。

---

## 5. AGENTS.md 项目配置

`AGENTS.md` 是 Codex 的项目级指令文件，放在项目根目录下，桌面端自动读取。

### 5.1 完整示例

```markdown
# AGENTS.md

## 项目概述
这是一个 Next.js 14 全栈应用，使用 TypeScript + Tailwind CSS + Prisma。

## 技术栈
- 框架：Next.js 14 App Router
- 语言：TypeScript（严格模式）
- 样式：Tailwind CSS
- 数据库：PostgreSQL + Prisma ORM
- 测试：Vitest + Testing Library

## 编码规范
- 组件使用函数式写法，不用 class
- 优先使用 Server Components
- API 路由统一返回 { data, error } 格式
- 错误处理使用 try-catch，不用 .catch()

## 禁止事项
- 不要修改 prisma/schema.prisma 除非明确要求
- 不要删除现有的测试文件
- 不要更改 .env 文件中的环境变量
```

### 5.2 AGENTS.md 层级

| 位置 | 优先级 | 说明 |
|------|--------|------|
| `~/.codex/AGENTS.md` | 最低 | 全局默认配置，适用于所有项目 |
| 项目根目录 `AGENTS.md` | 中 | 项目级配置 |
| 子目录 `AGENTS.md` | 最高 | 模块级配置，针对特定子模块的额外规则 |

> 桌面端打开项目时自动检测并加载 AGENTS.md，配置即时生效。

---

## 6. Skills 技能系统

Skills 是可复用的指令模块，存放在 `.codex/skills/` 目录下，桌面端自动识别并加载。

### 6.1 目录结构

```
.codex/
  skills/
    git-commit.md
    code-review.md
    test-generation.md
    api-design.md
```

### 6.2 编写 Skill

**`.codex/skills/git-commit.md`：**

```markdown
# Git Commit Skill

## 规则
- commit message 使用 Conventional Commits 格式
- 格式：type(scope): description
- type: feat, fix, refactor, docs, test, chore
- description 使用中文，简洁明了

## 示例
- feat(auth): 添加 JWT 刷新机制
- fix(api): 修复分页参数溢出问题
```

### 6.3 在桌面端使用 Skill

在聊天窗口中直接引用 skill 名称，Codex 自动加载对应指令。也可在 AGENTS.md 中声明默认加载的 skill：

```markdown
## 默认技能
- code-review: 每次代码审查时自动应用
- test-generation: 生成代码时自动补充测试
```

---

## 7. MCP 服务器集成

桌面端支持 Model Context Protocol (MCP)，可接入外部工具和数据源。

### 7.1 配置方式

在桌面端设置界面的「MCP 服务器」选项卡中添加，或编辑 `~/.codex/config.toml`：

```toml
[[mcp.servers]]
name = "filesystem"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]

[[mcp.servers]]
name = "github"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env = { GITHUB_PERSONAL_ACCESS_TOKEN = "ghp_xxx" }
```

### 7.2 常用 MCP 服务器

| 服务器 | 功能 |
|--------|------|
| `@modelcontextprotocol/server-filesystem` | 文件系统访问 |
| `@modelcontextprotocol/server-github` | GitHub API |
| `@modelcontextprotocol/server-postgres` | PostgreSQL 查询 |
| `@modelcontextprotocol/server-brave-search` | 网络搜索 |

侧边栏底部显示 MCP 连接状态指示器（🟢 已连接 / 🟡 连接中 / 🔴 已断开）。

---

## 8. Git 集成（桌面端）

### 8.1 可视化 Diff

桌面端内置 Git diff 视图：对话中生成的变更以 diff 视图实时预览，支持逐文件查看变更详情，修改行数统计一目了然。

### 8.2 提交与 PR

| 步骤 | 操作 |
|------|------|
| 审阅变更 | 在 diff 面板中确认所有修改 |
| 编写 message | 在提交框中输入 commit message |
| 提交 | 点击「Commit」完成本地提交 |
| 推送 | 点击「Push」推送到远程仓库 |
| 创建 PR | 点击 Git 面板中的「Create PR」，Codex 自动填充标题和描述 |

### 8.3 分支管理

| 操作 | 说明 |
|------|------|
| 创建分支 | 对话中要求 Codex 创建功能分支 |
| 切换分支 | 在 Git 面板的分支下拉菜单中选择 |
| 合并分支 | 通过对话或 Git 面板操作 |

---

## 9. 会话管理

### 9.1 基础操作

| 功能 | 说明 |
|------|------|
| 新建会话 | 侧边栏 `+` 按钮，开启独立对话上下文 |
| 切换会话 | 点击侧边栏历史会话，自动恢复上下文 |
| 删除会话 | 右键 → 删除，支持撤销（Ctrl+Z / ⌘+Z） |

### 9.2 Codex++ 增强功能

| 功能 | 说明 |
|------|------|
| 删除即撤销 | 删除会话后 5 秒内可通过弹窗或快捷键撤销 |
| 会话导出 | 导出为 Markdown 或 JSON 格式，便于归档分享 |
| 会话时间线 | 时间线视图浏览会话中每个关键节点 |
| 会话搜索 | 按关键词搜索历史会话 |
| 标签管理 | 为会话添加标签分类 |

桌面端自动将会话与项目目录关联：重新打开项目时自动显示关联历史会话，支持跨项目搜索。

---

## 10. Codex++ 插件系统

Codex++ 在 API Key 模式下可解锁插件扩展功能。

### 10.1 启用插件

在设置中使用 API Key 登录后，进入「插件」面板，浏览可用插件列表，点击「启用」激活。

### 10.2 常用插件

| 插件 | 功能 | 所需配置 |
|------|------|----------|
| 代码搜索 | 语义搜索代码片段 | 无 |
| 文档生成 | 自动生成 API 文档和 README | 无 |
| 测试运行器 | 在对话中运行测试 | 测试框架配置 |
| 数据库浏览器 | 可视化查看数据库结构和数据 | 数据库连接信息 |
| 部署助手 | 一键部署到主流云平台 | 云平台凭证 |

### 10.3 插件配置

插件以 JSON 文件形式声明，存放在 `.codex/plugins/` 目录：

```json
{
  "name": "my-custom-plugin",
  "description": "自定义项目插件",
  "version": "1.0.0",
  "capabilities": ["tool_call", "context_provider"],
  "config": { "endpoint": "http://localhost:3000/api" }
}
```

插件权限分为只读、读写、网络、完全四个级别，请仅启用来源可信的插件。

---

## 功能速查表

| 功能 | 桌面端支持 | 说明 |
|------|:----------:|------|
| Chat 对话 | ✅ | 核心交互方式 |
| 项目管理 | ✅ | 本地 + GitHub 仓库 |
| 代码编辑 | ✅ | 内联建议 + Diff 视图 |
| 图片输入 | ✅ | 拖放 / 粘贴 / 附件 |
| AGENTS.md | ✅ | 自动加载 |
| Skills 系统 | ✅ | 自动识别 `.codex/skills/` |
| MCP 服务器 | ✅ | 设置面板配置 |
| Git 集成 | ✅ | 可视化 Diff + PR |
| 会话管理 | ✅ | Codex++ 增强功能 |
| 插件系统 | ✅ | Codex++ API Key 模式 |
