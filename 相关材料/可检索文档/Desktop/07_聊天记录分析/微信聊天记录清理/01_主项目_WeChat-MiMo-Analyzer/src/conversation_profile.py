from __future__ import annotations

import argparse
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

try:
    import jieba  # type: ignore

    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

CJK = re.compile(r"[\u4e00-\u9fff]")
NEG_MARKERS = (
    "烦", "累", "没意思", "无聊", "焦虑", "迷茫", "压力", "emo", "算了",
    "随便", "无所谓", "难", "哭", "崩溃", "绝望", "抑郁", "躺平", "摆烂",
    "不想", "讨厌", "烦死", "累死", "恶心", "无语", "窒息", "熬", "硬撑",
)
POS_MARKERS = ("开心", "喜欢", "哈哈", "有趣", "好玩", "期待", "谢谢", "棒", "爱")


def keyword_tokens(text: str) -> list[str]:
    if not text:
        return []
    if HAS_JIEBA:
        words = [w.strip().lower() for w in jieba.cut(text) if len(w.strip()) >= 2]
        return [w for w in words if not w.isdigit()]
    bigrams = []
    compact = "".join(CJK.findall(text))
    for i in range(len(compact) - 1):
        bigrams.append(compact[i : i + 2])
    return bigrams


def main() -> None:
    parser = argparse.ArgumentParser(description="输出单个会话的第一阶段本地画像")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--display-name", default="", help="会话显示名（支持片段匹配）")
    args = parser.parse_args()

    connection = sqlite3.connect(args.database)
    connection.row_factory = sqlite3.Row

    conv = connection.execute(
        "SELECT * FROM conversations WHERE display_name LIKE ? ORDER BY last_ts DESC LIMIT 1",
        (f"%{args.display_name}%",),
    ).fetchone()
    if conv is None:
        raise SystemExit("找不到会话")
    conv_id = conv["id"]
    print(f"# 会话画像：{conv['display_name']} ({conv['source_relpath']})")

    rows = connection.execute(
        "SELECT is_send, create_ts, clean_content, local_type FROM messages "
        "WHERE conversation_id=? ORDER BY create_ts, local_id, id",
        (conv_id,),
    ).fetchall()

    mine = [r for r in rows if r["is_send"]]
    hers = [r for r in rows if not r["is_send"]]
    first_ts = rows[0]["create_ts"] if rows else 0
    last_ts = rows[-1]["create_ts"] if rows else 0
    days = max(1, (last_ts - first_ts) // 86400)
    print(f"总消息 {len(rows)}：我 {len(mine)} / 对方 {len(hers)}")
    if rows:
        print(
            f"时间跨度 {datetime.fromtimestamp(first_ts):%Y-%m-%d} ~ "
            f"{datetime.fromtimestamp(last_ts):%Y-%m-%d}（约 {days} 天）"
        )

    # 月度时间线
    monthly: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        key = datetime.fromtimestamp(r["create_ts"]).strftime("%Y-%m")
        monthly[key]["我" if r["is_send"] else "对方"] += 1
    print("\n## 月度消息量")
    for month in sorted(monthly):
        c = monthly[month]
        total = c["我"] + c["对方"]
        bar = "█" * max(1, total // 40)
        print(f"{month}: 我 {c['我']:>4} | 对方 {c['对方']:>4} | 共 {total:>5} {bar}")

    # 小时分布
    hours = Counter()
    for r in hers:
        hours[datetime.fromtimestamp(r["create_ts"]).hour] += 1
    print("\n## 对方发消息的时段（小时）")
    for h in range(24):
        n = hours.get(h, 0)
        if n:
            print(f"{h:02d}时: {n:>4} {'█' * min(40, n // 4)}")

    # 回复延迟（我发 → 她回，间隔 < 24h）
    def latency_stats(prev_side: int, next_side: int, label: str) -> None:
        gaps = []
        for a, b in zip(rows, rows[1:]):
            if a["is_send"] == prev_side and b["is_send"] == next_side:
                gap = b["create_ts"] - a["create_ts"]
                if 0 < gap < 86400:
                    gaps.append(gap)
        if gaps:
            gaps.sort()
            mean = sum(gaps) / len(gaps)
            median = gaps[len(gaps) // 2]
            print(
                f"\n## {label}（N={len(gaps)}）"
                f"\n平均 {mean/60:.1f} 分钟 | 中位 {median/60:.1f} 分钟"
            )

    latency_stats(1, 0, "她回我的延迟")
    latency_stats(0, 1, "我回她的延迟")

    # 文本长度
    texts = [r["clean_content"] for r in hers if r["local_type"] == "1" and r["clean_content"]]
    if texts:
        lengths = sorted(len(t) for t in texts)
        print(
            f"\n## 她的文本消息长度（N={len(lengths)}）"
            f"\n平均 {sum(lengths)/len(lengths):.0f} 字 | 中位 {lengths[len(lengths)//2]} 字"
            f" | 最长 {lengths[-1]} 字"
        )

    # 类型分布
    types = Counter(r["local_type"] for r in rows)
    print("\n## 消息类型（localType 基类型）")
    for t, n in types.most_common(12):
        print(f"{t}: {n}")

    # 关键词（她的发言）
    tokens: Counter[str] = Counter()
    for r in hers:
        tokens.update(keyword_tokens(r["clean_content"]))
    common = {t: n for t, n in tokens.most_common(400) if n >= 3}
    if common:
        print("\n## 她发言的高频词 Top 30（可能含口语词）")
        print("、".join(f"{t}({n})" for t, n in list(common.items())[:30]))

    # 悲观/正向信号
    neg_by_month: dict[str, int] = defaultdict(int)
    pos_by_month: dict[str, int] = defaultdict(int)
    for r in hers:
        text = r["clean_content"]
        month = datetime.fromtimestamp(r["create_ts"]).strftime("%Y-%m")
        neg_by_month[month] += sum(text.count(m) for m in NEG_MARKERS)
        pos_by_month[month] += sum(text.count(m) for m in POS_MARKERS)
    print("\n## 情绪信号（她的发言，按月：悲观词 / 正向词）")
    for month in sorted(set(neg_by_month) | set(pos_by_month)):
        neg, pos = neg_by_month[month], pos_by_month[month]
        bar = "▁▂▃▄▅▆▇█"[min(7, neg // 12)] if neg else " "
        print(f"{month}: 悲观 {neg:>3} {bar} | 正向 {pos:>3}")

    connection.close()


if __name__ == "__main__":
    main()
