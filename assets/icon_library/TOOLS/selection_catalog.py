"""Hand-curated Tabler outline icon catalog for PPT_ICON_LIBRARY_500_v1.0.

Each row is: source_icon_name | concise Chinese display name | Chinese search terms.
Rows are ordered from core/general to extended/specialized within each category.
"""

CATEGORIES = [
    ("01_制造与工厂", "MFG", 50, 20),
    ("02_设备与维护", "EQP", 55, 22),
    ("03_质量管理", "QUA", 35, 14),
    ("04_安全与风险", "SAF", 35, 14),
    ("05_物流与仓储", "LOG", 55, 22),
    ("06_数据与数字化", "DAT", 55, 22),
    ("07_人员与组织", "ORG", 40, 16),
    ("08_管理计划与流程", "MGT", 40, 16),
    ("09_成本财务与经营", "FIN", 30, 12),
    ("10_效率改善与精益", "LEA", 30, 12),
    ("11_能源环保与可持续", "ENV", 30, 12),
    ("12_科研教育与技术", "RND", 45, 18),
]


def _rows(text):
    rows = []
    for raw in text.strip().splitlines():
        source, zh, keywords = [part.strip() for part in raw.split("|", 2)]
        rows.append((source, zh, [x.strip() for x in keywords.split(",") if x.strip()]))
    return rows


CATALOG = {
"01_制造与工厂": _rows(r"""
building-factory|工厂|工厂,制造,工业,生产基地
building-factory-2|制造工厂|制造,车间,厂房,工业
assembly|装配|装配,组装,工序,生产
automation|工业自动化|自动化,控制,制造,工业
robot|机械臂与机器人|机械臂,机器人,自动化,装配
car-crane|工业机械设备|机械设备,自动化,智能制造,设备
settings-automation|自动化设置|自动化,设置,控制,工艺
engine|工业发动机|发动机,动力,设备,机器
circuit-ammeter|电机电流|电机,马达,驱动,设备
manual-gearbox|变速机构|齿轮箱,传动,机械,设备
settings|工艺设置|设置,工艺,参数,配置
settings-cog|制造配置|配置,制造,参数,控制
tools|生产工具|工具,生产,制造,工位
blade|加工刀具|工具,加工,工程,制造
hammer-drill|钻孔加工|钻孔,加工,机床,工具
hammer|锤击加工|锤子,加工,装配,工具
wave-saw-tool|锯切|切削,锯切,加工,工具
slice|切割|切割,切削,加工,工艺
scissors|剪切|剪切,加工,工具,工艺
ruler-measure|测量工装|测量,工装,尺寸,制造
components|组件|组件,部件,零件,装配
lego|零件模块|零件,模块,组件,装配
box-model|产品模型|产品,模型,设计,制造
box-model-2|包装成品|包装,成品,产品,封装
package|产品包装|包装,产品,成品,物料
packages|批量产品|批量,产品,包装,产出
box|物料箱|物料,箱体,原材料,半成品
stack|原材料堆叠|原材料,堆叠,物料,库存
layers-intersect|工艺叠层|工艺,层叠,加工,复合
geometry|工程几何|工程,几何,设计,尺寸
ruler-2|工程尺寸|尺寸,工程,设计,测量
automatic-gearbox|数控制造|数控,CNC,加工,制造
circuit-motor|电机控制|电机,控制,电路,自动化
propeller|旋转部件|旋转,叶轮,部件,机械
car-turbine|涡轮设备|涡轮,旋转,设备,动力
crane|工业起重|起重,吊装,工程,制造
barrier-block|工位隔离|工位,隔离,车间,布局
layout-grid|车间布局|布局,车间,工位,网格
layout-board|生产看板|生产看板,工位,车间,任务
hierarchy|生产层级|层级,工序,生产线,结构
binary-tree|工艺路线|工艺,路线,分支,流程
git-branch|工序分支|工序,分支,流程,生产
arrows-join|工序合流|工序,合流,装配,流程
arrows-split|工序分流|工序,分流,生产线,流程
progress-bolt|产能进度|产能,进度,生产,效率
player-play|设备运行|运行,开机,生产,启动
player-stop|设备停机|停机,停止,生产,设备
replace|生产换型|换型,替换,生产,切换
alert-circle|生产故障|故障,异常,生产,告警
arrow-up-circle|设备升级|升级,改造,设备,制造
"""),

"02_设备与维护": _rows(r"""
tools-off|维修工具箱|工具箱,维修,维护,工程师
tool|维修扳手|扳手,维修,维护,工具
circuit-switch-closed|检修开关|开关,维修,工具,装配
settings-check|设备点检|设备,点检,检查,设置
settings-search|设备诊断|诊断,设备,搜索,故障
settings-off|设备停用|停用,设备,关闭,故障
hammer-off|工具停用|停用,工具,维护,故障
device-desktop-cog|设备配置|设备,配置,终端,维护
device-desktop-search|设备检测|检测,设备,诊断,终端
device-desktop-check|设备确认|设备,确认,检查,终端
server-cog|服务器维护|服务器,维护,配置,设备
database-cog|数据库维护|数据库,维护,配置,存储
cpu|处理器|CPU,处理器,芯片,计算
circuit-cell|电子电路|电路,电子,设备,芯片
circuit-capacitor|电容元件|电容,电路,元件,备件
circuit-resistor|电阻元件|电阻,电路,元件,备件
plug-connected|设备连接|连接,插头,设备,电源
plug-off|设备断开|断开,插头,设备,电源
power|设备电源|电源,开关,设备,运行
battery|设备电池|电池,电量,设备,能源
battery-charging|电池充电|充电,电池,设备,电源
temperature|设备温度|温度,设备,监测,状态
gauge|设备仪表|仪表,设备,监测,压力
dashboard|状态仪表盘|仪表盘,状态,监控,设备
activity-heartbeat|设备健康|健康状态,设备,监测,运行
wave-sine|振动监测|振动,波形,监测,诊断
clock-cog|维护周期|周期,维护,计时,计划
calendar-cog|维护计划|维护计划,日历,保养,设备
calendar-time|保养时间|保养,时间,维护,计划
history|设备履历|履历,历史,生命周期,设备
refresh|设备刷新|刷新,设备,更新,维护
restore|设备恢复|恢复,设备,维护,修复
rotate-clockwise|部件旋转|旋转,部件,运行,设备
arrows-exchange|部件替换|替换,备件,零件,维护
alert-triangle|设备告警|告警,设备,故障,异常
alarm|故障报警|报警,故障,设备,提醒
bell-ringing|维护提醒|提醒,维护,保养,通知
player-pause|设备暂停|暂停,设备,运行,停机
lock|设备锁定|锁定,设备,安全,维护
lock-open|设备解锁|解锁,设备,权限,维护
shield-lock|设备防护|防护,设备,锁定,安全
camera|设备摄像|摄像头,设备,监控,检测
scan|设备扫描|扫描,检测,诊断,设备
radar|雷达检测|雷达,检测,传感器,监控
antenna-bars-5|信号监测|信号,监测,通信,设备
wifi|无线连接|WiFi,无线,连接,设备
cloud-cog|云端运维|云,运维,配置,设备
server|设备服务器|服务器,设备,终端,计算
database|设备数据存储|数据库,存储,设备,数据
device-desktop|设备终端|终端,设备,电脑,监控
device-laptop|维护电脑|电脑,维护,终端,工程师
stethoscope|设备听诊|听诊,诊断,预测维护,设备
user-cog|维护工程师|工程师,维护,人员,技术支持
headset|远程技术支持|技术支持,远程,服务,维护
lifebuoy|设备支持|支持,救援,维护,服务
"""),

"03_质量管理": _rows(r"""
shield-check|质量保证|质量,保证,合格,盾牌
clipboard-check|质量检查|质量,检查,清单,合格
checklist|检验清单|检验,清单,检查,质量
file-check|质量文件确认|质量,文件,确认,记录
certificate|质量认证|认证,证书,质量,标准
badge|质量标识|质量,标识,合格,认证
medal|质量奖章|质量,奖章,优秀,评价
award|质量荣誉|荣誉,质量,奖项,优秀
target-arrow|质量目标|质量,目标,精度,改进
focus|检验精度|精度,检验,聚焦,质量
circle-check|检验通过|通过,合格,检验,确认
checks|复核通过|复核,通过,确认,检查
zoom-check|放大检验|检验,放大,确认,质量
microscope|微观检测|显微镜,检测,实验,质量
file-certificate|标准规范|标准,规范,认证,文件
list-details|质量记录|记录,明细,质量,追溯
report|质量报告|报告,质量,记录,分析
file-report|检验报告|检验,报告,文件,记录
notes|质量记录单|记录,质量,笔记,追溯
timeline|质量追溯|追溯,时间线,过程,质量
search|质量搜索|搜索,质量,检查,追溯
zoom-scan|缺陷扫描|扫描,缺陷,检测,放大
bug|产品缺陷|缺陷,问题,异常,质量
circle-x|检验失败|失败,不合格,检验,错误
exclamation-circle|质量异常|异常,警告,质量,问题
alert-square-rounded|质量警告|警告,质量,风险,异常
eraser|质量纠正|纠正,消除,改进,质量
edit-circle|质量整改|整改,编辑,改进,质量
git-compare|质量对比|对比,质量,差异,复核
arrows-diff|差异分析|差异,分析,对比,质量
scale|质量判定|判定,标准,平衡,质量
ruler|尺寸检验|尺寸,检验,标准,精度
test-pipe|质量测试|测试,实验,质量,检测
flask|质量实验|实验,测试,质量,验证
progress-check|过程质量|过程质量,进度,检查,改进
"""),

"04_安全与风险": _rows(r"""
shield|安全防护|安全,防护,盾牌,风险
shield-exclamation|安全警示|安全,警示,盾牌,风险
shield-x|防护失效|防护,失效,风险,安全
shield-checkered|安全保障|安全,保障,防护,风险
alert-hexagon|危险警告|危险,警告,风险,告警
alarm-smoke|应急警报|应急,警报,事故,告警
flame|火灾风险|火灾,消防,危险,风险
fire-extinguisher|消防灭火|消防,灭火器,应急,安全
first-aid-kit|急救包|急救,医疗,应急,安全
ambulance|应急救援|救援,应急,医疗,事故
medical-cross|医疗急救|医疗,急救,安全,应急
heartbeat|生命体征|心跳,生命,医疗,人员安全
heart-rate-monitor|健康监护|健康,监护,心率,人员安全
emergency-bed|紧急医疗|紧急,医疗,救援,安全
ban|禁止操作|禁止,安全,操作,风险
circle-off|禁止进入|禁止,进入,隔离,安全
key|安全密钥|密钥,安全,权限,认证
fingerprint|身份认证|指纹,认证,身份,安全
password|访问密码|密码,访问,权限,数据安全
lock-access|访问控制|访问控制,权限,安全,锁
user-shield|人员安全|人员,安全,防护,权限
helmet|安全帽|安全帽,防护,人员安全,工地
face-mask|面部防护|口罩,面部,防护,人员安全
eye|安全监控|监控,观察,安全,检查
device-computer-camera|视频监控|监控,摄像,安全,风险
map-pin-exclamation|风险位置|位置,风险,事故,定位
door-exit|安全出口|出口,逃生,安全,应急
bolt|高压危险|高压,闪电,危险,电气安全
thermometer|高温风险|高温,温度,危险,安全
network|网络安全|网络,安全,连接,防护
cloud-lock|数据安全|数据,安全,锁,隐私
shield-half|隐私防护|隐私,防护,数据安全,盾牌
eye-off|隐私保护|隐私,不可见,安全,权限
clipboard-search|风险检查|风险,检查,评估,清单
chart-dots-3|风险评估|风险评估,分析,等级,监控
"""),

"05_物流与仓储": _rows(r"""
building-warehouse|仓库|仓库,仓储,物流,库存
layout-columns|仓储货架|货架,仓储,库存,仓库
layers-subtract|托盘堆叠|托盘,仓储,搬运,货物
forklift|叉车|叉车,装卸,搬运,仓储
truck|运输卡车|卡车,运输,物流,车辆
truck-delivery|物流配送|物流,配送,交付,卡车
truck-loading|货物装卸|装卸,货物,卡车,物流
package-import|货物入库|入库,货物,仓储,收货
package-export|货物出库|出库,货物,仓储,发货
package-off|缺货|缺货,包裹,库存,异常
box-multiple|批量货箱|货箱,批量,仓储,库存
container|物流容器|容器,物流,仓储,运输
building-store|配送中心|配送中心,仓储,门店,物流
shopping-cart|采购订单|采购,订单,购物车,供应
basket|收货篮|收货,采购,容器,物流
clipboard-list|物流清单|清单,物流,订单,仓储
list-check|交货确认|交货,确认,清单,物流
barcode|条码|条码,扫描,库存,物流
qrcode|二维码|二维码,扫描,追溯,物流
scan-position|扫码定位|扫描,定位,条码,仓储
route|配送路线|路线,配送,物流,运输
map|物流地图|地图,物流,运输,区域
map-pin|货物定位|定位,位置,货物,物流
navigation|运输导航|导航,运输,路线,物流
compass|物流方向|方向,导航,物流,路线
direction-sign|方向指引|方向,指引,仓储,物流
arrows-move|货物移动|移动,搬运,货物,物流
transfer|物流中转|中转,交换,物流,运输
arrow-back-up|物流退回|退回,返回,物流,货物
send|货物发运|发运,发送,物流,交付
inbox|收货|收货,入库,物流,货物
inbox-off|发货|发货,出库,物流,货物
hourglass|物流等待|等待,交期,物流,时间
clock-hour-4|交货时间|交货,时间,配送,物流
calendar-clock|交付日期|交付,日期,订单,物流
scale-outline|货物称重|称重,货物,物流,计量
plane|航空运输|飞机,航空,运输,物流
ship|海运|船舶,海运,运输,物流
train|铁路运输|铁路,火车,运输,物流
car|车辆运输|车辆,运输,配送,物流
bus|客货车辆|车辆,运输,路线,物流
sailboat|水路运输|船舶,水路,运输,物流
road|运输道路|道路,运输,路线,物流
world|全球供应链|全球,供应链,物流,运输
building-airport|物流港口|港口,物流中心,空运,仓储
buildings|货运中心|货运,物流中心,仓储,运输
box-multiple-0|库存短缺|库存,短缺,仓储,异常
box-off|库存减少|库存减少,货箱,出库,仓储
box-multiple-9|库存增加|库存增加,货箱,入库,仓储
shopping-bag|采购物料|采购,物料,供应,订单
receipt|收货凭证|收货,凭证,订单,物流
file-barcode|物流单据|单据,条码,物流,追溯
location|物流位置|位置,定位,物流,仓储
arrows-right-left|供需交换|供应,需求,交换,物流
chart-covariate|库存周转|库存周转,趋势,仓储,效率
"""),

"06_数据与数字化": _rows(r"""
database-search|数据检索|数据,数据库,搜索,数字化
database-export|数据导出|数据,导出,数据库,交换
database-import|数据导入|数据,导入,数据库,交换
database-share|数据共享|数据,共享,数据库,协同
server-2|数据服务器|服务器,数据,计算,数字化
server-bolt|计算服务器|服务器,计算,性能,数字化
cloud|云平台|云,平台,数据,数字化
cloud-computing|云计算|云计算,数据,服务器,数字化
cloud-data-connection|云数据连接|云,数据,连接,交换
api|应用接口|API,接口,软件,连接
code|软件代码|代码,软件,编程,数字化
braces|程序结构|程序,代码,结构,软件
binary|二进制数据|二进制,数据,计算,数字化
terminal|数字终端|终端,命令,软件,数字化
prompt|命令提示|命令,终端,软件,操作
brain|人工智能|人工智能,AI,算法,模型
sparkles|AI模型|AI,模型,算法,人工智能
circuit-ground-digital|物联网芯片|芯片,物联网,电路,数字化
device-desktop-analytics|数字化看板|看板,分析,电脑,数字化
chart-bar|数据柱状图|数据,柱状图,分析,统计
chart-line|数据趋势|趋势,折线图,数据,分析
chart-pie|数据占比|占比,饼图,数据,统计
chart-dots|数据分析|分析,数据,图表,趋势
report-analytics|分析报表|报表,分析,数据,统计
analyze|智能分析|分析,算法,数据,决策
filter|数据筛选|筛选,过滤,数据,分类
filter-search|筛选检索|筛选,搜索,数据,分类
sort-ascending|数据排序|排序,数据,规则,分类
download|数据下载|下载,数据,文件,交换
upload|数据上传|上传,数据,文件,交换
file|数字文件|文件,数据,信息,数字化
folder|数据文件夹|文件夹,数据,归档,数字化
table|数据表格|表格,数据,报表,统计
file-spreadsheet|电子表格|表格,文件,数据,报表
arrows-shuffle|数据流转|数据流,交换,流转,数字化
affiliate|数据节点|节点,连接,网络,数据
topology-ring|网络拓扑|拓扑,网络,节点,连接
topology-star|星型网络|拓扑,网络,节点,连接
link|数据链接|链接,连接,数据,网络
unlink|断开链接|断开,链接,数据,网络
wifi-2|物联网连接|物联网,WiFi,连接,网络
bluetooth|蓝牙通信|蓝牙,通信,连接,物联网
antenna|无线通信|通信,天线,无线,网络
broadcast|数据广播|广播,通信,数据,网络
device-mobile|移动端|移动端,手机,数据,数字化
device-tablet|平板终端|平板,终端,数据,数字化
device-imac|数字工作站|工作站,电脑,数据,终端
robot-face|智能机器人|机器人,智能,自动化,AI
schema|数据模型|模型,数据,结构,规则
chart-arrows|预测优化|预测,优化,趋势,决策
refresh-dot|数据同步|同步,刷新,数据,交换
cloud-download|云端备份|备份,云,下载,数据
cloud-upload|云端恢复|恢复,云,上传,数据
user-check|用户权限|用户,权限,数据,认证
info-circle|数据信息|信息,数据,通知,说明
"""),

"07_人员与组织": _rows(r"""
user|人员|人员,用户,员工,组织
users|团队|团队,人员,员工,组织
users-group|组织群组|群组,组织,团队,人员
user-circle|员工身份|员工,身份,人员,用户
user-star|专家人才|专家,人才,技能,人员
user-plus|增加人员|增加人员,招聘,团队,组织
user-minus|减少人员|减少人员,离职,团队,组织
user-heart|人员关怀|人员,关怀,员工,组织
friends|同事合作|合作,同事,团队,沟通
building-community|组织机构|组织,机构,部门,人员
building|企业组织|企业,组织,部门,管理
sitemap|组织架构|组织,架构,层级,部门
briefcase|岗位工作|岗位,工作,人员,职责
id|人员身份|身份,人员,员工,认证
id-badge|员工工牌|工牌,员工,身份,岗位
address-book|人员通讯录|通讯录,人员,联系人,组织
user-square|联系人|联系人,人员,沟通,客户
phone|电话沟通|电话,沟通,联系,人员
mail|邮件沟通|邮件,沟通,联系,人员
message|人员消息|消息,沟通,人员,协作
messages|团队沟通|沟通,团队,消息,协作
speakerphone|组织通知|通知,组织,沟通,公告
microphone|会议发言|发言,会议,沟通,人员
presentation|人员培训|培训,演示,人员,学习
chalkboard|现场教学|教学,培训,讲解,人员
school|学习培训|学习,培训,教育,人员
stairs-up|技能成长|技能,学习,成长,人员
rosette|人员资质|资质,认证,人员,技能
target|人员目标|目标,绩效,人员,管理
chart-bar-popular|人员绩效|绩效,人员,指标,增长
calendar|人员日历|日历,人员,计划,排班
calendar-event|人员排班|排班,日历,人员,任务
clock|工时|工时,时间,人员,工作
clipboard|工作任务|任务,工作,人员,清单
signature|责任签署|责任,签署,授权,人员
user-scan|人员审核|审核人,人员,确认,身份
user-question|人员问询|问询,人员,沟通,责任
user-exclamation|人员提醒|提醒,人员,责任,异常
heart-handshake|合作伙伴|合作,伙伴,供应商,客户
building-plus|部门人员|部门,人员,组织,团队
"""),

"08_管理计划与流程": _rows(r"""
calendar-stats|计划日历|计划,日历,进度,管理
calendar-check|计划完成|计划,完成,日历,任务
calendar-due|任务到期|任务,到期,日历,提醒
list-numbers|步骤清单|步骤,清单,流程,任务
list|任务列表|任务,列表,计划,管理
subtask|子任务|子任务,步骤,项目,流程
route-2|流程路线|流程,路线,步骤,执行
world-map|项目路线图|路线图,项目,战略,计划
flag|项目里程碑|里程碑,项目,目标,计划
flag-3|关键节点|关键节点,里程碑,项目,进度
navigation-east|战略方向|战略,方向,决策,管理
arrow-fork|流程分支|分支,流程,决策,步骤
git-merge|流程合并|合并,流程,审批,步骤
repeat|循环流程|循环,流程,执行,改进
reload|重新执行|重新执行,回滚,刷新,流程
rotate-2|流程同步|同步,流程,状态,管理
player-skip-forward|推进执行|推进,执行,步骤,进度
player-track-next|下一步骤|下一步,步骤,流程,执行
player-track-prev|流程回退|回退,流程,步骤,回滚
circle-dashed-check|流程完成|完成,流程,状态,确认
circle-dashed-x|流程终止|终止,流程,状态,停止
arrow-back|管理回滚|回滚,返回,流程,管理
adjustments|管理配置|配置,管理,规则,控制
adjustments-check|配置确认|配置,确认,规则,管理
filter-cog|管理规则|规则,筛选,配置,管理
sort-descending|优先级排序|优先级,排序,任务,管理
arrows-sort|任务排序|排序,任务,流程,管理
bell|任务通知|通知,任务,提醒,管理
bell-plus|新增提醒|提醒,新增,任务,通知
progress|项目进度|进度,项目,任务,管理
progress-alert|进度预警|进度,预警,项目,风险
status-change|状态变更|状态,变更,流程,管理
eye-check|执行监控|监控,执行,检查,管理
timeline-event|项目时间线|时间线,项目,进度,计划
chart-dots-2|甘特计划|甘特,计划,进度,项目
tournament|管理层级|层级,管理,组织,流程
binary-tree-2|决策树|决策,分支,层级,管理
file-like|文件审批|审批,文件,流程,管理
report-search|管理复核|复核,报告,检查,管理
device-desktop-up|执行控制|执行,控制,监控,管理
"""),

"09_成本财务与经营": _rows(r"""
currency-yuan|人民币金额|人民币,金额,货币,财务
wallet|企业钱包|钱包,资金,支付,财务
cash|现金|现金,资金,支付,财务
credit-card|企业支付|支付,信用卡,资金,财务
receipt-yuan|人民币账单|账单,人民币,支出,财务
file-invoice|财务发票|发票,财务,账单,文件
calculator|财务计算|计算器,财务,成本,金额
percentage|百分比|百分比,指标,折扣,财务
discount|折扣|折扣,价格,销售,经营
pig-money|预算储蓄|预算,储蓄,资金,财务
building-bank|银行金融|银行,金融,资金,财务
coins|资金资产|资金,资产,货币,财务
coin-yuan|人民币资金|人民币,资金,货币,财务
moneybag|资金包|资金,现金,预算,财务
businessplan|经营计划|经营,计划,商业,财务
report-money|经营报表|经营,报表,财务,指标
chart-infographic|经营指标|经营,指标,图表,分析
trending-up|经营增长|增长,趋势,经营,收入
trending-down|经营下降|下降,趋势,经营,支出
chart-area-line|利润增长|利润,增长,趋势,经营
trending-down-2|成本下降|成本降低,下降,趋势,财务
arrow-down-circle|降本|降本,成本降低,经营,改善
shopping-cart-dollar|采购成本|采购,成本,金额,经营
shopping-bag-discount|销售折扣|销售,折扣,价格,经营
building-skyscraper|企业经营|企业,经营,资产,管理
building-estate|经营资产|资产,企业,经营,投资
briefcase-2|商业经营|商业,经营,业务,管理
flag-dollar|财务目标|财务,目标,金额,经营
scale-off|经营权衡|经营,权衡,决策,成本
chart-sankey|现金流|现金流,收入,支出,经营
"""),

"10_效率改善与精益": _rows(r"""
rocket|效率提升|效率,提升,加速,改善
speedboat|快速推进|快速,推进,速度,效率
clock-bolt|快速响应|快速,时间,响应,效率
stopwatch|作业计时|计时,作业,效率,时间
clock-up|效率提升时间|效率,提升,时间,改善
arrow-big-up-lines|持续提升|提升,改善,效率,趋势
chart-arrows-vertical|效率趋势|效率,趋势,提升,分析
chart-histogram|效率分析|效率,分析,产能,绩效
activity|生产效率|效率,活动,生产率,绩效
bulb|改善创意|改善,创意,优化,精益
repeat-once|改善循环|循环,改善,精益,流程
recycle|精益循环|精益,循环,改善,减少浪费
arrows-minimize|减少浪费|减少,浪费,精益,优化
arrows-maximize|产能提升|产能,提升,效率,优化
zoom-in-area|聚焦改善|聚焦,改善,检查,优化
search-off|消除查找浪费|查找,浪费,减少,精益
hourglass-off|减少等待|等待,减少,时间,精益
walk|人员移动|移动,人员,搬运,浪费
arrows-transfer-up|搬运优化|搬运,优化,移动,精益
trash|浪费消除|浪费,消除,精益,改善
clipboard-data|标准作业|标准,作业,数据,精益
ruler-3|作业标准|标准,作业,测量,精益
layout-kanban|精益看板|看板,精益,可视化,流程
eye-table|目视化管理|目视化,管理,精益,看板
bolt-off|能耗浪费|浪费,能耗,减少,精益
square-check|快速完成|快速,完成,效率,任务
military-award|改善绩效|改善,绩效,优秀,效率
chart-bar-off|低效识别|低效,识别,分析,改善
trending-up-2|产能加速|产能,加速,进度,效率
arrows-random|流程优化|流程,优化,改善,精益
"""),

"11_能源环保与可持续": _rows(r"""
solar-panel|太阳能|太阳能,新能源,能源,可持续
wind|风能|风能,新能源,能源,环境
windmill|风力发电|风力,发电,能源,可持续
leaf|绿色环保|绿色,叶子,环保,可持续
tree|绿色树木|树木,绿色,生态,环境
trees|生态环境|生态,树木,环境,可持续
droplet|水资源|水,资源,环境,可持续
home-eco|全球生态|地球,生态,环境,可持续
plant|绿色植物|植物,绿色,生态,环境
seedling|生态成长|生态,成长,绿色,可持续
battery-eco|绿色电池|电池,绿色,能源,环保
battery-spark|新能源储能|储能,电池,新能源,能源
charging-pile|充电桩|充电桩,新能源车,能源,电力
scooter-electric|新能源车|新能源车,电动汽车,绿色,交通
plug|能源接入|能源,接入,电源,电力
circuit-bulb|节能照明|照明,节能,能源,电力
sun|太阳资源|太阳,自然,能源,环境
cloud-fog|气候环境|气候,环境,太阳,云
waves-electricity|水力发电|水力,发电,能源,可持续
droplet-bolt|水能源|水,能源,资源,可持续
flame-off|减排|减排,燃料,排放,环保
gas-station-off|减少化石燃料|燃料,减少,环保,能源
trash-off|减少废弃物|废弃物,减少,环保,资源
recycle-off|回收异常|回收,异常,环保,循环
world-check|全球环境|全球,环境,地球,可持续
mountain|自然资源|自然,资源,生态,环境
fish|水域生态|水域,生态,环境,自然
world-down|碳管理|碳,排放,环保,可持续
temperature-sun|气候温度|气候,温度,环境,可持续
leaf-2|可持续发展|可持续,生态,环保,绿色
"""),

"12_科研教育与技术": _rows(r"""
atom|原子科学|原子,科学,科研,技术
dna|生命科学|DNA,生命科学,科研,技术
telescope|科学观测|观测,望远镜,科研,科学
flask-2|实验研究|实验,研究,科研,技术
test-pipe-2|实验测试|实验,测试,科研,技术
book|知识书籍|书籍,知识,学习,教育
books|科研文献|文献,书籍,科研,知识
notebook|研究笔记|笔记,研究,科研,记录
file-text|研究文档|文档,研究,论文,科研
file-description|论文资料|论文,资料,文档,科研
pencil|科研编辑|编辑,科研,文档,设计
edit|技术编辑|编辑,技术,文档,设计
writing|研究写作|写作,研究,论文,科研
quote|文献引用|引用,文献,论文,科研
zoom|科研检索|检索,放大,科研,搜索
math|数学公式|数学,公式,计算,科研
math-function|函数计算|函数,计算,数学,科研
abacus|科学计算|计算,科研,数学,技术
presentation-analytics|科研演示|演示,科研,数据,讲解
chalkboard-teacher|课堂教学|教学,课堂,讲解,教育
book-2|课程教材|教材,课程,学习,教育
certificate-2|技术证书|证书,技术,教育,认证
bulb-off|创新问题|创新,问题,技术,解决方案
adjustments-spark|知识思考|知识,思考,学习,研究
code-dots|编程技术|编程,代码,技术,科研
terminal-2|技术终端|终端,编程,技术,工程
cpu-2|计算技术|计算,芯片,技术,科研
database-star|研究数据|研究,数据,统计,科研
chart-area|科研图表|图表,科研,数据,分析
chart-scatter|实验数据|实验,数据,分析,科研
robot-off|机器人研究|机器人,研究,技术,工程
message-question|科研问答|问答,问题,科研,交流
help|问题求助|问题,求助,解决方案,教育
question-mark|科学问题|问题,科学,研究,问答
puzzle|问题解决|解决方案,问题,创新,技术
settings-code|技术配置|技术,配置,代码,工程
vector|工程设计|工程,设计,几何,技术
ruler-off|设计校核|设计,校核,工程,技术
compass-off|技术方向|方向,技术,研究,设计
microscope-off|显微研究|显微镜,研究,科研,实验
school-off|远程教育|教育,学校,学习,课程
book-download|知识下载|知识,下载,学习,资料
notes-off|研究问题记录|记录,问题,研究,笔记
file-pencil|论文编辑|论文,编辑,文档,科研
file-vector|技术知识网络|知识,网络,技术,科研
"""),
}


ALIASES_ZH = {
    "机器": "设备", "机械": "设备", "机台": "设备", "维修": "设备维护", "检修": "设备维护",
    "保养": "设备维护", "运维": "设备维护", "点检": "设备检查", "发货": "物流配送", "出货": "物流配送",
    "寄送": "物流配送", "收货": "货物入库", "员工": "人员", "工人": "人员", "同事": "人员",
    "降本": "成本降低", "省钱": "成本降低", "提效": "效率改善", "增效": "效率改善", "品控": "质量管理",
    "质检": "质量检查", "品质": "质量", "安防": "安全防护", "EHS": "安全环保", "仓储": "仓库",
    "库房": "仓库", "货运": "物流运输", "数字化": "数据", "数智化": "数据", "信息化": "数据",
    "大数据": "数据分析", "AI": "人工智能", "智能化": "自动化", "培训": "人员培训", "学习": "教育",
    "科研": "研究", "研发": "研究", "课题": "研究", "绿色": "环保", "低碳": "碳管理",
    "双碳": "碳管理", "节能": "能源", "精益": "效率改善", "改善": "效率改善", "生产力": "生产率",
    "工艺流程": "流程", "工作流": "流程", "里程碑": "项目节点", "财务": "成本财务", "经营": "企业经营",
}


CATEGORY_KEYWORDS_EN = {
    "01_制造与工厂": ["manufacturing", "factory", "production", "industrial", "assembly"],
    "02_设备与维护": ["equipment", "maintenance", "repair", "machine", "diagnostics"],
    "03_质量管理": ["quality", "inspection", "verification", "standard", "audit"],
    "04_安全与风险": ["safety", "risk", "warning", "protection", "emergency"],
    "05_物流与仓储": ["logistics", "warehouse", "delivery", "transport", "inventory"],
    "06_数据与数字化": ["data", "digital", "analytics", "network", "software"],
    "07_人员与组织": ["people", "organization", "team", "employee", "communication"],
    "08_管理计划与流程": ["management", "planning", "process", "project", "workflow"],
    "09_成本财务与经营": ["finance", "cost", "business", "money", "performance"],
    "10_效率改善与精益": ["efficiency", "improvement", "lean", "optimization", "productivity"],
    "11_能源环保与可持续": ["energy", "environment", "sustainability", "ecology", "green"],
    "12_科研教育与技术": ["research", "education", "science", "technology", "learning"],
}
