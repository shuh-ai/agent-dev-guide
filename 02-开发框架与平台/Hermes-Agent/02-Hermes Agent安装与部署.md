# Hermes Agent 安装与部署（Windows 优化版）

---

## 一、安装指南

Hermes Agent 在 Windows 上有两条安装路径，按你的开发环境选择：

### 1.1 路径 A：PowerShell 原生安装（推荐）

这是官方推荐的 Windows 原生安装方式，使用 PowerShell 从脚本安装，**无需管理员权限**。

#### 前提条件
- Windows 10 或更高版本（64 位）
- PowerShell 5.1+（Win10 自带）或 PowerShell 7+
- 网络能访问 GitHub (raw.githubusercontent.com)
- **不需要** WSL2 或 Python 预装（安装器自带便携版）

#### 安装命令

以**管理员身份**打开 PowerShell（非必需但可避免权限问题），执行：

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

安装器会自动完成：
1. 下载并解压便携版 Git Bash（~45 MB，仅首次）
2. 创建 Hermes 虚拟环境（Python 捆绑在发布包中）
3. 配置 PATH，使 `hermes` 命令可在 PowerShell / CMD / Git Bash 中使用
4. 初始化数据目录到 `%LOCALAPPDATA%\hermes\`

#### 安装位置

| 变量形式 | 实际 Windows 路径 |
|----------|------------------|
| `%LOCALAPPDATA%\hermes\` | `C:\Users\当前用户名\AppData\Local\hermes\` |
| `%LOCALAPPDATA%\hermes\hermes-agent\` | `C:\Users\当前用户名\AppData\Local\hermes\hermes-agent\` |
| `%LOCALAPPDATA%\hermes\config.yaml` | `C:\Users\当前用户名\AppData\Local\hermes\config.yaml` |
| `%LOCALAPPDATA%\hermes\.env` | `C:\Users\当前用户名\AppData\Local\hermes\.env` |
| `%LOCALAPPDATA%\hermes\skills\` | `C:\Users\当前用户名\AppData\Local\hermes\skills\` |
| `%LOCALAPPDATA%\hermes\sessions\` | `C:\Users\当前用户名\AppData\Local\hermes\sessions\` |
| `%LOCALAPPDATA%\hermes\logs\` | `C:\Users\当前用户名\AppData\Local\hermes\logs\` |

> 在你的机器上，将 `当前用户名` 替换为你的 Windows 用户名即可。

---

### 1.2 路径 B：Git Bash / WSL2 安装

如果你已经在 Windows 上使用了 **Git Bash** 或 **WSL2（推荐）**，也可用 Linux 风格的安装脚本：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

此方式在 Git Bash（MSYS2 环境）下工作良好——Hermes 自带的 Python venv 和路径解析在 MSYS2 中均正常。本机当前环境即采用此方式安装。

---

### 1.3 验证安装

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

### 1.4 更新

```bash
hermes update
```

如有重要更新，`hermes doctor` 也会提示落后版本数。

---

### 1.5 Windows 安装常见问题

#### PowerShell 执行策略阻止脚本

```powershell
# 查看当前策略
Get-ExecutionPolicy

# 临时允许（当前会话）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# 或永久修改（当前用户）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 杀毒软件拦截

安装器下载可执行文件时可能触发 Windows Defender 或第三方杀毒。如遇拦截，添加排除项或临时关闭实时防护后再运行。

#### 中文路径问题

Hermes 的数据目录和配置路径均使用英文，不受系统用户名中包含中文的影响。但项目工作目录若包含中文，在 Git Bash 中可能遇到编码问题——建议在 Git Bash 的 `~/.bashrc` 中添加：

```bash
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8
```

#### 代理/网络问题

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

## 二、基础配置

### 2.1 选择模型提供商

Hermes 支持极广泛的模型提供商，**切换无需编辑配置文件**：

```bash
hermes model
```

该命令会列出所有可用的提供商和模型，输入对应序号选择即可：

终端会列出所有可用的提供商和模型，输入对应序号选择即可。

常用提供商包括：

| 提供商 | 特点 | 官网 | Base URL |
|--------|------|------|----------|
| **DeepSeek** | 性价比高，v4 flash 速度快 | [deepseek.com](https://deepseek.com) | `https://api.deepseek.com` |
| **Nous Portal**（官方默认）| 内置免配置，推荐入门使用 | [portal.nousresearch.com](https://portal.nousresearch.com) | 内置，无需填写 |
| **OpenRouter** | 200+ 模型，灵活切换 | [openrouter.ai](https://openrouter.ai) | `https://openrouter.ai/api/v1` |
| **OpenAI** | GPT-4o / o3 系列 | [openai.com](https://openai.com) | `https://api.openai.com/v1` |
| **Kimi / Moonshot** | 长上下文支持好 | [kimi.moonshot.cn](https://kimi.moonshot.cn) | `https://api.moonshot.cn/v1` |
| **MiniMax** | 中文能力优秀 | [minimax.com](https://minimax.com) | `https://api.minimax.chat/v1` |
| **Hugging Face** | 开源模型托管 | [huggingface.co](https://huggingface.co) | `https://api-inference.huggingface.co` |
| 自定义端点 | 任意兼容 OpenAI API 的服务 | — | 用户自行填写 |

**API 密钥配置**：

选择提供商后，Hermes 会引导输入 API Key。密钥存储在 `%LOCALAPPDATA%\hermes\.env` 文件中：

```
# .env 示例
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

也可直接编辑该文件手动添加。

---

### 2.2 配置工具（Toolsets）

```bash
hermes tools
```

交互式界面，按空格勾选/取消工具集，回车确认。常用工具集：

| 工具集 | 功能 |
|--------|------|
| `hermes-cli`（默认）| CLI 核心工具：文件、终端、搜索、编辑 |
| `web` | 网页搜索与内容提取 |
| `browser` | 自动化网页浏览（Playwright） |
| `vision` | 图像识别与分析 |
| `image_gen` | AI 图像生成 |
| `terminal` | 远程/容器终端后端 |
| `email` | 邮件收发 |
| `github` | GitHub Issue / PR / 代码管理 |
| `cronjob` | 定时任务调度 |

---

### 2.3 配置设置

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
hermes config set agent.disabled_toolsets=[\"browser\"]
```

**常用配置参数速查**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `agent.max_turns` | 60 | 单次对话最大工具调用轮次 |
| `agent.reasoning_effort` | medium | 推理深度：low / medium / high |
| `agent.verbose` | false | 是否输出详细调试信息 |
| `agent.image_input_mode` | auto | 图像输入模式：auto / disable |
| `agent.gateway_timeout` | 1800 | 网关超时（秒） |

---

### 2.4 完整设置向导

适合首次使用的交互式向导，一站式完成提供商选择、API Key 输入、工具集配置：

```bash
hermes setup
```

---

### 2.5 Windows 特有的配置注意事项

#### Git Bash 中使用 `hermes` 命令

PowerShell 安装器会将 Hermes 添加到 PATH。如果在 Git Bash 中找不到 `hermes` 命令，可手动添加：

```bash
# 在 ~/.bashrc 或 ~/.bash_profile 中添加
export PATH="$PATH:/c/Users/$USERNAME/AppData/Local/hermes/hermes-agent/venv/Scripts"

# 或直接用完整路径
/c/Users/$USERNAME/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes
```

#### 切换模型提供商时的网络提示

首次使用某个提供商时，`hermes model` 会尝试从网络拉取模型列表。如果你的网络需要代理，请确保 PowerShell / Git Bash 中的代理环境变量已设置（参见 1.5 节）。

#### 使用多个命令行的建议

- **日常使用**：推荐在 Git Bash 中运行 Hermes，体验最完整（支持 TUI、彩色输出、多行编辑）
- **配置修改**：PowerShell / CMD / Git Bash 均可，效果一致
- **更新**：建议在最初安装的同一种 shell 中执行 `hermes update`
