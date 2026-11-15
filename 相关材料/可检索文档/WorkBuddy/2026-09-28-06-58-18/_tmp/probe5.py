# -*- coding: utf-8 -*-
import os, sqlite3, datetime, re, statistics
IDX = r"C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite"
idx = sqlite3.connect("file:" + IDX.replace("\\", "/") + "?mode=ro", uri=True)
idx.row_factory = sqlite3.Row
def fmt(ts): return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

print("=== ① 王逸伦 全部 22 条回复原文（看语长/语感）===")
tot_len = []
for r in idx.execute("select ts, role, content from messages where session_key='wxid_4e4mad0ve4fn22' and role='them' order by ts"):
    ct = (r["content"] or "")
    if '<' in ct: ct = "[非文本]"
    ct = ct.replace("\n"," ")
    tot_len.append(len(ct))
    print("  [%s] (%2d字) %s" % (fmt(r["ts"]), len(ct), ct))
print("  → 他回复平均 %.1f 字 / 中位数 %d 字" % (statistics.mean(tot_len), statistics.median(tot_len)))

print()
print("=== ② 我发给王逸伦的平均长度（对比）===")
ml = [len((r["content"] or "").replace("\n"," ")) for r in idx.execute("select content from messages where session_key='wxid_4e4mad0ve4fn22' and role='me'")]
ml = [x for x in ml if x > 0 and x < 300]
print("  → 我平均 %.1f 字 / 中位数 %d 字" % (statistics.mean(ml), statistics.median(ml)))

print()
print("=== ③ 全库搜「银行 / 柜员 / 网点」相关（三人会话 + 群）===")
for sk, nm in [("wxid_4e4mad0ve4fn22","王逸伦"),("wxid_0ejd54z34nmv32","舒泽林"),
               ("wxid_g6ewa78cg30722","王若彤"),("6795601010@chatroom","群")]:
    hits = []
    for r in idx.execute("select ts, role, content from messages where session_key=? and ("
                         "content like '%银行%' or content like '%柜员%' or content like '%网点%' "
                         "or content like '%建行%' or content like '%工行%' or content like '%中行%' "
                         "or content like '%农行%' or content like '%交行%' or content like '%招行%' "
                         "or content like '%中信%' or content like '%北京银行%') order by ts", (sk,)):
        hits.append(r)
    print("--- %s：%d 条 ---" % (nm, len(hits)))
    for r in hits[:25]:
        who = "我" if r["role"]=="me" else nm
        print("  [%s] %-4s %s" % (fmt(r["ts"]), who, (r["content"] or "").replace("\n"," ")[:130]))

print()
print("=== ④ 舒泽林 2025-09-02 前后（贷款话术）上下文 ===")
t0 = int(datetime.datetime(2025,9,1).timestamp()); t1 = int(datetime.datetime(2025,9,5).timestamp())
for r in idx.execute("select ts, role, content from messages where session_key='wxid_0ejd54z34nmv32' and ts>=? and ts<? order by ts",(t0,t1)):
    who = "我" if r["role"]=="me" else "舒泽林"
    print("  [%s] %-4s %s" % (fmt(r["ts"]), who, (r["content"] or "").replace("\n"," ")[:150]))
