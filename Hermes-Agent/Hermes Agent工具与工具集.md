# Hermes Agent 工具与工具集

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
| 浏览器 | `browser` | 自动操控浏览器——截图、点击、填表。适合交互式网页任务 |
| 终端与文件 | `terminal` | 运行 shell 命令，管理后台进程 |
| 终端与文件 | `file` | 读写文件、搜索内容、查找文件 |
| 终端与文件 | `code_execution` | 安全沙箱中运行 Python 代码 |
| 媒体 | `vision` | 分析图片内容。识别截图、图表、手绘草图 |
| 媒体 | `image_gen` | 文本描述生成图片。适合配图、封面、原型 |
| 媒体 | `video` | 视频分析与生成 |
| 媒体 | `tts` | 文本转语音。生成语音回复或配音 |
| 记忆 | `memory` | 跨会话读写持久化记忆。让 Agent 记住你的偏好 |
| 记忆 | `session_search` | 全文检索历史对话。快速找到之前讨论过的内容 |
| 记忆 | `skills` | 浏览和管理技能库 |
| 任务调度 | `delegation` | 派生子 Agent 并行处理多项独立任务 |
| 任务调度 | `cronjob` | 定时执行任务。日报、备份、监控等自动化 |
| 任务调度 | `todo` | 当前会话的任务看板。拆解大型任务、标记进度 |
| 交互 | `clarify` | 遇到不确定时主动向用户提问 |
| 交互 | `messaging` | 跨平台发送消息 |
| 安全 | `safe` | 最小化工具集。仅保留最安全的操作 |
| 调试 | `debugging` | 调试和内省工具。默认关闭 |
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
