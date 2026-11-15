from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()

# 设置默认字体
style = doc.styles['Normal']
font = style.font
font.name = '微软雅黑'
font.size = Pt(10.5)

# ============ 标题 ============
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('蔡浩文 / Cai Haowen / Aaron')
run.bold = True
run.font.size = Pt(18)
run.font.name = '微软雅黑'

# 基本信息
info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
info.add_run('男 · 1999.02.16 · 北京海淀（京内生源）· 中共党员\n').font.size = Pt(10)
info.add_run('电话：17600118801 ｜ 邮箱：aaron.haowencai@gmail.com\n').font.size = Pt(10)
info.add_run('现居：北京\n').font.size = Pt(10)

doc.add_paragraph('─' * 50)

# ============ 教育背景 ============
h = doc.add_heading('教育背景', level=1)
h.runs[0].font.name = '微软雅黑'

table = doc.add_table(rows=4, cols=3)
table.style = 'Table Grid'
table.alignment = WD_TABLE_ALIGNMENT.CENTER

# 表头
headers = ['学校', '专业/学位', '时间']
for i, header in enumerate(headers):
    cell = table.rows[0].cells[i]
    cell.text = header
    cell.paragraphs[0].runs[0].bold = True

# 数据
data = [
    ['中央美术学院 实验艺术与科技艺术学院', '实验艺术与科技艺术 · 研究生在读（班长）', '当前'],
    ['格拉斯哥大学 (QS71)', '发展经济学 · 硕士', '2023.09 – 2024.12'],
    ['首都经济贸易大学', '区域经济学(主修) + 金融学(辅修) · 学士', '2017.09 – 2021.06'],
]
for i, row_data in enumerate(data):
    for j, text in enumerate(row_data):
        table.rows[i+1].cells[j].text = text

doc.add_paragraph()

# ============ 科研与项目经历 ============
h = doc.add_heading('科研与项目经历', level=1)
h.runs[0].font.name = '微软雅黑'

# 朗园项目
p = doc.add_paragraph()
run = p.add_run('基于 TouchDesigner 的新媒体交互装置设计——以"朗园"项目为例（课程论文）')
run.bold = True
run.font.size = Pt(11)
p.add_run('　　2026.03').font.size = Pt(10)

items = [
    '选取北京懋隆文化产业园区"朗园"为研究场域，围绕 AIGC 与体感交互技术进行设计实践',
    '目标：通过 TouchDesigner 与 AI 绘画工具的协同，实现视觉投影随参与者动作实时变化',
    '负责设计手势控制交互模块、选择数据驱动映射方案、评估原型效果',
    '完成项目规划文档、技术选型依据、交互流程图及开发日志',
    '初步搭建的系统已能通过摄像头检测手势，在 TouchDesigner 中实时触发视觉效果切换，形成可供课堂演示的原型作品',
    '技术栈：Python · MediaPipe · TouchDesigner · ComfyUI · AIGC（AnimateDiff / ControlNet / IP-Adapter）',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# 植墨工作室
p = doc.add_paragraph()
run = p.add_run('植墨工作室 · 时光收藏馆 / 栗壳纪 · 印迹系统')
run.bold = True
run.font.size = Pt(11)
p.add_run('　　2026.06 – 至今').font.size = Pt(10)

items = [
    '独立运营丝网版画文创项目，聚焦植物染料工艺与沉浸式文旅体验',
    '植物染料做墨：板栗壳、核桃皮、茶叶、槐花、洋葱皮煮染 → 调成丝网油墨 → 丝网印到纸',
    '商业设计：印迹系统 → 山到城扩散 → 驻印计划（青年艺术家驻留）',
    '运营体系：触达/留存/定价（68/98双层锚定）/ 课程体系',
    '空间设计：三进三出（外立面→窗→房间）、200-300㎡五站 / 20㎡三房',
    'AI 协作：SOUL.md / USER.md 工作流（Nano Banana / 即梦 出图）',
    '落地怀柔，融合版画创作、手作体验与艺术疗愈',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# 绿墨护未
p = doc.add_paragraph()
run = p.add_run('Movers4Climate 绿色乡村青年行动 ·「绿墨护未」')
run.bold = True
run.font.size = Pt(11)
p.add_run('　　2026').font.size = Pt(10)

items = [
    '边疆少数民族地区 绿色美育 + 普法 + 数字动画共创',
    '以央美社会美育资源为基础，把可持续发展知识与法律知识转化为图像、丝网印刷、数字动画',
    '回应边疆地区未成年人保护教育中"语言转译难、抽象法律难"等问题',
    '与植墨项目同源（丝网印刷 + 在地美育），公益向延伸',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# ============ 实习经历 ============
h = doc.add_heading('实习经历', level=1)
h.runs[0].font.name = '微软雅黑'

# 北京台
p = doc.add_paragraph()
run = p.add_run('北京广播电视台 + 北京重点科研实验室')
run.bold = True
run.font.size = Pt(11)
p.add_run('　　AIGC 科研实习生　　2026 上半年').font.size = Pt(10)

items = [
    '融媒体场景下智能体(Agent)架构设计',
    '新闻情报自动抓取 + 结构化摘要生成（模块优化）',
    '数字人播报系统研发：个性化训练与驱动',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# 惠民数科
p = doc.add_paragraph()
run = p.add_run('上海惠民数字科技有限公司（国企金控子公司）')
run.bold = True
run.font.size = Pt(11)
p.add_run('　　战略规划部实习生　　2023.01 – 09').font.size = Pt(10)

items = [
    '撰写第三代社会保障卡在中国人寿集团内的落地战略报告',
    '研究国内外社保卡发展趋势及金融功能创新，输出公司战略规划建议',
    '整理政府政策文件及行业数据，协助搭建战略分析框架',
    '参与跨部门项目汇报材料编写，协调内部战略讨论流程',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# Tronic Trace
p = doc.add_paragraph()
run = p.add_run('Tronic Trace (浙江) / 上海卓宇信息科技有限公司')
run.bold = True
run.font.size = Pt(11)
p.add_run('　　项目助理　　2022.03 – 09').font.size = Pt(10)

items = [
    '参与多个汽车电子项目的开发、测试与优化，涵盖 ECU 诊断与系统集成环节',
    '协助制定项目计划和里程碑，跟踪进度，配合技术文档编写与汇报',
    '与海外团队进行英文技术对接，处理多时区协作沟通',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# KPMG
p = doc.add_paragraph()
run = p.add_run('毕马威（KPMG）')
run.bold = True
run.font.size = Pt(11)
p.add_run('　　销售激励策略组实习生　　2019.01 – 06').font.size = Pt(10)

items = [
    '为戴姆勒-梅赛德斯奔驰设计销售返利政策方案',
    '驻场北京利星行广场/望京研发团队，参与 S-Class 项目需求访谈',
    '使用 VBA 建立数据模型，分析市场定价，协助制定销售激励策略',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# ============ 教学经历 ============
h = doc.add_heading('教学经历', level=1)
h.runs[0].font.name = '微软雅黑'

# 精华培训
p = doc.add_paragraph()
run = p.add_run('北京市海淀区精华培训学校')
run.bold = True
run.font.size = Pt(11)
p.add_run('　　初高中数学主讲老师 / 兼职高中英语教师 / 物理教师　　2025.09 – 至今').font.size = Pt(10)

items = [
    '担任初高中数学主讲教师，教学内容涵盖函数、导数、几何与代数模块，教学对象包括初一至高三学生及复读考生',
    '课堂融入数学史故事与实用案例，提升学生理解力与学习兴趣，获得学生好评',
    '教授阅读、听力和写作模块（英语），讲解牛顿力学、电磁学等核心模块（物理）',
    '独立命题数学模拟卷，参与物理教研组集体备课，整理高考力学真题分类资料',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# 新东方
p = doc.add_paragraph()
run = p.add_run('北京市朝阳区新东方培训学校')
run.bold = True
run.font.size = Pt(11)
p.add_run('　　高中英语教师（实习/试讲）　　2025.07 – 2025.08').font.size = Pt(10)

items = [
    '参与英语教学相关的课程研发工作，包括试题编写、题目解析撰写及知识框架梳理',
    '在助教实习中，协助主讲教师进行课前准备和课堂辅助，提升课堂效率与学生理解',
    '完成针对不同学生群体的授课试讲，展示互动式教学设计与课堂引导能力',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# 剑桥
p = doc.add_paragraph()
run = p.add_run('剑桥大学国王学院·中央美术学院版画交流展')
run.bold = True
run.font.size = Pt(11)
p.add_run('　　翻译/协调志愿者　　2021').font.size = Pt(10)

doc.add_paragraph('协助中外艺术家版画创作对话，协调布展与沟通', style='List Bullet')

doc.add_paragraph()

# ============ 技能与资质 ============
h = doc.add_heading('技能与资质', level=1)
h.runs[0].font.name = '微软雅黑'

# 语言
p = doc.add_paragraph()
run = p.add_run('语言与标准化考试')
run.bold = True
run.font.size = Pt(11)

items = [
    '雅思（IELTS）：6.5',
    '托福（TOEFL）：98',
    'GRE：333',
    '大学英语六级（CET6）：528',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# 职业资格
p = doc.add_paragraph()
run = p.add_run('职业资格与考试')
run.bold = True
run.font.size = Pt(11)

items = [
    'CPA（注册会计师）：财务管理/会计科目备考中',
    'CFA Level 1 Candidate（特许金融分析师一级候选人）',
    '会计初级：2026 全国初级资格考试已报名',
    '证券从业资格证、初级会计资格证、教师资格证（大学及中小学教学资质证书）',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# 技术技能
p = doc.add_paragraph()
run = p.add_run('技术技能')
run.bold = True
run.font.size = Pt(11)

items = [
    'AIGC 影像：ComfyUI（IP-Adapter / AnimateDiff）、ChatGPT、即梦、Nano Banana',
    '交互/装置：Unity（DMX512 灯控）、TouchDesigner',
    '编程：Python（LLM Agent / MediaPipe）、VBA、计算机语言 SQL/VB/Python',
    '计算机视觉：MediaPipe（手势控制交互模块）',
    '影像后期：Capture One、Adobe 全家桶（Photoshop / After Effects / Premiere Pro / Illustrator）、剪映',
    '办公软件：Office 四件套（Word/Excel/PPT/Visio）、WPS、Xmind',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# 项目管理
p = doc.add_paragraph()
run = p.add_run('项目管理能力')
run.bold = True
run.font.size = Pt(11)

items = [
    '项目流程规划与项目管理能力',
    '会场搭建管理、媒体投放规划与成本控制、设计师沟通对接',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# 跨学科
p = doc.add_paragraph()
run = p.add_run('跨学科与创意能力')
run.bold = True
run.font.size = Pt(11)

items = [
    '经济理性 + 良好的审美与创意能力 + 敏锐的数据分析能力',
    '能把复杂 AI 逻辑"翻译"成易懂的艺术创作语言——跨界文化传播',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# ============ 获奖经历 ============
h = doc.add_heading('获奖经历', level=1)
h.runs[0].font.name = '微软雅黑'

items = [
    '2020年12月：获得全国大学生数学建模竞赛北京市一等奖',
    '2019年12月：获"花旗金融信息服务"优秀志愿者、校级优秀志愿者、校级三好学生、校级优秀学生干部',
    '2019年9月：获首都大学生"一带一路"主题社会实践优秀成果奖',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

doc.add_paragraph()

# ============ 个人特质 ============
h = doc.add_heading('个人特质', level=1)
h.runs[0].font.name = '微软雅黑'

items = [
    '跨学科融合：能在经济建模（CFA/CPA）与艺术创作（版画/AIGC/TouchDesigner）之间自由切换',
    'AI 原生创作者：用 ChatGPT / ComfyUI / Nano Banana / 即梦 深度参与创作与运营（SOUL.md / USER.md 工作流）',
    '强叙事 + 商业化：植墨项目里把工艺、心理钩子、定价、TRIZ 融为一体',
    '国际化背景：海外硕士、双语教学、剑桥/新东方教学经验',
    '经济金融硬实力 + 教学表达力的复合组合',
]
for item in items:
    doc.add_paragraph(item, style='List Bullet')

# 保存
doc.save('C:/Users/wardc/Desktop/简历/蔡浩文_完整简历_2026.docx')
print('Word 文档已生成！')
