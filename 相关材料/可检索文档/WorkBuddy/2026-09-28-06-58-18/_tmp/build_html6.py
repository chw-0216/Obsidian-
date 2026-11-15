# -*- coding: utf-8 -*-
import io, os, re, html

WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
OUT = os.path.join(WS, '朋友圈与追求路径_2026-10-13.html')

def esc(t): return html.escape(str(t), quote=False)
def md(t):
    t = esc(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    return t

H = []; A = H.append
A('<!DOCTYPE html>')
A('<html lang="zh-CN"><head><meta charset="utf-8">')
A('<meta name="viewport" content="width=device-width,initial-scale=1">')
A('<title>「她们把我朋友圈关了」— 实测与路径 · 2026-10-13</title>')
A('''<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1b1e23;--sub:#5b6472;--line:#e3e6ea;
--acc:#1F3D2B;--acc2:#2f6b4a;--warn:#9E3B2E;--gold:#8a6d1f;--soft:#f0f4f1;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.75 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;}
.wrap{max-width:960px;margin:0 auto;padding:32px 22px 72px}
header{border-bottom:3px solid var(--acc);padding-bottom:18px;margin-bottom:26px}
h1{margin:0 0 8px;font-size:25px;letter-spacing:.3px}
.sub{color:var(--sub);font-size:13.5px}
h2{margin:34px 0 14px;font-size:19px;padding-left:11px;border-left:5px solid var(--acc);}
h3{margin:22px 0 10px;font-size:16px;color:var(--acc)}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:18px 20px;margin:14px 0;box-shadow:0 1px 2px rgba(20,30,40,.04)}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13.5px}
th,td{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600;color:var(--acc)}
code{background:#eef1f4;padding:1px 5px;border-radius:4px;font-size:12.5px;
font-family:"SFMono-Regular",Consolas,monospace}
.note{background:#fdf8ee;border-left:4px solid var(--gold);padding:12px 16px;
border-radius:0 8px 8px 0;margin:12px 0;font-size:13.5px}
.warn{background:#fdf1ef;border-left:4px solid var(--warn);padding:12px 16px;
border-radius:0 8px 8px 0;margin:12px 0;font-size:13.5px}
.key{background:var(--soft);border-left:4px solid var(--acc);padding:12px 16px;
border-radius:0 8px 8px 0;margin:12px 0;font-size:14.5px}
ul,ol{padding-left:22px;margin:10px 0}
li{margin:6px 0}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}
.kpi div{flex:1;min-width:140px;background:var(--card);border:1px solid var(--line);
border-radius:10px;padding:14px 16px}
.kpi b{display:block;font-size:20px;color:var(--acc);margin-bottom:2px}
.kpi span{font-size:12.5px;color:var(--sub)}
.bar{height:14px;background:var(--acc2);border-radius:3px;display:inline-block;vertical-align:middle}
.barw{background:#e8ebee;border-radius:3px;display:block;height:14px}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);
color:var(--sub);font-size:12.5px}
</style></head><body><div class="wrap">''')

A('<header>')
A('<h1>「她们把我朋友圈关了」—— 实测与路径</h1>')
A('<div class="sub">2026-10-13 · 自我理解引擎 第 70 号裁定 · 承 <code>05</code> 三·补·69</div>')
A('</header>')

A('<h2>一、先说一件反直觉的事</h2>')
A('<div class="key">你说「她们都把我朋友圈关了」，但数据查下来：'
  '<b>在「关」之前，她们本来就几乎不发朋友圈。</b></div>')
A('<div class="kpi">')
A('<div><b>8 帖</b><span>李紫懿（2 年）· 末 2025-12-03</span></div>')
A('<div><b>3 帖</b><span>朱子涵（2 年）· 末 2025-12-23</span></div>')
A('<div><b>0 次</b><span>她们点赞你（44 帖全查）</span></div>')
A('</div>')
A('<p>所以「关了」这个动作的<b>信息量，比你的直觉小得多</b> —— 你看到的空白，'
  '很可能大部分是因为<b>她们本来就不发</b>，不是专门针对你。</p>')

A('<h2>二、先分清「关了」是哪一种</h2>')
A('<table><tr><th>可能</th><th>含义</th><th>要不要反应</th></tr>')
A('<tr><td><b>A. 仅三天 / 一个月可见</b></td><td>对<b>所有人</b>生效</td><td><b>不是针对你</b> → 不用反应</td></tr>')
A('<tr><td><b>B. 不让他（你）看我的</b></td><td>针对你单设</td><td>是边界信号 → 要处理</td></tr>')
A('<tr><td><b>C. 她本来就不发</b></td><td>无信号</td><td>不用反应</td></tr>')
A('</table>')
A('<div class="warn"><b>这条只能你自己看</b> —— 微信的「不让他看我的朋友圈」是<b>纯服务端设置</b>，'
  '不落地到本地库。我查了三处（<code>contact.extra_buffer</code> 权限字段 / '
  '<code>SnsUserTimeLineBreakFlagV2</code> / 全文搜「屏蔽·拉黑·三天可见」）'
  '<b>全部零命中或零区分度</b> —— 所以这条<b>以你在手机上看到的为准</b>。</div>')

A('<h2>三、★★★ 实测：点赞是完全单向的</h2>')
A('<table><tr><th>方向</th><th>次数</th><th>明细</th></tr>')
A('<tr><td><b>你 → 她们</b></td><td><b>6</b></td>'
  '<td>李紫懿 <b>5 帖</b>（2025-10-10 / 10-26 / 11-15 / 11-22 / 12-03）· 朱子涵 <b>1 帖</b>（2025-09-20）</td></tr>')
A('<tr><td><b>她们 → 你</b></td><td><b>0</b></td>'
  '<td>你 44 条帖子，点赞里「榕」0 · 「001」0（截至 2026-07-23）</td></tr>')
A('</table>')
A('<div class="note"><b>唯一例外：</b>朱子涵在 <b>2026-08-27 23:50 主动点赞过你一次</b>'
  '（本地库 <code>SnsMessage_tmp3</code> 实证）。这是<b>两年里她唯一一次反向动作</b>，'
  '而且发生在私聊断了 7 个月之后 —— <b>这条比什么都值钱</b>。</div>')

A('<h2>四、李紫懿：窗口曾经开过一次</h2>')
A('<p>她 8 条帖子里，<b>6 条集中在 2025-10 → 12 这三个月</b>，而<b>你全部点了赞</b>。'
  '同期私聊也在高位：</p>')
A('<table><tr><th>月份</th><th>私聊条数</th><th></th></tr>')
for m, t in [('2025-09',438),('2025-10',206),('2025-11',223),('2025-12',147),
             ('2026-01',85),('2026-02',2),('2026-03',11),('2026-05',11),('2026-10',23)]:
    w = int(t/438*260)
    A('<tr><td>%s</td><td>%d</td><td><span class="barw"><span class="bar" style="width:%dpx"></span></span></td></tr>' % (m,t,max(w,2)))
A('</table>')
A('<div class="key">★ <b>2025-10~12 是李紫懿线的唯一高峰</b>（她发帖 + 你点赞 + 私聊高位三件事同时发生）。'
  '<b>2026-02 断崖</b>之后，剩下的 1,146 条里再也没有那个质地 —— 全是班务。</div>')

A('<h2>五、两条线的真实质地</h2>')
A('<table><tr><th>线</th><th>现状</th><th>关键事实</th></tr>')
A('<tr><td><b>李紫懿</b></td><td><b>纯事务</b></td>'
  '<td>1,146 条<b>全是班务</b>（考勤/分组/汇报/投票）· 她叫你「<b>班长</b>」· 你叫她「<b>李姐</b>」· '
  '<b>她从未点赞过你的朋友圈</b> · 2025-11-15 你约饭<b>被婉拒</b>（「和室友有约」）</td></tr>')
A('<tr><td><b>朱子涵</b></td><td><b>事务 + 一个活信号</b></td>'
  '<td>45 条全事务（统计/收作业/要票）· 私聊断 <b>7 个月</b>（末 2026-03-17）· '
  '★ <b>但 2026-08-27 她主动点赞过你</b></td></tr>')
A('</table>')
A('<p class="sub">「李姐」「班长」这两个称呼本身就说明问题 —— 互相把对方放在<b>平级客气的位子</b>上，不是暧昧位。</p>')

A('<h2>六、★★★ 最大的坑：她们同班</h2>')
A('<div class="warn">'
  '<p><b>研一班级 29 人，两人同班。</b></p>'
  '<p>引擎里记着一条机制：你过去能在不同圈子维持不同版本的身份，靠的是「<b>没人核对</b>」。'
  '但在一个 29 人的班里，<b>核对是默认行为</b>。</p>'
  '<p>所以：<b>同时对两人采取行动 → 被发现是时间问题，不是概率问题。</b></p>'
  '<p>⚠️ 而且<b>不要</b>把「身份先行」那套（编身份 / 抬高身份）用在这里 —— '
  '同班场景会<b>当场撞破</b>，代价比在陌生人圈子大得多。</p>'
  '</div>')

A('<h2>七、怎么办（我只给事实和风险，决定权在你）</h2>')
A('<div class="card"><ol>')
A('<li><b>朋友圈这条路，投入产出极低。</b> 她们不发，你点赞是单机游戏 —— '
  '<b>不要再把精力放在刷和点赞上</b>。</li>')
A('<li><b>朱子涵是唯一还有活信号的。</b> 她 8-27 主动点过你 → 这是<b>自然的回访由头</b>；'
  '但 7 个月私聊空白，需要一个<b>不像「在吗」的接触理由</b>。</li>')
A('<li><b>李紫懿需要「非事务接触」。</b> 现有 1,146 条全部事务性 —— '
  '缺的是<b>一个私人场景</b>，而这件事比朱子涵那条难。</li>')
A('<li><b>同班风险必须先想清楚。</b> 这是这份材料里最硬的一条。</li>')
A('<li><b>追谁、要不要追，由你定。</b> 系统不替你选。</li>')
A('</ol></div>')

A('<h2>八、红线（本节）</h2>')
A('<div class="warn"><ol>')
A('<li>「她们把我朋友圈关了」是<b>你的自述</b> → 本地库无字段可证，不写成数据结论。</li>')
A('<li>「我想泡」＝<b>意图</b>，不是关系事实。</li>')
A('<li>不替你决定追谁 / 选谁。</li>')
A('<li>不建议「同时推进」，也不建议「放弃」。</li>')
A('<li>朱子涵性别库内仍未确证。</li>')
A('<li><b>private</b> —— 不进公考隔离区、不进对外材料。</li>')
A('</ol></div>')

A('<footer>生成于 2026-10-13 · 自我理解引擎 · 数据全程本地处理<br>'
  '本节 private · 与公考隔离区不互通</footer>')
A('</div></body></html>')

html_out = '\n'.join(H)
bad = 0
for tag in ('html','head','body','table','div','tr','td','th','ul','ol','li','header','footer',
            'h1','h2','h3','p','span','style','code','b'):
    o = len(re.findall(r'<%s[\s>]' % tag, html_out))
    c = len(re.findall(r'</%s>' % tag, html_out))
    if o != c:
        print('!! 不配对 %s: %d/%d' % (tag, o, c)); bad += 1
print('标签不配对:', bad)
print('h2:', re.findall(r'<h2[^>]*>(.*?)</h2>', html_out, re.S))
io.open(OUT, 'w', encoding='utf-8', newline='').write(html_out)
print('HTML ->', OUT, len(html_out.encode('utf-8')), 'bytes')
