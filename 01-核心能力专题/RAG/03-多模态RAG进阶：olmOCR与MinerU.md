# Part 3. 多模态 RAG 系统进阶：olmOCR 与 MinerU 工具深度使用

> 本文是 笃行智元 AI 大模型技术社区「RAG 检索增强生成」系列的第 3 篇，深入介绍两款 PDF → Markdown 核心工具：Allen AI 的 **olmOCR**（VLM 型 OCR，SOTA 级精度）和阿里 OpenDataLab 的 **MinerU**（一站式文档解析管线）。
>
> 前置阅读：[Part 1. RAG 技术体系全景](./Part1-RAG技术体系全景.md) | [Part 2. 从零到一快速搭建多模态 RAG 引擎](./Part2-从零到一快速搭建多模态RAG引擎.md)

---

## 一、PDF → Markdown：多模态 RAG 的关键入口

### 1.1 为什么 PDF 转 Markdown 如此重要

在多模态 RAG 系统中，**PDF → Markdown（MD）是整条链路最关键的入口**。原因在于：

- PDF 是"版面/坐标"导向的格式——元素通过坐标定位，没有语义层级
- 检索需要的是**可切块、可对齐语义与结构**的文本
- 把 PDF 线性化为 Markdown 后，标题/段落/列表/表格/公式等要素被清晰暴露
- 便于后续用 `MarkdownHeaderTextSplitter` 做细粒度切分
- 可与图片、表格等"资产轨"对齐做多模态索引（文本向量 + 关键词 BM25 + 图像向量）
- 提升检索召回率与答案可解释性

### 1.2 两条主流技术路径

| 方案 | 开发者 | 核心思路 | 参数规模 | 许可证 |
|------|--------|----------|----------|--------|
| **olmOCR** | Allen AI (AI2) | VLM 微调实现"看懂图片→写出 Markdown" | 7B（基于 Qwen2.5-VL） | Apache 2.0 |
| **MinerU** | 阿里 OpenDataLab | 传统 OCR + 版面分析管线 | 轻量（CPU 可用） | AGPL-3.0 |

两者的本质区别：olmOCR 用一个微调过的视觉语言模型**端到端**完成识别+结构化，而 MinerU 用**多阶段管线**（检测→OCR→版面分析→重建）分步完成。

---

## 二、olmOCR：VLM 型 PDF 线性化工具

### 2.1 项目简介

**olmOCR** 是 Allen Institute for AI (AI2) 在 2024 年开源的 PDF 线性化工具包。核心能力：

- 将 PDF/PNG/JPEG 等基于图像的文档转成**干净的 Markdown/纯文本**
- 保留**自然阅读顺序**，对公式（LaTeX）、表格（Markdown Table）、手写体、多栏版式做专项优化
- 自动去除页眉/页脚
- 面向**大规模批处理**提供高效推理与集群/云端处理能力
- 支持 vLLM / SGLang 等主流推理引擎

olmOCR 的本质是一个经过特定功能微调的多模态大模型——基于 Qwen2.5-VL-7B-Instruct，使用约 25 万页标注数据（`olmOCR-mix-0225`）进行微调，使其具备"看到 PDF 页面图片 → 输出结构化 Markdown"的能力。

![olmOCR 系统概览](https://www.datocms-assets.com/64837/1761144967-ai2-olmocr-social-graphic-development-v1-3.png)

> ▲ olmOCR 系统架构：基于视觉语言模型（VLM），单次前向即可将 PDF 页转为结构化 Markdown

- **项目地址**：https://github.com/allenai/olmocr
- **模型权重**：https://huggingface.co/allenai/olmOCR-7B-0825-FP8（FP8 量化版）
- **在线测试**：https://olmocr.allenai.org/
- **微调数据集**：https://huggingface.co/datasets/allenai/olmOCR-mix-0225

### 2.2 Benchmark 表现

olmOCR 在 olmOCR-Bench 基准测试中表现突出。该基准覆盖 1,400+ 份 PDF 文档、7,000+ 测试用例，涵盖学术论文、历史扫描件、法律文档、手册等多种类型。

![olmOCR Benchmark](https://www.unsiloed.ai/olmocr_overall_performance.png)

> ▲ olmOCR-Bench 综合评测：olmOCR 2（7B 参数）在自然阅读顺序、复杂表格、公式识别等多个维度上达到 SOTA

关键发现：
- olmOCR 在"自然阅读顺序保持"上远超传统 OCR 流水线
- 表格和公式的 Markdown 还原质量显著优于 PaddleOCR + Unstructured 组合
- 但在**纯字符级极致精度**和**低算力/CPU 部署**场景，传统 OCR 仍有不可替代的优势

### 2.3 环境部署

**硬件要求：**

| 组件 | 要求 |
|------|------|
| GPU | NVIDIA GPU，显存 ≥ 15 GB（RTX 4090 / L40S / A100 / H100） |
| 磁盘 | 约 30 GB（模型权重 + 依赖） |
| 操作系统 | **仅支持 Linux** |

> ⚠️ olmOCR 目前只支持 Linux 部署。Windows 用户可通过 WSL2 或 Docker 运行。

**Step 1：安装系统依赖（PDF 渲染/字体）**

```bash
sudo apt-get update
sudo apt-get install -y poppler-utils ttf-mscorefonts-installer msttcorefonts \
  fonts-crosextra-caladea fonts-crosextra-carlito gsfonts lcdf-typetools
```

**Step 2：创建虚拟环境**

```bash
conda create -n olmocr python=3.11 -y
conda activate olmocr
```

**Step 3：安装 olmOCR（GPU 推理）**

```bash
# GPU 推理（推荐）
pip install "olmocr[gpu]" --extra-index-url https://download.pytorch.org/whl/cu128

# 可选：FlashInfer 加速（CUDA 12.8 + torch 2.7 对应版本）
# pip install https://download.pytorch.org/whl/cu128/flashinfer/flashinfer_python-0.2.5%2Bcu128torch2.7-cp38-abi3-linux_x86_64.whl
```

> 注意事项：
> - CPU 只能跑 bench 评测脚本，**真正的 OCR/VLM 推理必须用 GPU**
> - 此命令会自动安装 vLLM 作为推理引擎
> - 如果当前环境已有 vLLM，直接用 `pip install "olmocr[gpu]"` 即可

安装后验证：

```bash
pip show olmocr
pip show vllm
```

**Step 4：下载模型权重**

推荐通过 ModelScope（国内更快）：

```bash
pip install modelscope
modelscope download --model allenai/olmOCR-7B-0825-FP8 --local_dir ./olmOCR-7B-0825-FP8
```

也可从 HuggingFace 直接下载：

```bash
pip install huggingface_hub
huggingface-cli download allenai/olmOCR-7B-0825-FP8 --local-dir ./olmOCR-7B-0825-FP8
```

### 2.4 调用方式一：OpenAI 兼容 API（最灵活）

olmOCR 模型本质是微调过的 Qwen2.5-VL，可通过 vLLM 以 OpenAI 兼容协议提供服务。

**启动 vLLM 推理服务：**

```bash
vllm serve ./olmOCR-7B-0825-FP8 \
  --served-model-name olmocr \
  --max-model-len 16384
```

**Python 客户端调用（Jupyter 可用）：**

```python
import os, base64, requests
from pdf2image import convert_from_path
from PIL import Image

VLLM_ENDPOINT = "http://localhost:8000/v1/chat/completions"
MODEL_NAME    = "olmocr"
PDF_PATH      = "document.pdf"
OUT_MD        = "out.md"

# Step 1: PDF → 图片（逐页渲染）
pages = convert_from_path(PDF_PATH, dpi=200)
images = []
for i, img in enumerate(pages, start=1):
    # 限制最长边不超过 1600px，控制显存
    max_side = max(img.size)
    if max_side > 1600:
        scale = 1600 / max_side
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    buf_path = f"__page_{i}.png"
    img.save(buf_path, "PNG")
    images.append(buf_path)

# Step 2: 每页调用 vLLM 进行 OCR
def ocr_page(img_path):
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": MODEL_NAME,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Convert this page into clean Markdown in natural reading order. "
                        "Remove headers/footers. Keep tables as Markdown tables. "
                        "Represent math as LaTeX ($...$ or $$...$$). "
                        "Do not invent missing content."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "auto"},
                },
            ],
        }],
        "temperature": 0.2,
        "max_tokens": 4096,
    }

    r = requests.post(VLLM_ENDPOINT, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# Step 3: 逐页解析并合并
md_pages = []
for p in images:
    try:
        md_pages.append(ocr_page(p))
    except Exception as e:
        md_pages.append(f"\n<!-- ERROR on {p}: {e} -->\n")

full_md = "\n\n\\pagebreak\n\n".join(md_pages)
with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write(full_md)

print(f"Done. Saved Markdown to: {OUT_MD}")
```

**代码要点说明：**

| 步骤 | 说明 |
|------|------|
| `pdf2image.convert_from_path` | 将 PDF 逐页渲染为 PNG 图片（DPI 200~300） |
| `base64` 编码 | 将图片以 data URI 格式嵌入请求，无需额外文件服务 |
| Prompt 设计 | 明确要求"自然阅读顺序 + Markdown表格 + LaTeX公式 + 去除页眉页脚" |
| `temperature=0.2` | 低温度确保输出稳定一致 |
| `max_tokens=4096` | 足够覆盖单页复杂内容 |

> ⚠️ 注意：olmOCR 微调时未带入 VLM 图片语义理解的训练数据，因此 olmOCR 是**纯粹的 OCR 模型**，不具备"描述图片内容"等 VLM 能力。

### 2.5 调用方式二：官方 Pipeline 脚本（最便捷）

olmOCR 提供了 `olmocr.pipeline` 一行命令完成 PDF → Markdown 转换，内置自动旋转检测、页眉页脚清理、重试策略、阅读顺序增强等工程优化。

```bash
# vLLM 已启动时
python -m olmocr.pipeline ./workspace \
  --server http://localhost:8000 \
  --markdown \
  --pdfs ./document.pdf

# vLLM 未启动时（自动启动本地模型）
python -m olmocr.pipeline ./workspace \
  --markdown \
  --pdfs ./document.pdf
```

输出结构：

```
workspace/
├── markdown/          # 转换后的 Markdown 文件
├── results/           # 模型的原始 JSON 输出（含元数据）
└── images/            # 提取的图片（可选）
```

也支持处理单张图片：

```bash
python -m olmocr.pipeline ./workspace_image \
  --server http://localhost:8000 \
  --markdown \
  --pdfs ./scan.png
```

### 2.6 Pipeline 完整参数表

| 类别 | 参数 | 说明 | 典型值 |
|------|------|------|--------|
| **位置参数** | `workspace` | 工作区路径（本地或 S3） | `./ws` |
| **输入** | `--pdfs` | PDF 列表，支持通配符或清单文件 | `./*.pdf` 或 `list.txt` |
| **模型** | `--model` | 模型路径或 HF 仓库名 | `allenai/olmOCR-7B-0825-FP8` |
| **批大小** | `--pages_per_group` | 每组处理页数（控制显存） | `4`、`8` |
| **重试** | `--max_page_retries` | 单页最大重试次数 | `2`、`3` |
| **容错** | `--max_page_error_rate` | 允许的失败页比例 | `0.004`（≈1/250） |
| **并行** | `--workers` | 并发 worker 数 | `1`、`2`、`4` |
| **输出** | `--markdown` | 产出 Markdown 文件 | 开关 |
| **渲染** | `--target_longest_image_dim` | PDF 渲染图片最长边像素 | `1400`、`1600`、`1800` |
| **显存** | `--gpu-memory-utilization` | vLLM 可用显存比例 | `0.85`、`0.6` |
| **上下文** | `--max_model_len` | 最大上下文长度（tokens） | `16384` |
| **多 GPU** | `--tensor-parallel-size` | 张量并行份数 | `1`、`2` |
| **远程推理** | `--server` | 外部 vLLM 服务地址 | `http://host:8000` |
| **质量过滤** | `--apply_filter` | 过滤非英文/表单/SEO 垃圾 | 开关 |

### 2.7 进阶：元素感知 OCR（Image-Aware OCR）

在实际的多模态 RAG 流程中，我们常常需要先做**版面分析**（用 Unstructured 等工具拆分文字/表格/图片），然后**对拆分出的图片单独调用 olmOCR** 进行识别。这被称为"元素感知 OCR"。

**完整流程：**

```python
import os, re, io, base64, requests
from PIL import Image
from unstructured.partition.pdf import partition_pdf
import fitz

# === 第一阶段：版面分析（Unstructured + PaddleOCR） ===
pdf_path = "document.pdf"
output_dir = "pdf_images"
os.makedirs(output_dir, exist_ok=True)

elements = partition_pdf(
    filename=pdf_path,
    infer_table_structure=True,
    strategy="hi_res",
    ocr_languages="chi_sim+eng",
    ocr_engine="paddleocr"
)

# 提取图片
doc = fitz.open(pdf_path)
image_map = {}
for page_num, page in enumerate(doc, start=1):
    image_map[page_num] = []
    for img_index, img in enumerate(page.get_images(full=True), start=1):
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        img_path = os.path.join(output_dir, f"page{page_num}_img{img_index}.png")
        pix.save(img_path) if pix.n < 5 else fitz.Pixmap(fitz.csRGB, pix).save(img_path)
        image_map[page_num].append(img_path)

# === 第二阶段：对图片调用 olmOCR 进行深度识别 ===
def call_olmocr_image(img_path, vllm_url="http://localhost:8000/v1/chat/completions"):
    """用 olmOCR 解析单张图片，返回 alt/caption/content_md"""
    with Image.open(img_path) as im:
        bio = io.BytesIO()
        im.save(bio, format="PNG")
        img_bytes = bio.getvalue()

    prompt = (
        "You are an OCR & document understanding assistant.\n"
        "Analyze this image region and produce:\n"
        "1) ALT: a very short alt text (<=12 words).\n"
        "2) CAPTION: a 1-2 sentence concise caption.\n"
        "3) CONTENT_MD: if the image contains a table, output a clean Markdown table; "
        "if it contains a formula, output LaTeX ($...$ or $$...$$); "
        "otherwise provide 3-6 bullet points summarizing key content.\n"
        "Return strictly in the following format:\n"
        "ALT: <short alt>\nCAPTION: <caption>\nCONTENT_MD:\n<markdown>"
    )

    payload = {
        "model": "olmocr",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64.b64encode(img_bytes).decode()}",
                    "detail": "auto"
                }}
            ]
        }],
        "temperature": 0.2,
        "max_tokens": 2048,
    }

    r = requests.post(vllm_url, json=payload, timeout=180)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# === 第三阶段：组装 Markdown ===
md_lines = []
for el in elements:
    cat = str(el.category)
    text = el.text or ""
    page_num = el.metadata.page_number or 1

    if cat == "Title":
        md_lines.append(f"# {text}\n\n")
    elif cat in ("Header", "Subheader"):
        md_lines.append(f"## {text}\n\n")
    elif cat == "Image":
        for img_path in image_map.get(page_num, []):
            result = call_olmocr_image(img_path)
            md_lines.append(f"<!-- olmOCR: {result} -->\n")
            md_lines.append(f"![Image](./{img_path})\n\n")
    else:
        md_lines.append(text + "\n\n")

# 写入最终 Markdown
with open("output_enhanced.md", "w", encoding="utf-8") as f:
    f.write("".join(md_lines))
```

这样就能在版面分析的基础上，对每张图片进行深度识别，产出更丰富的 Markdown 知识库。

---

## 三、MinerU：一站式 PDF → Markdown 工具

### 3.1 项目简介

**MinerU** 由阿里巴巴达摩院与 OpenDataLab 社区联合开源。与 olmOCR 的 VLM 路线不同，MinerU 采用传统 OCR + 版面分析的多阶段管线，优势在于：

- 一站式 PDF → Markdown / JSON 转换
- 对学术论文中的公式、表格、图片引用保留度高
- CPU 可用（GPU 加速更好）
- CLI 和 Python API 双模式

![MinerU 文档解析管线](https://neurohive.io/wp-content/uploads/2024/09/mineru-pipeline-for-automatic-document-extraction.png)

> ▲ MinerU 文档解析 Pipeline：PDF 输入 → 布局分析 → OCR 识别 → 结构重建 → Markdown/JSON 输出

- **项目地址**：https://github.com/opendatalab/MinerU
- **许可证**：AGPL-3.0（闭源商用需注意）

### 3.2 快速安装

```bash
pip install mineru
```

### 3.3 基本使用

**Python API：**

```python
from mineru import MinerU

mineru = MinerU()

# PDF → Markdown
result = mineru.parse("document.pdf", output_format="markdown")

# PDF → JSON（含版面结构信息，便于下游处理）
result = mineru.parse("document.pdf", output_format="json")
```

**CLI 方式：**

```bash
mineru parse document.pdf -o output_dir/
```

### 3.4 MinerU 与 olmOCR 适用场景

| 场景 | 推荐工具 | 理由 |
|------|----------|------|
| 批量处理大量 PDF，追求阅读顺序保真 | **olmOCR** | VLM 端到端，质量最高 |
| 快速集成到 Python 项目，CPU 也能跑 | **MinerU** | 一行 `pip install`，轻量 |
| 学术论文（公式+表格密集型） | 两者均可 | olmOCR 阅读顺序更好，MinerU 公式精度更高 |
| Windows 环境 | **MinerU** | olmOCR 仅支持 Linux |
| 闭源商用项目 | **olmOCR** | Apache 2.0 许可，MinerU 为 AGPL-3.0 |
| 需要版面 JSON 元数据 | **MinerU** | 原生支持 JSON 输出含坐标信息 |

---

## 四、实战建议

```
你的场景是批量处理大规模 PDF，追求最高阅读顺序和格式保真？
  → 选择 olmOCR（VLM 方案，SOTA 级精度）

你的场景是快速集成、需要 CPU 运行或 Windows 环境？
  → 选择 MinerU（管线方案，开箱即用）

最优方案：双轨合并
  → olmOCR 做"文本轨"线性化（高质量 Markdown）
  → MinerU 做"结构轨"提取（JSON 版面坐标信息）
  → 双轨合并，构建最强多模态 RAG 知识库
```
