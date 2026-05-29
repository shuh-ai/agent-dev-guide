# Hermes Agent 持久记忆

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

切换命令：

```bash
hermes memory setup          # 交互式配置
hermes memory off            # 关闭记忆
```

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

每个 Profile 拥有独立的记忆空间：

```bash
hermes profile create work     # 新建工作 Profile
hermes profile use work        # 切换到工作 Profile
```

工作 Profile 的记忆与默认 Profile 完全隔离，互不影响。
