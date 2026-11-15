# -*- coding: utf-8 -*-
r"""probe14.py —— ★ 全库审计：① 备注名 vs 正文 检索盲区 ② 人物档案条数 vs 索引库真值 ③ 今日动态"""
import sqlite3, datetime, re, os, io, json
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M")

print("#" * 92)
print("A. 索引库总览")
print("#" * 92)
n_msg = con.execute("select count(*) c from messages").fetchone()["c"]
n_ses = con.execute("select count(*) c from sessions").fetchone()["c"]
mn = con.execute("select min(ts), max(ts) from messages").fetchone()
print("  消息 %d 条 · 会话 %d 个 · 窗口 %s ~ %s" % (n_msg, n_ses, f(mn[0]), f(mn[1])))

print()
print("#" * 92)
print("B. ★ 检索盲区：display_name 里是「人名」，但正文里搜不到的人")
print("   （= 任何「按正文关键词搜人名」的分析都会漏掉的人）")
print("#" * 92)
rows = con.execute("""select talker, display_name, session_type, message_count, first_ts, last_ts
                      from sessions where message_count>=100 order by message_count desc""").fetchall()
# 人名判定：2-4 个汉字，且不含数字/英文/表情/群标记
CJK = re.compile(r'^[\u4e00-\u9fa5]{2,4}$')
cands = []
for r in rows:
    dn = (r["display_name"] or "").strip()
    if CJK.match(dn):
        cands.append(r)
print("  ≥100 条会话中，display_name 是纯 2-4 汉字人名的：%d 个" % len(cands))

blind = []
for r in cands:
    dn = r["display_name"]
    c = con.execute("select count(*) c from messages where content like ?", ("%" + dn + "%",)).fetchone()["c"]
    blind.append((dn, r["message_count"], c, r["talker"], r["first_ts"], r["last_ts"]))
blind.sort(key=lambda x: -x[1])
print()
print("  %-12s %8s %8s  %-28s %s" % ("备注名", "总条数", "正文命中", "talker", "窗口"))
for dn, mc, c, tk, t0, t1 in blind:
    flag = "  ★★ 正文 0 命中" if c == 0 else ("  ★ 正文极少" if c < 5 else "")
    print("  %-12s %8d %8d  %-28s %s ~ %s%s" % (dn, mc, c, tk[:28], f(t0)[:11], f(t1)[:11], flag))

print()
print("#" * 92)
print("C. ★ 人物档案条数 vs 索引库真值（审计 Obsidian 里的数字）")
print("#" * 92)
VAULT = r"C:/Users/wardc/Documents/Obsidian Vault/03_微信聊天分析/01_人物档案"
# 建 name -> 真值 索引
truth = {}
for r in con.execute("select talker, display_name, message_count, last_ts from sessions"):
    dn = (r["display_name"] or "").strip()
    if dn and dn not in truth:
        truth[dn] = (r["message_count"], r["last_ts"], r["talker"])
    else:
        if dn and r["message_count"] > truth[dn][0]:
            truth[dn] = (r["message_count"], r["last_ts"], r["talker"])

files = [x for x in os.listdir(VAULT) if x.endswith(".md") and not x.startswith("_") and not x.startswith(".")]
bad = []
for fn in files:
    name = fn[:-3]
    p = os.path.join(VAULT, fn)
    try:
        s = io.open(p, encoding="utf-8").read()
    except Exception:
        continue
    # 取 frontmatter 的 messages: 或正文里「X,XXX 条」
    m = re.search(r'^messages:\s*([0-9]+)', s, re.M)
    claimed = int(m.group(1)) if m else None
    if claimed is None:
        mm = re.search(r'\*\*([0-9][0-9,]{2,})\s*条\*\*', s)
        if mm:
            claimed = int(mm.group(1).replace(",", ""))
    if claimed is None:
        continue
    t = truth.get(name)
    if not t:
        continue
    real, last_ts, tk = t
    if real != claimed:
        bad.append((name, claimed, real, real - claimed, f(last_ts), tk))

bad.sort(key=lambda x: -abs(x[3]))
print("  对比了 %d 份有数字的人物档案，**%d 份与索引库不一致**：" % (len(files), len(bad)))
print()
print("  %-16s %9s %9s %9s  %s" % ("人物", "档案写的", "索引真值", "差额", "索引末条"))
for name, cl, rl, d, lt, tk in bad:
    print("  %-16s %9d %9d %+9d  %s  %s" % (name, cl, rl, d, lt, tk[:26]))

print()
print("#" * 92)
print("D. 今日（10-07）动态")
print("#" * 92)
t0 = int(datetime.datetime(2026, 10, 7).timestamp())
rows = con.execute("""select m.session_key, s.display_name, m.ts, m.role, m.content
                      from messages m left join sessions s on s.talker=m.session_key
                      where m.ts>=? order by m.ts""", (t0,)).fetchall()
print("  今日 %d 条" % len(rows))
from collections import Counter
c = Counter()
for r in rows: c[(r["session_key"], r["display_name"])] += 1
print("  活跃会话 %d 个：" % len(c))
for (sk, dn), n in c.most_common(30):
    print("    %-32s %-26s %4d" % (sk[:32], (dn or "")[:26], n))

print()
print("  --- 关键人物今日逐条 ---")
KEY = {"wxid_vk33qtlz3yyn22": "极狐售后", "gh_4fe8de031b84": "企业微信/王义",
       "wxid_wdnk6ue9kiyn22": "笑一", "wxid_0ejd54z34nmv32": "舒泽林",
       "6795601010@chatroom": "gay学现场", "huxiaomi123": "何一沙",
       "wxid_5049180491911": "柯益盈", "wxid_1wa75s1kze3o22": "母亲",
       "45219356839@chatroom": "T5极狐服务群", "wxid_4e4mad0ve4fn22": "王逸伦"}
for sk, lab in KEY.items():
    rr = con.execute("select ts, role, content from messages where session_key=? and ts>=? order by ts", (sk, t0)).fetchall()
    if not rr: continue
    print("  【%s】%d 条" % (lab, len(rr)))
    for x in rr[-12:]:
        cc = (x["content"] or "").replace("\n", " ")[:170]
        if "<" in cc: cc = cc.split("<")[0].strip()[:120] or "〔媒体〕"
        print("     [%s] %-4s %s" % (f(x["ts"]), "我" if x["role"] == "me" else ("他" if x["role"] == "them" else "sys"), cc))
