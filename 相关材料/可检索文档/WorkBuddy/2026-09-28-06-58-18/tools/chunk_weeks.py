# -*- coding: utf-8 -*-
r"""
chunk_weeks.py —— 把 81 个周包切成「适合模型上下文」的连续片段

为什么要切
----------
周包平均 4,000+ 条消息 / 1.1 MB，**单周超出一次模型调用的合理上下文**。
但**不能只给模型周摘要** —— 摘要会丢掉原话、时间、语气与前后因果。
所以要切成「**模型能一次读完、且不丢前后文**」的连续片段。

切分规则（★ 三条硬规则）
------------------------
1. **会话内不切断**：同一会话在同一周内优先放进同一片段（对话是有上下文的）。
2. **超长会话按时间窗拆，带重叠**：单会话超过预算 → 切成带 `OVERLAP` 条重叠的窗口，
   每个片段头部回带**上一窗口的最后 N 条**，尾部**预告下一窗口**（前后文不丢）。
3. **小会话按时间顺序打包**：一周里大量只有几条消息的会话，按时间顺序合并进同一片段，
   同时保留会话边界标记 —— 这样模型能看到「同期背景」。

三态分开登记（对应任务书要求）
------------------------------
  extracted  正文已提取（本脚本产出即置 1）
  modeled    已送进模型（由调用方回写）
  analyzed   模型分析完成（由调用方回写）

用法
----
  python tools\chunk_weeks.py --build      # 生成片段
  python tools\chunk_weeks.py --report     # 统计
"""
import os, io, re, sys, csv, json, glob, time, sqlite3, datetime, argparse, traceback

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
BATCH = os.path.join(WS, "_tmp", "batch")
DB = os.path.join(BATCH, "batch.sqlite")
WEEKDIR = os.path.join(BATCH, "weeks")
CHUNKDIR = os.path.join(BATCH, "chunks")

BUDGET = 30000      # 每片段目标字符数（≈18,750 token）
OVERLAP = 0         # ★ 正文不重叠（避免重复计数）；前后文改用「回带 / 预告」单独给
CTX_HEAD = 25       # 片段头部回带的「上文」条数（只作衔接，不计入正文与 token 估算）
CTX_TAIL = 5        # 片段尾部预告的「下文」条数

UNREADABLE = ("当前版本不支持展示该内容", "请升级至最新版本")


# ──────────────────────────────────────────────────────── DB
def db():
    c = sqlite3.connect(DB)
    c.execute("""create table if not exists chunks(
        cid text primary key, week text, lo text, hi text,
        session_key text, session_name text, session_type text,
        kind text,            -- single / window / pack
        nmsg integer, mine integer, theirs integer,
        nchars integer, est_tokens integer,
        path text, extracted integer default 0,
        modeled integer default 0, analyzed integer default 0,
        note text)""")
    c.execute("create index if not exists ix_chunks_week on chunks(week)")
    c.commit()
    return c


# ──────────────────────────────────────────────────────── 渲染
def clean(s, limit=1200):
    s = (s or "").replace("\r", " ").replace("\n", " ").strip()
    s = re.sub(r"\s{2,}", " ", s)
    return s[:limit]


def is_unreadable(s):
    return any(k in (s or "") for k in UNREADABLE)


def render_msg(m, prev_sess=None):
    r = m.get("r")
    who = "我" if r == "me" else ("系统" if r == "system" else "对方")
    c = clean(m.get("c"))
    t = (m.get("t") or "")[11:16]
    y = m.get("y") or ""
    if is_unreadable(c):
        c = "[不可读] link 卡片 —— 导出时未落正文（内容缺失，不得据此推断）"
    tag = ("〔%s〕" % y) if y and y not in ("text", "txt") else ""
    return "- `%s` **%s**%s：%s" % (t, who, tag, c)


def header_lines(week, lo, hi, sname, stype, kind, n, note=""):
    L = ["# %s ｜ %s → %s ｜ %s" % (week, lo, hi, sname),
         "",
         "> 会话类型：%s ｜ 片段类型：%s ｜ 消息 %d 条%s" % (stype, kind, n, (" ｜ " + note) if note else ""),
         "> ★ 读法：`我` = 本人；`对方` = 该会话另一方；`〔link〕` 等方括号为消息类型标记。",
         "> ★ 纪律：`[不可读]` 的消息**内容缺失**，不得据此推断任何事实。",
         ""]
    return L


# ──────────────────────────────────────────────────────── 主流程
def build(limit_weeks=None):
    os.makedirs(CHUNKDIR, exist_ok=True)
    c = db()
    c.execute("delete from chunks")
    c.commit()

    files = sorted(glob.glob(os.path.join(WEEKDIR, "*.jsonl")))
    if limit_weeks:
        files = files[:limit_weeks]

    rows = []
    t0 = time.time()
    tot_chars = 0

    for fp in files:
        # ---- 读一周 ----
        head = None
        sessions = []          # [(sess_meta, [msgs])]
        cur = None
        for line in io.open(fp, encoding="utf-8"):
            o = json.loads(line)
            if "week" in o:
                head = o
            elif "session_key" in o:
                cur = (o, [])
                sessions.append(cur)
            else:
                if cur is not None:
                    cur[1].append(o)
        if not head:
            continue
        week, lo, hi = head["week"], head["lo"], head["hi"]
        wdir = os.path.join(CHUNKDIR, week)
        os.makedirs(wdir, exist_ok=True)

        # ---- 超长会话：按时间窗拆，带重叠 ----
        smalls = []
        for meta, msgs in sessions:
            sname = meta.get("session_name") or meta.get("session_key")
            stype = meta.get("session_type") or ""
            skey = meta.get("session_key") or ""
            chars = sum(len(m.get("c") or "") for m in msgs)
            if chars <= BUDGET:
                smalls.append((meta, msgs, chars))
                continue
            # 切窗
            i = 0
            wi = 0
            while i < len(msgs):
                j = i
                acc = 0
                while j < len(msgs) and acc < BUDGET:
                    acc += len(msgs[j].get("c") or "")
                    j += 1
                win = msgs[i:j]
                wi += 1
                cid = "%s_%s_w%02d" % (week, re.sub(r"[^\w]", "", skey)[:12] or "s", wi)
                L = header_lines(week, lo, hi, sname, stype, "window",
                                 len(win), "第 %d 窗 ｜ 上文回带 %d 条" % (wi, min(CTX_HEAD, i)))
                if i > 0:
                    L += ["## ↑ 上文回带（上一窗末尾 %d 条，仅供衔接，不重复计入）" % min(CTX_HEAD, i), ""]
                    L += [render_msg(m) for m in msgs[max(0, i - CTX_HEAD):i]]
                    L += ["", "## 本片段正文", ""]
                else:
                    L += ["## 本片段正文", ""]
                L += [render_msg(m) for m in win]
                if j < len(msgs):
                    L += ["", "## ↓ 下文预告（下一窗开头 %d 条，仅供衔接）" % min(CTX_TAIL, len(msgs) - j), ""]
                    L += [render_msg(m) for m in msgs[j:j + CTX_TAIL]]
                body = "\n".join(L)
                p = os.path.join(wdir, "%02d_%s.md" % (wi, re.sub(r"[^\w\u4e00-\u9fff]", "", sname)[:20] or "s"))
                io.open(p, "w", encoding="utf-8").write(body)
                nc = sum(len(m.get("c") or "") for m in win)
                rows.append((cid, week, lo, hi, skey, sname, stype, "window",
                             len(win), meta.get("mine") or 0, meta.get("theirs") or 0,
                             nc, int(nc / 1.6), p, 1, 0, 0, "第 %d 窗" % wi))
                tot_chars += nc
                i = j   # ★ 正文不重叠；前后文由「回带 / 预告」提供

        # ---- 小会话：按时间顺序打包 ----
        if smalls:
            buf, buf_chars, buf_n, buf_mine, idx = [], 0, 0, 0, 0
            pack = []
            def flush():
                nonlocal buf, buf_chars, buf_n, buf_mine, idx, pack
                if not buf:
                    return
                idx += 1
                cid = "%s_pack%02d" % (week, idx)
                L = header_lines(week, lo, hi,
                                 "本周 %d 个会话（打包）" % len(pack), "混合", "pack",
                                 buf_n, "含 %d 个会话" % len(pack))
                L += ["", "## 会话清单", ""]
                for nm, nt, nn in pack:
                    L.append("- **%s**（%s）%d 条" % (nm, nt, nn))
                L += ["", "## 正文（按时间顺序，会话切换处有分隔）", ""]
                L += buf
                body = "\n".join(L)
                p = os.path.join(wdir, "pack%02d.md" % idx)
                io.open(p, "w", encoding="utf-8").write(body)
                rows.append((cid, week, lo, hi, "", "本周 %d 个会话（打包）" % len(pack),
                             "混合", "pack", buf_n, buf_mine, buf_n - buf_mine,
                             buf_chars, int(buf_chars / 1.6), p, 1, 0, 0, ""))
                buf, buf_chars, buf_n, buf_mine = [], 0, 0, 0
                pack = []

            for meta, msgs, chars in smalls:
                sname = meta.get("session_name") or meta.get("session_key")
                stype = meta.get("session_type") or ""
                if buf_chars + chars > BUDGET and buf:
                    flush()
                if not buf:
                    pack = []
                buf.append("### 〔%s〕%s" % (stype, sname))
                buf += [render_msg(m) for m in msgs]
                buf.append("")
                buf_chars += chars
                buf_n += len(msgs)
                buf_mine += meta.get("mine") or 0
                pack.append((sname, stype, len(msgs)))
                tot_chars += chars
            flush()

    c.executemany("""insert or replace into chunks
        (cid,week,lo,hi,session_key,session_name,session_type,kind,nmsg,mine,theirs,
         nchars,est_tokens,path,extracted,modeled,analyzed,note)
        values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", rows)
    c.commit()
    return len(rows), tot_chars, time.time() - t0


def report(c):
    tot = c.execute("select count(*),coalesce(sum(nchars),0),coalesce(sum(est_tokens),0),"
                    "coalesce(sum(nmsg),0) from chunks").fetchone()
    print("=" * 78)
    print("片段切分现状")
    print("=" * 78)
    print("片段 %s 个 ｜ 字符 %s ｜ est_tokens %s ｜ 覆盖消息 %s 条"
          % ("{:,}".format(tot[0]), "{:,}".format(tot[1]),
             "{:,}".format(tot[2]), "{:,}".format(tot[3])))
    print("\n三态：")
    for k, lab in [("extracted", "已提取正文"), ("modeled", "已送入模型"), ("analyzed", "模型分析完成")]:
        n = c.execute("select count(*) from chunks where %s=1" % k).fetchone()[0]
        print("  %-12s %7d" % (lab, n))
    print("\n按片段类型：")
    for r in c.execute("select kind,count(*),sum(nchars),sum(est_tokens) from chunks group by 1"):
        print("  %-8s %6d 个 ｜ %s 字符 ｜ est %s" % (r[0], r[1], "{:,}".format(r[2] or 0),
                                                      "{:,}".format(r[3] or 0)))
    print("\n按周（前 10 与后 6）：")
    wk = list(c.execute("select week,count(*),sum(nchars),sum(est_tokens) from chunks "
                        "group by 1 order by 1"))
    for r in wk[:10] + ([("…", "", "", "")] if len(wk) > 16 else []) + wk[-6:]:
        if r[0] == "…":
            print("  …")
        else:
            print("  %-10s %4d 片 ｜ %9s 字符 ｜ est %s" % (r[0], r[1], "{:,}".format(r[2] or 0),
                                                           "{:,}".format(r[3] or 0)))
    big = c.execute("select cid,nchars,est_tokens from chunks order by nchars desc limit 5").fetchall()
    print("\n最大片段 TOP5（用于验证没超上下文）：")
    for r in big:
        print("  %-40s %8s 字符 ｜ est %s" % (r[0][:40], "{:,}".format(r[1]), "{:,}".format(r[2])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--weeks", type=int, default=None, help="只处理前 N 周（调试）")
    a = ap.parse_args()
    c = db()
    if a.build or not a.report:
        n, ch, dt = build(a.weeks)
        print("生成片段 %s 个 ｜ %s 字符 ｜ %.1f 秒" % ("{:,}".format(n), "{:,}".format(ch), dt))
    report(c)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
