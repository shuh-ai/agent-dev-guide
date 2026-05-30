# Hermes Agent MCP 扩展 AI 工具能力

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

连接远程或共享的 MCP 服务器：

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
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
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
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
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
- 连字符和点号自动转为下划线

### 4.3 工具过滤

通过 `hermes mcp configure NAME` 可以选择暴露哪些工具：

```bash
hermes mcp configure github
# 交互式开启/关闭特定工具
```

### 4.4 热重载

```bash
/reload-mcp
```

修改配置后无需重启 Hermes，立即生效。

### 4.5 将 Hermes 作为 MCP 服务

```bash
hermes mcp serve
```

其他 MCP 客户端可以连接此服务并使用 Hermes 的能力。

---

## 五、安全机制

### 5.1 环境变量过滤

Stdio 子进程默认只继承安全的系统变量（PATH、HOME、LANG 等），API Key 等敏感信息必须通过 `env` 显式声明。

### 5.2 凭据自动掩饰

工具调用失败的错误信息中，GitHub PAT、OpenAI Key、Bearer Token 等凭据自动屏蔽。

### 5.3 工具粒度控制

通过 `hermes mcp configure` 精细控制每个服务器的工具可见性。

---

## 六、常见示例

**时间服务器：**

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

**文件系统服务器：**

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"]
```

**GitHub 服务器：**

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxxxxxxxxxxxxxx"
```
