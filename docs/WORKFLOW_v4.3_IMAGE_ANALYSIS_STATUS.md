# v4.3 图片自动识别模块｜实现与验收状态

## 目标

降低从截图到页面 JSON 的重复劳动，优先自动提取可机器识别的文字和几何证据；不将 OCR 或轮廓检测误称为完整语义理解。

## 当前实现

| 子模块 | 实现 | 输出 | 边界 |
|---|---|---|---|
| OCR 适配 | RapidOCR（优先）/ Tesseract（回退） | 文本、像素 bbox、置信度 | 依赖安装与语言模型；低置信度需复核 |
| 坐标归一化 | 像素坐标转 0–1 bbox，裁剪越界框 | `bbox_norm` | 仅文字框位置，不理解布局层级 |
| 区域候选 | 可选 OpenCV 矩形轮廓 | 候选框、颜色提示、低置信度 | 不推断卡片、表格或业务含义 |
| 可视化 | 原图叠加 OCR 框与置信度 | `overlay_*.png` | 只用于定位识别结果 |
| 草稿生成 | 生成符合 page_spec schema 的文字元素 | `draft_spec.json` | 字号、对齐、背景为启发式估计 |
| 草稿构建 | 原生文本框写入 PPTX；按图片比例设置画布 | `draft.pptx`、QA、预览 | 不包含自动识别出的箭头/图标语义/复杂表格 |

## CLI

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-image-analysis.txt
python run_workflow.py analyze-image --input "D:\PPT图片\批次" --output-dir outputs\batch01 --build-draft
```

## 验收结果（开发环境）

- 24 项基础与回归测试全部通过（v4.2 原测试 + v4.3 纯函数测试）。
- 基础 `smoke_test.py` 通过。
- `engine=none` 路径完成 CLI、JSON Schema、PPTX 构建、QA 和 LibreOffice 预览检查。
- Tesseract 英文样例实测识别 2 段文字，OpenCV 实测提出 1 个矩形候选。
- 以上是工程功能测试，不代表中文复杂 PPT 截图的识别准确率，也不代表端到端复刻准确率。

## 未实现 / 后续版本

1. 图标语义识别与 500 SVG 库自动匹配。
2. 箭头/连线端点、方向和跨元素关系识别。
3. 表格、图表与多栏布局的结构化解析。
4. OCR 与视觉语言模型联合校验、低置信度局部重识别。
5. 与参考图进行语义级自动差异解释。

任何自动识别草稿均标记 `REVIEW_REQUIRED`，未人工确认前不得作为最终交付。
