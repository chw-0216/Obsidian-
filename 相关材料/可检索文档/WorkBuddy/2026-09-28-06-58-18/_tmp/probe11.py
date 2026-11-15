# -*- coding: utf-8 -*-
r"""probe11.py —— 何一沙9条 / 舒泽林10-06 / 关键 wxid 身份 / 柯益盈关键段"""
import sqlite3, datetime
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
con = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
def f(ts): return datetime.datetime.fromtimestamp(ts).strftime("%y-%m-%d %H:%M:%S")
def cl(c):
    if not c: return ""
    if '<' in c:
        h = c.split('<')[0].strip()
        tag = "〔图〕" if '<img' in c else ("〔语音〕" if '<voicemsg' in c else ("〔视频〕" if '<videomsg' in c else ("〔表情〕" if '<emoji' in c else "〔卡片〕")))
        return (h[:250] + " " + tag) if h else tag
    return c.replace("\n", " ")[:300]

def dump(sk, lab, t0=None, t1=None):
    q = "select ts, role, content from messages where session_key=?"
    p = [sk]
    if t0: q += " and ts>=?"; p.append(t0)
    if t1: q += " and ts<?"; p.append(t1)
    q += " order by ts"
    rows = con.execute(q, p).fetchall()
    print("=" * 84); print("【%s】%s  共 %d 条" % (lab, sk, len(rows))); print("=" * 84)
    for r in rows:
        print("  [%s] %-4s %s" % (f(r["ts"]), "我" if r["role"] == "me" else ("他" if r["role"] == "them" else "sys"), cl(r["content"])))
    print()

print("### 1. 何一沙 / Yisharlot🍬 全部 9 条")
dump("huxiaomi123", "何一沙（央美美术馆媒体部主任）")

print("### 2. 舒泽林 私聊 10-05 12:00 → 现在")
dump("wxid_0ejd54z34nmv32", "舒泽林", int(datetime.datetime(2026, 10, 5, 12).timestamp()))

print("### 3. 关键 wxid 身份定位")
for w in ["wxid_o9to6kw5j35x12", "wxid_1wa75s1kze3o22", "wxid_qcfx1y0f6f9122", "wxid_wdnk6ue9kiyn22", "wxid_y7lve7qibx8132", "deerluna", "WangSnow"]:
    r = con.execute("select talker, display_name, session_type, message_count, first_ts, last_ts from sessions where talker=?", (w,)).fetchone()
    if r:
        print("  %-26s → dn=%-22s %s %5d 条  %s ~ %s" % (w, r["display_name"], r["session_type"], r["message_count"], f(r["first_ts"])[:11], f(r["last_ts"])[:11]))
    else:
        # 可能只是群里 sender
        rr = con.execute("select session_key, count(*) c from messages where sender=? group by session_key order by c desc limit 3", (w,)).fetchall()
        print("  %-26s → 非独立会话；作为 sender 出现在: %s" % (w, [(x["session_key"][:26], x["c"]) for x in rr]))

print()
print("### 4. wxid_o9to6kw5j35x12（拉他进 Tripothon 的人）私聊 10-05 全天")
dump("wxid_o9to6kw5j35x12", "Tripo 拉群者", int(datetime.datetime(2026, 10, 5).timestamp()))

print("### 5. wxid_1wa75s1kze3o22（9-26《在场与回应》那条）9-26 前后")
dump("wxid_1wa75s1kze3o22", "?", int(datetime.datetime(2026, 9, 20).timestamp()))
