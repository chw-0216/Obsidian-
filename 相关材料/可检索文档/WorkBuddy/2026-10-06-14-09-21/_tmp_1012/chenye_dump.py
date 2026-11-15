# -*- coding: utf-8 -*-
"""抽取陈晔（deerluna）会话全部消息，并按井邻相关关键词筛选。

用法: python chenye_dump.py [--all]
输出: _chenye_all.jsonl / _chenye_jinglin.jsonl
"""
import sqlite3, glob, json, os, re, sys, datetime

BASE = r"C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted\message"
T = "Msg_f349341f7efaa6679217d8c436e64d91"   # md5('deerluna')
OUT = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012"

try:
    import zstandard
    Z = zstandard.ZstdDecompressor()
except Exception:
    Z = None

# ---- 井邻相关关键词 ----
KW = [
    "井邻", "洞台", "工作站", "怀柔", "渤海镇", "驻村", "开街", "动漫谷",
    "丝网", "网版", "制版", "正片", "硫酸纸", "菲林", "晒版", "刮印", "套印", "套色", "印染",
    "版画", "印制", "印刷", "工作坊", "体验", "植墨", "栗", "油墨", "造纸",
    "偏移", "四型", "八版", "MBTI", "飞鸟", "手势", "MediaPipe", "互动",
    "接待", "来访", "到访", "区委", "政协", "组织部", "宣传部", "文旅", "科学城",
    "领导", "区长", "书记", "讲解", "英文",
    "物料", "采购", "安装", "空调", "水槽", "展区", "布展", "海报", "易拉宝",
    "马慧楠", "技师", "陈老师", "导师",
    "汇报", "中期", "PPT", "汇报稿", "讲稿", "答辩",
    "棉T", "T恤", "恤", "工作服", "胸牌",
]
# 排除明显无关（避免误报）
NOT = ["外卖", "红包"]

def decompress(mc, cc, ct):
    """★ ct==4 表示 zstd；压缩体可能在 compress_content，也可能直接就是 message_content。
       两者都要试（通话 type=50 / 名片 type=42 走的是后者）。"""
    txt = mc
    if ct == 4 and Z is not None:
        blob = cc if cc else mc
        if blob:
            try:
                txt = Z.decompress(blob).decode("utf-8", "ignore")
            except Exception:
                try:
                    txt = Z.decompress(blob, max_output_size=8 << 20).decode("utf-8", "ignore")
                except Exception:
                    txt = mc
    if isinstance(txt, bytes):
        txt = txt.decode("utf-8", "ignore")
    return txt or ""

def clean(s):
    """把 XML 结构压成可读文本"""
    if not s:
        return ""
    s = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", s, flags=re.S)
    keep = []
    for tag in ("title", "des", "url", "displayname", "nickname", "appname",
                "sourcedisplayname", "finderFeed", "username", "content"):
        for m in re.findall(r"<%s[^>]*>(.*?)</%s>" % (tag, tag), s, flags=re.S):
            m = m.strip()
            if m and m not in keep:
                keep.append(m)
    if keep:
        return " ⟂ ".join(keep)[:600]
    return re.sub(r"<[^>]+>", " ", s).strip()[:600]

def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(BASE, "message_*.db"))):
        c = sqlite3.connect("file:" + f + "?mode=ro", uri=True)
        names = [r[0] for r in c.execute("select name from sqlite_master where type='table'")]
        if T not in names:
            c.close(); continue
        q = ("select create_time, local_type, real_sender_id, message_content, "
             "compress_content, WCDB_CT_message_content from \"%s\" order by create_time" % T)
        for ts, lt, sid, mc, cc, ct in c.execute(q):
            body = clean(decompress(mc, cc, ct))
            rows.append({
                "t": ts,
                "dt": datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"),
                "day": datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                "type": lt,
                "sender": sid,
                "src": os.path.basename(f),
                "body": body,
            })
        c.close()

    # ---- 自动判定「谁是谁」 ----
    # real_sender_id 随登录设备变化（旧 395/10，2026-08-09 起 107/2）。
    # 规则：按源库分组，含「老师」字样最多的 sender = 本人（学生称导师为老师）；
    #       组内另一个主要 sender = 陈晔。若该库只有单一 sender，沿用最近一次已知映射。
    from collections import Counter
    known = {}          # src -> (我, 陈晔)
    for src in sorted({r["src"] for r in rows}):
        sub = [r for r in rows if r["src"] == src and r["type"] == 1]
        c2 = Counter(r["sender"] for r in sub)
        c3 = Counter(r["sender"] for r in sub if "老师" in r["body"])
        if c3:
            me = c3.most_common(1)[0][0]
            others = [s for s, _ in c2.most_common() if s != me]
            other = others[0] if others else None
            known[src] = (me, other)
        else:
            known[src] = (None, None)
    # 用最近一次有效映射补空
    last = (None, None)
    for src in sorted(known):
        if known[src][0] is not None:
            last = known[src]
        else:
            known[src] = last
    for r in rows:
        me, other = known.get(r["src"], (None, None))
        r["who"] = "陈晔" if (other is not None and r["sender"] == other) else "我"

    with open(os.path.join(OUT, "_chenye_all.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    hit = []
    for r in rows:
        b = r["body"]
        if any(k in b for k in KW) and not any(n in b for n in NOT):
            hit.append(r)
    with open(os.path.join(OUT, "_chenye_jinglin.jsonl"), "w", encoding="utf-8") as fh:
        for r in hit:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("总消息:", len(rows))
    print("sender 判定:", known)
    print("井邻相关命中:", len(hit))
    if rows:
        print("范围:", rows[0]["dt"], "→", rows[-1]["dt"])
    d = Counter(r["day"] for r in hit)
    print("命中覆盖天数:", len(d))
    print("命中 TOP20 日期:", d.most_common(20))
    print("按年分布:", Counter(r["day"][:4] for r in hit))
    print("谁说的:", Counter(r["who"] for r in hit))

if __name__ == "__main__":
    main()
