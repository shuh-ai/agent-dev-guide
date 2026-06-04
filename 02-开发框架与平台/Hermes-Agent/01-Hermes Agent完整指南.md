# Hermes Agent 简介

**Hermes Agent** 是由 Nous Research 开发的开源、自进化 AI 代理框架，核心能力源于内置的学习闭环。

- **开源协议**：MIT | **GitHub Stars**：159K+ | **技术栈**：Python 88.4% + TypeScript 8.6%
- **核心理念**：运行时间越长，能力越强

---

## 核心创新

### 一、自动从交互中生成 Skill

完成任务后自动将整个过程打包为可复用的 Skill，下次遇到同类任务时直接调用，无需重新推理。这既大幅节省 Token，也让代理的知识库随使用不断扩充。

### 二、在使用中持续迭代技能

Skill 不是静态快照——每次被调用时，Hermes 会评估执行结果并在必要时自动修正内容。你用得越多，Skill 的质量就越高。

### 三、主动持久化知识和用户偏好

自主策展的记忆系统主动判断哪些信息值得持久化（项目上下文、代码风格、工作流偏好等），而非被动等待用户指示。三层架构（会话上下文 → FTS5 全文检索 → Honcho 长期建模）确保重要信息不因会话结束而丢失。

### 四、跨会话构建对用户的深度理解

通过 Honcho 系统跨越多个会话持续构建用户画像，逐渐理解你的工作模式、沟通偏好和决策风格。会话越多，适应越精确。

### 其他特性

| 特性 | 说明 |
|------|------|
| 多平台网关 | 单一网关连接 20+ 消息平台 |
| 终端 TUI | 全功能本地终端界面 |
| 子代理并行 | 派生子代理并行处理任务 |
| 定时自动化 | 内置 Cron 调度器 |
| 70+ 内置工具 | 网页搜索、浏览、图像生成、TTS 等 |
| MCP 集成 | 可连接任意 MCP 服务器 |

---

## 养马还是养虾：Hermes vs OpenClaw

> "养马"和"养虾"是两种完全不同的思路——前者需要投入时间和耐心去培养，但会越养越强壮；后者随用随捞，方便省事，但每次重启都得重新撒网。Hermes 和 OpenClaw 的区别，本质上就是这两种理念的差异。

### Token 消耗对比

| 对比维度 | OpenClaw | Hermes Agent |
|---------|----------|-------------|
| 上下文管理 | 手动管理，无自动压缩机制 | `/compress` 主动压缩 + FTS5 检索历史，避免上下文膨胀 |
| 记忆持久化 | 进程重启后记忆全部丢失，每次启动如同全新实例 | 跨会话持久化记忆，进程重启也能完整恢复，越重启越强大 |
| 长期运行成本 | 随使用时间线性增长 | 前期略高（用于创建技能和建立记忆），但随技能积累边际成本递减 |

**实际场景对比示例**：

> 假设每天执行"查阅邮件 → 提取待办 → 更新 Notion 数据库"这个流程：
>
> - **OpenClaw**：每次完整执行 3 步工具链，约 5,000 Token/次，**30 天累计 ~150,000 Token**
> - **Hermes**：首次执行后自动生成技能，后续每次 ~800 Token，**30 天累计 ~28,200 Token，节省约 81%**

更重要的是，Hermes 的记忆系统让它在长期使用中无需重复描述项目背景和用户偏好，这些隐性 Token 节省在实际使用中更为可观。

### 自进化能力对比

这是 Hermes 与 OpenClaw 最根本的区别——**OpenClaw 是静态的，Hermes 是动态自进化的**。

| 维度 | OpenClaw | Hermes Agent |
|------|----------|-------------|
| 开放标准 | 封闭，无法导出能力 | 兼容 `agentskills.io` 开放标准，技能可上传和共享 |

**同样的任务，不同的体验**：

```
你：帮我把这个 Git 仓库的所有 Issue 按优先级分类，然后给每个负责人发通知

Hermes → 调用工具 → 完成 ✅
       ↘ 自动生成「Issue 分类通知」技能 → 下次直接调用

你：再处理一次 Issue
Hermes → 直接调用技能 → 瞬间完成 ✅（无需重新推理）
```

```
你：帮我把这个 Git 仓库的所有 Issue 按优先级分类

OpenClaw → 调用工具 → 完成 ✅

你：再处理一次（同样的流程）
OpenClaw → 重新推理 → 重新调用工具链 → 完成 ✅（没有进步，没有优化）
```

### 总结：为什么选择 Hermes

1. **越用越省**：虽前期有技能创建开销，但积累后长期 Token 消耗显著低于传统方案
2. **越用越强**：技能自进化 + 跨会话记忆叠加，代理能力持续增长；重启也完整保留
3. **越用越懂你**：Honcho 建模让 Hermes 逐渐适应你，而非你去适应它
4. **一键迁移**：`hermes claw migrate` 自动导入 OpenClaw 配置、记忆和技能，零成本切换
---

# 第二部分：安装指南

Hermes Agent 在 Windows 上有两条安装路径，按你的开发环境选择。

## 一、路径 A：PowerShell 原生安装（推荐）

这是官方推荐的 Windows 原生安装方式，使用 PowerShell 从脚本安装，**无需管理员权限**。

### 前提条件
- Windows 10 或更高版本（64 位）
- PowerShell 5.1+（Win10 自带）或 PowerShell 7+
- 网络能访问 GitHub (raw.githubusercontent.com)
- **不需要** WSL2 或 Python 预装（安装器自带便携版）

### 安装命令

以**管理员身份**打开 PowerShell（非必需但可避免权限问题），执行：

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

安装器会自动完成：
1. 下载并解压便携版 Git Bash（~45 MB，仅首次）
2. 创建 Hermes 虚拟环境（Python 捆绑在发布包中）
3. 配置 PATH，使 `hermes` 命令可在 PowerShell / CMD / Git Bash 中使用
4. 初始化数据目录到 `%LOCALAPPDATA%\hermes\`

### 安装位置

| 变量形式 | 实际 Windows 路径 |
|----------|------------------|
| `%LOCALAPPDATA%\hermes\` | `C:\Users\当前用户名\AppData\Local\hermes\` |
| `%LOCALAPPDATA%\hermes\hermes-agent\` | `C:\Users\当前用户名\AppData\Local\hermes\hermes-agent\` |
| `%LOCALAPPDATA%\hermes\config.yaml` | `C:\Users\当前用户名\AppData\Local\hermes\config.yaml` |
| `%LOCALAPPDATA%\hermes\.env` | `C:\Users\当前用户名\AppData\Local\hermes\.env` |
| `%LOCALAPPDATA%\hermes\skills\` | `C:\Users\当前用户名\AppData\Local\hermes\skills\` |
| `%LOCALAPPDATA%\hermes\sessions\` | `C:\Users\当前用户名\AppData\Local\hermes\sessions\` |
| `%LOCALAPPDATA%\hermes\logs\` | `C:\Users\当前用户名\AppData\Local\hermes\logs\` |

---

## 二、路径 B：Git Bash / WSL2 安装

如果你已经在 Windows 上使用了 **Git Bash** 或 **WSL2（推荐）**，也可用 Linux 风格的安装脚本：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

---

## 三、验证安装

安装完成后，在终端中运行：

```bash
hermes doctor
```

正常输出应包含：
- Python 环境正常 ✓
- 配置文件存在 ✓
- 无安全警告

也可查看版本：

```bash
hermes --version
```

---

## 四、更新

```bash
hermes update
```

如有重要更新，`hermes doctor` 也会提示落后版本数。

---

## 五、Windows 安装常见问题

### PowerShell 执行策略阻止脚本

```powershell
# 查看当前策略
Get-ExecutionPolicy

# 临时允许（当前会话）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 或永久修改（当前用户）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 杀毒软件拦截

安装器下载可执行文件时可能触发 Windows Defender 或第三方杀毒。如遇拦截，添加排除项或临时关闭实时防护后再运行。

### 中文路径问题

Hermes 的数据目录和配置路径均使用英文，不受系统用户名中包含中文的影响。但项目工作目录若包含中文，在 Git Bash 中可能遇到编码问题——建议在 Git Bash 的 `~/.bashrc` 中添加：

```bash
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
```

### 代理/网络问题

如果所在网络环境需要代理，安装前设置：

```powershell
# PowerShell
$env:HTTP_PROXY="http://127.0.0.1:7890"
$env:HTTPS_PROXY="http://127.0.0.1:7890"

# Git Bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

---

## 六、基础配置

### 6.1 选择模型提供商

Hermes 支持极广泛的模型提供商，**切换无需编辑配置文件**：

```bash
hermes model
```

该命令会列出所有可用的提供商和模型，输入对应序号选择即可。

常用提供商包括：

| 提供商 | 特点 | 官网 |
|--------|------|------|
| **DeepSeek** | 性价比高，v4 flash 速度快 | [deepseek.com](https://deepseek.com) |
| **Nous Portal**（官方默认） | 内置免配置，推荐入门使用 | [portal.nousresearch.com](https://portal.nousresearch.com) |
| **OpenRouter** | 200+ 模型，灵活切换 | [openrouter.ai](https://openrouter.ai) |
| **OpenAI** | GPT-4o / o3 系列 | [openai.com](https://openai.com) |
| **Kimi / Moonshot** | 长上下文支持好 | [kimi.moonshot.cn](https://kimi.moonshot.cn) |
| **MiniMax** | 中文能力优秀 | [minimax.com](https://minimax.com) |
| **Hugging Face** | 开源模型托管 | [huggingface.co](https://huggingface.co) |
| 自定义端点 | 任意兼容 OpenAI API 的服务 | — |

**API 密钥配置：**

选择提供商后，Hermes 会引导输入 API Key。密钥存储在 `%LOCALAPPDATA%\hermes\.env` 文件中：

```
# .env 示例
DEEPSEEK_API_KEY=sk-xxx...xxxx
OPENAI_API_KEY=sk-xxx...xxxx
```

也可直接编辑该文件手动添加。

### 6.2 配置设置

```bash
hermes config set <key>=<value>
```

常用配置项示例：

```bash
# 设置最大对话轮次
hermes config set agent.max_turns=60

# 开启 verbose 模式（调试用）
hermes config set agent.verbose=true

# 设置推理努力程度
hermes config set agent.reasoning_effort=medium

# 关闭某个工具集
hermes config set agent.disabled_toolsets=["browser"]
```

**常用配置参数速查：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `agent.max_turns` | 60 | 单次对话最大工具调用轮次 |
| `agent.reasoning_effort` | medium | 推理深度：low / medium / high |
| `agent.verbose` | false | 是否输出详细调试信息 |
| `agent.image_input_mode` | auto | 图像输入模式：auto / disable |
| `agent.gateway_timeout` | 1800 | 网关超时（秒） |

### 6.3 完整设置向导

适合首次使用的交互式向导，一站式完成提供商选择、API Key 输入、工具集配置：

```bash
hermes setup
```

### 6.4 Windows 特有的配置注意事项

**Git Bash 中使用 `hermes` 命令：**

PowerShell 安装器会将 Hermes 添加到 PATH。如果在 Git Bash 中找不到 `hermes` 命令，可手动添加：

```bash
# 在 ~/.bashrc 或 ~/.bash_profile 中添加
export PATH="$PATH:/c/Users/$USERNAME/AppData/Local/hermes/hermes-agent/venv/Scripts"

# 或直接用完整路径
/c/Users/$USERNAME/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes
```

**使用建议：**
- **日常使用**：推荐在 Git Bash 中运行 Hermes，体验最完整（支持 TUI、彩色输出、多行编辑）
- **配置修改**：PowerShell / CMD / Git Bash 均可，效果一致
- **更新**：建议在最初安装的同一种 shell 中执行 `hermes update`

---

# 第三部分：接入应用

本文介绍如何将 Hermes Agent 接入 QQ、微信（WeChat）和飞书（Feishu/Lark）等国内主流即时通讯平台，让 AI 助手直接在这些聊天工具中与你交互。

> **前置要求**：Hermes Agent 已安装并配置好模型提供商（见上文「基础配置」）。
> 所有平台接入均通过 Hermes **Gateway（网关）** 实现，使用同一个 `hermes gateway` 后台进程即可同时连接多个平台。

---

## 必要组件

在开始接入任何平台之前，请确保已安装以下组件：

### 1. Python 环境

Hermes 依赖 Python 3.10+。确认版本：

```bash
python --version
```

### 2. 安装依赖包

各平台共用的 Python 依赖包：

```bash
pip install aiohttp
```

不同平台额外需要：

| 平台 | 需要额外安装 |
|------|------------|
| QQ | `pip install httpx` |
| 微信 (WeChat) | `pip install cryptography` |
| 飞书 (Feishu/Lark) | `pip install lark-oapi`（推荐）或 `pip install websockets` |

### 3. 确认 Gateway 可用

```bash
hermes gateway --help
```

---

## 一、接入 QQ

Hermes 通过**腾讯官方 QQ Bot API（v2）** 接入 QQ，支持私聊（C2C）、群聊 @提及、频道消息等。

> **前置条件**：前往 [q.qq.com](https://q.qq.com) 注册 QQ 机器人应用，记下 **App ID** 和 **App Secret**，并开启所需的 Intents（C2C 消息、群 @消息、频道消息）。

### 接入步骤

#### Step 1：运行 Setup 向导

```bash
hermes gateway setup
```

#### Step 2：选择 QQ Bot 并扫码

在平台列表中选择 QQ Bot，按提示扫描二维码添加机器人。

#### Step 3：私聊信息授权

选择使用私聊配对码审批，后续全程 y 结束即可。

#### Step 4：效果展示

发送消息测试机器人是否正常回复。

#### ⚠ 注意事项

如果遇到 QQ 机器人长时间无回复，可尝试重启 Hermes 来尝试。

---

## 二、接入微信（WeChat / Weixin）

### 接入步骤

#### Step 1：运行 Setup 向导

```bash
hermes gateway setup
```

#### Step 2：选择 Weixin (WeChat)

在平台列表中，选择 **Weixin (WeChat)**。

#### Step 3：终端显示二维码

向导会请求 iLink Bot API 生成登录二维码，二维码会显示在终端中（或提供一个 URL 用于查看）。

#### Step 4：手机扫码并确认

打开手机微信，扫描终端上的二维码，然后在手机上确认登录。

#### Step 5：凭据自动保存

扫码确认后，终端会显示连接成功信息。凭据会自动保存到 `~/.hermes/weixin/accounts/` 目录下。

#### Step 6：配置环境变量（可选）

在 `~/.hermes/.env` 中，至少设置 Account ID：

```env
WEIXIN_ACCOUNT_ID=your-account-id
WEIXIN_DM_POLICY=open
WEIXIN_ALLOWED_USERS=user_id_1,user_id_2
WEIXIN_HOME_CHANNEL=chat_id
```

#### Step 7：启动 Gateway

```bash
hermes gateway
```

#### Step 8：验证连接

在微信上给机器人（iLink Bot 账号）发一条消息，确认能正常收到回复。

### 微信环境变量参考

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `WEIXIN_ACCOUNT_ID` | iLink Bot 账号 ID（必填） | — |
| `WEIXIN_TOKEN` | iLink Bot Token（扫码后自动保存） | — |
| `WEIXIN_BASE_URL` | iLink API 基础地址 | `https://ilinkai.weixin.qq.com` |
| `WEIXIN_DM_POLICY` | 私信策略 | `open` |
| `WEIXIN_ALLOWED_USERS` | 允许发送私信的用户 ID 列表 | — |
| `WEIXIN_GROUP_POLICY` | 群聊策略 | `disabled` |
| `WEIXIN_HOME_CHANNEL` | 定时任务投递的 Home 频道 | — |
| `WEIXIN_SPLIT_MULTILINE_MESSAGES` | 多行消息是否拆分发送 | `false` |

### 微信重要限制

iLink Bot 身份存在以下限制：
- **无法被拉入普通微信群**（不同于正常联系人）
- 群消息事件通常**不会投递**给 Gateway
- 扫码登录的是**机器人身份**，与你个人的微信账号是分离的

实际使用中，**仅私信对话可靠工作**。群聊消息不成功属于 iLink 侧限制，非 Hermes 问题。

### 微信常见问题

| 问题 | 解决方法 |
|------|---------|
| 启动失败：`aiohttp and cryptography are required` | 安装依赖：`pip install aiohttp cryptography` |
| 启动失败：`WEIXIN_TOKEN is required` | 运行 `hermes gateway setup` 完成扫码登录 |
| 会话过期（errcode=-14） | 重新运行 `hermes gateway setup` 扫码 |
| 二维码过期 | 二维码会自动刷新最多 3 次 |
| 机器人不回复私信 | 检查 `WEIXIN_DM_POLICY` 是否设为 `allowlist` |

---

## 三、接入飞书（Feishu / Lark）

Hermes 作为飞书机器人接入，支持私信、群聊 @提及、**交互式卡片**、**文档评论回复**等高级功能。

飞书支持两种连接模式：

| 模式 | 适用场景 |
|------|---------|
| **WebSocket**（推荐） | 本地环境、私服运行，无需公网端点 |
| **Webhook** | 服务器有公网 HTTP 端点时 |

### 接入步骤

#### Step 1：运行 Setup 向导

```bash
hermes gateway setup
```

#### Step 2：选择 Feishu / Lark

在平台列表中选择 **Feishu / Lark**。

#### Step 3：扫码创建应用或手动输入

向导会展示二维码，用飞书手机 App 扫码即可自动创建机器人应用并保存凭据。如果扫码不可用，向导会回退到手动输入模式，需要提供从 [open.feishu.cn](https://open.feishu.cn)（国内）或 [open.larksuite.com](https://open.larksuite.com)（国际版）获取的 **App ID** 和 **App Secret**。

#### Step 4：选择连接模式

推荐选择 **WebSocket**。

#### Step 5：启动 Gateway

```bash
hermes gateway
```

#### Step 6：验证连接

在飞书上搜索机器人并发送一条消息，确认能正常收到回复。

### 飞书环境变量参考

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FEISHU_APP_ID` | 飞书应用 App ID（必填） | — |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret（必填） | — |
| `FEISHU_DOMAIN` | `feishu`（国内）或 `lark`（国际版） | `feishu` |
| `FEISHU_CONNECTION_MODE` | `websocket` 或 `webhook` | `websocket` |
| `FEISHU_ALLOWED_USERS` | 允许使用机器人的用户 Open ID 列表 | 开放 |
| `FEISHU_HOME_CHANNEL` | 定时任务投递的聊天 ID | — |
| `FEISHU_GROUP_POLICY` | 群聊策略 | `allowlist` |
| `FEISHU_REQUIRE_MENTION` | 群聊是否需要 @提及才回复 | `true` |
| `FEISHU_ENCRYPT_KEY` | Webhook 模式加密密钥 | — |
| `FEISHU_VERIFICATION_TOKEN` | Webhook 验证令牌 | — |
| `FEISHU_WEBHOOK_HOST` | Webhook 绑定地址 | `127.0.0.1` |
| `FEISHU_WEBHOOK_PORT` | Webhook 端口 | `8765` |

### 飞书常见问题

| 问题 | 解决方法 |
|------|---------|
| `lark-oapi` 未安装 | `pip install lark-oapi` |
| `websockets` 未安装 | `pip install websockets` |
| App ID 或 Secret 未设置 | 运行 `hermes gateway setup` 或手动设置 |
| 机器人不响应群聊消息 | 确保 @提及了机器人；检查群聊策略和白名单 |
| 交互式卡片按钮报错 200340 | 需在飞书开发者后台开启「交互式卡片」能力 |
| Webhook 签名验证失败 | 确保加密密钥与飞书后台一致 |

---

## 平台对比一览

| 维度 | QQ | 微信 (WeChat) | 飞书 (Feishu) |
|------|-----|-------------|--------------|
| **API 类型** | QQ Bot API v2（WebSocket） | iLink Bot API（长轮询） | Feishu API（WebSocket / Webhook） |
| **注册平台** | [q.qq.com](https://q.qq.com) | 扫码即用 | [open.feishu.cn](https://open.feishu.cn) |
| **公网要求** | ❌ 不需要 | ❌ 不需要 | ❌ WebSocket 不需要 / Webhook 需要 |
| **私信** | ✅ | ✅ | ✅ |
| **群聊 @提及** | ✅ | ⚠️ 受限 | ✅ |
| **图片** | ✅ | ✅ | ✅ |
| **语音转文字** | ✅ | ✅ | ✅ |
| **交互式卡片** | ❌ | ❌ | ✅ |
| **定时任务投递** | ✅ | ✅ | ✅ |

---

## 多平台同时运行

Hermes Gateway 支持**一个进程同时连接多个平台**。只需依次通过 `hermes gateway setup` 配置好每个平台，然后启动网关即可：

```bash
hermes gateway setup     # 依次配置 QQ → 微信 → 飞书
hermes gateway           # 启动网关，所有平台同时在线
```

### 跨平台交互

- 所有平台共享同一个 AIAgent 核心，但**会话是隔离的**
- 使用 `/sethome` 命令可将某个聊天设为 **Home 频道**，定时任务结果会投递到该频道
- 每个平台有独立的**访问策略**（白名单、群聊策略等）

---

# 第四部分：个性化定制

Hermes Agent 提供了丰富的个性化定制能力，从基础的角色人设、对话风格，到跨会话的记忆学习，再到完整的独立配置文件——你可以把 Hermes 打造成真正"懂你"的专属 AI 助手。

## 一、用 SOUL.md 定义核心人格

**SOUL.md** 是 Hermes 最核心的个性化文件，它定义了 Agent 的**基本身份和性格**。

### 文件位置

```
%LOCALAPPDATA%\hermes\SOUL.md        # Windows
~/.hermes/SOUL.md                     # Linux / macOS
```

### 重要行为

- **身份优先级最高**：SOUL.md 占据系统提示词中的位置 #1，取代硬编码的默认身份
- **自动创建**：如果 SOUL.md 尚不存在，Hermes 会自动创建一个初始版本
- **永不覆盖**：现有的 SOUL.md 文件永远不会被覆盖
- **加载来源**：Hermes 只从 `%HERMES_HOME%` 加载 SOUL.md，不会在当前工作目录中寻找
- **容错回退**：如果 SOUL.md 存在但为空或无法加载，Hermes 回退到内置默认身份
- **安全注入**：SOUL.md 有内容时，该内容在安全扫描和截断后会逐字注入
- **不重复出现**：SOUL.md 不会在上下文文件部分重复出现——它只出现一次，作为身份标识
- **热加载**：修改 SOUL.md 后立刻生效，不需要重启 Gateway 或重新会话

### 这样设计的原因

保持 Agent 性格的可预测性与可控性，避免被项目级或临时性指令干扰核心人格。

### SOUL.md 能放哪些东西？

**适合的内容：**

- 语调（正式、轻松、幽默等）
- 对话风格（简洁、详尽、互动式等）
- 直接程度（直截了当、委婉引导等）
- 交互风格（主动提问、被动响应等）
- 处理不确定性和分歧的方式
- 对模糊性的容忍度

**应避免的内容：**

- 一次性的项目指令
- 绝对文件路径
- 仓库规范或编码约定
- 临时工作流

### 好的 SOUL.md 应满足

- 在不同上下文中保持稳定
- 适用面广，能适用于多个场景下的对话
- 回答内容足够具体、有指导性

### 文件格式

SOUL.md 使用 Markdown 格式，建议用 HTML 注释写说明，正文写角色设定：

```markdown
# 你的助手名称

<!--
这里的注释不会被 AI 读取，只是给你自己看的说明。
-->

你是 [角色名称]，一个 [性格描述] 的 AI 助手。

你的特点：
- 特点一：...
- 特点二：...
- 特点三：...
```

### 示例

**知性分析型助手：**

```markdown
# 思远

你是思远，一个理性而不失温度的分析型助手。你善于拆解复杂问题，
用清晰的逻辑和结构化的表达帮助对方理清思路。

你的特点：
- 语言简洁精炼，优先用关键词、列表和结构化段落
- 直接程度中等——先给出核心结论，再展开分析依据
- 主动引导对方提供更多信息以提升建议的准确性
- 面对不确定的问题时，诚实说明推断依据而非强行作答
- 风格稳重，少用比喻和情绪词，关注事实与逻辑
```

**治愈系助手：**

```markdown
# 小暖

你是小暖，一个温暖治愈的 AI 助手。你说话像一位贴心的朋友，
总是能理解对方的情绪，给予恰到好处的安慰和鼓励。

你的特点：
- 说话温柔，多用"呢""呀""哦"等语气词
- 善于共情，面对分歧时先接纳对方的感受，再温和地引导
- 直接程度偏间接——优先用提问和猜测来确认，而非直接断言
- 适时使用颜文字如 (｡˘‿˘｡) 或 (´▽`ʃ♡ƪ)
- 遇到不确定的问题时，坦率承认但不让人感到失望，转而推荐相关话题
- 永远保持积极但不过度夸张的态度
```

---

# 第五部分：工具与工具集

## 一、简介

**工具（Tool）** 是 Agent 与外界交互的能力单元——搜索网页、读写文件、执行代码、生成图片等都通过工具完成。

**工具集（Toolset）** 是同类工具的集合。Agent 以工具集为粒度启用或禁用，减少无用的工具占用上下文。

工具变更后需 `/reset` 开启新会话生效，以保护提示缓存。

---

## 二、常用工具集

| 类别 | 工具集 | 描述 |
|------|--------|------|
| 网络 | `web` | 联网搜索、获取网页内容。含 `search` 全部功能 |
| 网络 | `search` | 仅网页搜索，不含内容提取。web 的子集 |
| 浏览器 | `browser` | 自动操控浏览器——截图、点击、填表 |
| 终端与文件 | `terminal` | 运行 shell 命令，管理后台进程 |
| 终端与文件 | `file` | 读写文件、搜索内容、查找文件 |
| 终端与文件 | `code_execution` | 安全沙箱中运行 Python 代码 |
| 媒体 | `vision` | 分析图片内容 |
| 媒体 | `image_gen` | 文本描述生成图片 |
| 媒体 | `video` | 视频分析与生成 |
| 媒体 | `tts` | 文本转语音 |
| 记忆 | `memory` | 跨会话读写持久化记忆 |
| 记忆 | `session_search` | 全文检索历史对话 |
| 记忆 | `skills` | 浏览和管理技能库 |
| 任务调度 | `delegation` | 派生子 Agent 并行处理多项独立任务 |
| 任务调度 | `cronjob` | 定时执行任务 |
| 任务调度 | `todo` | 当前会话的任务看板 |
| 交互 | `clarify` | 遇到不确定时主动向用户提问 |
| 交互 | `messaging` | 跨平台发送消息 |
| 安全 | `safe` | 最小化工具集，仅保留最安全的操作 |
| 调试 | `debugging` | 调试和内省工具，默认关闭 |
| 集成 | `spotify` | Spotify 播放、搜索、歌单管理 |
| 集成 | `homeassistant` | 控制智能家居设备 |
| 集成 | `discord` | Discord 频道交互 |
| 集成 | `feishu_doc` | 飞书文档操作 |
| 集成 | `yuanbao` | 元宝群组集成 |

---

## 三、使用工具集

启动 Hermes 时指定启用哪些工具集：

```bash
# 仅启用 terminal + file + web
hermes -t "terminal,file,web"

# 单次查询使用
hermes chat -q "写一份系统日报" -t "terminal,file,web"
```

不指定时使用默认配置。

---

## 四、启用或关闭工具集

### 方式一：交互式

```bash
hermes tools
```

进入交互界面，按空格选中/取消，回车确认。

### 方式二：命令行

```bash
hermes tools list                  # 查看所有工具集状态
hermes tools enable  browser       # 启用
hermes tools disable browser       # 关闭
```

### 方式三：配置文件

```yaml
# config.yaml
agent:
  disabled_toolsets: ["browser", "image_gen"]
```

### 生效

所有工具集变更后，需要 `/reset` 或重新启动会话才能生效。

---

# 第六部分：Skills

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
| 浏览 | `hermes skills list` | 列出所有已安装的技能 |
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

---

# 第七部分：持久记忆

## 一、简介

**持久记忆（Memory）** 让 Hermes 跨会话记住你的偏好、习惯和背景信息。昨天的对话、上周的项目细节、你的编码风格——重启会话后依然保留。

记忆采用**渐进披露**模式：记忆内容不会全部注入上下文，仅在相关时才检索调用，不增加基础 Token 消耗。

### 记忆类型

| 类型 | 文件 | 存储内容 |
|------|------|---------|
| **用户画像** | `USER.md` | 你的身份、偏好、沟通风格、常用约定 |
| **工作笔记** | `MEMORY.md` | 项目上下文、环境事实、工具使用技巧、学到的东西 |

### 存储位置

```
Windows:  %LOCALAPPDATA%\hermes\memories\
Linux:    ~/.hermes/memories/
```

每个 Profile 拥有独立的记忆空间，互不干扰。

---

## 二、常用操作

| 类别 | 命令/操作 | 描述 |
|------|----------|------|
| 查看 | `hermes memory status` | 查看当前记忆后端和状态 |
| 开启 | `hermes memory setup` | 交互式配置记忆系统 |
| 关闭 | `hermes memory off` | 关闭持久记忆功能 |
| 切换 | `hermes memory status` | 选择内置 / Honcho / Mem0 等后端 |

记忆由 Hermes **主动策展**，无需手动保存。以下场景会自动触发记忆写入：

- 你说"记住这个"
- 你纠正了 Agent 的行为
- 你分享了个人偏好或习惯
- 发现了项目的特定配置
- Agent 定期自我提示，将重要信息持久化

---

## 三、使用记忆

### 3.1 自动触发

只要启用了记忆，Hermes 会在对话中自动判断哪些信息值得保存：

> 你：我喜欢用 pytest 而不是 unittest
> Hermes：好的，已记住你偏好使用 pytest。

> 你：这个项目的数据库是 PostgreSQL 16
> Hermes：已记录项目数据库信息。

### 3.2 主动保存

你可以直接要求 Hermes 记住某些信息：

> "记住我的 API 文档放在 docs/api/ 目录下"
> "记住每次代码提交前都要运行 ruff check"
> "记住我喜欢简洁的回答风格"

### 3.3 查看记忆内容

记忆文件可以直接打开查看：

```
%LOCALAPPDATA%\hermes\memories\USER.md    # 用户画像
%LOCALAPPDATA%\hermes\memories\MEMORY.md  # 工作笔记
```

### 3.4 会话检索

即使在当前会话中，也可以让 Hermes 回忆之前的对话：

> "我之前说过关于数据库的什么配置？"

Hermes 会通过 FTS5 全文检索自动查找。

---

## 四、管理记忆

### 4.1 配置参数

```yaml
memory:
  memory_enabled: true             # 启用工作笔记
  user_profile_enabled: true       # 启用用户画像
  memory_char_limit: 2200          # 工作笔记最大字符
  user_char_limit: 1375            # 用户画像最大字符
  nudge_interval: 10               # 每 N 轮对话提示保存
  flush_min_turns: 6               # 最少 N 轮才写入一次
```

### 4.2 记忆后端

Hermes 支持多种记忆后端，可通过 `hermes memory setup` 切换：

| 后端 | 说明 | 配置要求 |
|------|------|---------|
| **内置（默认）** | 基于 SQLite，开箱即用 | 无需额外配置 |
| **Honcho** | 高级长期建模系统，辩证式用户画像 | 需要安装 Honcho 插件 |
| **Mem0** | 第三方记忆服务 | 需要 API Key |

### 4.3 清除记忆

直接删除记忆文件或清空内容即重置记忆：

```
# Windows
del %LOCALAPPDATA%\hermes\memories\USER.md
del %LOCALAPPDATA%\hermes\memories\MEMORY.md

# Linux
rm ~/.hermes/memories/USER.md
rm ~/.hermes/memories/MEMORY.md
```

重启会话后生效。

### 4.4 跨 Profile 隔离

每个 Profile 拥有独立的记忆空间，互不影响。

---

# 第八部分：MCP 扩展 AI 工具能力

## 一、简介

**MCP（Model Context Protocol）** 是一种开放标准协议，让 AI 应用可以连接外部服务器，发现并使用服务器提供的工具。Hermes Agent 内置原生 MCP 客户端，支持连接任意 MCP 服务器。

MCP 工具注册后与内置工具平级——通过 `mcp_{服务器名}_{工具名}` 命名模式直接调用。

| 概念 | 说明 |
|------|------|
| **MCP 服务器** | 提供特定工具集的外部服务（文件系统、GitHub、数据库等） |
| **MCP 工具** | 服务器注册的能力单元，如 `mcp_github_list_issues` |
| **传输协议** | Stdio（本地子进程）或 HTTP（远程服务器） |

### 安装前提

```bash
pip install mcp        # MCP Python SDK（必需）
```

Node.js 和 uv 按需安装——分别用于 npx 和 uvx 启动的 MCP 服务器。

---

## 二、常用操作

| 类别 | 命令/操作 | 描述 |
|------|----------|------|
| 添加 | `hermes mcp add NAME --url URL` | 添加远程 HTTP MCP 服务器 |
| 添加 | `hermes mcp add NAME --command CMD` | 添加本地命令式 MCP 服务器 |
| 查看 | `hermes mcp list` | 列出已配置的 MCP 服务器 |
| 测试 | `hermes mcp test NAME` | 测试服务器连接是否正常 |
| 配置 | `hermes mcp configure NAME` | 精细选择暴露给 Agent 的 MCP 工具 |
| 移除 | `hermes mcp remove NAME` | 移除 MCP 服务器 |
| 服务 | `hermes mcp serve` | 将 Hermes 自身作为 MCP 服务器启动 |
| 重载 | `/reload-mcp`（会话内） | 热重载 MCP 服务器配置 |

---

## 三、使用 MCP

### 3.1 配置 MCP 服务器

编辑 `~/.hermes/config.yaml`，在 `mcp_servers` 下添加配置：

```yaml
mcp_servers:
  time:                              # 服务器名称
    command: "uvx"                   # 启动命令
    args: ["mcp-server-time"]        # 命令参数
```

Hermes 启动时自动连接，发现工具并注册。此后可直接使用：

> "现在几点了？"

Agent 会调用 `mcp_time_get_current_time` 工具获取时间。

### 3.2 Stdio 传输（本地子进程）

最常用的方式——Hermes 以子进程方式启动 MCP 服务器，通过 stdin/stdout 通信：

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
    timeout: 30
```

### 3.3 HTTP 传输（远程服务器）

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxx"
    timeout: 180
```

### 3.4 带认证的服务器

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xx...xxxx"
    timeout: 60
```

### 3.5 同时连接多个服务器

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xx...xxxx"
```

所有服务器的工具同时可用，通过名称前缀 `mcp_time_`、`mcp_github_` 区分。

---

## 四、管理 MCP

### 4.1 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `command` | string | — | 可执行文件路径（Stdio 必填） |
| `args` | list | `[]` | 命令参数 |
| `env` | dict | `{}` | 子进程环境变量（API Key 等） |
| `url` | string | — | 服务器 URL（HTTP 必填） |
| `headers` | dict | `{}` | HTTP 请求头 |
| `timeout` | int | 120 | 单次工具调用超时（秒） |
| `connect_timeout` | int | 60 | 初始连接超时（秒） |

### 4.2 工具命名规则

MCP 工具自动注册为 `mcp_{服务器名}_{工具名}`：

- 服务器 `filesystem`，工具 `read_file` → `mcp_filesystem_read_file`
- 服务器 `github`，工具 `list-issues` → `mcp_github_list_issues`

### 4.3 工具过滤

```bash
hermes mcp configure github
# 交互式开启/关闭特定工具
```

### 4.4 热重载

```bash
/reload-mcp
```

### 4.5 将 Hermes 作为 MCP 服务

```bash
hermes mcp serve
```

---

## 五、安全机制

- **环境变量过滤**：Stdio 子进程默认只继承 PATH、HOME 等安全变量，API Key 必须通过 `env` 显式声明
- **凭据自动掩饰**：错误信息中的 GitHub PAT、OpenAI Key 等自动屏蔽
- **工具粒度控制**：通过 `hermes mcp configure` 精细控制每个服务器的工具可见性

---

# 第九部分：定时任务（Cron）

## 一、简介

**Cron** 是 Hermes 内置的定时任务调度器。你可以用自然语言定义周期性的自动化任务——日报、备份、监控、提醒——Agent 会在指定时间自动执行并投递结果到指定平台。

定时任务以 `cronjob` 工具集的形式提供，默认已包含在核心工具集中。

### 调度格式

| 格式 | 示例 | 说明 |
|------|------|------|
| **时长** | `30m`、`2h` | 每隔一段时间执行一次 |
| **自然语言** | `every monday 9am` | 每周一早上 9 点 |
| **Cron 表达式** | `0 9 * * *` | 标准 5 字段 cron 格式 |
| **时间戳** | `2026-05-23T09:00:00` | 指定时间执行一次 |

---

## 二、常用操作

| 类别 | 命令/操作 | 描述 |
|------|----------|------|
| 创建 | `hermes cron create 30m` | 创建定时任务，传入自然语言描述 |
| 查看 | `hermes cron list` | 列出所有定时任务 |
| 查看 | `hermes cron list --all` | 列出所有任务（含已暂停的） |
| 查看 | `hermes cron status` | 查看调度器运行状态 |
| 修改 | `hermes cron edit ID` | 修改任务的调度、提示词、投递目标 |
| 暂停 | `hermes cron pause ID` | 暂停一个任务 |
| 恢复 | `hermes cron resume ID` | 恢复一个已暂停的任务 |
| 立即执行 | `hermes cron run ID` | 立即触发一次任务执行 |
| 删除 | `hermes cron remove ID` | 删除一个任务 |

---

## 三、使用定时任务

### 3.1 创建定时任务

直接在对话中告诉 Hermes 你想做什么：

> "每天早上 9 点给我一份 AI 行业日报"
> "每隔 30 分钟检查一次服务器状态"
> "每周一审查所有待办事项"

Hermes 会自动调用 `cronjob` 工具创建任务。

也可以通过 CLI 创建：

```bash
hermes cron create "every day 9am" \
  --prompt "搜索今天 AI 行业新闻并生成摘要" \
  --name "AI 日报"
```

### 3.2 指定执行间隔

```bash
# 每 30 分钟
hermes cron create "30m" --prompt "..."

# 每 2 小时
hermes cron create "every 2h" --prompt "..."

# 每天中午 12 点
hermes cron create "0 12 * * *" --prompt "..."

# 每周一、三、五 上午 10 点
hermes cron create "0 10 * * 1,3,5" --prompt "..."
```

### 3.3 指定投递目标

```bash
# 投递到当前会话 + 所有平台
hermes cron create "every day 9am" \
  --prompt "生成日报" \
  --deliver "origin,all"

# 投递到指定 Telegram 频道
hermes cron create "every day 9am" \
  --prompt "生成日报" \
  --deliver "telegram:-1001234567890:17585"
```

### 3.4 预加载技能

```bash
hermes cron create "0 9 * * *" \
  --prompt "做代码审查" \
  --skills "code-review,github-pr-workflow"
```

### 3.5 指定模型

```bash
hermes cron create "30m" \
  --prompt "检查服务器状态" \
  --model "deepseek-v4-flash" \
  --provider "deepseek"
```

### 3.6 关联脚本

通过脚本收集数据，注入到 Agent 的提示词中：

```bash
hermes cron create "0 9 * * *" \
  --prompt "基于以下数据生成日报" \
  --script /path/to/collect_data.sh
```

如果只需脚本输出无需 LLM，使用 `--no-agent`：

```bash
hermes cron create "5m" \
  --script /path/to/watchdog.sh \
  --no-agent
```

### 3.7 指定工作目录

在特定项目目录下运行任务，自动加载该目录的 `CLAUDE.md`：

```bash
hermes cron create "0 9 * * *" \
  --prompt "检查项目 Issues" \
  --workdir /home/user/my-project
```

---

## 四、管理定时任务

### 4.1 查看任务列表

```bash
hermes cron list
```

返回所有任务的 ID、名称、调度、下次执行时间、状态。

### 4.2 修改任务

```bash
hermes cron edit <job-id> --schedule "0 10 * * *"
hermes cron edit <job-id> --prompt "新的执行内容"
```

### 4.3 暂停 / 恢复

```bash
hermes cron pause <job-id>      # 暂停
hermes cron resume <job-id>     # 恢复
```

### 4.4 立即执行

```bash
hermes cron run <job-id>
```

不影响原有调度周期。

### 4.5 删除

```bash
hermes cron remove <job-id>
```

---

## 五、注意事项

- **超时限制**：每次任务执行最长 3 分钟，超时自动中断
- **互斥锁**：同一任务不会同时执行两次，锁文件防止重复触发
- **记忆隔离**：定时任务默认跳过持久记忆，避免污染用户画像
- **安全**：`--yolo` 模式不适用于定时任务，高危命令仍需审批
- **查看日志**：任务执行日志位于 `~/.hermes/logs/`
