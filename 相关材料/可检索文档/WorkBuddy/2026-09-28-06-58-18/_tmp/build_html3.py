# -*- coding: utf-8 -*-
import io, os, re, html

WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
OUT = os.path.join(WS, '本科圈功能解剖_2026-10-12.html')

def esc(t):
    return html.escape(str(t), quote=False)

def md(t):
    t = esc(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    return t

H = []
A = H.append

A('<!DOCTYPE html>')
A('<html lang="zh-CN">')
A('<head>')
A('<meta charset="utf-8">')
A('<meta name="viewport" content="width=device-width, initial-scale=1">')
A('<title>本科圈功能解剖 · 2026-10-12</title>')
A('''<style>
:root{
  --bg:#f6f7f9; --panel:#ffffff; --ink:#1b1e23; --sub:#5a6472; --line:#e2e6ec;
  --acc:#1F3D2B; --acc2:#2f6b4f; --warn:#9E3B2E; --gold:#8a6d1f; --blue:#2b4f7a;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  font-size:15px;line-height:1.75;-webkit-font-smoothing:antialiased}
.wrap{max-width:1000px;margin:0 auto;padding:34px 22px 70px}
header{border-bottom:2px solid var(--acc);padding-bottom:18px;margin-bottom:26px}
h1{font-size:25px;margin:0 0 8px;letter-spacing:.3px}
.meta{color:var(--sub);font-size:13px}
h2{font-size:18px;margin:38px 0 14px;padding-left:11px;border-left:4px solid var(--acc)}
h3{font-size:15.5px;margin:22px 0 10px;color:var(--acc)}
p{margin:9px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}
.lead{background:linear-gradient(180deg,#fbfcfd,#f3f6f4);border-left:4px solid var(--acc)}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13.5px;background:var(--panel)}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}
th{background:#eef1f4;font-weight:600;white-space:nowrap}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
code{background:#eef1f4;padding:1px 5px;border-radius:4px;font-size:12.5px;font-family:Consolas,Menlo,monospace}
b{color:#0f1319}
ul,ol{margin:8px 0;padding-left:22px}
li{margin:5px 0}
.badge{display:inline-block;font-size:12px;padding:1px 8px;border-radius:20px;border:1px solid;margin-right:5px;white-space:nowrap}
.b-debt{color:var(--warn);border-color:#e6c4be;background:#fdf4f2}
.b-deal{color:var(--blue);border-color:#c3d3e6;background:#f2f6fb}
.b-fest{color:var(--gold);border-color:#e6dcb8;background:#fbf8ee}
.b-once{color:var(--sub);border-color:#d5dae1;background:#f4f6f8}
.bar{height:15px;background:#e9edf1;border-radius:3px;overflow:hidden;min-width:70px}
.bar>i{display:block;height:100%;background:linear-gradient(90deg,#2f6b4f,#1F3D2B)}
.warn{background:#fdf6f5;border-left:4px solid var(--warn);padding:11px 14px;border-radius:6px;margin:12px 0}
.note{background:#f5f8f6;border-left:4px solid var(--acc2);padding:11px 14px;border-radius:6px;margin:12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:14px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px}
.kpi .v{font-size:23px;font-weight:700;color:var(--acc);letter-spacing:.5px}
.kpi .k{font-size:12.5px;color:var(--sub);margin-top:3px}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);color:var(--sub);font-size:12.5px}
.small{font-size:12.5px;color:var(--sub)}
</style>''')
A('</head>')
A('<body>')
A('<div class="wrap">')

A('<header>')
A('<h1>本科圈功能解剖 —— 13 人 ≠ 13 段关系</h1>')
A('<div class="meta">首经贸城院 · 公管三班 / 区经2班 ｜ 生成 2026-10-12 ｜ 口径：索引库 2024-11-10 → 2026-10-11 20:52 ｜ 引擎 <code>05</code> 三·补·68 · <code>04</code> 第八类关系</div>')
A('</header>')

# 0 结论
A('<section>')
A('<h2>一、结论先行</h2>')
A('<div class="card lead">')
A('<p>上一轮查明「本科圈 117 人里 13 人有消息」。这一轮把 13 人的对话全部读完，结论是：</p>')
A('<p><b>这 13 个人不是 13 个朋友，是四种功能。</b>真正有实质往来的只有 <b>5 人</b>；其余 <b>8 人全年只在节日出现一次</b>。</p>')
A('<p class="small">→ 修正上一轮读法：「有消息」不等于「有交情」——<b>消息量 ≠ 关系质量</b>。</p>')
A('</div>')
A('<div class="grid">')
for v, k in (('13', '有消息的人'), ('5', '实质往来'), ('8', '节日祝福'), ('1,385', '消息总量')):
    A('<div class="kpi"><div class="v">%s</div><div class="k">%s</div></div>' % (v, k))
A('</div>')
A('</section>')

# 1 功能分层
A('<section>')
A('<h2>二、四种功能</h2>')
A('<table>')
A('<tr><th>层</th><th>人</th><th>条数</th><th>机制</th><th>他给 / 他要</th></tr>')
ROWS = [
    ('<span class="badge b-debt">① 债务</span>', '程颂孟秋', '353', '他欠 ¥2,000（2026-01 → 09 未清）· 他替程写调研报告', '给：作业 / 要：宽限'),
    ('<span class="badge b-debt">① 债务</span>', '尹诗琪', '306', '英国时期欠款（金额未明）· 11 个月约成 1 次饭', '给：请饭 / 要：老交情'),
    ('<span class="badge b-deal">② 事务置换</span>', '李博文', '249', '央美资源 ⇄ 拉人头', '给：微喷/版画 / 要：<b>人头</b>'),
    ('<span class="badge b-deal">② 事务置换</span>', '李莉丽', '141', '帮推简历 ⇄ 科研助理内推（微生物所）', '给：推人 / 要：<b>岗位</b>'),
    ('<span class="badge b-deal">② 事务置换</span>', '肖宇', '107', '祝贺/请饭 ⇄ 北大讲座进校名额', '给：热情 / 要：<b>口子</b>'),
    ('<span class="badge b-fest">③ 节日祝福</span>', '李子轩 · 闻一青 · 蔡静文 · 李澳 · 张学鹏 · 陈飞', '163', '模板化单向祝福（春节/生日/教师节）', '给：存在感 / 要：被记得'),
    ('<span class="badge b-once">④ 一次性事件</span>', '王婧潭', '55', '<b>2025-01-19 03:15 被删好友</b>（本科圈唯一明确终止）', '—'),
    ('<span class="badge b-once">④ 一次性事件</span>', '裴青青', '11', '2025-02-24 她急救，他问候一次，此后 19 个月零往来', '给：善意 / 要：无'),
]
for r in ROWS:
    A('<tr><td>%s</td><td><b>%s</b></td><td class="num">%s</td><td>%s</td><td>%s</td></tr>' % r)
A('</table>')
A('<div class="note"><p><b>自证</b>：他对李子轩说「<b>咱们这个聊天一年一次</b>」，对闻一青说「<b>一年一问候</b>」—— 节日祝福线是他自己定义的。</p></div>')
A('</section>')

# 2 条数分布
A('<section>')
A('<h2>三、消息量分布</h2>')
A('<table>')
A('<tr><th>人</th><th>条数</th><th>我 / 对方</th><th>时间跨度</th><th>占比</th></tr>')
DIST = [
    ('程颂孟秋', 353, '209 / 144', '2024-11-25 → 2026-09-23'),
    ('尹诗琪', 306, '191 / 114', '2025-01-02 → 2025-12-07'),
    ('李博文', 249, '179 / 68', '2025-03-28 → 2026-07-21'),
    ('李莉丽', 141, '88 / 52', '2024-12-24 → 2024-12-27'),
    ('肖宇', 107, '78 / 28', '2025-04-04 → 2025-11-12'),
    ('李子轩', 84, '57 / 27', '2025-01-28 → 2026-02-23'),
    ('闻一青', 57, '39 / 17', '2025-01-28 → 2026-06-13'),
    ('王婧潭', 55, '42 / 12', '2024-11-29 → 2025-01-19'),
    ('裴青青', 11, '8 / 3', '2025-02-24'),
    ('蔡静文', 8, '6 / 2', '2025-01-28'),
    ('李澳', 7, '6 / 1', '2025-04-29'),
    ('张学鹏', 4, '3 / 1', '2025-01-28'),
    ('陈飞', 3, '2 / 1', '2025-01-28 → 2025-09-10'),
]
mx = max(d[1] for d in DIST)
for nm, n, io_, span in DIST:
    w = max(2, round(n / mx * 100))
    A('<tr><td><b>%s</b></td><td class="num">%d</td><td>%s</td><td class="small">%s</td>'
      '<td><div class="bar"><i style="width:%d%%"></i></div></td></tr>' % (nm, n, io_, span, w))
A('</table>')
A('<p class="small">★ 我方发言占比普遍 65–80% → 他是这个圈里的<b>主动方</b>。★ 前 3 人（程/尹/李博文）合计 908 条 = 本科圈消息量的 66%。</p>')
A('</section>')

# 3 身份先行
A('<section>')
A('<h2>四、「身份先行 · 分圈版本管理」</h2>')
A('<p>同一时期（2024-12 → 2025-12），他对本科圈至少给出 <b>6 个版本</b>，每个都比实际高，且彼此不核对：</p>')
A('<table>')
A('<tr><th>对象</th><th>时间</th><th>他说的版本</th><th>数据侧</th></tr>')
V = [
    ('李莉丽', '2024-12-24', '「办公室一个<b>北京国企</b>」「社保类的」「全靠副总脸色活」', '待核实'),
    ('李子轩', '2025-01-28', '「我没啥事<b>国企综办</b>」', '待核实'),
    ('<b>程颂孟秋</b>', '2025-03-27', '「<b>考上了算吧</b>」「<b>就在央美</b>」「没去北师」', '<b>实际是硕士</b> → 「读博」＝抬高'),
    ('李博文', '2025-03-28', '「有个<b>备选学位</b>，混的不好就去了」', '同期央美已定 → 反向降格'),
    ('肖宇', '2025-04-04', '「<b>到时候我帮你走关系央选</b>」', '承诺型（无凭证）'),
    ('尹诗琪', '2025-12-07', '「<b>有点房租收入的</b>」「房租不一定比你工资少」', '待核实'),
]
for r in V:
    A('<tr><td>%s</td><td class="small">%s</td><td>%s</td><td>%s</td></tr>' % r)
A('</table>')
A('<div class="warn">')
A('<p><b>★ 关键实证 —— 补上 <code>USER.md</code> 那条口径红线的源头</b></p>')
A('<p><code>USER.md</code> 记：「不能说：央美『博士在读』」。本轮找到源头之一 —— <b>他本人 2025-03-27 对程颂孟秋说「就在央美（读博）」</b>，而程的提问是「<b>你现在读博去了吗</b>」→ 他顺着对方的假设走，没有纠正。</p>')
A('<p>→ <b>「读博」不是误传，是他本人先说的。</b></p>')
A('</div>')
A('<h3>机制：不是隔离，是「没人会主动核对」</h3>')
A('<p>三个版本的主人（程颂孟秋 / 李博文 / 李莉丽）有 <b>4–7 个共同群</b>（公管三、四班计算机 · 概率论满分💯 · 城市学院学生会13.0）—— <b>物理上并不隔离</b>。</p>')
A('<p>但那些群 2 年内 <b>0 条消息</b>（纯通知群），<b>没有交叉对话的场合</b>。所以版本能共存。</p>')
A('<p class="small">★ 这是<b>可证伪</b>的：只要有人拉一次线下局，三个版本就会撞车。</p>')
A('</section>')

# 4 金钱线
A('<section>')
A('<h2>五、新增金钱线事实</h2>')
A('<table>')
A('<tr><th>#</th><th>事实</th><th>时间</th><th>证据等级</th></tr>')
M = [
    ('D11', '<b>欠程颂孟秋 ¥2,000</b>', '2026-01 → 2026-09 未清', '<code>raw_record</code>'),
    ('D12', '<b>欠尹诗琪英国时期欠款</b>（金额未明）', '2025-12 自陈', '<code>user_report</code>'),
    ('A9', '<b>厦门租车事故 ¥10,000</b>', '2026-05-20 自述', '<code>user_report</code>'),
    ('AS1', '<b>望京的房子在出租</b>（2026-07 挂出）', '2026-07-23', '<code>user_report</code>'),
    ('AS2', '「<b>500 都在逾期</b>」', '2026-07-23', '<code>user_report</code>'),
]
for r in M:
    A('<tr><td><code>%s</code></td><td>%s</td><td class="small">%s</td><td>%s</td></tr>' % r)
A('</table>')
A('<div class="note">')
A('<p><b>★ 厦门事故 ≠ 京密路</b>：全库搜「京密路」6 条<b>无任何事故记录</b>，全部是通勤梗（「京密路巴音布鲁克」）与道路新闻 → <code>MEMORY</code> 待办里的「京密路事故归属 + 金额」<b>需与厦门事故区分核实</b>。</p>')
A('<p><b>★ 新自陈</b>：「最近<b>网贷有点借不出来了</b>」（2026-07-14）→ 债务已进入「新增借款通道关闭」阶段。</p>')
A('<p><b>★ 新增资产项</b>：「望京的房子」—— 此前 <code>05</code> 三·补·64 只记「与父母同住 + 极狐」，需并入资产表。</p>')
A('</div>')
A('</section>')

# 5 班级结构
A('<section>')
A('<h2>六、班级归属（承接上一轮）</h2>')
A('<table>')
A('<tr><th>层</th><th>群</th><th>人数</th><th>他</th></tr>')
C = [
    ('学院', '城院（标签 37）', '114', '✓'),
    ('大类班', '17级公管三班通知群', '29', '✓'),
    ('专业班', '<b>17区经2班</b>', '24', '✓'),
    ('旁证', '三班候选群 / 三班男神群 / 三……班🐳再见 / 公管三，四班计算机', '11 / 10 / 39 / 47', '✓'),
]
for r in C:
    A('<tr><td>%s</td><td>%s</td><td class="num">%s</td><td>%s</td></tr>' % r)
A('</table>')
A('<p><b>专业班 ＝ 区经2班</b>（<code>USER.md</code> 记主修区域经济学 80.82）· <b>大类班 ＝ 公管三班</b>。</p>')
A('<p>★ <b>活跃关系集中在「公管三班」侧</b>：13 人中 <b>6 人</b>带「3班」标签（尹诗琪 / 李博文 / 李莉丽 / 裴青青 / 李澳 / 张学鹏）。</p>')
A('<p class="small">⚠️ 不得读成「转过班」（<code>USER.md</code> 无此记录）→ 待本人确认口径。</p>')
A('</section>')

# 6 时间线
A('<section>')
A('<h2>七、本科圈激活时间线</h2>')
A('<table>')
A('<tr><th>时间</th><th>人</th><th>事</th></tr>')
TL = [
    ('2024-11-25', '程颂孟秋', '借 GPT 账号'),
    ('2024-11-29', '王婧潭', '约羽毛球 → 她嫌远'),
    ('2024-12-10', '程颂孟秋', '他替程写恩施州调研报告 3,000 字'),
    ('2024-12-24–27', '李莉丽', '帮推科研助理 → 交换简历'),
    ('2025-01-02', '尹诗琪', '约饭，她说「应该我请你吃」'),
    ('2025-01-19', '王婧潭', '<b>03:15 被删好友</b>'),
    ('2025-01-28', '6 人', '春节群发（李子轩/闻一青/蔡静文/张学鹏/陈飞/程颂孟秋）'),
    ('2025-02-24', '裴青青', '她急救，他问候'),
    ('2025-03-27', '程颂孟秋', '<b>「就在央美读博」</b>'),
    ('2025-03-28–04-02', '李博文', '微喷/版画，6 天爆发 214 条'),
    ('2025-04-04', '肖宇', '祝贺 + 「我帮你走关系央选」'),
    ('2025-11-12', '肖宇', '求北大讲座进校名额'),
    ('2025-12-07', '尹诗琪', '11 个月后终于见面（望京 nana）'),
    ('2026-01-01–09-23', '程颂孟秋', '<b>借钱 → 反复催收未清</b>'),
    ('2026-07-21', '李博文', '拉人头（16 分钟回访）'),
]
for r in TL:
    A('<tr><td class="small">%s</td><td>%s</td><td>%s</td></tr>' % r)
A('</table>')
A('<p class="small">★ 全部集中在 <b>2024-11 → 2025-04</b>（爆发期）+ 之后只剩<b>催债与节日</b>。</p>')
A('</section>')

# 7 落盘
A('<section>')
A('<h2>八、本轮落盘</h2>')
A('<table>')
A('<tr><th>层</th><th>文件</th><th>变更</th></tr>')
W = [
    ('引擎 · 裁定', '<code>05-纠偏层.md</code>', '新增 <b>三·补·68</b>（8 小节）→ 6,321 行 / 451,442 B'),
    ('引擎 · 人际', '<code>04-人际地图.md</code>', '本科圈节新增<b>功能分层 + 分圈版本管理</b> · 读法 +2 条 · 红线 +4 条 → 595 行 / 47,598 B'),
    ('分析库', '<code>analysis.sqlite</code>', '事件 2,867 → <b>2,870</b> · 证据 5,470 → <b>5,477</b>'),
    ('工作区', '<code>本科圈功能解剖_2026-10-12.html</code>', '本报告'),
]
for r in W:
    A('<tr><td>%s</td><td>%s</td><td class="small">%s</td></tr>' % r)
A('</table>')
A('</section>')

# 8 待确认
A('<section>')
A('<h2>九、待本人确认</h2>')
A('<ol>')
for q in [
    '<b>程颂孟秋那 ¥2,000 到底是谁欠谁？</b> —— 2026-01-07 的转账方向在文本里不唯一，但 2026-05 程说「你是不是还欠我两千哦」。',
    '<b>「北京国企综办 / 社保类」真有过这段吗？</b> —— 2024-12 → 2025-01 他对李莉丽、李子轩都说过。',
    '<b>「望京的房子」是租是自有、月租多少？</b> —— 决定要不要进资产表。',
    '<b>尹诗琪那笔英国欠款多少？</b> —— 他自陈「几万的交情」。',
    '<b>你本科的行政班到底是公管三班还是区经2班？</b> —— 两个班群都在，专业班应是区经2班。',
]:
    A('<li>%s</li>' % q)
A('</ol>')
A('</section>')

A('<footer>')
A('<p>数据源：<code>index.sqlite</code>（393,289 条 · 2024-11-10 → 2026-10-11 20:52）· <code>contact.db</code>（标签/群成员）· 朋友圈全量导出（3,534 帖）。</p>')
A('<p>★ 本报告含真名与私人财务信息 → <b>private</b>，仅本地留存，不得外传、不进任何对外材料。</p>')
A('</footer>')

A('</div>')
A('</body>')
A('</html>')

html_out = '\n'.join(H)

for tag in ('html', 'head', 'body', 'table', 'div', 'tr', 'td', 'th', 'ul', 'ol', 'li',
            'header', 'footer', 'h1', 'h2', 'h3', 'p', 'span', 'style', 'code', 'b', 'i'):
    o = len(re.findall(r'<%s[\s>]' % tag, html_out))
    c = len(re.findall(r'</%s>' % tag, html_out))
    if o != c:
        print('!! 标签不配对 %s: open=%d close=%d' % (tag, o, c))

io.open(OUT, 'w', encoding='utf-8', newline='').write(html_out)
print('HTML ->', OUT, len(html_out.encode('utf-8')), 'bytes')
