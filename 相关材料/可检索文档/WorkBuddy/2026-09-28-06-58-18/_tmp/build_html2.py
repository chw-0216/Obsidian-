# -*- coding: utf-8 -*-
"""生成 本科圈打通·班级结构 HTML"""
import io, os, re, html

WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
OUT = os.path.join(WS, '本科圈打通_班级结构_2026-10-11.html')

def esc(t): return html.escape(str(t), quote=False)
def md(t):
    t = esc(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    return t

H = []; A = H.append

SYNC = [
    ('① decrypt（系统 Python 3.12 · 跑两次）', '22 库全部 skip —— 0 decrypted / 22 fresh / 0 failed', '无新增'),
    ('② index-incremental.py', '并入前 393,289 条，最新 2026-10-11 20:52', '+0 条'),
    ('③ gen_live_json.py', '实时 JSON 水位已更新', 'OK'),
    ('④ index-incremental.py --reconcile', '全量对账（补「发送时间早于水位、后来才补到源库」的消息）', '+0 条 · 28.8 秒'),
    ('⑤ FTS 完整性校验', 'messages = messages_fts = 393,289 · 孤儿 0', '✅ 1:1'),
]

BOUND = [
    ('索引库 index.sqlite', '2024-11-10 04:12', '2026-10-11 20:52', '393,289 条'),
    ('WeFlow 全量导出（725 个私聊 JSON）', '2024-11-10 16:52', '2026-07-23 10:09', '私聊_方列丰.json 为最早期'),
    ('解密原始库 Msg_* 表', '同上', '同上', '表级时间与索引一致'),
]

WJ = [
    ('wxid', 'wxid_uhulgmrvfq4a12'),
    ('备注 / 昵称 / 微信号', '周雯娟 / <b>Sora</b> / sora4811'),
    ('标签', '<b>37（城院）＋ 107（全部）</b> —— ★ <b>没有打「3班」</b>'),
    ('所在群', '<b>24 个</b>（全部为本科班级 / 课程群）'),
    ('私聊消息', '<b>0 条</b> —— 原始库<b>无 Msg_ 表</b> · SessionTable 无行 · 索引库 0 · WeFlow 无 JSON'),
    ('朋友圈', '2026-10-11 16:16 有帖（正文未缓存）· 19:35 已读'),
]

CLASS = [
    ('学院', '<b>城院 ＝ 首都经济贸易大学城市经济与公共管理学院</b>', '标签 37 = <b>114 人</b>', '群名「城院人」「城院分团委」「2021届城院毕业生通知群」'),
    ('班级 A', '<b>公管三班</b>', '群 <b>29 人</b> · 标签「3班」<b>24 人</b>', '17级公管三班通知群 · 三班候选群 · 公管三，四班计算机'),
    ('班级 B', '<b>区经2班</b>（区域经济）', '群 <b>24 人</b>', '17区经2班 · 17区经二班资料完善群 · 区域规划课，2班-2017'),
]

TOPLIST = [
    ('程颂孟秋（前室友）', 353, '209 / 144', '2024-11-25 → 2026-09-23'),
    ('尹诗琪', 306, '191 / 114', '2025-01-02 → 2025-12-07'),
    ('<b>李博文</b>', 249, '179 / 68', '2025-03-28 → 2026-07-21'),
    ('李莉丽', 141, '88 / 52', '2024-12-24 → 2024-12-27（3 天）'),
    ('肖宇', 107, '78 / 28', '2025-04-04 → 2025-11-12'),
    ('李子轩', 84, '57 / 27', '2025-01-28 → 2026-02-23'),
    ('闻一青', 57, '39 / 17', '2025-01-28 → 2026-06-13'),
    ('脾气不好的王婧潭', 55, '42 / 12', '2024-11-29 → 2025-01-19'),
]

GROUPS = [
    ('17区经2班', 4, 0),
    ('2021届城院毕业生通知群', 44, 0),
    ('17级公管三班通知群', 0, 0),
    ('三班候选群', 0, 0),
    ('公管三，四班计算机', 0, 0),
    ('城市学院学生会13.0', 0, 0),
    ('其余 8 个课程群', 0, 0),
]

PIT = [
    ('★★ extra_buffer 的标签字段是 <b>ASCII 文本</b>，不是字节列表',
     'field 30 ＝ <code>\\xf2\\x01</code> + <b>varint 长度</b> + <code>"37,107"</code>（逗号分隔的标签 ID <b>字符串</b>）。'
     '误读成字节列表会得到 <code>[51,55,44,49,48,55]</code> —— 看起来像 ID，其实全是 ASCII 码（0x33=\'3\' 0x2c=\',\' …）。'
     '<b>校验法</b>：解析出的 ID 若大量不在 <code>contact_label</code> 字典里 → 一定读错了。'),
    ('contact.db 在子目录', '<code>decrypted/contact/contact.db</code>，不是 <code>decrypted/contact.db</code>。'),
    ('chatroom_member 是数字 ID', '<code>(room_id, member_id)</code> → 需 join <code>contact.id</code> / <code>chat_room.id</code>，<b>不能按 username 查</b>。'),
    ('WeFlow JSON 在各自子目录内', '<code>私聊_XXX/私聊_XXX.json</code>（不是顶层）。'),
    ('WeFlow JSON 时间字段是 createTime', '不是 <code>create_time</code>。'),
    ('sqlite URI 路径必须用正斜杠', '反斜杠会报 <code>unable to open database file</code>。'),
]

RED = [
    '★★ <b>不得把「零消息」读成「没聊过 / 没关系」</b> —— 数据下限 <b>2024-11-10</b>，本科时期（2017–2021）<b>本地不可知</b>。',
    '★★ <b>不得把标签当事实</b> —— 「3班」标签 24 人 vs 公管三班群 29 人；<b>周雯娟有群无标签</b>。标签是本人手工产物，<b>只能作线索</b>。',
    '★ <b>不得把「89% 零消息」读成「人缘差」</b> —— 这是<b>毕业 5 年后的正常沉降</b>，不是关系质量指标。',
    '★ 不得推断周雯娟为何零私聊（可能本科时用别的渠道 / 线下）—— 库内无依据。',
    '★ 不得把「他同时在两个班群」读成「转过班 / 有隐情」。',
    '⚠️ 班群成员名单含大量真名 → <b>private，不得外传</b>。',
]

TODO = [
    '<b>周雯娟是什么时候加的？</b> —— 群内共处但零私聊，是「毕业前就没加」还是「加了没说过话」。',
    '<b>「3班」标签要不要给她补上？</b>（数据侧＝她在群里；标签侧＝缺失）',
    '本科圈 13 个有消息的人里，<b>程颂孟秋 353 条</b>是最大线 → 是否单独建人物档案。',
    '<b>2024-11-10 之前的数据能否补？</b> —— 需在旧手机 / 微信迁移备份里找，<b>当前不可得</b>。',
]

A('<!DOCTYPE html>')
A('<html lang="zh-CN">')
A('<head>')
A('<meta charset="utf-8">')
A('<meta name="viewport" content="width=device-width,initial-scale=1">')
A('<title>本科圈打通 · 班级结构 · 2026-10-11</title>')
A('<style>')
A(':root{--bg:#f6f7f9;--ink:#1b1e23;--sub:#5a6270;--line:#e3e6ea;--card:#fff;--acc:#1F3D2B;--warn:#9E3B2E;--gold:#8a6d1f}')
A('*{box-sizing:border-box}')
A('body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}')
A('.wrap{max-width:1080px;margin:0 auto;padding:40px 24px 80px}')
A('header{border-bottom:3px solid var(--acc);padding-bottom:20px;margin-bottom:32px}')
A('h1{font-size:27px;margin:0 0 10px;letter-spacing:.3px}')
A('.meta{color:var(--sub);font-size:13px;line-height:1.9}')
A('h2{font-size:19px;margin:44px 0 14px;padding-left:11px;border-left:4px solid var(--acc)}')
A('h3{font-size:16px;margin:26px 0 10px;color:var(--acc)}')
A('p{margin:10px 0}')
A('table{width:100%;border-collapse:collapse;background:var(--card);font-size:14px;margin:12px 0;border:1px solid var(--line)}')
A('th,td{padding:8px 11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}')
A('th{background:#eef1f0;font-weight:600;font-size:13px;color:#2a3a31}')
A('tr:last-child td{border-bottom:none}')
A('code{background:#eceff1;padding:1px 5px;border-radius:3px;font-size:13px;font-family:Consolas,Menlo,monospace}')
A('.box{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--acc);padding:14px 18px;margin:16px 0;border-radius:3px}')
A('.box.warn{border-left-color:var(--warn);background:#fdf6f4}')
A('.box.gold{border-left-color:var(--gold);background:#fdfaf0}')
A('.kpi{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0}')
A('.kpi div{flex:1;min-width:150px;background:var(--card);border:1px solid var(--line);border-radius:4px;padding:14px 16px}')
A('.kpi b{display:block;font-size:24px;color:var(--acc);line-height:1.3}')
A('.kpi span{font-size:12.5px;color:var(--sub)}')
A('ol,ul{padding-left:22px;margin:10px 0}')
A('li{margin:6px 0}')
A('.bar{height:9px;background:#e6eae8;border-radius:5px;overflow:hidden;min-width:70px;display:inline-block;vertical-align:middle}')
A('.bar i{display:block;height:100%;background:var(--acc)}')
A('footer{margin-top:56px;padding-top:18px;border-top:1px solid var(--line);color:var(--sub);font-size:12.5px}')
A('</style>')
A('</head>')
A('<body>')
A('<div class="wrap">')
A('<header>')
A('<h1>本科圈打通 · 班级结构首次确定</h1>')
A('<div class="meta">')
A('2026-10-11 深夜 · 触发：「<b>继续打通全部消息，周文娟是也是我本科同班同学</b>」<br>')
A('消息层彻底打通（三层链路 + 全量对账）· 周雯娟改档 · 本科班级三层结构 · 数据源下限实测')
A('</div>')
A('</header>')

# 摘要 KPI
A('<div class="kpi">')
A('<div><b>393,289</b><span>索引库消息（+0 · 已全量对账）</span></div>')
A('<div><b>2024-11-10</b><span>数据源时间下限（全源一致）</span></div>')
A('<div><b>117 人</b><span>本科圈（城院 ∪ 3班）</span></div>')
A('<div><b>89%</b><span>零消息占比（104 / 117）</span></div>')
A('</div>')

A('<div class="box warn"><b>三句话结论</b><br>'
  '① <b>消息层已完全打通</b> —— 三层链路 + 全量对账均为 <b>+0</b>，FTS 1:1（孤儿 0），无遗漏。<br>'
  '② <b>周雯娟是本科同班同学</b>（本人确认）—— 她<b>在 24 个本科群里</b>，却<b>零私聊</b>；<b>标签漏了，关系没漏</b>。<br>'
  '③ <b>数据下限 ＝ 2024-11-10</b> —— 本科时期（2017–2021）本地任何源都没有 → <b>「零消息」不得读成「没聊过」</b>。'
  '</div>')

# 一
A('<h2>一、消息层彻底打通（执行记录）</h2>')
A('<table><tr><th>步骤</th><th>说明</th><th>结果</th></tr>')
for a, b, c in SYNC:
    A('<tr><td>%s</td><td>%s</td><td><b>%s</b></td></tr>' % (md(a), md(b), md(c)))
A('</table>')
A('<p>→ <b>索引库已完全同步，无遗漏。</b>最新消息 <b>2026-10-11 20:52</b>。</p>')

# 二
A('<h2>二、★★ 数据源时间下限 ＝ 2024-11-10（本轮实测）</h2>')
A('<table><tr><th>源</th><th>最早</th><th>最晚</th><th>备注</th></tr>')
for a, b, c, d in BOUND:
    A('<tr><td>%s</td><td><b>%s</b></td><td>%s</td><td>%s</td></tr>' % (md(a), md(b), md(c), md(d)))
A('</table>')
A('<div class="box warn">'
  '<b>本科时期（2017–2021）的聊天记录，本地任何源都不存在。</b><br>'
  '→ ★ <b>「零消息」的准确口径 ＝「2024-11-10 之后零消息」</b> —— <b>不得读成「本科时没聊过」</b>。<br>'
  '→ ★ 这<b>不是索引器截断</b>（WeFlow 是本人自己导的全量），是<b>微信本地库本身就没有更早的</b>。'
  '</div>')

# 三
A('<h2>三、★★★ 周雯娟 ＝ 本科同班同学</h2>')
A('<table><tr><th>项</th><th>值</th></tr>')
for a, b in WJ:
    A('<tr><td>%s</td><td>%s</td></tr>' % (md(a), md(b)))
A('</table>')
A('<div class="box gold"><b>★★ 关键：她没打「3班」标签，但人在「17级公管三班通知群」里 —— 标签漏了，关系没漏。</b><br>'
  '教训：<b>标签是本人手工打的，不完整。判定关系时标签只能作线索，不能作事实。</b></div>')
A('<h3>她的 24 个群（全部为本科班级 / 课程群）</h3>')
A('<table><tr><th>类别</th><th>群名</th></tr>')
A('<tr><td>班级群</td><td>17级公管三班通知群 · 17区经2班 · 三班候选群 · 17区经二班资料完善群 · 公管三，四班计算机 · 区域规划课，2班-2017</td></tr>')
A('<tr><td>年级 / 学院</td><td>🎓2021届城院毕业生通知群 · 城市学院学生会13.0 · SUEPA入党积极分子201903</td></tr>')
A('<tr><td>课程群</td><td>概率论满分💯 · 城市社会学课程群2020 · 城市生态经济学2⃣️班 · 首都区域经济课程群2020 · 空间计量学习群2班 · 城市地理学 · 地理信息系统17级区经 · 区域产业与发展2⃣️班 · 城市营销学课程群 · 中国经济地理17区经 · 124区域经济发展战略 · 17区域经济毕业班论文选题 · “计算机制图”交流群</td></tr>')
A('<tr><td>其他</td><td>阿三大巴开车群👏</td></tr>')
A('</table>')
A('<p><b>她与李博文的共同群 8 个</b>（含 17级公管三班通知群 · 三班候选群 · 公管三，四班计算机 · 城市学院学生会13.0）→ <b>两人确为同班</b>。</p>')

# 四
A('<h2>四、★★★ 本科班级结构首次确定</h2>')
A('<h3>验证链（群成员实证，非推断）</h3>')
A('<div class="box"><code>标签「3班」(49) 共 24 人<br>'
  '&nbsp;&nbsp;∩ 「17级公管三班通知群」(29 人) ＝ 22 人<br>'
  '&nbsp;&nbsp;仅 2 人不在该群：ward、苗成<br>'
  '→ 「3班」＝ 公管三班，确认<br>'
  '★ 周雯娟、李博文、蔡浩文本人 均在该群</code></div>')
A('<table><tr><th>层</th><th>名称</th><th>规模</th><th>依据</th></tr>')
for a, b, c, d in CLASS:
    A('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (md(a), md(b), md(c), md(d)))
A('</table>')
A('<p>→ ★ <b>他本人同时在两个班群里</b>（城院 2017 级大类招生 + 分方向）—— <b>不得</b>读成「转过班 / 有隐情」。</p>')

# 五
A('<h2>五、★ 本科圈消息量普查（口径：2024-11-10 之后）</h2>')
A('<div class="kpi">')
A('<div><b>117</b><span>城院 ∪ 3班</span></div>')
A('<div><b>13</b><span>有消息（11%）</span></div>')
A('<div><b>104</b><span>零消息（89%）</span></div>')
A('<div><b>≈1,428</b><span>消息总量</span></div>')
A('</div>')
A('<table><tr><th>人</th><th>条数</th><th>我 / 他</th><th>时间跨度</th><th></th></tr>')
mx = 353
for nm, n, who, span in TOPLIST:
    w = int(round(100.0 * n / mx))
    A('<tr><td>%s</td><td><b>%d</b></td><td>%s</td><td>%s</td><td><span class="bar" style="width:110px"><i style="width:%d%%"></i></span></td></tr>'
      % (md(nm), n, md(who), md(span), w))
A('<tr><td>其余 5 人</td><td>33</td><td>—</td><td>裴青青 11 · 蔡静文 8 · 李澳 7 · 张学鹏 4 · 陈飞 3</td><td></td></tr>')
A('</table>')
A('<div class="box">'
  '→ ★ <b>有消息的人全部集中在 2024-11 → 2025-12</b> → <b>本科圈是「最近两年才被重新激活」的</b>，与「2025-09 央美入学」拐点同段。<br>'
  '→ ★ 我方发言占比 <b>65–80%</b> → <b>他是这个圈里的主动方</b>。<br>'
  '→ ★ <b>周雯娟在 104 人里</b> —— 她<b>不是孤例</b>。'
  '</div>')

# 六
A('<h2>六、★ 本科班群状态：静音（他一条都没发）</h2>')
A('<table><tr><th>群</th><th>2 年内条数</th><th>他发言</th></tr>')
for nm, n, me in GROUPS:
    A('<tr><td>%s</td><td>%d</td><td><b>%d</b></td></tr>' % (md(nm), n, me))
A('</table>')
A('<div class="box warn">'
  '→ <b>本科圈对他不是「活跃的社交资产」，是「沉在通讯录里的历史层」</b> —— '
  '与「<b>身份先行</b>」的<b>位置策略</b>相互印证：<b>他占的是位置，不是日常往来</b>。'
  '</div>')

# 七
A('<h2>七、★ 技术坑（本轮新增）</h2>')
A('<table><tr><th>坑</th><th>说明</th></tr>')
for a, b in PIT:
    A('<tr><td>%s</td><td>%s</td></tr>' % (a, b))
A('</table>')

# 八
A('<h2>八、⚠️ 红线（本节）</h2>')
A('<ol>')
for r in RED: A('<li>%s</li>' % r)
A('</ol>')

# 九
A('<h2>九、⬜ 待本人确认</h2>')
A('<ul>')
for t in TODO: A('<li>%s</li>' % t)
A('</ul>')

A('<footer>')
A('数据源：<code>index.sqlite</code> · <code>contact.db</code>（含 <code>chatroom_member</code> / <code>contact_label</code>）· '
  '<code>sns/sns.db</code> · 解密原始库 <code>message_*.db</code> · WeFlow 全量导出（725 私聊 JSON）—— 全部本地只读<br>')
A('引擎裁定：<code>05-纠偏层.md</code> 三·补·67 ｜ <code>04-人际地图.md</code> 第八类关系（本科圈）｜ 分析库：事件 2,867 / 证据 5,470')
A('</footer>')

A('</div>')
A('</body>')
A('</html>')

html_out = '\n'.join(H)
bad = 0
for tag in ('html','head','body','table','div','tr','td','th','ul','ol','li','header','footer','h1','h2','h3','p','span','i','b','code'):
    o = len(re.findall(r'<%s[\s>]' % tag, html_out))
    c = len(re.findall(r'</%s>' % tag, html_out))
    if o != c:
        print('!! 标签不配对 %s: open=%d close=%d' % (tag, o, c)); bad += 1
print('标签校验完成', '（全部配对）' if bad == 0 else '（%d 处异常）' % bad)
io.open(OUT, 'w', encoding='utf-8', newline='').write(html_out)
print('HTML ->', OUT, len(html_out.encode('utf-8')), 'bytes')
