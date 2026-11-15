# -*- coding: utf-8 -*-
import io, os, shutil, sys, html
sys.stdout.reconfigure(encoding='utf-8')
WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
OUT = os.path.join(WS, '本科圈同步_李博文与周雯娟_2026-10-11.html')

# 1) 转写文本落地
src = os.path.join(WS, '_tmp', 'lbowen_full.txt')
dst = os.path.join(WS, '李博文_私聊全量_2026-10-11.txt')
shutil.copyfile(src, dst)
print('transcript ->', dst, os.path.getsize(dst), 'bytes')

# 2) 时间轴数据
TL = [
 ("2025-03-28", "爆发 · 第 1 天", "邀约版画/微喷 · 「来央美一趟」「我带你」「材料费我出了」「你来当我学生吧」", "他 214 条里的主体"),
 ("2025-03-29", "爆发 · 第 2 天", "改约 → 电话 → 称呼「**博文姐**」", "—"),
 ("2025-03-30", "爆发 · 第 3 天", "**线下见面成立**：他开车到东城（后永康胡同）→「你要包子吗」", "★ 唯一一次线下"),
 ("2025-03-31", "爆发 · 第 4 天", "爵士乐邀约 · 「顺便把你卡给你」· 她讲体制内（科员/科长/处级）→ 他回「只要科员够少，科长就是我的兵」", "★ 双向都在往下定性"),
 ("2025-04-01~02", "爆发 · 收尾", "扫描完成 → 「明天就给你发文件」", "事务闭环"),
 ("2025-04-02 → 2026-07-21", "★★ 466 天空窗", "零条消息", "—"),
 ("2026-07-21", "回访 · 16 分钟", "京郊民宿商业街开业「**主要是拉人头**」→ 她以「下雨要值班」推掉 → 他连说三次「打扰了」「上次抱歉弄着弄着就弄忘了」", "★ 他自陈动机"),
]

LIKES = [
 ("2025-07", "2.8%", "起点（此前 0）"), ("2025-08", "10.5%", ""), ("2025-09", "18.0%", ""),
 ("2025-10", "12.2%", ""), ("2025-11", "12.1%", ""), ("2025-12", "11.0%", ""),
 ("2026-01", "12.0%", ""), ("2026-02", "13.6%", ""), ("2026-03", "16.4%", ""),
 ("2026-04", "29.8%", "★ 峰值"), ("2026-05", "20.0%", ""), ("2026-06", "28.6%", ""), ("2026-07", "15.3%", ""),
]

GAPS = [
 ("他的点赞动作", "★ 本地库**结构性取不到** —— `SnsMessage_tmp3`（274 行）只记「**别人点赞他**」（`to_username=本人`），不记他点赞别人。", "只能按本人自述记 `user_report`"),
 ("两人帖子的正文/图片", "`SnsTimeLine`（304 行）**无「环球 / 影城 / 哈利」任何命中**；WeFlow 实时接口 `usernames=周雯娟 / 李博文` 返回 **`count:0`**（而刘华赞 19 条 / 陈昶文 2 条正常）。", "**不得**描述内容"),
 ("李博文 10-11 是否有帖", "本地 feed 31 条，最新 **2026-10-10 09:07**。可能 ① 她今天没发 ② 本地 feed 未刷新。", "只记「**未观测到**」，**不记「没发」**"),
]

IDENT = [
 ("本科 2017–2021", "**冒充官二代** → 「有些占领位置关系」", "★ **本人 2026-10-11 自述**", "his"),
 ("2025-04-09", "朋友圈：「路上冒犯的大叔，**其实我不是学法的**，但是确实下次不该这么讹你」", "★ 他自己发的帖", "his"),
 ("2026-05-01", "朋友圈：「重生之黑道班主任短期体验卡 … **五一假期冒名版**」", "★ 同上", "his"),
 ("2025-03-28", "对李博文：「**有个备选学位**，混的不好就去了」", "本轮聊天全文", "his"),
 ("2026-10-04", "母亲署名：「**不知道，我自己办的**」", "`05` 三·补·19 八", "other"),
]

def esc(t):
    return html.escape(t, quote=False)

def md(t):
    t = esc(t)
    # **bold**
    import re
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`(.+?)`', r'<code>\1</code>', t)
    return t

H = []
A = H.append
A('<!DOCTYPE html>')
A('<html lang="zh-CN">')
A('<head>')
A('<meta charset="utf-8">')
A('<meta name="viewport" content="width=device-width,initial-scale=1">')
A('<title>本科圈同步 · 李博文与周雯娟 · 2026-10-11</title>')
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
A('table{width:100%;border-collapse:collapse;background:var(--card);margin:14px 0;font-size:14px;border:1px solid var(--line)}')
A('th,td{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}')
A('th{background:#eef1f3;font-weight:600;color:#2a2f36}')
A('code{background:#eef1f3;padding:1px 5px;border-radius:3px;font-size:13px;font-family:Consolas,Monaco,monospace}')
A('.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:18px 20px;margin:16px 0}')
A('.kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:18px 0}')
A('.kpi div{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:14px 16px}')
A('.kpi .n{font-size:23px;font-weight:700;color:var(--acc);display:block;line-height:1.3}')
A('.kpi .l{font-size:12.5px;color:var(--sub)}')
A('.hi{background:#fdf6f4;border-left:4px solid var(--warn);padding:12px 16px;margin:14px 0;border-radius:0 5px 5px 0}')
A('.ok{background:#f3f7f4;border-left:4px solid var(--acc);padding:12px 16px;margin:14px 0;border-radius:0 5px 5px 0}')
A('.gold{background:#fdfaf0;border-left:4px solid var(--gold);padding:12px 16px;margin:14px 0;border-radius:0 5px 5px 0}')
A('.tag{display:inline-block;font-size:12px;padding:1px 8px;border-radius:10px;border:1px solid var(--line);background:#fff;color:var(--sub);margin-right:5px}')
A('.tag.r{color:var(--warn);border-color:#e8cfc9;background:#fdf6f4}')
A('.tag.g{color:var(--acc);border-color:#cfe0d5;background:#f3f7f4}')
A('.tag.y{color:var(--gold);border-color:#e8dfc0;background:#fdfaf0}')
A('ul{margin:10px 0;padding-left:22px}li{margin:5px 0}')
A('.bar{display:flex;align-items:center;gap:9px;margin:4px 0;font-size:13px}')
A('.bar .lb{width:74px;color:var(--sub);flex:none}')
A('.bar .tr{flex:1;background:#eceff2;height:15px;border-radius:3px;overflow:hidden}')
A('.bar .fl{height:100%;background:var(--acc)}')
A('.bar .vl{width:52px;text-align:right;flex:none;color:var(--sub)}')
A('footer{margin-top:52px;padding-top:18px;border-top:1px solid var(--line);color:var(--sub);font-size:12.5px;line-height:1.9}')
A('@media(max-width:640px){.wrap{padding:24px 14px 60px}h1{font-size:21px}table{font-size:13px}}')
A('</style>')
A('</head>')
A('<body><div class="wrap">')

A('<header>')
A('<h1>本科圈同步 · 李博文与周雯娟</h1>')
A('<div class="meta">')
A('触发：本人 2026-10-11 21:09「刚刚周文娟和李博文去了环球影城，拍照发了朋友圈，<b>我在本科冒充过官二代所以有些占领位置关系</b>，帮我同步，刚刚给她俩都点赞了，还有之前和李博文的聊天记录也同步一下吧」<br>')
A('数据源：<code>contact.db</code> · <code>sns/sns.db</code> · <code>index.sqlite</code> · 朋友圈全量导出（2026-07-23）｜ 全程本地只读 · 生成 2026-10-11 21:40')
A('</div>')
A('</header>')

# KPI
A('<div class="kpi">')
for n, l in [('114 人', '通讯录「城院」标签 —— 本科圈首次识别'),
             ('249 条', '李博文私聊全量（已读透）'),
             ('466 天', '李博文线空窗期'),
             ('0 条', '周雯娟消息层记录'),
             ('473 / 3534', '他点赞过的帖子（13.4%）')]:
    A('<div><span class="n">%s</span><span class="l">%s</span></div>' % (n, l))
A('</div>')

# 1
A('<h2>一、本轮同步了三件事</h2>')
A('<table><tr><th style="width:30%">事</th><th>状态</th></tr>')
A('<tr><td>① 两人今天去环球影城 · 发圈</td><td>✅ 记入（<span class="tag y">本人自述</span>）· 周雯娟 16:16 有帖 ✅ 本地库实证</td></tr>')
A('<tr><td>② 他给两人点赞</td><td>⚠️ 记入但只能标 <span class="tag y">user_report</span> —— <b>本地库结构性取不到他的点赞动作</b></td></tr>')
A('<tr><td>③ 李博文聊天记录同步</td><td>✅ <b>249 条全文回捞并读透</b> → <code>李博文_私聊全量_2026-10-11.txt</code></td></tr>')
A('</table>')

# 2
A('<h2>二、★★★ 「城院」＝ 首经贸城市学院 —— 本科圈首次识别</h2>')
A('<p>通讯录标签 <code>37=城院</code> 共 <b>114 人</b>，此前引擎<b>从未识别</b>这个圈。定位靠<b>群名实证</b>（不是推断）：</p>')
A('<table><tr><th style="width:36%">来源</th><th>名称</th></tr>')
A('<tr><td><code>4654460826@chatroom</code></td><td><b>「18级首经贸城院公管新生闲聊答疑」</b></td></tr>')
A('<tr><td><code>18144316201@chatroom</code></td><td><b>「🎓2021届城院毕业生通知群」</b></td></tr>')
A('<tr><td><code>20859882417@chatroom</code></td><td>「🦆🐛2021届城院烤鸭群!」</td></tr>')
A('<tr><td><code>gh_3e4e976dedb6</code> / <code>gh_d5fb5626efe1</code></td><td>「城院人」/「城院分团委」</td></tr>')
A('</table>')
A('<div class="ok"><b>→ 城院 ＝ 首都经济贸易大学城市经济与公共管理学院</b>（与 <code>01</code> 的「区域经济学」方向一致）<br>')
A('<b>→ 2021 届毕业 → 本科圈 ＝ 2017–2021</b>，与 <code>07</code> 的 P1 阶段吻合<br>')
A('★ <b>交叉验证</b>：<code>04</code> 已记「程颂孟秋 ＝ 前本科室友」—— 他<b>带 <code>37=城院</code> 标签</b> ✓ 自洽</div>')
A('<div class="hi">⚠️ <b>修正一条旧结论</b>：<code>05</code> 三·补·22 记「2017–2024 的人<b>现在都不联系了</b>」→ <b>需修正</b>：不是「没有」，是<b>没有被识别出来</b> —— 114 人躺在通讯录里，标签就写着「城院」。</div>')
A('<p><b>圈内已知成员</b>（带 <code>37=城院</code> 者 114 人，此处只列引擎已认识的）：</p>')
A('<p><span class="tag">程颂孟秋</span><span class="tag">李博文</span><span class="tag">周雯娟</span><span class="tag">马腾</span><span class="tag">贾甲</span><span class="tag">尹诗琪</span><span class="tag">苏童</span><span class="tag">田浩然</span><span class="tag">王瑞霖</span><span class="tag">谭瑶</span><span class="tag">朱冰淇</span><span class="tag">李坤琪</span><span class="tag">顾家麟</span><span class="tag">裴青青</span><span class="tag">程思卓</span> …</p>')
A('<p>另：<code>49=3班</code> <b>24 人</b>，与城院圈部分重叠（<b>李博文 ＝ 3班 + 城院</b>）。</p>')

# 3
A('<h2>三、★★ 李博文线复核（249 条全文已读）</h2>')
A('<table><tr><th style="width:22%">项</th><th>值</th></tr>')
A('<tr><td>身份</td><td><b>本科同学（首经贸城院 · 3班）</b> · 现<b>体制内在职</b></td></tr>')
A('<tr><td>账号</td><td><code>wxid_4yurl8wrbi4a22</code> · 备注「李博文 城市学院」· 昵称 <code>bownbown</code> · alias <code>St-reborn</code></td></tr>')
A('<tr><td>结构</td><td>249 条 · 我 <b>179</b> / 她 <b>68</b> / system 2（<b>我发 72.4%</b>）· 2025-03-28 12:11 → 2026-07-21 21:06</td></tr>')
A('<tr><td>称呼</td><td>她叫他「<b>大哥</b>」· 他叫她「<b>博文姐</b>」</td></tr>')
A('</table>')
A('<h3>时间轴</h3>')
A('<table><tr><th style="width:19%">时间</th><th style="width:16%">阶段</th><th>内容</th><th style="width:16%">备注</th></tr>')
for d, ph, c, note in TL:
    A('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (esc(d), md(ph), md(c), md(note)))
A('</table>')
A('<h3>★★ 判定：与 <code>04</code> 现记「追求中（第二档）」不符 → 标 <span class="tag r">待复核</span></h3>')
A('<table><tr><th style="width:30%">检验（<code>wechat-data-forensics</code> §5.10）</th><th>实测</th></tr>')
A('<tr><td>我方推进信号</td><td><b>0</b>（无「喜欢你 / 女朋友 / 在一起 / 宝贝 / 老婆」类）</td></tr>')
A('<tr><td>她方推进信号</td><td><b>0</b></td></tr>')
A('<tr><td>邀约</td><td><b>有</b>（央美 / 爵士乐 / 京郊）—— 但<b>目的自陈为「拉人头」与「版画/微喷」</b></td></tr>')
A('<tr><td>定性词</td><td>她叫他「大哥」· 他叫她「博文姐」← <b>双向都往下定性</b></td></tr>')
A('<tr><td>亲密事实</td><td><b>0</b></td></tr>')
A('</table>')
A('<div class="ok"><b>数据侧读法</b>：<b>「央美社交货币 + 事务性邀约」</b>，不是情感推进。<br>')
A('与 <code>05</code> 三·补·26 记的「<b>社交货币 ＝ 带人看央美</b>」<b>完全同型</b> —— 他 2025-03 的话术（「来央美一趟」「我带你」「材料费我出了」「你来当我学生吧」）与对其他人一致。<br>')
A('★ 按 <code>65.6 红线 5</code>（<b>陈旧 ≠ 已错</b>）：<b>只标 <code>待复核</code>，不自动改。</b></div>')

# 4
A('<h2>四、周雯娟（本轮新增人物 · 库内零消息）</h2>')
A('<table><tr><th style="width:22%">项</th><th>值</th></tr>')
A('<tr><td>wxid</td><td><code>wxid_uhulgmrvfq4a12</code></td></tr>')
A('<tr><td>备注 / 昵称 / 微信号</td><td>周雯娟 / <b>Sora</b> / <code>sora4811</code></td></tr>')
A('<tr><td>标签</td><td><code>37=城院</code> + <code>107=全部</code></td></tr>')
A('<tr><td>消息层</td><td>★ <b>0 条</b> —— 无私聊、无群发言、正文提及 <b>0</b></td></tr>')
A('<tr><td>朋友圈</td><td><code>SnsTopItem_1</code> <b>1 条</b>：post ＝ <b>2026-10-11 16:16</b>（read 19:35）</td></tr>')
A('<tr><td>在他人朋友圈</td><td>2026-02-12 点赞<b>田浩然</b> · 2026-01-04 点赞<b>尹诗琪</b>（<b>与本人同场</b>）</td></tr>')
A('</table>')
A('<div class="ok"><b>读法：「通讯录里的人」</b> —— 加了、有标签、但<b>从未单独聊过一句</b>，只靠<b>朋友圈在场</b>维持。<br>')
A('<b>不计入人际投入，计入关系资产。</b>（与「母辈代维」<b>不同类</b>：那一类靠<b>备注特殊</b>，这一类靠<b>标签 + 朋友圈</b>。）</div>')
A('<div class="hi">⚠️ <b>本人写「周文娟」，通讯录为「周雯娟」＝ 同音字</b> → <b>以通讯录为准</b>。</div>')

# 5
A('<h2>五、★★ 本人自述：「本科冒充过官二代 → 有些占领位置关系」</h2>')
A('<p>这是本轮唯一由本人主动披露的新机制。★ <b>它不是孤例，是一个模式</b> —— 命名为 <b>「身份先行」</b>：</p>')
A('<table><tr><th style="width:16%">时间</th><th>事件</th><th style="width:22%">来源</th></tr>')
for t, e, s_, k in IDENT:
    A('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (esc(t), md(e), md(s_)))
A('</table>')
A('<div class="gold"><b>机制</b>：<b>先用一个更高的身份占住位置，再决定要不要兑现。</b><br>')
A('· 对<b>陌生人</b>：冒认（学法的人 / 黑道班主任 / 官二代）<br>')
A('· 对<b>有对价的机构</b>：未授权署名（母亲的推荐）<br>')
A('· 对<b>同龄人</b>：抬高备选项（「备选学位」）</div>')
A('<div class="hi"><b>⚠️ 四条边界（极重要）</b><br>')
A('① <b>「占领位置关系」是本人用语</b> → <b>不得</b>改写成「靠欺骗获得关系」—— 他自陈的是<b>机制</b>，不是<b>道德评价</b>。<br>')
A('② <b>不得读成「人品有问题」</b> —— 这是<b>资源约束下的位置策略</b>，与「先玩玩」（<code>01</code> 五·补·3）<b>同源</b>：<b>在什么都没有的时候，先占住一个能被看见的位置</b>。<br>')
A('③ <b>不得建议他「去坦白 / 去解释」</b> —— 等于让他拆掉自己在本科圈的唯一立足点。<br>')
A('④ <b>本节默认 private</b>，只留引擎层 —— 与公考隔离区<b>不互通</b>，<b>不得</b>进任何对外材料。</div>')

# 6
A('<h2>六、环球影城事件（2026-10-11）· 证据分级</h2>')
A('<table><tr><th style="width:34%">项</th><th>内容</th><th style="width:22%">证据等级</th></tr>')
A('<tr><td>两人去了环球影城</td><td>本人 21:09 口述</td><td><span class="tag y">user_report</span></td></tr>')
A('<tr><td>拍照发了朋友圈</td><td>同上</td><td><span class="tag y">user_report</span></td></tr>')
A('<tr><td><b>他给两人都点了赞</b></td><td>同上 —— ⚠️ <b>库内取不到</b></td><td><span class="tag y">user_report</span></td></tr>')
A('<tr><td>周雯娟今天有发帖</td><td><code>SnsTopItem_1</code> post ＝ <b>2026-10-11 16:16</b></td><td><span class="tag g">raw_record</span></td></tr>')
A('<tr><td>李博文今天有发帖</td><td>❌ 本地库最新为 <b>2026-10-10 09:07</b></td><td><span class="tag r">未观测到</span></td></tr>')
A('</table>')
A('<h3>⚠️ 三条必须写明的缺口</h3>')
A('<table><tr><th style="width:22%">缺口</th><th>说明</th><th style="width:22%">因此不得</th></tr>')
for a, b, c in GAPS:
    A('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (md(a), md(b), md(c)))
A('</table>')

# 7
A('<h2>七、★ 朋友圈点赞行为首次量化</h2>')
A('<p>数据源：<code>朋友圈导出_2026-07-23</code> —— <b>3,534 帖</b> · 2012-10-12 → 2026-07-23 · 每条含 <code>likes[]</code>（<b>他点赞别人的唯一可读来源</b>）。</p>')
A('<div class="kpi">')
for n, l in [('473 / 3,534', '他点赞过的帖子 ＝ 13.4%'), ('261 人', '点赞过的作者数'), ('44 条', '他自己发的帖（同一导出）')]:
    A('<div><span class="n">%s</span><span class="l">%s</span></div>' % (n, l))
A('</div>')
A('<h3>点赞率随时间单调上升</h3>')
for m, v, note in LIKES:
    w = float(v.strip('%')) / 30 * 100
    A('<div class="bar"><span class="lb">%s</span><span class="tr"><span class="fl" style="width:%.1f%%"></span></span><span class="vl">%s</span><span style="width:88px;color:#8a6d1f;font-size:12px">%s</span></div>' % (m, w, v, note))
A('<div class="ok">★ <b>2025-07 之前点赞率恒为 0</b> —— 与「他 2025-07 才真正开始用朋友圈」自洽。<br>')
A('与 <code>05</code> 三·补·32/33「真拐点 2025-09 央美入学」<b>方向一致，但起点更早（2025-07）</b>。</div>')
A('<h3>点赞 TOP 12</h3>')
A('<p>薛伟东 <b>21</b> · 章燕紫 11 · 栩栩 7 · Darwin 7 · 张哲铭 7 · <b><code>*</code>（刘华赞）7</b> · 罗文迪 7 · <b>刘丽萍（母亲）6</b> · 榆巷 6 · 李竞一 6 · momo 6 · 李润泽 6</p>')
A('<div class="ok">★ <b>母亲排第 8</b> —— 与 <code>09</code> 记的「母亲是朋友圈唯一稳定互动者」<b>双向印证</b>。<br>')
A('★ <b>薛伟东（21）是点赞第一名</b> —— 与 <code>04</code> 中距离表「朋友 · 1,091 条」一致。</div>')
A('<div class="hi">⚠️ <b>城院圈在他的点赞里只占 6 条</b>（尹诗琪 ×4 · 闫家睿 · 谭瑶）→ <b>不得</b>把「本科圈」读成他的朋友圈主力；<b>它是小圈，不是主圈</b>。</div>')

# 8
A('<h2>八、⚠️ 红线（本节）</h2>')
A('<ol>')
for x in ['<b>「冒充官二代」＝ 本人自述的机制</b> → 不得外传、不得进公考隔离区、<b>不得</b>建议他「去坦白」',
          '<b>李博文「追求中」只标 <code>待复核</code>，不自动改</b>（承 65.6-5「陈旧 ≠ 已错」）',
          '<b>他的点赞 ＝ <code>user_report</code></b>，本地库结构性取不到 → 不得写成 <code>raw_record</code>',
          '<b>两人帖子正文未取到</b> → <b>不得</b>描述内容；不得写「她发了什么照片」',
          '<b>李博文 10-11 无帖 ＝ 未观测</b> → 不得写成「她没发」',
          '<b>城院圈 114 人 ＝ 真人实名</b> → <b>仅本地</b>，不得进对外材料',
          '<b>周雯娟</b> 不得因「今天点赞了」升级为「关系升温」',
          '<b>李博文 2025-03-31 的「科员/科长/处级」是她的单位信息</b> → 不得外传']:
    A('<li>%s</li>' % x)
A('</ol>')

# 9
A('<h2>九、⬜ 待本人确认</h2>')
A('<table><tr><th style="width:46%">问题</th><th>为什么要问</th></tr>')
A('<tr><td><b>李博文的档位改不改？</b></td><td><code>04</code> 现记「追求中（第二档）」，数据侧读到「事务性 + 央美社交货币」→ 改还是不改</td></tr>')
A('<tr><td><b>周雯娟是怎么加的？</b></td><td>通讯录 <b>0 消息</b> → 何时、何场合</td></tr>')
A('<tr><td><b>「占领位置关系」具体指哪些？</b></td><td>现在还占着吗 —— 决定本科圈要不要单列一类</td></tr>')
A('<tr><td>2025-03-30 那次线下之后发生了什么？</td><td>库内<b>无记录</b>，随后即 466 天空窗</td></tr>')
A('</table>')

A('<h2>十、落盘清单</h2>')
A('<table><tr><th style="width:34%">层</th><th>落点</th></tr>')
for a, b in [('引擎 · 裁定层', '<code>05-纠偏层.md</code> 新增 <b>三·补·66</b>（8 小节）· 5847 → 6039 行'),
             ('引擎 · 人际层', '<code>04-人际地图.md</code> 新增 <b>本科圈（第八类关系）</b> · 修正李博文行 · 周雯娟入中距离表'),
             ('引擎 · 无人时层', '<code>09-无人时档案.md</code> 新增 <b>第六节 · 他点赞谁</b> · 刷新 4.4 数字'),
             ('分析库', '<code>analysis.sqlite</code>：人 <b>1876 → 1877</b> · 事件 <b>2864 → 2866</b> · 证据 <b>5463 → 5466</b>'),
             ('Obsidian', '新建 <code>周雯娟.md</code> · 修正 <code>李博文 城市学院.md</code> · 打通页 <b>三·补·66</b>'),
             ('工作区', '<code>李博文_私聊全量_2026-10-11.txt</code>（16.5 KB · 249 条）')]:
    A('<tr><td>%s</td><td>%s</td></tr>' % (a, b))
A('</table>')

A('<footer>')
A('数据主权：微信原始数据全程本地处理，未上传任何第三方。<br>')
A('证据分级：<span class="tag g">raw_record</span> 本地库可回链 · <span class="tag y">user_report</span> 本人自述 · <span class="tag r">未观测</span> 不写成「没发生」<br>')
A('生成 2026-10-11 21:40 · 引擎 <code>05</code> 三·补·66 · Obsidian 打通页 三·补·66')
A('</footer>')

A('</div></body></html>')

html_out = '\n'.join(H)

# 标签配对校验
import re
for tag in ('html', 'head', 'body', 'table', 'div', 'tr', 'td', 'th', 'ul', 'ol', 'li', 'header', 'footer', 'h1', 'h2', 'h3', 'p', 'span'):
    o = len(re.findall(r'<%s[\s>]' % tag, html_out))
    c = len(re.findall(r'</%s>' % tag, html_out))
    if o != c:
        print('!! 标签不配对 %s: open=%d close=%d' % (tag, o, c))
print('标签校验完成')

io.open(OUT, 'w', encoding='utf-8', newline='').write(html_out)
print('HTML ->', OUT, len(html_out.encode('utf-8')), 'bytes')
