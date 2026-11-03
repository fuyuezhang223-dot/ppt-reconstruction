# PPT_ICON_LIBRARY_500_v1.0

面向中文 PPT、工业工程、制造业、企业管理与科研教学的本地专业 SVG 图标库。

## 概览

- 总数：500 个唯一 SVG
- 风格：Tabler Icons outline，24×24 viewBox，默认 stroke-width 2
- 优先级：P1 200 / P2 200 / P3 100
- 来源：[https://github.com/tabler/tabler-icons](https://github.com/tabler/tabler-icons)
- Source family：Tabler Icons
- Source repository：tabler/tabler-icons
- Source commit：`5a0fe38e97784d94279ce4eb1bf85f9a91bf027e`
- License：MIT
- Retrieval date：2026-08-27

## 分类数量

- 01_制造与工厂: 50
- 02_设备与维护: 55
- 03_质量管理: 35
- 04_安全与风险: 35
- 05_物流与仓储: 55
- 06_数据与数字化: 55
- 07_人员与组织: 40
- 08_管理计划与流程: 40
- 09_成本财务与经营: 30
- 10_效率改善与精益: 30
- 11_能源环保与可持续: 30
- 12_科研教育与技术: 45

## 使用

```powershell
python TOOLS/search_icons.py "设备维护"
python TOOLS/qa_icons.py
python TOOLS/build_contact_sheets.py
```

搜索工具仅使用 Python 标准库，不联网。QA 与预览渲染优先使用 Node.js `sharp`，也支持环境变量 `NODE_PATH` 指向已安装的 sharp。

## 索引

- `INDEX/icon_manifest.json` / `.csv`：完整元数据、SHA-256、优先级与 10 维筛选评分。
- `INDEX/semantic_index_zh.json`：中文语义到 icon ID 的反向索引。
- `INDEX/aliases_zh.json`：中文自然语言别名归一化。
- `INDEX/priority_index.json`：P1/P2/P3 分组。

## 筛选原则

图标按 PPT 通用性、工业工程、制造业、企业管理、科研教学、16–32px 辨识度、混淆风险、小众程度、正式汇报适配度和近似重复风险十项审查。排除品牌 Logo、娱乐、宗教、地域化和过度生活化图标。三层去重覆盖源文件名、SVG 内容 SHA-256 与视觉/语义家族人工审查。

## 授权

所有 SVG 均来自 Tabler Icons 官方仓库，按 MIT License 使用。完整许可见 `LICENSES/TABLER_LICENSE.txt`。
