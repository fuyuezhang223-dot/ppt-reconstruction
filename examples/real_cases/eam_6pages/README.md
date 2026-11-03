# EAM 真实六页案例（205—210）

本案例供 **真实截图重构复验及母版复用**，不是任意截图自动识别模型。使用统一 `pages.json` 配置和 `core/eam_course_template.py` 母版，建立四步流程、五步流程、双栏对比三类页面。

## 快速运行

在本 ZIP 解压后的工作流根目录执行：

```powershell
python -m pip install -r requirements.txt
python examples/real_cases/eam_6pages/build.py
python examples/real_cases/eam_6pages/audit_real_case.py
```

需有 LibreOffice (`soffice` 或 `libreoffice`) 才能自动渲染并执行完整 PDF 文字审计。缺少此环境仍可生成 PPTX，需用 PowerPoint/WPS 导出预览做目视复核。

## 素材路由（强制）

| 元素 | 生成方式 | 是否从截图裁剪 |
|---|---|---|
| 流程、步骤、表格、文本、卡片、箭头、标题背景、编号 | 原生 PowerPoint | 否 |
| 标准图标（含步骤、栏目、徽章、摘要） | `assets/icon_library/SVG`，通过 `icon_id` 调用；本程序渲染为独立高清 PNG 图标对象 | **禁止** |
| 工人、设备与工业场景照片 | 独立图片 | 可以，需不夹带文字和卡片边框 |
| 复杂工业线稿背景 | 独立装饰图片 | 可以 |

本案例已移除旧 `assets/icons/` 截图裁剪图标目录和旧 `prepare_assets.py`。如果要重新从六张参考图准备*照片*，运行 `prepare_photo_assets.py`，不会产生标准图标裁剪。课程徽章也改用本地图标库调用。

`pages.json` 每页配置 `step_icons/pre_icons/post_icons`，填写图标 ID。`core/icon_library.py` 从 500 个 SVG 中检索并引用。由于当前库主要是线性图标，与参考截图中的实心/渐变图标存在风格差异；**这不属于像素级一致复刻**。

## 输出

- `outputs/EAM_6pages_editable.pptx`：重构的 PPTX；
- `outputs/preview/`：渲染预览、缩略图；
- `outputs/REAL_CASE_AUDIT.json`：字体与文字完整性、对象数量、图标来源等审计；
- `outputs/REFERENCE_VS_EDITABLE.png`：参考图/结果并排复核；
- `outputs/EAM_6pages_editable.inventory.json`：对象 ID、来源、原生可编辑性清单。

原生对象占比只按**对象数量**计算，不能称为“像素可编辑率”。带 `kind=icon_png` 的图标对象可以单独移动、缩放、替换，但内部 SVG 路径不可用原生形状逐点修改。

## 更换内容

更换标题、步骤、说明、总结、页码：修改 `pages.json`，无需重写绘图代码；更换照片：替换 `assets/worker_<页码>.png`。新布局族需先定义和验证新的组件，不能假装当前模板自动理解任意版式。
