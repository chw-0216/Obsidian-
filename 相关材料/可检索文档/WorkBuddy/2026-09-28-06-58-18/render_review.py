# -*- coding: utf-8 -*-
"""render_review.py — 事件复核台（可筛选 / 可点选复核 / 可导出结果）。"""
import csv
import json
import os
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "events_review.csv")
OUT = os.path.join(HERE, "事件复核台.html")

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
data = [{
    "id": r["编号"], "t": r["层级"], "s": int(r["分"]), "sub": r["主体"],
    "d": r["日期"], "y": r["年份"],
    "c": r["类别"], "n": r["性质"], "e": r["事件"], "w": r["对话人"],
    "p": r["涉及人"], "m": r["条数"], "cf": r["置信度"], "ev": r["证据"], "f": r["标记"],
} for r in rows]

CATS = ["学业/学术", "求职/职场", "项目/商务", "展演/创作", "生活/事务",
        "比赛/活动", "出行/迁移", "社交/见面"]
cat_cnt = Counter(r["c"] for r in data)
nat_cnt = Counter(r["n"] for r in data)
tier_cnt = Counter(r["t"] for r in data)
year_cnt = Counter(r["y"] for r in data)
sub_cnt = Counter(r["sub"] for r in data)
SUBS = ["我", "双方", "对方", "第三方"]

PAYLOAD = json.dumps({"rows": data, "cats": CATS}, ensure_ascii=False)

HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>事件复核台</title>
<style>
:root{--ink:#1f2a33;--soft:#42505c;--mute:#6b7885;--paper:#faf8f4;--p2:#f2eee6;
--line:#e0dacd;--ls:#cfc6b4;--ac:#9e3b32;--blue:#2a4a63;--gr:#3b6d11;--gold:#8a6d3b;
--A:#9e3b32;--B:#8a6d3b;--C:#8a949e;}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:"Microsoft YaHei","PingFang SC",system-ui,sans-serif;font-size:15px;line-height:1.7}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px 80px}
header{border-bottom:2px solid var(--ink);padding:48px 0 22px}
.kick{font-size:12px;letter-spacing:.3em;color:var(--ac);font-weight:700;margin-bottom:12px}
h1{font-family:"Songti SC",Georgia,serif;font-size:30px;margin:0 0 10px}
.sub{font-family:"Songti SC",Georgia,serif;font-size:15.5px;color:var(--soft);margin:0 0 18px}
.meta{display:flex;gap:8px 22px;flex-wrap:wrap;font-size:12.5px;color:var(--mute);
border-top:1px solid var(--line);padding-top:12px}
.stats{display:flex;flex-wrap:wrap;gap:11px;margin:20px 0}
.st{flex:1;min-width:104px;border:1px solid var(--line);border-radius:6px;padding:12px;
background:#fff;text-align:center}
.st .v{font-family:Georgia,serif;font-size:24px;font-weight:700;color:var(--ac)}
.st .l{font-size:12px;color:var(--mute);margin-top:2px}
h2{font-family:"Songti SC",Georgia,serif;font-size:20px;margin:40px 0 14px;
padding-bottom:8px;border-bottom:1px solid var(--ls)}
h2 .n{color:var(--ac);font-size:14px;margin-right:9px;font-family:Georgia,serif}
.note{background:#fff;border:1px solid var(--ls);border-left:4px solid var(--ac);
border-radius:0 6px 6px 0;padding:16px 20px;margin:18px 0;font-size:13.8px}
.note p{margin:0 0 8px}.note p:last-child{margin:0}
.note.warn{border-left-color:var(--gold)}
.ctrl{display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin:14px 0;padding:12px 14px;
background:#fff;border:1px solid var(--line);border-radius:6px;position:sticky;top:0;z-index:9;
box-shadow:0 2px 8px rgba(0,0,0,.04)}
select,input{padding:6px 10px;border:1px solid var(--ls);border-radius:5px;font-size:13.4px;
font-family:inherit;background:#fff;color:var(--ink)}
input{flex:1;min-width:160px}
.btn{padding:6px 13px;border:1px solid var(--ls);border-radius:5px;background:#fff;cursor:pointer;
font-size:13px;font-family:inherit;color:var(--ink)}
.btn:hover{background:var(--p2)}
.btn.pri{background:var(--ink);color:#fff;border-color:var(--ink)}
.btn.pri:hover{background:#000}
#prog{font-size:12.8px;color:var(--mute);margin-left:auto;white-space:nowrap}
table{width:100%;border-collapse:collapse;font-size:13.1px;background:#fff;
border:1px solid var(--line);border-radius:6px;overflow:hidden}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
thead th{background:var(--p2);font-size:12.2px;font-weight:700;border-bottom:1.5px solid var(--ls);
white-space:nowrap;position:sticky;top:57px;z-index:6}
tbody tr:hover{background:#fdfcf9}
tr.done-ok{background:#f4f8f0}
tr.done-no{background:#f9f4f3;opacity:.62}
tr.done-mg{background:#f3f6f9}
td.d{white-space:nowrap;color:var(--mute);font-family:Consolas,monospace;font-size:12.2px}
td.n{text-align:right;font-family:Consolas,monospace;color:var(--mute)}
td.who{white-space:nowrap;color:var(--blue);font-size:12.6px}
td.subj{white-space:nowrap;font-size:12.2px;color:var(--mute);text-align:center}
td.subj.s-me{color:var(--ac);font-weight:600}
td.ev{line-height:1.55;cursor:pointer}
td.tier{text-align:center;font-weight:700;font-family:Georgia,serif;font-size:14px}
.t-A{color:var(--A)}.t-B{color:var(--B)}.t-C{color:var(--C)}
.tag{display:inline-block;padding:1px 7px;border-radius:20px;font-size:10.6px;font-weight:700;
background:#eef2f5;color:var(--blue);border:1px solid #dbe4ea;white-space:nowrap}
.n-done{color:var(--gr);font-weight:600}.n-plan{color:var(--gold)}
.n-run{color:var(--blue)}.n-cxl{color:var(--ac)}.n-unc{color:var(--mute)}
.ck{white-space:nowrap}
.ck button{border:1px solid var(--ls);background:#fff;cursor:pointer;font-size:11.5px;
padding:2px 7px;border-radius:4px;margin-right:3px;font-family:inherit;color:var(--soft)}
.ck button:hover{border-color:var(--mute)}
.ck button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.ck button.ok.on{background:var(--gr);border-color:var(--gr)}
.ck button.no.on{background:var(--ac);border-color:var(--ac)}
.ck button.mg.on{background:var(--blue);border-color:var(--blue)}
.det{background:#fbfaf7;font-size:12.6px;color:var(--soft)}
.det b{color:var(--ink)}
.flag{color:var(--gold);font-size:11.5px;font-weight:600}
footer{margin-top:50px;padding-top:18px;border-top:1px solid var(--line);font-size:12.4px;
color:var(--mute);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
</style></head><body><div class="wrap">
<header>
<div class="kick">全量事件挖掘 · 人工复核</div>
<h1>事件复核台</h1>
<p class="sub">从 71,550 条消息中挖出 __TOTAL__ 个事件候选 · 按重要性分为 A/B/C 三级</p>
<div class="meta"><span><b>数据源：</b>wechat-analysis-scale.sqlite3 · v3_annotations</span>
<span><b>生成：</b>2026-09-29</span><span><b>复核进度：</b><span id="prog2">—</span></span></div>
</header>

<div class="stats">
<div class="st"><div class="v">__TOTAL__</div><div class="l">事件候选</div></div>
<div class="st"><div class="v">__A__</div><div class="l">A 级 · 先看</div></div>
<div class="st"><div class="v">__B__</div><div class="l">B 级</div></div>
<div class="st"><div class="v">__C__</div><div class="l">C 级 · 长尾</div></div>
<div class="st"><div class="v">__SELF__</div><div class="l">主体＝我</div></div>
<div class="st"><div class="v">2024–2026</div><div class="l">覆盖年份</div></div>
</div>

<div class="note">
<p><b>怎么复核</b>：默认按重要性排序。建议顺序 —— ①筛「A 级」106+ 条过一遍；②筛「主体＝我」把和你直接相关的事件挑出来。</p>
<p>· <b>✓ 确认</b>＝真事件　· <b>✗ 否定</b>＝噪音/误判　· <b>⊕ 合并</b>＝与另一条是同一件事</p>
<p>· 点事件文字可展开证据细节。复核状态自动存在浏览器本地，<b>随时点「导出结果」</b>存成 CSV。</p>
</div>

<h2><span class="n">01</span>分布总览</h2>
<div class="note" style="border-left-color:var(--blue)">
<p><b>类别</b>：__CATLINE__</p>
<p><b>主体</b>：__SUBLINE__</p>
<p><b>性质</b>：__NATLINE__</p>
<p><b>年份</b>：__YEARLINE__</p>
</div>

<h2><span class="n">02</span>复核清单</h2>
<div class="ctrl">
<select id="ft"><option value="">全部层级</option><option value="A">A 级（__A__）</option><option value="B">B 级（__B__）</option><option value="C">C 级（__C__）</option></select>
<select id="fsub"><option value="">全部主体</option>__SUBOPT__</select>
<select id="fc"><option value="">全部类别</option>__CATOPT__</select>
<select id="fn"><option value="">全部性质</option>__NATOPT__</select>
<select id="fy"><option value="">全部年份</option>__YEAROPT__</select>
<select id="fs"><option value="">全部状态</option><option value="todo">未复核</option><option value="ok">已确认</option><option value="no">已否定</option><option value="mg">待合并</option></select>
<input id="q" placeholder="搜索事件 / 对话人 / 涉及人…">
<button class="btn" id="clr">清空复核</button>
<button class="btn pri" id="exp">导出结果 CSV</button>
<span id="prog"></span>
</div>
<table><thead><tr>
<th style="width:40px">层</th><th style="width:78px">日期</th><th style="width:52px">主体</th>
<th style="width:76px">类别</th>
<th style="width:60px">性质</th><th>事件</th><th style="width:88px">对话人</th>
<th style="width:44px">条数</th><th style="width:126px">复核</th>
</tr></thead><tbody id="tb"></tbody></table>

<div class="note warn" style="margin-top:24px">
<p><b>已知偏差</b>：① 系统/商业账号噪音已过滤，但可能仍有残留（标「系统号」的 13 条可优先否定）；
② 「计划」类事件未必真的发生；③ 日期取自消息时间戳，与事件实际日期可能有偏差；
④ 同一件事可能被拆成多条（跨人/跨天），用「合并」标出。</p>
</div>
<footer><span>事件复核台 · 2026-09-29</span><span>__TOTAL__ 条 · 全量本地生成</span></footer>
</div>
<script>
const DB = __PAYLOAD__;
const rows = DB.rows, CATS = DB.cats;
const LS = 'event_review_v1';
let state = {};
try { state = JSON.parse(localStorage.getItem(LS) || '{}'); } catch(e){ state = {}; }
const save = () => localStorage.setItem(LS, JSON.stringify(state));

const tb = document.getElementById('tb');
const clsNat = n => ({'已完成':'n-done','已发生':'n-done','计划':'n-plan','进行中':'n-run',
  '已取消':'n-cxl','不确定':'n-unc'}[n] || 'n-unc');

const frag = document.createDocumentFragment();
rows.forEach((r, i) => {
  const tr = document.createElement('tr');
  tr.dataset.i = i; tr.dataset.t = r.t; tr.dataset.c = r.c;
  tr.dataset.n = r.n; tr.dataset.y = r.y; tr.dataset.sub = r.sub;
  tr.dataset.s = r.e + ' ' + r.w + ' ' + r.p;
  tr.innerHTML =
    '<td class="tier t-'+r.t+'">'+r.t+'</td>'+
    '<td class="d">'+r.d+'</td>'+
    '<td class="subj'+(r.sub==='我'?' s-me':'')+'">'+r.sub+'</td>'+
    '<td><span class="tag">'+r.c+'</span></td>'+
    '<td class="'+clsNat(r.n)+'">'+r.n+'</td>'+
    '<td class="ev">'+esc(r.e)+(r.f?' <span class="flag">['+r.f+']</span>':'')+'</td>'+
    '<td class="who">'+esc(r.w)+'</td>'+
    '<td class="n">'+r.m+'</td>'+
    '<td class="ck"><button class="ok" data-v="ok">✓</button>'+
    '<button class="no" data-v="no">✗</button>'+
    '<button class="mg" data-v="mg">⊕</button></td>';
  const det = document.createElement('tr');
  det.className = 'det'; det.style.display = 'none';
  det.innerHTML = '<td></td><td colspan="8"><b>涉及人：</b>'+esc(r.p||'—')+
    '　<b>置信度：</b>'+r.cf+'　<b>证据：</b>'+esc(r.ev)+
    '　<b>分值：</b>'+r.s+'　<b>标记：</b>'+(r.f||'—')+'</td>';
  frag.appendChild(tr); frag.appendChild(det);
});
tb.appendChild(frag);

function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g, m =>
  ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m])); }

const all = [...tb.querySelectorAll('tr:not(.det)')];
const ft=document.getElementById('ft'), fsub=document.getElementById('fsub'),
      fc=document.getElementById('fc'),
      fn=document.getElementById('fn'), fy=document.getElementById('fy'),
      fs=document.getElementById('fs'), q=document.getElementById('q'),
      prog=document.getElementById('prog'), prog2=document.getElementById('prog2');

function applyState(){
  all.forEach(tr=>{
    const v = state[tr.dataset.i];
    tr.className = v==='ok'?'done-ok':v==='no'?'done-no':v==='mg'?'done-mg':'';
    tr.querySelectorAll('.ck button').forEach(b=>b.classList.toggle('on', b.dataset.v===v));
    tr.nextElementSibling.style.display = 'none';
  });
}
function upd(){
  const T=ft.value,U=fsub.value,C=fc.value,N=fn.value,Y=fy.value,S=fs.value,
        s=q.value.trim().toLowerCase();
  let k=0, done=0;
  all.forEach(tr=>{
    const v = state[tr.dataset.i] || '';
    if(v) done++;
    const ok = (!T||tr.dataset.t===T)&&(!U||tr.dataset.sub===U)&&
      (!C||tr.dataset.c===C)&&(!N||tr.dataset.n===N)&&
      (!Y||tr.dataset.y===Y)&&
      (!S||(S==='todo'?!v:v===S))&&
      (!s||tr.dataset.s.toLowerCase().includes(s));
    tr.style.display = ok?'':'none';
    tr.nextElementSibling.style.display='none';
    if(ok) k++;
  });
  prog.textContent = '显示 '+k+' / '+all.length+' · 已复核 '+done;
  prog2.textContent = done+' / '+all.length;
}
tb.addEventListener('click', e=>{
  const b = e.target.closest('.ck button');
  if(b){
    const tr = b.closest('tr'), i = tr.dataset.i, v = b.dataset.v;
    state[i] = (state[i]===v) ? '' : v;
    if(!state[i]) delete state[i];
    save(); applyState(); upd(); return;
  }
  const ev = e.target.closest('td.ev');
  if(ev){
    const det = ev.closest('tr').nextElementSibling;
    det.style.display = det.style.display==='none' ? '' : 'none';
  }
});
[ft,fsub,fc,fn,fy,fs,q].forEach(el=>el.addEventListener('input',upd));
document.getElementById('clr').addEventListener('click',()=>{
  if(confirm('清空所有复核标记？此操作不可撤销。')){ state={}; save(); applyState(); upd(); }
});
document.getElementById('exp').addEventListener('click',()=>{
  const head = ['编号','层级','日期','主体','类别','性质','事件','对话人','涉及人','条数','复核','备注'];
  const lines = [head.join(',')];
  const q2 = s => '"'+String(s==null?'':s).replace(/"/g,'""')+'"';
  rows.forEach((r,i)=>{
    lines.push([r.id,r.t,r.d,r.sub,r.c,r.n,r.e,r.w,r.p,r.m,state[i]||'', ''].map(q2).join(','));
  });
  const blob = new Blob(['\\ufeff'+lines.join('\\r\\n')], {type:'text/csv;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = '事件复核结果_'+new Date().toISOString().slice(0,10)+'.csv';
  a.click();
});
applyState(); upd();
</script></body></html>"""

catline = "　".join(f"{c} {cat_cnt[c]}" for c in CATS)
natline = "　".join(f"{n} {v}" for n, v in nat_cnt.most_common())
yearline = "　".join(f"{y} {v}" for y, v in sorted(year_cnt.items()))
subline = "　".join(f"{s} {sub_cnt[s]}" for s in SUBS if sub_cnt[s])
catopt = "".join(f'<option value="{c}">{c}（{cat_cnt[c]}）</option>' for c in CATS)
natopt = "".join(f'<option value="{n}">{n}（{v}）</option>' for n, v in nat_cnt.most_common())
yearopt = "".join(f'<option value="{y}">{y}（{v}）</option>' for y, v in sorted(year_cnt.items()))
subopt = "".join(f'<option value="{s}">{s}（{sub_cnt[s]}）</option>' for s in SUBS if sub_cnt[s])

HTML = (HTML.replace("__PAYLOAD__", PAYLOAD)
        .replace("__TOTAL__", str(len(data)))
        .replace("__A__", str(tier_cnt.get("A", 0)))
        .replace("__B__", str(tier_cnt.get("B", 0)))
        .replace("__C__", str(tier_cnt.get("C", 0)))
        .replace("__SELF__", str(sub_cnt.get("我", 0)))
        .replace("__CATLINE__", catline)
        .replace("__SUBLINE__", subline)
        .replace("__NATLINE__", natline)
        .replace("__YEARLINE__", yearline)
        .replace("__CATOPT__", catopt)
        .replace("__SUBOPT__", subopt)
        .replace("__NATOPT__", natopt)
        .replace("__YEAROPT__", yearopt))

open(OUT, "w", encoding="utf-8").write(HTML)
print(f"→ {OUT}")
print(f"事件 {len(data)} · A{tier_cnt.get('A',0)} B{tier_cnt.get('B',0)} C{tier_cnt.get('C',0)}")
