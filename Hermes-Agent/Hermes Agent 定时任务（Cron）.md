# Hermes Agent 定时任务（Cron）

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

任务结果默认投递到当前会话。可以指定其他平台：

```bash
hermes cron create "every day 9am" \
  --prompt "生成日报" \
  --deliver "origin,all"          # 投递到当前会话 + 所有平台
```

```bash
hermes cron create "every day 9am" \
  --prompt "生成日报" \
  --deliver "telegram:-1001234567890:17585"  # 投递到指定 Telegram 频道
```

### 3.4 预加载技能

任务执行时可以加载指定技能：

```bash
hermes cron create "0 9 * * *" \
  --prompt "做代码审查" \
  --skills "code-review,github-pr-workflow"
```

### 3.5 指定模型

为定时任务指定专属模型和提供商：

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

脚本的 stdout 会作为上下文传入 Agent。如果只需脚本输出无需 LLM，使用 `--no-agent`：

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

不会影响原有的调度周期。

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
