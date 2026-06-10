# Codex 完整指南

> Codex 原生只支持 OpenAI 模型，但通过 **Codex++** 的中转注入功能，你可以接入任意第三方大模型 API（DeepSeek、Claude、Gemini、Qwen 等），实现低成本甚至免费使用。

---

## 一、什么是 Codex

Codex 是 OpenAI 推出的 AI 编程助手，提供独立桌面客户端（Codex App），通过自然语言对话完成代码编写、项目管理和 Git 工作流。

**核心定位：** 桌面端 AI 编程助手，原本绑定 OpenAI 模型，但借助 Codex++ 可接入第三方 API。

| 属性 | 说明 |
|------|------|
| 开发商 | OpenAI |
| 主要形态 | Codex App 桌面客户端（macOS / Windows） |
| 开源协议 | Apache 2.0 |
| GitHub Stars | 89K+ |
| 默认模型 | o4-mini / gpt-4o / gpt-5-codex |
| **第三方模型** | **通过 Codex++ 中转注入接入** |

---

## 二、为什么要用第三方 API

### 2.1 原生 Codex 的限制

| 限制 | 说明 |
|------|------|
| 模型绑定 | 默认只能使用 OpenAI 的模型（o4-mini、gpt-4o 等） |
| 费用较高 | ChatGPT Pro $200/月，API 按量计费也不便宜 |
| 网络要求 | 直连 OpenAI 服务器，国内访问不稳定 |
| 账号风控 | 多设备登录、频繁切换 IP 容易触发风控 |

### 2.2 第三方 API 的优势

| 优势 | 说明 |
|------|------|
| **成本低** | 中转平台价格通常为官方的 10%~60%，部分平台有免费额度 |
| **模型丰富** | 一个 API Key 可切换 DeepSeek、Claude、Gemini、Qwen 等多种模型 |
| **国内直连** | 中转平台服务器在国内，延迟低、无需梯子 |
| **稳定可靠** | 自动故障转移、智能路由，比直连更稳定 |

### 2.3 Codex++ 官方赞助商/中转平台

以下平台均为 Codex++ 官方赞助商，经过社区验证，可放心使用：

| 平台 | 特点 | 价格参考 |
|------|------|----------|
| **JOJO Code** | Codex++ 官方中转站，稳定接入 | 官方价优惠 |
| **AIGoCode** | Claude Code + Codex + Gemini 一体化 | 首充额外 10% 奖励 |
| **RunAPI** | 150+ 模型，高效稳定 | 低至 1 折 |
| **APIKEY.FUN** | 全球主流大模型，价格低至 7% | 永久 95 折 |
| **PackyCode** | 稳定高效，支持多种中转服务 | 首充 9 折 |
| **AIHub2API** | 专注 Codex 中转，高缓存命中 | 赠送 $10 体验额度 |
| **0029云桥** | 支持个人和企业接入 | 包月/按量计费 |
| **RawChat** | 老牌中转站，低倍率调用 | 包月套餐 |
| **VisionCoder** | 可靠高效，Token Plan 限时活动 | 买 1 个月送 1 个月 |
| **优云智算** | UCloud 旗下，高性价比国模套餐 | 低至 49 元/月 |
| **Cubence** | 稳定高效，长期运营 | 首充 8.8 折 |
| **Unity2.ai** | 高性能，日均 300 亿 token | 最高领 $12 免费额度 |

> 以上平台均可通过 Codex++ 的中转注入功能一键接入。

---

## 三、Codex++ 的核心价值

[Codex++](https://github.com/BigPizzaV3/CodexPlusPlus) 是面向 Codex App 的外部增强启动器和管理工具（GitHub Stars: 16.6K+）。它不修改 Codex App 原始安装文件，而是通过 Chromium DevTools Protocol (CDP) 注入增强脚本。

**技术栈：** Rust + Tauri + React

### 3.1 中转注入（核心功能）

中转注入是 Codex++ 最关键的功能——它允许你配置第三方 API 提供商，将 Codex App 的模型请求路由到你指定的 API 端点。

**工作原理：**

1. Codex++ 通过 CDP 协议注入增强脚本到 Codex App
2. 拦截模型请求，路由到配置的第三方 API
3. 第三方 API 返回结果，Codex App 正常显示

**配置方式：**

在 `~/.codex/config.toml` 中写入：

```toml
model_provider = "CodexPlusPlus"

[model_providers.CodexPlusPlus]
name = "CodexPlusPlus"
wire_api = "responses"
requires_openai_auth = true
base_url = "https://your-api-endpoint.com/v1"
experimental_bearer_token = "sk-your-api-key"
```

### 3.2 其他增强功能

| 功能 | 说明 |
|------|------|
| 插件解锁 | API Key 模式下解锁 Codex App 的插件功能 |
| 会话管理 | 会话删除（带撤销）、会话迁移 |
| Markdown 导出 | 将完整对话导出为 Markdown 文件 |
| 对话时间线 | 快速跳转到对话中的任意位置 |
| 用户脚本 | 独立管理，可在启动时注入自定义脚本 |
| Provider 同步 | 启动前同步本地会话 metadata，切换供应商后旧会话仍可见 |
| Zed 打开入口 | 识别远程 SSH 上下文后，可从 Codex 直接打开对应文件到 Zed |
| 自动更新 | 通过 Codex++ Manager 检查和安装更新 |

### 3.3 产品家族

| 产品 | 说明 | 推荐度 |
|------|------|--------|
| **Codex + Codex++** | 桌面端 + 第三方 API，**本文档的核心方案** | ⭐⭐⭐⭐⭐ |
| Codex Web | chatgpt.com/codex，在线版 | ⭐⭐⭐ |
| IDE 扩展 | VS Code / JetBrains 插件 | ⭐⭐⭐ |

---

## 四、认证与 API 配置

### 4.1 两种认证方式

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| **ChatGPT 账户登录** | 使用 Plus/Pro 订阅的额度 | 已有 ChatGPT 订阅的用户 |
| **API Key 模式（BYOK）** | 填入第三方 API Key | **推荐**，灵活、低成本 |

### 4.2 推荐：API Key + 第三方中转

这是社区最流行的用法：

1. 在第三方平台（如 JOJO Code、RunAPI）注册并充值
2. 获取 API Key
3. 在 Codex++ Manager 的"中转注入"页面配置
4. 启动 Codex++，即可使用第三方模型

> **详细配置步骤：** [Codex 桌面端安装与配置](./02-Codex安装与配置.md)

---

## 五、定价对比

### 5.1 原生方案 vs 第三方 API

| 方案 | 月费 / 单价 | 可用模型 | 说明 |
|------|------------|----------|------|
| ChatGPT Plus | $20/月 | OpenAI 系列 | 有额度限制 |
| ChatGPT Pro | $200/月 | OpenAI 系列 | 额度充足但贵 |
| OpenAI API | 按 token 计费 | OpenAI 系列 | o4-mini 便宜，gpt-4o 较贵 |
| **第三方中转** | **官方价 10%~60%** | **多厂商模型** | **推荐** |

### 5.2 常用模型第三方价格参考

| 模型 | 官方价（输入/百万token） | 中转价（参考） | 适合场景 |
|------|------------------------|---------------|----------|
| o4-mini | $1.10 | ¥0.5~1.0 | 日常开发 |
| gpt-4o | $2.50 | ¥1.5~3.0 | 复杂任务 |
| gpt-5-codex | $5.00 | ¥3.0~5.0 | 大型重构 |
| DeepSeek V3 | $0.27 | ¥0.1~0.3 | 性价比之选 |
| Claude Sonnet | $3.00 | ¥1.5~3.0 | 代码质量高 |

> 具体价格以各平台实时报价为准。

---

## 六、快速开始

### 步骤一：安装 Codex++

1. 前往 [Codex++ GitHub Releases](https://github.com/BigPizzaV3/CodexPlusPlus/releases)
2. 下载对应系统的安装包：
   - Windows：`CodexPlusPlus-*-windows-x64-setup.exe`
   - macOS（Apple Silicon）：`CodexPlusPlus-*-macos-arm64.dmg`
   - macOS（Intel）：`CodexPlusPlus-*-macos-x64.dmg`
3. 运行安装程序

### 步骤二：配置第三方 API

1. 启动 **Codex++ 管理工具**（Tauri 控制面板）
2. 进入"中转注入"页面
3. 添加中转配置，填写 Base URL 和 API Key
4. 选择配置并应用中转注入

### 步骤三：开始使用

1. 启动 **Codex++**（静默启动入口，不显示管理界面）
2. 在 Codex App 中创建新会话
3. 关联 GitHub 仓库或打开本地项目
4. 通过对话框输入指令，Codex 会通过第三方 API 响应

> **详细安装指南：** [Codex 桌面端安装与配置](./02-Codex安装与配置.md)

---

## 七、数据位置

| 路径 | 说明 |
|------|------|
| `~/.codex/config.toml` | Codex 配置文件 |
| `~/.codex/auth.json` | Codex 登录状态 |
| `~/.codex/state_5.sqlite` | Codex 本地数据库 |
| `~/.codex-session-delete/` | Codex++ 状态与日志 |
| `~/.codex/backups_state/provider-sync` | Provider 同步备份 |

---

## 八、学习路径

| 顺序 | 文档 | 内容 |
|------|------|------|
| 1 | [Codex 完整指南](./01-Codex完整指南.md)（本文） | 产品概览、第三方 API 方案、定价对比 |
| 2 | [Codex 桌面端安装与配置](./02-Codex安装与配置.md) | Codex++ 安装、中转注入配置、认证 |
| 3 | [Codex 桌面端核心功能详解](./03-Codex核心功能详解.md) | AGENTS.md、Skills、MCP、会话管理 |
| 4 | [Codex 桌面端实战技巧与踩坑](./04-Codex实战技巧与踩坑.md) | Prompt 技巧、Codex++ 高级功能、FAQ |
