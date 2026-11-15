# -*- coding: utf-8 -*-
"""
probe_jinglin.py —— 井邻（怀柔洞台村乡村美育工作站）线专项探测（只读）

背景：用户指令「井邻在怀柔洞台村把所有东西打通」。
     井邻 = 读研期间最大实践主线（2025-10 起），但事件库/距离地图几乎空白。

产出（全部落 _tmp/）：
  jinglin_timeline.csv   —— 井邻线全部消息时间轴（含会话/角色/内容）
  jinglin_stats.txt      —— 命中统计：按会话 / 按月 / 关键实体
只读：DB 一律 file:...?mode=ro
"""
import csv, io, os, re, sqlite3, datetime
from collections import Counter, defaultdict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
OUT_CSV = os.path.join(WS, "_tmp", "jinglin_timeline.csv")
OUT_TXT = os.path.join(WS, "_tmp", "jinglin_stats.txt")

# 井邻线核心词（LIKE，因 trigram FTS 不支持 2 字词）
KW = ["井邻", "洞台", "乡村美育", "美育工作站", "怀柔", "驻村", "动漫谷",
      "渤海", "长城乡村", "碳迹", "栗子期货", "植墨", "从山到城", "印迹扩散",
      "护未", "悲鸿"]

def t(ts):
    try:
        return datetime.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts)

def clean(ct):
    ct = (ct or "").replace("\n", " / ")
    if ct.startswith("<?xml") or ct.startswith("<msg") or ct.startswith("<msgsource"):
        ct = ct[:80] + " …(XML)"
    return ct

con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True)
q = con.cursor()

# ---------- 0) 排除「他 0 发言的群」（★ 2026-10-04 修正）----------
# 实测：Q&L北京29家教老师群（23988728170@chatroom）等家教刷屏群里，
# 家教订单的【地点】含「怀柔」→ 被「怀柔」关键词误命中 440/968 条（45.5%）。
# 规则：群聊里他从未发过言 → 视为刷屏群，剔除；私聊与公众号不受影响。
active = set(sk for (sk,) in q.execute(
    "select distinct session_key from messages where role='me'"))
print("他发过言的会话 %d 个" % len(active))

def keep(sk):
    return not (sk.endswith("@chatroom") and sk not in active)

# ---------- 1) 逐词命中 ----------
stats = []
hits_by_kw = {}
dropped = 0
for k in KW:
    raw = list(q.execute("""select m.session_key, coalesce(s.display_name,''), m.ts, m.role, m.content
                     from messages m left join sessions s on s.talker=m.session_key
                     where m.content like ? order by m.ts""", ("%" + k + "%",)))
    rows = [r for r in raw if keep(r[0])]
    dropped += len(raw) - len(rows)
    hits_by_kw[k] = rows
    span = ""
    if rows:
        span = "%s → %s" % (t(rows[0][2])[:10], t(rows[-1][2])[:10])
    stats.append("  「%s」 %5d 条   %s" % (k, len(rows), span))

# ---------- 2) 并集时间轴 ----------
merged = {}
for k, rows in hits_by_kw.items():
    for sk, dn, ts, role, ct in rows:
        merged.setdefault((sk, ts, (ct or "")[:120]), [sk, dn, ts, role, ct, []])
        merged[(sk, ts, (ct or "")[:120])][5].append(k)

timeline = sorted(merged.values(), key=lambda r: r[2])

# ---------- 3) 会话聚合 ----------
by_sess = Counter()
sess_name = {}
for r in timeline:
    by_sess[r[0]] += 1
    sess_name[r[0]] = r[1] or r[0]

# ---------- 4) 实体抽取 ----------
ENT = {
    "地点": r"(洞台村|渤海镇|响水湖|宽沟|怀柔|慕田峪|桥梓|X008|南铁路)",
    "地址号": r"洞台村\s*(\d+)\s*号",
    "车牌": r"(京[A-Z][0-9A-Z]{5})",
    "项目名": r"(井邻|洞见温度|碳迹合约|栗子期货|植墨|从山到城|印迹扩散系统|乡村美育工作站|长城国际动漫谷|动漫谷)",
    "作品": r"(栗子灯|风起轴转|栗化了|第五向量|网球计划|栗子球|地问|风洞|网住的云|融化栗子|黑洞|稻草人)",
    "机构": r"(北京逐日计划科技有限公司|中央美术学院|香港理工|北京印刷学院|中国小动物保护协会)",
}
ent_hits = defaultdict(Counter)
for r in timeline:
    ct = r[4] or ""
    for label, pat in ENT.items():
        for m in re.findall(pat, ct):
            ent_hits[label][m] += 1

# ---------- 5) 落盘 ----------
with io.open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["时间", "会话key", "会话名", "角色", "命中词", "内容"])
    for sk, dn, ts, role, ct, ks in timeline:
        w.writerow([t(ts), sk, dn, role, "|".join(ks), clean(ct)[:600]])

with io.open(OUT_TXT, "w", encoding="utf-8") as fh:
    P = lambda s: fh.write(s + "\n")
    P("井邻线专项探测 · 统计")
    P("=" * 62)
    P("")
    P("⚠️ 已排除「他 0 发言的群」（刷屏群）：剔除 %d 条误命中" % dropped)
    P("   实测污染源：Q&L北京29家教老师群的家教单【地点】含「怀柔」")
    P("")
    P("【一】逐词命中")
    for s in stats:
        P(s)
    P("")
    P("【二】并集去重后 %d 条，跨度 %s → %s" % (
        len(timeline), t(timeline[0][2])[:10], t(timeline[-1][2])[:10]))
    P("")
    P("【三】按会话分布（TOP 40）")
    for sk, n in by_sess.most_common(40):
        P("  %-26s %-28s %4d 条" % (sk, sess_name[sk][:26], n))
    P("")
    P("【四】按月分布")
    for k, v in sorted(Counter(t(r[2])[:7] for r in timeline).items()):
        P("  %s  %4d" % (k, v))
    P("")
    P("【五】关键实体")
    for label, cnt in ent_hits.items():
        P("  · %s" % label)
        for v, n in cnt.most_common(25):
            P("      %-32s %d" % (v, n))
con.close()
print("OK → %s" % OUT_CSV)
print("OK → %s" % OUT_TXT)
print("剔除刷屏群误命中 %d 条" % dropped)
print("并集 %d 条 / %d 会话" % (len(timeline), len(by_sess)))
