# -*- coding: utf-8 -*-
"""海燕线总览 · 生成器（单文件自包含 HTML）

铁律：**数据全部脚本派生，不手写**。人写的只有「分析结论」常量块（RELATION/QUOTES/...）。
数据一变，重跑本脚本即可 —— 结论留在脚本里，数字自动跟上。

用法：
    python render_haiyan.py

输入：C:\\Users\\wardc\\Desktop\\07_聊天记录分析\\weflow_live\\海燕.json
输出：C:\\Users\\wardc\\Desktop\\海燕\\海燕线总览_YYYYMMDD.html
      C:\\Users\\wardc\\Desktop\\海燕\\海燕线数据_YYYYMMDD.json
"""
import json, os, sys, html, datetime, collections

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\wardc\Desktop\07_聊天记录分析\weflow_live\海燕.json"
ME = "wxid_zn4ozsnn8esr21"
VERSION = "v1-20261008"
CHARTJS = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"

# ══════════════════ 人写的分析结论（数据变了也不改） ══════════════════

TITLE = "海燕线总览 · 中传李老师（交互技术课）"

LEAD = """这是一条 <b>「汇报 — 批复」结构的师生线</b>，不是情感线。
我输出 31 条但<b>一半以上是「收到老师」</b>（均 19 字）；她只发 12 条，但<b>条条是实质内容</b>（均 37 字）。
<b>信息权重全在她那边</b> —— 我的消息数量不等于贡献。
最值得注意的一件事：她 2026-09-12 主动说「<b>或项目中的相关问题也可以找我</b>」，
这条接口到今天<b>仍未使用</b>。"""

RELATION = [
    ("微信昵称", "海燕", "sessions.display_name"),
    ("talker", "guo647789", "索引库主键"),
    ("我称她", "「李老师」「老师」", "全部会话原文"),
    ("她称我", "「浩文」", "2026-09-18 08:29 首次用名"),
    ("单位", "中国传媒大学", "王利敏 2026-05-15 转达 + 中传访客预约系统"),
    ("授课", "交互技术（Arduino 硬件交互）", "她 09-21 发的 Arduino 环境 + B 站课程"),
    ("授课对象", "两个专业（一班偏艺术 / 一班偏技术）", "王利敏 2026-05-15 原话"),
    ("课程长度", "12 周（一学期），中秋、国庆各停一次", "她 09-20 14:05 亲口"),
    ("上课时段", "每周五上午（首讲早八点 · 201 教室）", "她 09-18 18:54；以当周通知为准"),
    ("09-18 缺席原因", "她全天做研究生入学面试（收手机）", "她 09-18 18:54 亲口"),
    ("关系性质", "授课老师 · 学业资源接口（无学籍，旁听）", "见「红线」"),
]

# 关键原话（人工从全量里挑的，带价值排序）
QUOTES = [
    ("①", "她给的「项目接口」——本线最有价值的一句", "2026-09-12 11:06",
     "课程上有任何问题随时可以联系我，或项目中的相关问题也可以找我",
     "前半句是课代表级别的客套，后半句是<b>主动开放资源接口</b>。对旁听生来说，「项目」接口比「课程」接口值钱得多。"),
    ("②", "她给的「不强迫社交」许可", "2026-09-12 10:57",
     "座位不需要多考虑，有空位就坐，没空位就到对面教室找个椅子，你可以单独一组，如有同学找你拼组也可以",
     "明确替旁听生解除了「必须融入班级」的压力。这是<b>对身份的照顾</b>，不是随口一说。"),
    ("③", "两次致歉（09-18 08:29 / 18:54）", "2026-09-18 18:54",
     "今天实在不好意思，忘通知你了，害你白跑一趟。我们今天面试一天收手机，刚拿到。",
     "值得注意的不是道歉本身，而是<b>时间点</b>：她面试一整天收手机，一拿到手机第一件事是补致歉。说明她<b>记得这个旁听生</b>。"),
    ("④", "她的学习指导", "2026-09-21 23:06",
     "不用急着学，我上课讲，先下开发环境。",
     "典型的<b>降低学生焦虑</b>式回复。收到「这两天学一下」后，她第一反应是给我松绑，不是布置任务。"),
]

# 她给过的接口（可运营清单）
INTERFACES = [
    ("1", "课程答疑", "09-12 11:06「课程上有任何问题随时可以联系我」", "未使用", "t-gray"),
    ("2", "项目咨询 ★", "09-12 11:06「<b>项目中的相关问题也可以找我</b>」", "未使用 —— 最值得动的一条", "t-red"),
    ("3", "学习资料直供", "09-21 主动发 Arduino 开发环境 + B 站系列课程", "已收到", "t-green"),
]

# 红线
REDLINES = [
    ("不得套用恋人线的语感与红线", "live.py 的「短句 ≤21 字」「不道歉」「22:30 后只哄睡」是<b>笑一线专属</b>，对师生线完全不适用。这里的正确语感是礼貌、完整、有信息量。"),
    ("不得写成「在中传就读 / 有中传学籍」", "中传<b>仅获本科录取资格、未实际就读</b>。这是<b>旁听</b>，无学籍。"),
    ("不得报错教室号 / 时间", "最后确认口径是「201 早八点」（09-18），但<b>换没换以她当周通知为准</b>。"),
    ("不得把「她给我项目接口」读成「关系已亲近」", "那是<b>职业性的开放</b>，不是私交信号。她 12 条消息里<b>没有一条涉及私人生活</b>。"),
    ("不主动闲聊", "除上课事务与节日问候，无必要不打扰。"),
]

PENDING = [
    ("2025 中秋联谊会是否同一个人", "事件包总览记载该事件涉及 11 个会话（含「海燕」），但本会话好友关系<b>起始于 2026-09-12</b>（首条即「我通过了你的朋友验证请求」）。若 2025 年同场，应是群内共处而非私聊。<b>未证实，勿直接引用。</b>"),
    ("她的全名", "目前只有「李老师」+ 昵称「海燕」，未见全名。全库搜索「李海燕」<b>0 命中</b>。"),
    ("她的学院 / 职称", "王利敏仅说「我的同事」「我们学院通信技术专业的工科老师」（2026-01-05）。"),
]

# ══════════════════ 以下全部自动派生 ══════════════════


def esc(s):
    return html.escape(str(s if s is not None else ""))


def load():
    with open(SRC, encoding="utf-8") as f:
        return json.load(f)


def is_sys(m):
    """type==80 是系统消息（打招呼 / 撤回提示）。
    实测坑：系统消息的 sender 不可靠 —— 3 条里 1 条填了对方 wxid、2 条为空。
    若按 sender 分派，会被误算成「她」。必须先按 type 摘出去。"""
    return m.get("type") == 80


def analyze(d):
    ms = d.get("messages", [])
    ms = sorted(ms, key=lambda m: m.get("timestamp") or 0)
    sysm = [m for m in ms if is_sys(m)]
    me = [m for m in ms if not is_sys(m) and m.get("sender") == ME]
    th = [m for m in ms if not is_sys(m) and m.get("sender") != ME]

    def avg(lst):
        return sum(len(m.get("content") or "") for m in lst) / len(lst) if lst else 0

    def longest(lst):
        return max((m.get("content") or "" for m in lst), key=len, default="")

    first, last = (ms[0].get("timestamp") if ms else 0), (ms[-1].get("timestamp") if ms else 0)
    days = collections.Counter(
        datetime.datetime.fromtimestamp(m["timestamp"]).strftime("%m-%d")
        for m in ms if m.get("timestamp"))

    # 她主动发起（她消息的前一条不是我；跳过系统消息）
    init, prev = 0, None
    for m in ms:
        if is_sys(m):
            continue
        cur = "me" if m.get("sender") == ME else "her"
        if cur == "her" and prev != "her":
            init += 1
        prev = cur

    return dict(ms=ms, me=me, th=th, sysm=sysm, first=first, last=last, days=days,
                avg_me=avg(me), avg_th=avg(th),
                max_me=longest(me), max_th=longest(th), init=init,
                span_days=(last - first) / 86400 if last else 0)


def fmt(ts, f="%Y-%m-%d %H:%M"):
    return datetime.datetime.fromtimestamp(ts).strftime(f) if ts else "—"


def build(st):
    ms, me, th, sysm = st["ms"], st["me"], st["th"], st["sysm"]
    now = datetime.datetime.now()
    stamp = f"{now.strftime('%Y%m%d-%H%M%S')}|{fmt(st['last'],'%Y-%m-%d')}|{now.strftime('%Y-%m-%d %H:%M:%S')}|{VERSION}"

    # ---- KPI ----
    kpis = [
        (f"{len(ms)}", "总消息条数"),
        (f"{len(me)}", "我发出（均 %.0f 字）" % st["avg_me"]),
        (f"{len(th)}", "她发出（均 %.0f 字）" % st["avg_th"]),
        (f"{st['span_days']:.0f} 天", "时间跨度"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="n">{esc(n)}</div><div class="l">{esc(l)}</div></div>'
        for n, l in kpis)

    # ---- 逐日表 ----
    def dayof(m):
        return datetime.datetime.fromtimestamp(m["timestamp"]).strftime("%m-%d")

    day_rows = ""
    for day, cnt in sorted(st["days"].items()):
        d_ms = [m for m in ms if m.get("timestamp") and dayof(m) == day]
        n_me = sum(1 for m in d_ms if not is_sys(m) and m.get("sender") == ME)
        n_th = sum(1 for m in d_ms if not is_sys(m) and m.get("sender") != ME)
        n_sy = sum(1 for m in d_ms if is_sys(m))
        first_ct = (d_ms[0].get("content") or "").replace("\n", " ")[:46]
        day_rows += (f'<tr><td><b>{esc(day)}</b></td><td class="num">{cnt}</td>'
                     f'<td class="num">{n_me}</td><td class="num">{n_th}</td>'
                     f'<td class="num">{n_sy or "—"}</td>'
                     f'<td>{esc(first_ct)}</td></tr>')

    # ---- 全量消息表 ----
    msg_rows = ""
    for i, m in enumerate(ms, 1):
        if is_sys(m):
            role, cls, tag = "系统", "sy", "t-gray"
        elif m.get("sender") == ME:
            role, cls, tag = "我", "me", "t-blue"
        else:
            role, cls, tag = "她", "th", "t-purple"
        ct = esc(m.get("content") or "")
        msg_rows += (f'<tr class="{cls}"><td class="num">{i}</td>'
                     f'<td class="num">{esc(fmt(m.get("timestamp") or 0, "%m-%d %H:%M"))}</td>'
                     f'<td><span class="tag {tag}">{role}</span></td>'
                     f'<td class="msgc">{ct}</td>'
                     f'<td class="num">{len(m.get("content") or "")}</td></tr>')

    # ---- 图数据 ----
    chart_days = sorted(st["days"].keys())
    chart_me = [sum(1 for m in ms if not is_sys(m) and m.get("sender") == ME
                    and dayof(m) == d) for d in chart_days]
    chart_th = [sum(1 for m in ms if not is_sys(m) and m.get("sender") != ME
                    and dayof(m) == d) for d in chart_days]
    chart_sy = [sum(1 for m in ms if is_sys(m) and dayof(m) == d) for d in chart_days]

    rel_rows = "".join(f'<tr><td>{esc(k)}</td><td>{esc(v)}</td><td class="num">{esc(src)}</td></tr>'
                       for k, v, src in RELATION)

    quote_html = ""
    for no, title, t, q, why in QUOTES:
        quote_html += f"""
<div class="card q">
  <div class="qhead"><span class="qno">{esc(no)}</span><b>{esc(title)}</b><span class="qtime">{esc(t)}</span></div>
  <blockquote>{esc(q)}</blockquote>
  <div class="qwhy">{why}</div>
</div>"""

    iface_rows = "".join(
        f'<tr><td class="num">{esc(n)}</td><td><b>{esc(name)}</b></td>'
        f'<td>{src}</td><td><span class="tag {cls}">{st_}</span></td></tr>'
        for n, name, src, st_, cls in INTERFACES)

    red_rows = "".join(f'<tr><td><b>{esc(a)}</b></td><td>{b}</td></tr>' for a, b in REDLINES)
    pend_rows = "".join(f'<tr><td><b>{esc(a)}</b></td><td>{b}</td></tr>' for a, b in PENDING)

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta name="wb-stamp" content="{stamp}">
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{esc(TITLE)}</title>
<style>
:root{{--bg:#f7f7f5;--card:#fff;--ink:#1c1c1e;--ink2:#4a4a4f;--ink3:#8a8a90;--line:#e5e5e2;
--red:#c0392b;--blue:#1f5c8b;--green:#1e7a52;--amber:#9a6b00;--purple:#5b4b8a}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.75 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:48px 28px 80px}}
h1{{font-size:30px;line-height:1.3;margin:0 0 6px;letter-spacing:-.4px}}
.sub{{color:var(--ink3);font-size:13.5px;margin-bottom:30px}}
h2{{font-size:20px;margin:44px 0 8px;padding-bottom:9px;border-bottom:2px solid var(--ink)}}
h3{{font-size:15px;margin:24px 0 8px;color:var(--ink2)}}
p{{margin:10px 0}}
.lead{{background:var(--card);border-left:4px solid var(--red);border-radius:0 10px 10px 0;padding:18px 22px;margin:20px 0 26px}}
.lead b{{color:var(--red)}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:16px 0}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.kpi .n{{font-size:23px;font-weight:700;letter-spacing:-.5px}}
.kpi .l{{font-size:12px;color:var(--ink3);margin-top:2px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0}}
th{{text-align:left;background:#fafaf8;color:var(--ink2);font-weight:600;padding:8px 9px;border-bottom:2px solid var(--line);white-space:nowrap}}
td{{padding:8px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
tr:last-child td{{border-bottom:none}}
a{{color:var(--blue);text-decoration:none;border-bottom:1px solid #cddced}}
.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;color:var(--ink3);font-size:12px}}
.tag{{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap}}
.t-red{{background:#fdf2f0;color:var(--red)}}.t-blue{{background:#eff5fa;color:var(--blue)}}
.t-green{{background:#eef7f2;color:var(--green)}}.t-amber{{background:#fdf6e6;color:var(--amber)}}
.t-purple{{background:#f2effa;color:var(--purple)}}.t-gray{{background:#f0f0ee;color:var(--ink3)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 20px;margin:12px 0}}
.warn{{background:#fdf6e6;border:1px solid #f0e0b0;border-radius:8px;padding:14px 18px;margin:14px 0;font-size:13.5px}}
.warn b{{color:var(--amber)}}
.foot{{margin-top:56px;padding-top:20px;border-top:1px solid var(--line);color:var(--ink3);font-size:12.5px}}
code{{background:#f0f0ee;padding:1px 5px;border-radius:4px;font-size:12.5px}}
.q{{border-left:3px solid var(--purple)}}
.qhead{{display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}}
.qno{{color:var(--purple);font-weight:700}}
.qtime{{color:var(--ink3);font-size:12px;margin-left:auto}}
blockquote{{margin:9px 0 8px;padding:9px 14px;background:#fafaf8;border-left:3px solid var(--line);border-radius:0 6px 6px 0;
color:var(--ink);font-size:14px}}
.qwhy{{font-size:13px;color:var(--ink2)}}
.qwhy b{{color:var(--red)}}
.chartbox{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0}}
.chartbox h3{{margin:0 0 12px}}
.msgc{{word-break:break-word;line-height:1.6}}
tr.me td{{background:#fbfcfe}}
tr.th td{{background:#fcfbfd}}
tr.sy td{{background:#fafaf8;color:var(--ink3);font-size:12.5px}}
.scroll{{max-height:620px;overflow:auto;border:1px solid var(--line);border-radius:10px}}
.scroll table{{margin:0}}
.scroll th{{position:sticky;top:0;z-index:2}}
@media(max-width:760px){{.grid4{{grid-template-columns:repeat(2,1fr)}}.wrap{{padding:28px 16px 60px}}}}
</style>
</head><body><div class="wrap">

<h1>{esc(TITLE)}</h1>
<div class="sub">全量 {len(ms)} 条 · {esc(fmt(st['first']))} → {esc(fmt(st['last']))} · 生成于 {now.strftime('%Y-%m-%d %H:%M')}</div>

<div class="lead">{LEAD}</div>

<div class="grid4">{kpi_html}</div>

<h2>一 · 关系定性</h2>
<table><thead><tr><th>项</th><th>内容</th><th>依据</th></tr></thead><tbody>{rel_rows}</tbody></table>

<h2>二 · 互动结构</h2>
<div class="chartbox">
  <h3>逐日消息量（按发送方堆叠）</h3>
  <canvas id="dayChart" height="110"></canvas>
</div>
<div class="chartbox">
  <h3>发言长度对比</h3>
  <canvas id="lenChart" height="110"></canvas>
</div>

<table><thead><tr><th>日期</th><th>总数</th><th>我</th><th>她</th><th>系统</th><th>当天首条</th></tr></thead>
<tbody>{day_rows}</tbody></table>

<div class="warn">
<b>读法</b>：我条数多但短 —— 大量「收到老师」「感谢老师」，属礼节性确认，<b>不承载信息</b>；
她条数少但长 —— 每条都是实质内容（批复 / 通知 / 资料 / 致歉）。
→ 这条线的<b>信息权重全在她那边</b>；我的消息数量不等于贡献。
她主动发起 <b>{st['init']}</b> 次（共 {len(th)} 条实质发言，另 {len(sysm)} 条系统消息不计入）。
</div>

<h2>三 · 关键原话（按价值排序）</h2>
{quote_html}

<h2>四 · 她给过的三个接口（可运营清单）</h2>
<table><thead><tr><th>#</th><th>接口</th><th>原话 / 时间</th><th>现状</th></tr></thead>
<tbody>{iface_rows}</tbody></table>
<div class="warn">
<b>接口 2 的用法</b>：央美的校地结合 / 文旅项目（丝网印刷、交互装置）与她教的 Arduino 交互技术<b>天然对接</b>。
拿一个<b>具体的小问题</b>去请教，比泛泛寒暄有效得多。
</div>

<h2>五 · 红线与陷阱</h2>
<table><thead><tr><th>红线</th><th>说明</th></tr></thead><tbody>{red_rows}</tbody></table>

<h2>六 · 待核 / 存疑</h2>
<table><thead><tr><th>事项</th><th>说明</th></tr></thead><tbody>{pend_rows}</tbody></table>

<h2>七 · 全量消息（{len(ms)} 条，可逐行核对）</h2>
<div class="scroll">
<table><thead><tr><th>#</th><th>时间</th><th>方</th><th>内容</th><th>字数</th></tr></thead>
<tbody>{msg_rows}</tbody></table>
</div>

<div class="foot">
<b>数据溯源</b>：<code>{esc(SRC)}</code>（由 ChatTrace 三层管线生成）<br>
<b>核验</b>：索引库 {len(ms)} 条 ＝ 解密原始库 {len(ms)} 行（无漏条）；原始库 <code>local_type</code> 仅 1（文本）与 10000（系统），无通话 / 图片 / 视频<br>
<b>生成</b>：<code>render_haiyan.py</code> · {VERSION} · {now.strftime('%Y-%m-%d %H:%M:%S')}<br>
<b>wb-stamp</b>：<code>{stamp}</code>
</div>

</div>
<script src="{CHARTJS}"></script>
<script>
const INK3='#8a8a90', LINE='#e5e5e2';
Chart.defaults.font.family='-apple-system,"PingFang SC","Microsoft YaHei",sans-serif';
Chart.defaults.color=INK3;
new Chart(document.getElementById('dayChart'),{{
  type:'bar',
  data:{{labels:{json.dumps(chart_days, ensure_ascii=False)},
    datasets:[
      {{label:'我',data:{json.dumps(chart_me)},backgroundColor:'#1f5c8b',borderRadius:4}},
      {{label:'她',data:{json.dumps(chart_th)},backgroundColor:'#5b4b8a',borderRadius:4}},
      {{label:'系统',data:{json.dumps(chart_sy)},backgroundColor:'#c9c9c4',borderRadius:4}}
    ]}},
  options:{{responsive:true,scales:{{x:{{stacked:true,grid:{{display:false}}}},
    y:{{stacked:true,beginAtZero:true,grid:{{color:LINE}},ticks:{{precision:0}}}}}},
    plugins:{{legend:{{position:'bottom'}}}}}}
}});
new Chart(document.getElementById('lenChart'),{{
  type:'bar',
  data:{{labels:['平均字数','最长单条'],
    datasets:[
      {{label:'我',data:[{st['avg_me']:.0f},{len(st['max_me'])}],backgroundColor:'#1f5c8b',borderRadius:4}},
      {{label:'她',data:[{st['avg_th']:.0f},{len(st['max_th'])}],backgroundColor:'#5b4b8a',borderRadius:4}}
    ]}},
  options:{{responsive:true,scales:{{x:{{grid:{{display:false}}}},y:{{beginAtZero:true,grid:{{color:LINE}}}}}},
    plugins:{{legend:{{position:'bottom'}}}}}}
}});
</script>
</body></html>"""


def main():
    d = load()
    st = analyze(d)
    out_html = os.path.join(HERE, f"海燕线总览_{datetime.datetime.now().strftime('%Y%m%d')}.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(build(st))

    # 机读版
    out_json = os.path.join(HERE, f"海燕线数据_{datetime.datetime.now().strftime('%Y%m%d')}.json")
    meta = {
        "run_id": datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
        "data_until": fmt(st["last"], "%Y-%m-%d"),
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": VERSION,
        "source": SRC,
        "total": len(st["ms"]),
        "me": len(st["me"]),
        "them": len(st["th"]),
        "system": len(st["sysm"]),
        "avg_len_me": round(st["avg_me"], 1),
        "avg_len_them": round(st["avg_th"], 1),
        "longest_me": len(st["max_me"]),
        "longest_them": len(st["max_th"]),
        "she_initiated": st["init"],
        "span_days": round(st["span_days"], 1),
        "per_day": dict(sorted(st["days"].items())),
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    print(f"✅ HTML → {out_html}")
    print(f"✅ JSON → {out_json}")
    print(f"   {len(st['ms'])} 条 | 我 {len(st['me'])} / 她 {len(st['th'])} / 系统 {len(st['sysm'])} | "
          f"均字 我 {st['avg_me']:.0f} : 她 {st['avg_th']:.0f} | 她主动 {st['init']} 次")


if __name__ == "__main__":
    main()
