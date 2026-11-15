# -*- coding: utf-8 -*-
import io, os, re, html

WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
OUT = os.path.join(WS, '中期汇报与婚恋意向_2026-10-13.html')

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
A('<title>中期汇报落地 · 汇报口径收缩 · 婚恋线新增两人 — 2026-10-13</title>')
A('''<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1b1e23;--sub:#5b6472;--line:#e3e6ea;
--acc:#1F3D2B;--acc2:#2f6b4a;--warn:#9E3B2E;--gold:#8a6d1f;--blue:#1f4e79;--soft:#f0f4f1;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.75 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;}
.wrap{max-width:1000px;margin:0 auto;padding:32px 22px 72px}
header{border-bottom:3px solid var(--acc);padding-bottom:18px;margin-bottom:26px}
h1{margin:0 0 8px;font-size:26px;letter-spacing:.3px}
.sub{color:var(--sub);font-size:13.5px}
h2{margin:36px 0 14px;font-size:19px;padding-left:11px;border-left:5px solid var(--acc);}
h3{margin:24px 0 10px;font-size:16px;color:var(--acc)}
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
border-radius:0 8px 8px 0;margin:12px 0;font-size:14px}
ul,ol{padding-left:22px;margin:10px 0}
li{margin:5px 0}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}
.kpi div{flex:1;min-width:150px;background:var(--card);border:1px solid var(--line);
border-radius:10px;padding:14px 16px}
.kpi b{display:block;font-size:21px;color:var(--acc);margin-bottom:2px}
.kpi span{font-size:12.5px;color:var(--sub)}
.bar{height:16px;background:var(--acc2);border-radius:3px;display:inline-block;vertical-align:middle}
.barw{background:#e8ebee;border-radius:3px;display:block;height:16px}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);
color:var(--sub);font-size:12.5px}
.tag{display:inline-block;background:var(--soft);color:var(--acc);border-radius:4px;
padding:1px 8px;font-size:12px;margin-right:5px}
.big{font-size:15px}
</style></head><body><div class="wrap">''')

# ---------- header ----------
A('<header>')
A('<h1>中期汇报落地 · 汇报口径收缩 · 婚恋线新增两人</h1>')
A('<div class="sub">2026-10-13 · 自我理解引擎 第 69 号裁定 · 承 <code>05</code> 三·补·59 / 66–68</div>')
A('</header>')

# ---------- 一 ----------
A('<h2>一、今天你说了四件事</h2>')
A('<div class="card"><ul class="big">')
A('<li><b>中期汇报已完成</b> —— 自评「估计给我的分还成」</li>')
A('<li><b>汇报材料删减</b> —— 「为了稳妥，我老师让我删去很多东西，<b>所有领导接待、北京台实习都删了</b>」</li>')
A('<li><b>朱子涵</b> —— 「出生在北京感觉还挺有钱的，可以考虑交往，感觉有可能」</li>')
A('<li><b>李紫懿</b> —— 「也有可能」</li>')
A('</ul></div>')

# ---------- 二 ----------
A('<h2>二、中期汇报（<code>三·补·59</code> 定档 → 本轮闭环）</h2>')
A('<div class="kpi">')
A('<div><b>10-13 13:00</b><span>研二综合测评汇报 · 已完成</span></div>')
A('<div><b>6 + 2 分钟</b><span>汇报 + 问答</span></div>')
A('<div><b>待出</b><span>官方结果（涉及评奖学金）</span></div>')
A('</div>')
A('<div class="warn"><b>口径提醒：</b>「估计给我的分还成」是<b>你的估分</b>，不是官方结果 —— '
  '记录里不会写成「已得分 / 已通过」。另外这轮汇报内容<b>是删减过的</b>，不是完整经历呈现。</div>')

# ---------- 三 ----------
A('<h2>三、★★★ 汇报口径收缩 ——「分圈版本管理」的减法侧</h2>')
A('<div class="key">你的原话：「我中期汇报<b>为了稳妥</b>，我老师<b>让我删去很多东西</b>，'
  '<b>所有领导接待、北京台实习都删了</b>」</div>')
A('<h3>被删的两类（素材侧可对应）</h3>')
A('<table><tr><th>素材包</th><th>内容</th><th>对应</th></tr>')
A('<tr><td><code>04_第五届美学与艺术研究学术研讨会会务</code></td>'
  '<td>2025-09-30 专家接待志愿者</td><td>「<b>领导接待</b>」</td></tr>')
A('<tr><td><code>07_北京广播电视台AIGC科研实习</code></td>'
  '<td>2026-01-07 → 02-12 北京台 AIGC 实习</td><td>「<b>北京台实习</b>」</td></tr>')
A('</table>')
A('<h3>★ 关键区分：加法 vs 减法</h3>')
A('<table><tr><th>模式</th><th>方向</th><th>性质</th><th>例</th></tr>')
A('<tr><td><b>身份先行</b>（<code>三·补·66.4</code>）</td><td><b>加法</b></td>'
  '<td><b>虚构</b></td><td>本科冒充官二代 · 「备选学位」· 对程颂孟秋说「读博」</td></tr>')
A('<tr><td><b>汇报口径收缩</b>（本节）</td><td><b>减法</b></td>'
  '<td><b>省略</b>（删的是<b>真事</b>）</td><td>删领导接待 · 删北京台实习</td></tr>')
A('</table>')
A('<div class="warn">两者同属「<b>分圈版本管理</b>」，但<b>性质不同</b>：一个是<b>虚构</b>，一个是<b>省略</b>。'
  '<br><b>不得混为一谈</b> —— 不能把「删掉北京台实习」读成「北京台实习是编的」。</div>')
A('<div class="note"><b>北京台 AIGC 实习是已确认事实</b>（USER.md 红线：2026-01-07 → 02-12）'
  '→ <b>删的是呈现，不是事实</b>。不得据「汇报材料里没有」反推「这件事没发生」。</div>')

# ---------- 四 ----------
A('<h2>四、★ 「领导接待」到底是什么（库内定位）</h2>')
A('<p>不是「接待领导」，是<b>学术研讨会的专家接待志愿者</b>。出处：</p>')
A('<div class="card">')
A('<p>2025-09-30 · <code>wxid_u240wu17qzc222</code>：</p>')
A('<ul><li>「hello蔡帅哥，你去<b>接待深圳的李心锋老师</b>可以吗」</li>')
A('<li>「让我找几个<b>靠谱的志愿者接待京外的老师</b>」</li>')
A('<li>「<b>刚刚陈晔老师说你还有别的工作，让你不接待了</b>」</li></ul>')
A('<p>2025-09-30 · <code>47952610494@chatroom</code>：「各位志愿者们…我会将<b>外校专家的接待事项</b>和分配发在群里」</p>')
A('</div>')

# ---------- 五 ----------
A('<h2>五、★★ 婚恋线新增两人（你主动提名）</h2>')
A('<div class="warn"><b>口径：</b>你说的全是<b>主观评估</b>（「感觉」「有可能」）→ 记录里按「<b>意向</b>」记，'
  '<b>不记关系事实</b>。<b>不与笑一线并列</b>，也不会读成「同时追三个」。</div>')
A('<table><tr><th>人</th><th>库内身份</th><th>消息量</th><th>你的判断（原话）</th></tr>')
A('<tr><td><b>朱子涵</b></td><td>研一 · 班级事务联络人</td><td>45（我发 36）</td>'
  '<td>「北京出生」「感觉还挺有钱」「可以考虑交往」</td></tr>')
A('<tr><td><b>李紫懿</b></td><td>研一 · 班委（同学叫你「班长」）</td><td><b>1,146</b>（我发 771）</td>'
  '<td>「也有可能」</td></tr>')
A('</table>')

# ---------- 六 ----------
A('<h2>六、朱子涵线（45 条全读）</h2>')
A('<table>')
A('<tr><th>wxid</th><td><code>wxid_utdeb3kw2z5j22</code></td></tr>')
A('<tr><th>备注 / 昵称 / 微信号</th><td>朱子涵 / <code>001</code> / <code>Johanne_001</code></td></tr>')
A('<tr><th>消息量 / 时间</th><td>45 条（我发 36 = 80%）· 2025-11-20 → 2026-03-17</td></tr>')
A('<tr><th>角色</th><td>★ <b>班级事务联络人</b></td></tr>')
A('</table>')
A('<h3>她（他）在群里/私聊里做的事</h3>')
A('<ul>')
A('<li>2025-11-20 爬山课程统计（「看看有谁去，大家都不去就和老师说不安全教学课程了」）</li>')
A('<li>2025-12-11 爱马仕大赛统计（「<b>系里让统计一下</b>」）</li>')
A('<li>2026-01-12 <b>收作业</b>（「作业要交了」「确实老师马上也放假了」「有点急！」）</li>')
A('<li>2026-03-17 要票</li>')
A('</ul>')
A('<p><b>调子 ＝ 事务性 + 客气</b>：全程敬语「打扰了」「抱歉打扰啦」· 称「<b>朱子涵同学</b>」。</p>')
A('<div class="note"><b>早于私聊的既有事件：</b>'
  '<b>2025-09-23 大使馆免费观影活动</b>（「管接送管饭」，<b>她/他邀请，你拒了</b>）→ <b>有资源</b>；'
  '2025-10-24 艺术创作灵感交流（栗子壳发光工艺）。</div>')
A('<div class="warn"><b>两个未确认：</b>① <b>性别库内未确证</b>（昵称 <code>Johanne</code> 偏女性名，但<b>不作判据</b>）；'
  '② 「北京出生 / 有钱」是<b>你的感觉</b>，库内无佐证 → 记「本人判断」，不写成事实。</div>')

# ---------- 七 ----------
A('<h2>七、李紫懿线（1,146 条全读）</h2>')
A('<table>')
A('<tr><th>wxid</th><td><code>wxid_f77sxlrwo0tr12</code></td></tr>')
A('<tr><th>备注 / 昵称 / 微信号</th><td>李紫懿 / <code>榕</code> / <code>Annyehuo3456</code></td></tr>')
A('<tr><th>消息量 / 时间</th><td><b>1,146 条</b>（我发 771 = 67%）· 2025-09-09 → 2026-10-08</td></tr>')
A('<tr><th>关系</th><td>研一同班 · <b>你任班委 / 同学叫你「班长」</b>（2025-09-11 她说「班长你的卡」）</td></tr>')
A('<tr><th>称呼</th><td>你叫她「<b>李姐</b>」· 她叫你「<b>班长</b>」/「浩文」</td></tr>')
A('</table>')
A('<h3>时间结构：开学即爆发 → 断崖 → 回访</h3>')
A('<table><tr><th>月份</th><th>条数</th><th>我</th><th>她</th><th></th></tr>')
MX = [('2025-09',438,264,174),('2025-10',206,138,68),('2025-11',223,155,68),
      ('2025-12',147,112,35),('2026-01',85,66,19),('2026-02',2,1,1),
      ('2026-03',11,8,3),('2026-05',11,8,3),('2026-10',23,19,4)]
for m,t,a,b in MX:
    w = int(t / 438 * 220)
    A('<tr><td>%s</td><td>%d</td><td>%d</td><td>%d</td>'
      '<td><span class="barw"><span class="bar" style="width:%dpx"></span></span></td></tr>' % (m,t,a,b,max(w,2)))
A('</table>')
A('<div class="key">★ <b>2025-09 开学即爆发 438 条</b> → 逐月递减 → <b>2026-02 断崖（2 条）</b> → '
  '零星 → <b>2026-10-08 回访 23 条</b>。</div>')
A('<h3>关键节点</h3>')
A('<table><tr><th>时间</th><th>事</th></tr>')
KN = [('2025-11-15','你约饭 → 她以「<b>和室友有约</b>」<b>婉拒</b>（她的边界）'),
      ('2025-12-19','<b>尖锐矛盾</b>（你因家事紧急求助贴海报，她身体不适需就医）'),
      ('2026-01-05','她生病，你：「<b>保护世上最好的李姐！</b>」（情感浓度高点）· 同日你「老人病重了」'),
      ('2026-05-29','她问「<b>你有挂科和处分吗</b>」→ 疑似帮做资格审查'),
      ('2026-10-08','<b>人大代表投票</b>（学院推「焦洋」）')]
for t,e in KN:
    A('<tr><td>%s</td><td>%s</td></tr>' % (t,e))
A('</table>')
A('<div class="warn"><b>红线：</b>「约饭被拒 + 室友有约」是<b>她的边界</b> → <b>不得读成「她有意」</b>。'
  '你的判断属<b>意向</b>，<b>不得</b>写成「已确立 / 双向」。</div>')

# ---------- 八 ----------
A('<h2>八、与既有婚恋线的关系</h2>')
A('<table><tr><th>线</th><th>状态</th></tr>')
A('<tr><td><b>笑一</b></td><td>现任 · 10-07 核心不满＝「说话做不到」→ 她要可验证的行动</td></tr>')
A('<tr><td>沐茜妍（林立娜）</td><td>09-16 由你终止</td></tr>')
A('<tr><td>柯益盈</td><td>你标注「可以结婚的对象」（高中圈外个体）</td></tr>')
A('<tr><td>孔新雅 / 小水</td><td>中距离婚恋候选</td></tr>')
A('<tr><td><b>朱子涵 / 李紫懿</b></td><td><b>★ 新增「意向层」</b> —— 不与上面并列，不读成「已决定换人」</td></tr>')
A('</table>')

# ---------- 九 ----------
A('<h2>九、红线（本节）</h2>')
A('<div class="warn"><ol>')
A('<li><b>中期汇报结果</b>：估分 ≠ 官方结果 → 不写成「已得分 / 已通过」。</li>')
A('<li><b>汇报口径收缩</b>：删的是<b>呈现</b>不是事实 → 不得据汇报材料反推「北京台实习不存在」。</li>')
A('<li>★ <b>「身份先行」（虚构）与「汇报收缩」（省略）性质不同</b>，不得混为一谈。</li>')
A('<li><b>朱子涵 / 李紫懿</b>：全部是<b>本人意向</b> → 不得写成关系事实。</li>')
A('<li>不得写成「候选人排名」，不得建议选谁。</li>')
A('<li>李紫懿「约饭被拒」是她的边界 → 不得读成「她有意」。</li>')
A('<li>朱子涵性别库内未确证 → 不得推断。</li>')
A('<li>「领导接待」＝ 会务志愿者，不得写成「接待领导 / 有领导资源」。</li>')
A('<li><b>private</b> —— 不进公考隔离区、不进对外材料。</li>')
A('</ol></div>')

# ---------- 十 ----------
A('<h2>十、需要你回答的</h2>')
A('<table><tr><th>#</th><th>问题</th><th>为什么问</th></tr>')
Q = [('G1','中期汇报正式结果出来了吗？','自评 ≠ 官方结果 · 涉及评奖学金'),
     ('G2','被删的素材还有哪些？','老师说「删去很多东西」→ 需要完整清单才能定边界'),
     ('G3','朱子涵 / 李紫懿档位怎么定？','现有档位不含她们 → 是「候选」还是「观察中」'),
     ('G4','朱子涵是女生吗？','库内无确证 · 影响后续全部记录口径'),
     ('G5','汇报分组结果？','1 组资料室 / 2 组讲堂（`三·补·59` 遗留）')]
for a,b,c in Q:
    A('<tr><td><b>%s</b></td><td>%s</td><td>%s</td></tr>' % (a, md(b), md(c)))
A('</table>')
A('<p class="sub">已并入 <code>Vault\\04_工作台\\信息需求单_20261009.md</code> G 档（唯一入口）。</p>')

# ---------- 落盘 ----------
A('<h2>十一、本轮落盘（10 处）</h2>')
A('<table><tr><th>层</th><th>内容</th></tr>')
LP = [('引擎 <code>05-纠偏层.md</code>','+<b>三·补·69</b>（6,462 行 / 460,627 B）'),
      ('引擎 <code>04-人际地图.md</code>','+<b>第九类关系 · 婚恋意向层</b>（636 行 / 50,823 B）'),
      ('<code>analysis.sqlite</code>','事件 <b>2,873</b>（+3）/ 证据 <b>5,483</b>（+6）· persons note 更新'),
      ('Vault 人物档案','<code>朱子涵.md</code>（4,208 B）· <code>李紫懿.md</code>（5,402 B）—— 修正过期数据 + 加意向块'),
      ('<code>MEMORY.md</code>','第 13 次维护：16,024 → <b>15,990 B</b>（15 节）· 新增 §十五 + 裁定 69 + 红线 20'),
      ('<code>00-真相源·数字基准.md</code>','已重跑（消息总量 394,601）'),
      ('<code>信息需求单_20261009.md</code>','+<b>G 档 5 条</b>'),
      ('当日日志 <code>2026-10-13.md</code>','新建（8,204 B）')]
for a,b in LP:
    A('<tr><td>%s</td><td>%s</td></tr>' % (a,b))
A('</table>')

A('<footer>生成于 2026-10-13 · 自我理解引擎 · 数据全程本地处理，未上传第三方<br>'
  '本节 <b>private</b> · 与公考隔离区不互通 · 不进对外材料</footer>')
A('</div></body></html>')

html_out = '\n'.join(H)

bad = 0
for tag in ('html','head','body','table','div','tr','td','th','ul','ol','li','header','footer',
            'h1','h2','h3','p','span','style','code','b'):
    o = len(re.findall(r'<%s[\s>]' % tag, html_out))
    c = len(re.findall(r'</%s>' % tag, html_out))
    if o != c:
        print('!! 标签不配对 %s: open=%d close=%d' % (tag, o, c)); bad += 1
print('标签不配对:', bad)
print('h2:', re.findall(r'<h2[^>]*>(.*?)</h2>', html_out, re.S))

io.open(OUT, 'w', encoding='utf-8', newline='').write(html_out)
print('HTML ->', OUT, len(html_out.encode('utf-8')), 'bytes')
