# PPT 图片高保真可编辑重建工作流 v4.2｜三模块技术设计（规划稿，非已实现功能）

## 0. 设计结论

在 v4.1 `run_workflow.py → core/ppt_builder.py → core/quality.py` 基础上增量建设，不推翻现有生成器。唯一数据来源是可版本化的 `page_spec.json`；组件模板负责扩展为原生 PPT 对象；参考图 QA 检出问题；修复器仅修改 JSON 补丁并重新生成。避免对生成后的 PPTX 直接做不可追溯修改。

**交付边界**：此文档是设计规范，不代表组件模板、参考图比较和自动修复已经编程实现。

## 1. 统一数据契约（先于三个模块）

为现有 `elements[]` 扩展或新增：

- `id`：同一页内唯一且固定；可存至 PowerPoint shape.name，便于从 JSON/PPTX 双向定位。
- `bbox_norm`：标准化 `[x,y,width,height]`。严格复刻不能默默重排。
- `type`：原生元素类型。组合对象允许 `component` 字段，并在构建前展开成若干原生元素。
- `style_ref`：引用 Design Tokens；元素层覆盖需显式记录。
- `locked`：该元素不允许自动修复。
- `confidence`：来源识别置信度，仅用于分流检查，不能代替验证。
- `source_ref`：源图片与对应参考框，方便 QA 追踪。
- `relationships`：连接线用 `from_id/to_id + anchors` 指定节点，而不是只有孤立坐标；具体端点由布局器确定。
- `qa_exceptions`：记录经人工批准的偏差及理由。

要求：图片内容不确定时标记 `manual_required`；不得以自动修复名义猜测文字、数据、箭头方向。

## 2. 模块一：页面组件模板库（P1）

### 2.1 分层

1. 原生基础对象：text / shape / connector / icon / image / table / chart（v4.1 已有）。
2. 组合组件：title_block、icon_card、flow_node、horizontal_flow、table_block、image_text、timeline、comparison_matrix。v4.2 首批不超过 8 种。
3. 页面结构：严格复刻路由不强制使用整页模板。美化/重设计路由才提供 split、grid、process 等布局建议。

### 2.2 统一组件接口

`render(component_spec, tokens) -> list[element_spec]`，输出仍必须是现有 Builder 可以接受的原生 `elements[]`。先做纯数据展开，不引入第二套渲染引擎。

示例：

```json
{
  "component":"horizontal_flow",
  "id":"flow_01",
  "bbox_norm":[0.08,0.30,0.84,0.32],
  "nodes":[
    {"id":"n1","title":"订单输入"},
    {"id":"n2","title":"生产调度"},
    {"id":"n3","title":"执行反馈"}
  ],
  "style_ref":"academic_blue"
}
```

严格复刻必须允许在 `nodes[]` 内用显式 `bbox_norm` 覆盖自动布局。生成的元素 ID 如 `flow_01/n1/title` 保持稳定。连线优先与 `node_id + anchor` 绑定，切忌盲目计算固定端点。

### 2.3 组件测试

参数变化回归：中文长标题 / 多行文字 / 1至6流程节点 / 左右箭头 / 不同宽高比例 / 空白图标；验证原生可编辑、稳定顺序、不越界、文字不低于12pt。组件通过测试后才纳入可调用清单。

## 3. 模块二：参考图与渲染预览比较（P1）

### 3.1 输入输出

输入：`reference.png + page_spec.json + rendered_slide.png`。
输出：`visual_qa.json + diff_overlay.png + per-element diagnostics`；每条问题包含 `page_id, element_id, issue_type, severity, measured_value, expected_value, suggestion, auto_fixable`。

### 3.2 检查层次

- **A. 结构 QA（硬门槛）**：原生对象数、文字内容、图表数据来源、箭头业务方向、页面尺寸、元素越界。能基于 JSON/PowerPoint 对象验证的先验证。
- **B. 几何 QA（可量化）**：依据 `source_ref` 或人工/视觉模型确认的参考 bbox，计算位置中心差、宽高差、框 IoU、相对对齐与间距；明确参考框不是来自完全准确的人工标注时，结果只能作线索。
- **C. 像素/边缘 QA（辅助）**：源图裁切/透视矫正、配准至同等画布、按区域生成 alpha overlay / 颜色差异 / edge diff。不能仅以全图 SSIM 判断是否通过，字体渲染器差异和图像重采样会产生伪差异。
- **D. 语义 QA（需模型/人工）**：图标含义、箭头关联关系、原图文字是否识别错误、照片主体是否完整。不可伪装成全自动确定性检测。

### 3.3 推荐初始阈值（须经真实数据校准，不是普适标准）

主元素 bbox IoU <0.90 或中心偏差 >1% 页面宽高时标记 `REVIEW`；任一结构性内容缺失直接 `P0`；字体字号 <12pt 为 `P0`；可读性异常是 `P1/P0` 人工判定。禁止把 IoU 达标视为语义正确。

### 3.4 渲染一致性

首选使用最终使用者的 PowerPoint 或等效环境进行终验；LibreOffice 渲染用于自动化初筛，不把 LibreOffice 字体换行差异误当成原生 PPT 逻辑错误。

## 4. 模块三：自动修复与返工（P2）

### 4.1 原则

修复对象是**源 page_spec.json**，不是生成后的 PPTX。每轮 `qa → propose_patch → validate_patch → rebuild → qa`；保留 `before.json / patch.json / after.json / QA_DIFF.json`，最多 2 轮自动修复，失败转人工，不允许无界自循环。

### 4.2 可自动修复白名单

- 轻微元素越界：在保留内容前提下微调 bbox。
- 文字框空间不足：优先增加高度/宽度与可用留白；不能自动将正文缩到12pt以下，也不能改写原文字。
- 元素间异常间距：仅在已指定网格或对齐关系时纠正。
- 连线端点漂移：仅当 `from_id/to_id`、箭头方向和锚点已确定时重算。
- 设计 Token 不统一：在严格复刻没有专门例外的情况下修正异常覆盖。

### 4.3 不可自动修复黑名单

原图文字不清、数据不完整、图标语义不确定、连线逻辑不明确、缺失素材、严格复刻下必须改变结构的调整。一律输出 `manual_required`。

### 4.4 回归与回滚

只有目标问题得到改善、未引入新的 P0/P1 且已锁定对象保持不变，才接受补丁。否则回滚到前一 JSON。任何修复不得暗改文本和数字。

## 5. 文件建议（增量建设）

```text
core/
  ppt_builder.py           # 既有；接受展开后的原生 elements
  quality.py               # 既有；机器 QA
  component_registry.py    # 新：注册/参数校验/组件展开
  geometry.py              # 新：节点锚点、对齐、间距、碰撞
  reference_compare.py     # 新：参考图配准、几何与视觉差异
  repair_engine.py         # 新：白名单补丁、回滚、再检查
components/
  title_block.py
  icon_card.py
  horizontal_flow.py
  ...
config/
  design_tokens.json
  qa_thresholds.json       # 初始阈值，可根据样本调优
  repair_policy.json       # 自动修复白名单
schemas/
  page_spec.schema.json    # 扩展稳定 ID、组件和关系
  qa_issue.schema.json
examples/
  01_title_card.json
  02_process.json
  03_table.json
  04_image_text.json
tests/
  test_components.py
  test_reference_compare.py
  test_repairs.py
  golden_cases/             # 包含至少8–12种典型页面与预期结果
```

## 6. 开发顺序与验收门槛

### M0 数据协议（必须先做）
- schema 校验、稳定元素 ID、JSON 中保留来源/设计锁、连接关系。
- 验收：修改一处 JSON 元素后，能在 PPT 中定位同一对象并可靠重新构建。

### M1 组件库（P1）
- 优先 title_block、icon_card、horizontal_flow、table_block，再按复用频率补其余。
- 验收：相同图形通过换数据/位置就可复用；内容和对象保持可编辑。

### M2 视觉对比（P1）
- 首版仅做同尺寸叠图、参考框几何差异和报告；复杂的自动分割和学习型相似度延后。
- 验收：在人为引入位置偏移、字体变化、漏节点、箭头反向的对照样本中，能区分可检测问题与必须人工复核的问题。

### M3 定向修复（P2）
- 首版只修越界、部分对齐、确定性连线端点漂移。文字溢出和语义问题保持人工核验。
- 验收：固定回归样本中，修复确实降低违规数量；不改变原文、不减字号至12pt以下、不引入新 P0/P1，失败能回滚。

## 7. 最重要的设计边界

- 简单基线：现有原生元素 + 页面 JSON 已能完成不少页面；不应为了复杂性而强制用模板。
- 标准组件优先解决代码复用，而不是逼近像素级完全一致。
- 参考图像素相似不等于可编辑性、内容准确性或连接逻辑正确。
- 自动修复绝不应成为对原图的擅自再设计。
- 首版测试用 8–12 张多类型真实页面，而不是只测自己绘制的演示页。
