# Hermes Agent 接入应用

本文介绍如何将 Hermes Agent 接入 QQ、微信（WeChat）和飞书（Feishu/Lark）等国内主流即时通讯平台，让 AI 助手直接在这些聊天工具中与你交互。

> **前置要求**：Hermes Agent 已安装并配置好模型提供商（参见 [安装与部署](Hermes Agent安装与部署.md)）。
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
| 飞书 (Feishu/Lark) | `pip install lark-oapi`（推荐 WebSocket 模式）或 `pip install websockets` |

### 3. 确认 Gateway 可用

```bash
hermes gateway --help
```

如果正常显示帮助信息，说明 Gateway 组件已就绪。

---

## 一、接入 QQ

Hermes 通过**腾讯官方 QQ Bot API（v2）** 接入 QQ，支持私聊（C2C）、群聊 @提及、频道消息等。

> **前置条件**：前往 [q.qq.com](https://q.qq.com) 注册 QQ 机器人应用，记下 **App ID** 和 **App Secret**，并开启所需的 Intents（C2C 消息、群 @消息、频道消息）。

### 接入步骤

#### Step 1：运行 Setup 向导

在终端执行：

```bash
hermes gateway setup
```

终端会显示平台选择列表，输入对应数字即可选择平台。

---

#### Step 2：选择 QQ Bot

输入 1，选择"扫描二维码添加机器人"方式。

---

#### Step 3：点击QQ扫码链接

终端会输出一个 QQ 扫码链接，将其复制到浏览器中打开，页面会显示 QQ 二维码，使用手机 QQ 扫码登录。

---

#### Step 4：私聊信息授权

选择 1，使用私聊配对码审批，后续全程输入 `y` 确认即可。

---

#### Step 5：效果展示

配置完成后，在 QQ 中私聊机器人发送消息，即可收到回复。

---

#### ⚠注意

> 如果遇到QQ机器人长时间无回复，可尝试重启Hermes来尝试

---

## 二、接入微信（WeChat / Weixin）

### 接入步骤

#### Step 1：运行 Setup 向导

```bash
hermes gateway setup
```

终端会显示平台选择列表。

---

#### Step 2：选择 Weixin (WeChat)

在平台列表中，输入13，选择 **Weixin (WeChat)**。

---

#### Step 3：终端显示二维码

向导会请求 iLink Bot API 生成登录二维码，二维码会显示在终端中（或提供一个 URL 用于浏览器查看）。复制链接到浏览器打开即可看到二维码。

---

#### Step 4：手机扫码并确认

打开手机微信，扫描终端上的二维码，然后在手机上确认登录。

---

#### Step 5：凭据自动保存

扫码确认后，终端会显示连接成功信息：

```
微信连接成功，account_id=your-account-id
```

凭据会自动保存到 `~/.hermes/weixin/accounts/` 目录下。

---

#### Step 6：配置环境变量（可选）

在 `~/.hermes/.env` 中，至少设置 Account ID：

```env
WEIXIN_ACCOUNT_ID=your-account-id
# 以下按需配置
WEIXIN_DM_POLICY=open
WEIXIN_ALLOWED_USERS=user_id_1,user_id_2
WEIXIN_HOME_CHANNEL=chat_id
```

---

#### Step 7：启动 Gateway

```bash
hermes gateway
```

启动后，适配器会自动恢复已保存的凭据，连接到 iLink API，开始长轮询接收消息。

---

#### Step 8：验证连接

在微信上给机器人（iLink Bot 账号）发一条消息，确认能正常收到回复。

> 【需要你补充：你的 iLink Bot 账号的微信联系人页面截图？注意打码隐私信息。】

---

### 微信环境变量参考

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `WEIXIN_ACCOUNT_ID` | iLink Bot 账号 ID（必填） | — |
| `WEIXIN_TOKEN` | iLink Bot Token（扫码后自动保存） | — |
| `WEIXIN_BASE_URL` | iLink API 基础地址 | `https://ilinkai.weixin.qq.com` |
| `WEIXIN_DM_POLICY` | 私信策略：`open` / `allowlist` / `disabled` / `pairing` | `open` |
| `WEIXIN_ALLOWED_USERS` | 允许发送私信的用户 ID 列表（逗号分隔） | — |
| `WEIXIN_GROUP_POLICY` | 群聊策略：`open` / `allowlist` / `disabled` | `disabled` |
| `WEIXIN_GROUP_ALLOWED_USERS` | 允许回复的群聊 ID 列表（注意：是群 ID，不是用户 ID） | — |
| `WEIXIN_HOME_CHANNEL` | 定时任务投递的 Home 频道 | — |
| `WEIXIN_SPLIT_MULTILINE_MESSAGES` | 多行消息是否拆分为多条发送 | `false` |

### 微信重要限制

iLink Bot 身份（如 `a5ace6fd482e@im.bot`）存在以下限制：
- **无法被拉入普通微信群**（不同于正常联系人）
- 群消息事件通常**不会投递**给 Gateway
- 扫码登录的是**机器人身份**，与你个人的微信账号是分离的

实际使用中，**仅私信对话可靠工作**。群聊消息不成功属于 iLink 侧限制，非 Hermes 问题。

### 微信常见问题

| 问题 | 解决方法 |
|------|---------|
| 启动失败：`aiohttp and cryptography are required` | 安装依赖：`pip install aiohttp cryptography` |
| 启动失败：`WEIXIN_TOKEN is required` | 运行 `hermes gateway setup` 完成扫码登录 |
| 启动失败：`WEIXIN_ACCOUNT_ID is required` | 设置 `WEIXIN_ACCOUNT_ID` 或运行 setup 向导 |
| 会话过期（errcode=-14） | 重新运行 `hermes gateway setup` 扫码 |
| 二维码过期 | 二维码会自动刷新最多 3 次，如仍过期检查网络 |
| 机器人不回复私信 | 检查 `WEIXIN_DM_POLICY` 是否设为 `allowlist` 且发送者不在白名单中 |
| 无法加载图片/文件 | 确保已安装 `cryptography`，检查 CDN 网络连通性 |

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

---

#### Step 2：选择 Feishu / Lark

在平台列表中，选择 **Feishu / Lark**。

---

#### Step 3：扫码创建应用（推荐）或手动输入

向导会展示一个二维码，用飞书手机 App 扫码即可自动创建机器人应用并保存凭据。

如果扫码不可用，向导会回退到手动输入模式，需要你提供从 [open.feishu.cn](https://open.feishu.cn)（国内）或 [open.larksuite.com](https://open.larksuite.com)（国际版）获取的 **App ID** 和 **App Secret**。

---

#### Step 4：选择连接模式

按提示选择连接模式，推荐选择 **WebSocket**。

---

#### Step 5：启动 Gateway

```bash
hermes gateway
```

---

#### Step 6：验证连接

在飞书上搜索机器人并发送一条消息，确认能正常收到回复。如果使用 WebSocket 模式，SDK 会自动维持连接和心跳。

---

### 飞书环境变量参考

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FEISHU_APP_ID` | 飞书应用 App ID（必填） | — |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret（必填） | — |
| `FEISHU_DOMAIN` | `feishu`（国内）或 `lark`（国际版） | `feishu` |
| `FEISHU_CONNECTION_MODE` | `websocket` 或 `webhook` | `websocket` |
| `FEISHU_ALLOWED_USERS` | 允许使用机器人的用户 Open ID 列表 | 开放 |
| `FEISHU_HOME_CHANNEL` | 定时任务投递的聊天 ID | — |
| `FEISHU_GROUP_POLICY` | 群聊策略：`open` / `allowlist` / `disabled` | `allowlist` |
| `FEISHU_REQUIRE_MENTION` | 群聊是否需要 @提及才回复 | `true` |
| `FEISHU_ENCRYPT_KEY` | Webhook 模式加密密钥 | — |
| `FEISHU_VERIFICATION_TOKEN` | Webhook 验证令牌 | — |
| `FEISHU_ALLOW_BOTS` | 是否响应其他机器人的消息 | `none` |
| `FEISHU_WEBHOOK_HOST` | Webhook 绑定地址 | `127.0.0.1` |
| `FEISHU_WEBHOOK_PORT` | Webhook 端口 | `8765` |

### 飞书常见问题

| 问题 | 解决方法 |
|------|---------|
| `lark-oapi` 未安装 | `pip install lark-oapi` |
| `websockets` 未安装 | `pip install websockets` |
| `FEISHU_APP_ID` 或 `FEISHU_APP_SECRET` 未设置 | 运行 `hermes gateway setup` 或手动设置环境变量 |
| 机器人不响应群聊消息 | 确保 @提及了机器人；检查 `FEISHU_GROUP_POLICY` 和 `FEISHU_ALLOWED_USERS` |
| 交互式卡片按钮报错 200340 | 需要在飞书开发者后台开启「交互式卡片」能力并配置卡片请求地址 |
| Webhook 签名验证失败 | 确保 `FEISHU_ENCRYPT_KEY` 与飞书开发者后台的加密密钥一致 |

---

## 平台对比一览

| 维度 | QQ | 微信 (WeChat) | 飞书 (Feishu) |
|------|-----|-------------|--------------|
| **API 类型** | QQ Bot API v2（WebSocket） | iLink Bot API（长轮询） | Feishu API（WebSocket / Webhook） |
| **注册平台** | [q.qq.com](https://q.qq.com) | 扫码即用 | [open.feishu.cn](https://open.feishu.cn) |
| **公网要求** | ❌ 不需要 | ❌ 不需要 | ❌ WebSocket 不需要 / Webhook 需要 |
| **配置复杂度** | ⭐⭐ 中 | ⭐ 低 | ⭐⭐⭐ 中高 |
| **私信** | ✅ | ✅ | ✅ |
| **群聊 @提及** | ✅ | ⚠️ 受限 | ✅ |
| **图片** | ✅ | ✅ | ✅ |
| **语音转文字** | ✅（内置 ASR + 回退 STT） | ✅ | ✅ |
| **视频** | ✅ | ✅ | ✅ |
| **文件** | ✅ | ✅ | ✅ |
| **Markdown** | ✅（需配置） | ✅ | ✅（富文本 Post） |
| **交互式卡片** | ❌ | ❌ | ✅ |
| **文档回复** | ❌ | ❌ | ✅ |
| **定时任务投递** | ✅ | ✅ | ✅ |

---

## 多平台同时运行

Hermes Gateway 支持**一个进程同时连接多个平台**。只需依次通过 `hermes gateway setup` 配置好每个平台，然后启动网关即可：

```bash
hermes gateway setup     # 依次配置 QQ → 微信 → 飞书
hermes gateway           # 启动网关，所有平台同时在线
```

### 跨平台交互

- 所有平台共享同一个 AIAgent 核心，但**会话是隔离的**——QQ 上的对话不会干扰微信上的对话
- 使用 `/sethome` 命令可将某个聊天设为 **Home 频道**，定时任务结果会投递到该频道
- 每个平台有独立的**访问策略**（白名单、群聊策略等）

---

> **参考链接**
> - [Hermes Gateway 官方文档](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/)
> - [QQ Bot 适配器文档](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/qqbot)
> - [微信适配器文档](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/weixin/)
> - [飞书适配器文档](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/feishu/)
