# -*- coding: utf-8 -*-
"""render_events.py — 把 events_candidates.csv 渲染成可筛选的复核台 HTML。"""
import csv
import os
import sys
import html
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "events_candidates.csv")
OUT = os.path.join(HERE, "事件总览_复核台.html")

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
cat_cnt = Counter(r["类别"] for r in rows)
nat_cnt = Counter(r["性质"] for r in rows)
year_cnt = Counter((r["日期"] or "?")[:4] for r in rows)

CATS = ["学业/学术", "社交/见面", "项目/商务", "出行/迁移",
        "求职/职场", "生活/事务", "展演/创作", "比赛/活动"]

# 类别 × 年份
mat = {c: Counter((r["日期"] or "?")[:4] for r in rows if r["类别"] == c) for c in CATS}
years = ["2024", "2025", "2026"]


def esc(s):
    return html.escape(str(s or ""))


def cls_of(nat):
    return {"已完成": "n-done", "已发生": "n-done", "计划": "n-plan",
            "进行中": "n-run", "已取消": "n-cxl", "不确定": "n-unc"}.get(nat, "n-unc")


# 高条数事件（每类前 5）
top = []
for c in CATS:
    rs = sorted([r for r in rows if r["类别"] == c], key=lambda x: -int(x["条数"]))[:5]
    top += rs

trs = []
for r in rows:
    trs.append(
        f'<tr class="row" data-c="{esc(r["类别"])}" data-n="{esc(r["性质"])}">'
        f'<td class="d">{esc(r["日期"])}</td>'
        f'<td><span class="tag">{esc(r["类别"])}</span></td>'
        f'<td class="{cls_of(r["性质"])}">{esc(r["性质"])}</td>'
        f'<td class="ev">{esc(r["事件"])}</td>'
        f'<td class="who">{esc(r["对话人"])}</td>'
        f'<td class="n">{esc(r["条数"])}</td>'
        f'<td class="ck"></td></tr>'
    )

opts = "".join(f'<option value="{c}">{c}（{cat_cnt[c]}）</option>' for c in CATS)
nats = "".join(f'<option value="{n}">{n}（{nat_cnt[n]}）</option>' for n, _ in nat_cnt.most_common())

mat_rows = ""
for c in CATS:
    cells = "".join(f'<td>{mat[c].get(y,0) or ""}</td>' for y in years)
    mat_rows += f'<tr><th>{c}</th>{cells}<td class="tot">{cat_cnt[c]}</td></tr>'

top_rows = ""
for r in top:
    top_rows += (f'<tr><td class="d">{esc(r["日期"])}</td>'
                 f'<td><span class="tag">{esc(r["类别"])}</span></td>'
                 f'<td class="ev">{esc(r["事件"][:110])}</td>'
                 f'<td class="who">{esc(r["对话人"])}</td>'
                 f'<td class="n">{esc(r["条数"])}</td></tr>')

HTML = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>事件总览 · 复核台</title>
<style>
:root{{--ink:#1f2a33;--soft:#42505c;--mute:#6b7885;--paper:#faf8f4;--p2:#f2eee6;
--line:#e0dacd;--ls:#cfc6b4;--ac:#9e3b32;--blue:#2a4a63;--gr:#3b6d11;--gold:#8a6d3b;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;font-size:15px;line-height:1.75}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 26px 90px}}
header{{border-bottom:2px solid var(--ink);padding:54px 0 24px}}
.kick{{font-size:12px;letter-spacing:.3em;color:var(--ac);font-weight:700;margin-bottom:14px}}
h1{{font-family:"Songti SC",Georgia,serif;font-size:31px;margin:0 0 12px;font-weight:700}}
.sub{{font-family:"Songti SC",Georgia,serif;font-size:16px;color:var(--soft);margin:0 0 20px}}
.meta{{display:flex;gap:10px 24px;flex-wrap:wrap;font-size:12.5px;color:var(--mute);
border-top:1px solid var(--line);padding-top:14px}}
h2{{font-family:"Songti SC",Georgia,serif;font-size:21px;margin:48px 0 16px;padding-bottom:9px;
border-bottom:1px solid var(--ls)}}
h2 .n{{color:var(--ac);font-size:15px;margin-right:10px;font-family:Georgia,serif}}
.stats{{display:flex;flex-wrap:wrap;gap:12px;margin:22px 0}}
.st{{flex:1;min-width:120px;border:1px solid var(--line);border-radius:6px;padding:14px;background:#fff;text-align:center}}
.st .v{{font-family:Georgia,serif;font-size:26px;font-weight:700;color:var(--ac)}}
.st .l{{font-size:12px;color:var(--mute);margin-top:4px}}
table{{width:100%;border-collapse:collapse;font-size:13.2px;background:#fff;
border:1px solid var(--line);border-radius:6px;overflow:hidden}}
th,td{{padding:8px 11px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}
thead th{{background:var(--p2);font-size:12.4px;font-weight:700;border-bottom:1.5px solid var(--ls);white-space:nowrap}}
td.d{{white-space:nowrap;color:var(--mute);font-family:Consolas,monospace;font-size:12.4px}}
td.n{{text-align:right;font-family:Consolas,monospace;color:var(--mute)}}
td.who{{white-space:nowrap;color:var(--blue)}}
td.ev{{line-height:1.6}}
td.ck{{width:70px}}
.tag{{display:inline-block;padding:1px 8px;border-radius:20px;font-size:11px;font-weight:700;
background:#eef2f5;color:var(--blue);border:1px solid #dbe4ea;white-space:nowrap}}
.n-done{{color:var(--gr);font-weight:600}} .n-plan{{color:var(--gold)}}
.n-run{{color:var(--blue)}} .n-cxl{{color:var(--ac)}} .n-unc{{color:var(--mute)}}
.ctrl{{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:16px 0;padding:14px 16px;
background:#fff;border:1px solid var(--line);border-radius:6px;position:sticky;top:0;z-index:5}}
select,input{{padding:7px 11px;border:1px solid var(--ls);border-radius:5px;font-size:13.5px;
font-family:inherit;background:#fff;color:var(--ink)}}
input{{flex:1;min-width:180px}}
#cnt{{font-size:13px;color:var(--mute);margin-left:auto}}
.note{{background:#fff;border:1px solid var(--ls);border-left:4px solid var(--ac);
border-radius:0 6px 6px 0;padding:18px 22px;margin:22px 0;font-size:14px}}
.note p{{margin:0 0 10px}} .note p:last-child{{margin:0}}
.warn{{border-left-color:var(--gold)}}
.tot{{font-weight:700;color:var(--ac)}}
footer{{margin-top:60px;padding-top:20px;border-top:1px solid var(--line);font-size:12.5px;color:var(--mute);
display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}}
</style></head><body><div class="wrap">
<header>
<div class="kick">事件全量挖掘 · 待人工复核</div>
<h1>事件总览 · 复核台</h1>
<p class="sub">从 71,550 条消息中挖掘出的 {len(rows)} 个事件候选（此前只整理了 11 个）</p>
<div class="meta"><span><b>数据源：</b>wechat-analysis-scale.sqlite3 · v3_annotations</span>
<span><b>生成：</b>2026-09-29</span><span><b>状态：</b>待复核</span></div>
</header>

<div class="stats">
<div class="st"><div class="v">{len(rows)}</div><div class="l">事件候选</div></div>
<div class="st"><div class="v">{nat_cnt.get('已发生',0)+nat_cnt.get('已完成',0)}</div><div class="l">已发生/完成</div></div>
<div class="st"><div class="v">{nat_cnt.get('计划',0)}</div><div class="l">计划中</div></div>
<div class="st"><div class="v">{nat_cnt.get('进行中',0)}</div><div class="l">进行中</div></div>
<div class="st"><div class="v">8</div><div class="l">事件类别</div></div>
</div>

<div class="note">
<p><b>怎么复核</b>：用下面的筛选器按类别/性质/关键词定位，逐条判断。</p>
<p>· <b>确认</b>＝这是真事件　· <b>否定</b>＝噪音/误判　· <b>合并</b>＝与另一条是同一件事</p>
<p>复核结果填到 <code>events_candidates.csv</code> 的「复核」列即可。</p>
</div>

<h2><span class="n">01</span>类别 × 年份分布</h2>
<table><thead><tr><th>类别</th>{''.join(f'<th>{y}</th>' for y in years)}<th>合计</th></tr></thead>
<tbody>{mat_rows}</tbody></table>

<h2><span class="n">02</span>各类别重点事件（按消息密度）</h2>
<table><thead><tr><th>日期</th><th>类别</th><th>事件</th><th>对话人</th><th>条数</th></tr></thead>
<tbody>{top_rows}</tbody></table>

<h2><span class="n">03</span>全量清单（可筛选）</h2>
<div class="ctrl">
<select id="fc"><option value="">全部类别</option>{opts}</select>
<select id="fn"><option value="">全部性质</option>{nats}</select>
<input id="q" placeholder="搜索事件 / 对话人…">
<span id="cnt"></span>
</div>
<table><thead><tr><th>日期</th><th>类别</th><th>性质</th><th>事件</th><th>对话人</th><th>条数</th><th>复核</th></tr></thead>
<tbody id="tb">{''.join(trs)}</tbody></table>

<div class="note warn" style="margin-top:26px">
<p><b>已知偏差</b>（复核时请重点核）：① 系统/商业账号的噪音已过滤，但可能仍有残留；
② 「计划」类事件（{nat_cnt.get('计划',0)} 条）未必真的发生；③ 日期取自消息时间戳，与实际事件日期可能有偏差；
④ 同一件事可能被拆成多条（跨人/跨天），需合并。</p>
</div>

<footer><span>事件总览 · 复核台 · 2026-09-29</span><span>全量 {len(rows)} 条 · 待人工复核</span></footer>
</div>
<script>
const tb=document.getElementById('tb'),fc=document.getElementById('fc'),fn=document.getElementById('fn'),
q=document.getElementById('q'),cnt=document.getElementById('cnt');
const all=[...tb.querySelectorAll('tr')];
function upd(){{
 const c=fc.value,n=fn.value,s=q.value.trim().toLowerCase();let k=0;
 all.forEach(tr=>{{
  const ok=(!c||tr.dataset.c===c)&&(!n||tr.dataset.n===n)&&
   (!s||tr.textContent.toLowerCase().includes(s));
  tr.style.display=ok?'':'none';if(ok)k++;
 }});
 cnt.textContent='显示 '+k+' / '+all.length+' 条';
}}
[fc,fn,q].forEach(e=>e.addEventListener('input',upd));upd();
</script></body></html>"""

open(OUT, "w", encoding="utf-8").write(HTML)
print(f"→ {OUT}")
print(f"事件 {len(rows)} 条 · 类别 {len(CATS)} · 年份 {years}")
