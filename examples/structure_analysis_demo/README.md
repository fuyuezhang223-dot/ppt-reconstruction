# v4.4 结构识别演示样例

本目录是用于展示 v4.4 识别模块的**合成示例**，不是真实业务截图，也不是识别准确率基准。

## 文件

- `source.png`：合成的流程卡片、箭头、表格和图标标签示例。
- `overlay.png`：OCR 与结构候选叠加图。橙色为几何轮廓、蓝色为表格网格、紫色为箭头、青色为图标候选、绿色/红色为 OCR 置信度。
- `analysis.json`：识别结果、候选坐标、图标建议和方法边界。
- `draft_spec.json`：可继续人工修改的页面 JSON。
- `draft.pptx`：根据当前识别候选生成的第一版可编辑 PPT。
- `QA_REPORT.json`：PPTX 基础机器检查结果。

## 此示例识别到什么

- Tesseract 英文 OCR 提取 3 个文本框。
- 识别到 3 个卡片矩形、1 个流程箭头、1 个表格网格候选、1 个紧凑图标候选和 1 组重复卡片布局假设。
- `Factory` 邻近标签检索到 `MFG-001`（工厂）和 `MFG-002`（制造工厂）两个 SVG 候选。它是标签语义检索，不是图标像素级分类。
- 表格 OCR 仅填入 1 个单元格，因此没有擅自构建完整原生表格；请人工核对后补齐。
- `draft.pptx` 通过基础 QA（P0=0、P1=0），但仍需人工核对文字完整性、图标语义、箭头连接关系和视觉相似度。

可用以下命令重新运行（需安装 `requirements-image-analysis.txt` 并安装 Tesseract）：

```powershell
python run_workflow.py analyze-image --input examples/structure_analysis_demo/source.png --output-dir outputs/structure_demo --engine tesseract --lang eng --build-draft
```
