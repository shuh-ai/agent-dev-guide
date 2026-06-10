# Codex 桌面端安装与配置

## 1. 概述

Codex App 是 OpenAI 官方推出的桌面端编码代理应用。推荐通过 **Codex++** 增强启动器来使用，它在不修改原始 Codex 的基础上，注入大量实用增强功能，提供更完整的桌面端体验。

| 使用方式 | 推荐度 | 说明 |
|----------|--------|------|
| **Codex++ 桌面应用** | ⭐⭐⭐⭐⭐ | 增强启动器，功能最全，推荐日常使用 |
| 原始 Codex App | ⭐⭐⭐ | 官方原版，功能较少 |

> **本文档仅覆盖桌面端安装。** 不涉及任何 CLI 命令行安装方式。

---

## 2. Codex++ 安装

### 2.1 什么是 Codex++

Codex++ 是面向 Codex App 的**外部增强启动器和管理工具**（GitHub Stars: 16.6K+）。它不修改 Codex App 原始安装文件，而是通过 Chromium DevTools Protocol (CDP) 注入增强脚本。

**技术栈：** Rust + Tauri + React

核心设计理念：

- **不修改原始 Codex** — Codex++ 是独立的增强层，原版 Codex 文件不受影响
- **基于 CDP 协议** — 通过 DevTools 协议与 Codex App 通信，安全可靠
- **透明增强** — 启动后自动生效，无需手动操作

**项目地址：** [github.com/BigPizzaV3/CodexPlusPlus](https://github.com/BigPizzaV3/CodexPlusPlus)

### 2.2 核心增强功能

| 功能 | 说明 |
|------|------|
| **中转注入** | 支持多个中转配置，将模型请求路由到第三方 API |
| **插件解锁** | API Key 模式下解锁 Codex App 的插件功能 |
| **会话删除（带撤销）** | 支持删除不需要的会话记录，误删可立即撤销 |
| **Markdown 导出** | 将完整对话导出为 Markdown 文件 |
| **对话时间线** | 可视化对话时间线，快速定位历史消息 |
| **用户脚本** | 独立管理，可在启动时注入自定义脚本 |
| **Provider 同步** | 启动前同步本地会话 metadata，切换供应商后旧会话仍可见 |
| **Zed 打开入口** | 识别远程 SSH 上下文后，可从 Codex 直接打开对应文件到 Zed |
| **自动更新** | 通过 Codex++ Manager 检查和安装更新 |

### 2.3 Windows 安装

1. 访问 [CodexPlusPlus Releases 页面](https://github.com/BigPizzaV3/CodexPlusPlus/releases)
2. 找到最新版本，下载 `CodexPlusPlus-*-windows-x64-setup.exe`
3. 双击运行安装程序，按向导完成安装
4. 安装完成后，桌面和开始菜单自动生成快捷方式

### 2.4 macOS 安装

根据芯片架构选择对应版本：

| 芯片类型 | 安装包 | 说明 |
|----------|--------|------|
| **Apple Silicon**（M1/M2/M3/M4） | `CodexPlusPlus-*-macos-arm64.dmg` | 推荐大多数 Mac 用户 |
| **Intel** | `CodexPlusPlus-*-macos-x64.dmg` | 适用于 Intel 芯片 Mac |

安装步骤：

1. 访问 [CodexPlusPlus Releases 页面](https://github.com/BigPizzaV3/CodexPlusPlus/releases)
2. 下载与芯片对应的 `.dmg` 文件
3. 打开 DMG，将 Codex++ 拖入 Applications 文件夹
4. 首次打开时，macOS 可能提示"无法验证开发者"或"已损坏"

**macOS 未签名/未公证解决方案：**

```bash
sudo xattr -rd com.apple.quarantine /Applications/Codex++\ 管理工具.app
sudo xattr -rd com.apple.quarantine /Applications/Codex++.app
```

执行后重新打开即可。

### 2.5 安装后入口

安装完成后，系统中会出现两个入口：

| 入口 | 用途 |
|------|------|
| **Codex++** | 静默启动入口，不显示管理界面，只负责启动 Codex 并注入增强功能。**日常使用此入口** |
| **Codex++ 管理工具** | Tauri 控制面板，用于启动、检查、修复、更新、配置中转注入、管理增强功能和用户脚本 |

> ⚠️ **重要提示：** 日常使用请**始终**通过 **Codex++** 快捷方式启动，而非原始的 Codex App。如果直接启动原始 Codex，增强功能将不会生效。

---

## 3. 首次启动与认证

### 3.1 ChatGPT 账户登录

首次启动 Codex++ 时，应用会提示登录 ChatGPT 账户。支持以下订阅计划：

| 计划 | 支持情况 |
|------|----------|
| Plus | ✅ 支持 |
| Pro | ✅ 支持 |
| Business | ✅ 支持 |
| Enterprise | ✅ 支持 |

登录流程：点击登录按钮 → 浏览器跳转至 OpenAI 授权页面 → 完成登录 → 自动返回应用。

### 3.2 API Key 模式（BYOK）

如果不想使用 ChatGPT 账户，可以使用自有 API Key（Bring Your Own Key）：

1. 在首次启动的认证界面选择 **"Use API Key"**
2. 填入 OpenAI API Key（格式：`sk-pro-...`）
3. 点击确认保存

如需后续修改 API Key，可在 Codex App 的 **Settings** 界面中更新。

### 3.3 认证文件位置

认证信息保存在本地文件中：

| 平台 | 路径 |
|------|------|
| Windows | `C:\Users\<用户名>\.codex\auth.json` |
| macOS | `~/.codex/auth.json` |

> 如遇认证问题，可尝试删除 `auth.json` 文件后重新启动 Codex++ 进行重新登录。

---

## 4. Codex++ 管理工具

Codex++ 管理工具是独立的 Tauri 控制面板，用于维护和配置 Codex++ 增强层。

### 4.1 更新管理

| 操作 | 说明 |
|------|------|
| **检查更新** | 打开管理工具，自动检测是否有新版本可用 |
| **安装更新** | 点击更新按钮，管理工具自动下载并安装最新版 Codex++ |
| **更新日志** | 查看每个版本的功能变更和修复记录 |

> 建议定期检查更新，以获得最新功能和 Bug 修复。更新 Codex++ 不会影响已有的 Codex App 数据和配置。

### 4.2 中转注入配置（核心功能）

中转注入是 Codex++ 最重要的功能——它允许你将 Codex App 的模型请求路由到**第三方 API 平台**，突破 OpenAI 模型限制，实现低成本使用。

**官方赞助商/中转平台：**

| 平台 | 特点 | 注册地址 |
|------|------|----------|
| **JOJO Code** | Codex++ 官方中转站，稳定接入 | jojocode.com |
| **AIGoCode** | Claude Code + Codex + Gemini 一体化 | aigocode.com |
| **RunAPI** | 150+ 模型，高效稳定 | runapi.co |
| **APIKEY.FUN** | 全球主流大模型，价格低至 7% | apikey.fun |
| **PackyCode** | 稳定高效，支持多种中转服务 | packyapi.com |
| **AIHub2API** | 专注 Codex 中转，高缓存命中 | aihub2api.cloud |
| **0029云桥** | 支持个人和企业接入 | 0029.org |
| **RawChat** | 老牌中转站，低倍率调用 | rawchat.cn |
| **VisionCoder** | 可靠高效，Token Plan 限时活动 | coder.visioncoder.cn |
| **优云智算** | UCloud 旗下，高性价比国模套餐 | compshare.cn |
| **Cubence** | 稳定高效，长期运营 | cubence.com |
| **Unity2.ai** | 高性能，日均 300 亿 token | unity2.ai |

**配置步骤：**

1. 在第三方平台注册并获取 **API Key** 和 **Base URL**
2. 打开 **Codex++ 管理工具** → **中转注入** 页面
3. 添加一个或多个中转配置，填写 Base URL 和 Key
4. 选择当前配置并应用中转注入
5. 启动 **Codex++**

**中转注入后 config.toml 配置示例：**

```toml
model_provider = "CodexPlusPlus"

[model_providers.CodexPlusPlus]
name = "CodexPlusPlus"
wire_api = "responses"
requires_openai_auth = true
base_url = "https://your-api-endpoint.com/v1"
experimental_bearer_token = "sk-..."
```

**中转注入模式的边界：**

- 官方 ChatGPT/Codex 登录态继续负责 Codex App 的账号能力和插件入口
- 中转配置只接管模型请求使用的 Base URL、Key 和模型名称
- 清除 API 模式后应能回到官方登录态

### 4.3 诊断与日志

遇到问题时，可使用管理工具的诊断功能：

| 功能 | 说明 |
|------|------|
| **连接诊断** | 检测 Codex++ 与 Codex App 的 CDP 连接状态 |
| **查看日志** | 打开 Codex++ 运行日志，定位错误原因 |
| **重置配置** | 将 Codex++ 配置恢复到默认状态 |

**手动测试后端连接：**

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:57321/backend/status -Body "{}" -ContentType "application/json"
```

---

## 5. 配置文件

### 5.1 全局配置 `config.toml`

Codex App 的全局配置文件位于：

| 平台 | 路径 |
|------|------|
| Windows | `C:\Users\<用户名>\.codex\config.toml` |
| macOS | `~/.codex/config.toml` |

常用配置项：

```toml
# ~/.codex/config.toml

[model]
default = "o4-mini"          # 默认模型

[sandbox]
mode = "suggest"             # 沙箱模式: suggest | auto-edit | full-auto

[approvals]
auto_approve = false         # 是否自动批准命令执行
```

**沙箱模式说明：**

| 模式 | 行为 | 适用场景 |
|------|------|----------|
| **suggest** | 仅提供建议，不自动执行 | 初次使用、审阅代码变更 |
| **auto-edit** | 自动编辑文件，命令需确认 | 日常开发 |
| **full-auto** | 完全自动执行 | 信任环境、批量操作 |

### 5.2 项目级配置 `AGENTS.md`

在项目根目录创建 `AGENTS.md` 文件，定义项目级别的指令和约束。Codex 在处理该项目时会自动读取。

```markdown
# AGENTS.md

## 项目规范
- 使用 TypeScript 编写所有代码
- 遵循 ESLint 规则
- 提交前必须通过测试

## 代码风格
- 使用 2 空格缩进
- 优先使用 const，避免 let
- 函数使用箭头函数语法
```

> `AGENTS.md` 的详细用法和高级配置，请参阅 [03-AGENTS.md 项目配置](./03-AGENTS.md项目配置.md)。

---

## 6. 模型选择

### 6.1 OpenAI 原生模型

在 Codex App 桌面端中，可以通过 UI 切换使用的模型：

| 模型 | 说明 | 适用场景 |
|------|------|----------|
| **o4-mini** | 默认模型，性价比高 | 日常开发、一般编码任务 |
| **gpt-4o** | 多模态能力强 | 复杂任务、图片理解 |
| **gpt-5-codex** | 最新旗舰模型 | 复杂架构设计、大型重构 |

**在桌面端切换模型的方法：**

1. 在 Codex App 主界面中，找到模型选择下拉菜单（通常位于对话输入区域附近）
2. 点击下拉菜单，选择目标模型
3. 切换立即生效，后续对话使用新模型

> 也可以在 `config.toml` 中设置默认模型（参见 5.1 节），这样每次启动时自动使用指定模型。

### 6.2 第三方模型（通过中转注入）

配置中转注入后，你可以在 Codex 中使用来自其他厂商的模型：

| 模型 | 厂商 | 特点 | 中转价格参考 |
|------|------|------|-------------|
| **DeepSeek V3** | DeepSeek | 性价比极高，中文能力强 | ¥0.1~0.3/百万token |
| **DeepSeek R1** | DeepSeek | 推理能力强 | ¥0.5~1.0/百万token |
| **Claude Sonnet 4** | Anthropic | 代码质量高 | ¥1.5~3.0/百万token |
| **Claude Opus 4** | Anthropic | 最强推理能力 | ¥5.0~10.0/百万token |
| **Gemini 2.5 Pro** | Google | 超长上下文（1M tokens） | ¥1.0~2.0/百万token |
| **Qwen3** | 阿里 | 中文编程能力强 | 免费~¥0.5/百万token |

> 以上模型需通过中转注入配置第三方 API 平台后使用。具体可用模型取决于所选平台的支持范围。

---

## 7. 数据位置

| 路径 | 说明 |
|------|------|
| `~/.codex/config.toml` | Codex 配置文件 |
| `~/.codex/auth.json` | Codex 登录状态 |
| `~/.codex/state_5.sqlite` | Codex 本地数据库 |
| `~/.codex-session-delete/` | Codex++ 状态与日志 |
| `~/.codex/backups_state/provider-sync` | Provider 同步备份 |

---

## 8. 故障排除

### 8.1 Codex++ 菜单不显示

**现象：** 启动后看不到 Codex++ 增强菜单。

| 检查项 | 解决方法 |
|--------|----------|
| 启动入口错误 | 确认使用的是 **Codex++** 快捷方式，而非原始 Codex App |
| CDP 连接失败 | 打开管理工具 → 诊断，检查连接状态 |
| 版本不匹配 | 通过管理工具更新 Codex++ 至最新版本 |
| 防火墙拦截 | 检查本地防火墙是否阻止了 CDP 通信端口 |

### 8.2 插件后端断开连接

**现象：** 插件功能突然不可用，提示后端断开。

**解决步骤：**

1. 关闭 Codex App（完全退出，包括系统托盘）
2. 重新通过 **Codex++** 启动
3. 如问题持续，打开管理工具 → 诊断 → 重置插件配置
4. 重新启动 Codex++

### 8.3 认证问题

**现象：** 登录失败、API Key 无效、频繁要求重新登录。

| 问题 | 解决方法 |
|------|----------|
| 登录循环 | 删除 `~/.codex/auth.json`，重新启动并登录 |
| API Key 失效 | 前往 OpenAI 平台检查 Key 状态，在 Settings 中更新 |
| 企业账户限制 | 联系组织管理员确认 Codex 访问权限 |
| 网络问题 | 检查代理/VPN 设置，确保能正常访问 OpenAI 服务 |

### 8.4 更新问题

**现象：** 管理工具提示更新失败，或更新后功能异常。

| 问题 | 解决方法 |
|------|----------|
| 更新下载失败 | 检查网络连接，或手动从 GitHub Releases 下载安装 |
| 更新后菜单消失 | 重新打开管理工具，执行诊断检查 |
| 版本回退 | 在管理工具中查看历史版本，必要时手动安装旧版本 |
| 更新冲突 | 关闭 Codex App 后再执行更新操作 |

---

## 附录：快速参考

### 关键文件位置

| 文件 | Windows 路径 | macOS 路径 |
|------|-------------|------------|
| 认证信息 | `C:\Users\<用户名>\.codex\auth.json` | `~/.codex/auth.json` |
| 全局配置 | `C:\Users\<用户名>\.codex\config.toml` | `~/.codex/config.toml` |
| 项目配置 | `<项目根目录>\AGENTS.md` | `<项目根目录>/AGENTS.md` |
| Codex++ 日志 | `C:\Users\<用户名>\.codex-session-delete\` | `~/.codex-session-delete/` |

### 常用链接

| 资源 | 链接 |
|------|------|
| Codex++ 项目 | [github.com/BigPizzaV3/CodexPlusPlus](https://github.com/BigPizzaV3/CodexPlusPlus) |
| Codex++ Releases | [Releases 页面](https://github.com/BigPizzaV3/CodexPlusPlus/releases) |
| OpenAI Platform | [platform.openai.com](https://platform.openai.com) |
| QQ 交流群 | 1103050832 |
| Telegram 频道 | [t.me/CodexPlusPlus](https://t.me/CodexPlusPlus) |
