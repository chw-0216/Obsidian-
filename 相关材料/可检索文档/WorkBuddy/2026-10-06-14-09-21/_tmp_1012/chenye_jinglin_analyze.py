# -*- coding: utf-8 -*-
"""从陈晔会话中还原井邻项目的完整脉络。

策略：
  1) 核心词（强相关）→ 定位「井邻活跃日」
  2) 活跃日的全部对话 → 作为上下文窗口纳入
  3) 按主题聚类 → 输出结构化 JSON，供撰写梳理文档
"""
import json, collections, os, re, datetime

OUT = r"C:\Users\wardc\WorkBuddy AI\2026-10-06-14-09-21\_tmp_1012"
rows = [json.loads(l) for l in open(os.path.join(OUT, "_chenye_all.jsonl"), encoding="utf-8")]
for r in rows:
    r["ts"] = r["t"]

# ---- 核心词：出现即说明当天在谈井邻 ----
CORE = ["井邻", "洞台", "渤海镇", "驻村", "工作站", "植墨", "偏移四型", "四型",
        "MBTI", "八版", "飞鸟", "栗蓬", "栗子", "栗壳", "怀柔", "动漫谷", "开街"]
# ---- 辅助词：井邻工作内容（用于主题归类，不单独定日）----
AUX = ["丝网", "网版", "制版", "正片", "硫酸纸", "菲林", "晒版", "刮印", "套印", "套色",
       "版画", "印制", "印刷", "工作坊", "体验", "油墨", "造纸",
       "接待", "来访", "到访", "区委", "政协", "组织部", "宣传部", "文旅", "科学城",
       "领导", "区长", "书记", "讲解", "英文", "物料", "采购", "安装", "空调",
       "水槽", "展区", "布展", "海报", "易拉宝", "马慧楠", "技师", "关总", "王总",
       "汇报", "中期", "PPT", "讲稿", "答辩", "T恤", "恤", "胸牌", "承诺", "低碳"]

# 1) 找活跃日
active = collections.Counter()
for r in rows:
    if any(k in r["body"] for k in CORE):
        active[r["day"]] += 1
days = sorted(active)
print("井邻核心词覆盖天数:", len(days))
print("首日:", days[0] if days else "-", " 末日:", days[-1] if days else "-")

# 2) 活跃日 → 扩展为「连续段」（相邻日期<=3天视为同一段）
segs = []
for d in days:
    dd = datetime.date.fromisoformat(d)
    if segs and (dd - segs[-1][1]).days <= 3:
        segs[-1][1] = dd
    else:
        segs.append([dd, dd])
print("\n连续段:", len(segs))
for a, b in segs:
    n = sum(1 for r in rows if a <= datetime.date.fromisoformat(r["day"]) <= b)
    print("  %s → %s  (%d天, %d条)" % (a, b, (b - a).days + 1, n))

# 3) 段内全部对话 = 井邻语料
def in_seg(day):
    d = datetime.date.fromisoformat(day)
    return any(a <= d <= b for a, b in segs)

corpus = [r for r in rows if in_seg(r["day"])]
print("\n井邻语料总条数:", len(corpus))

# 4) 主题归类
THEME = {
    "A 缘起与策划": ["井邻", "策划", "方案", "植墨", "概念", "理念", "低碳", "合约", "游戏", "期货"],
    "B 工作站建设": ["工作站", "建设", "水槽", "空调", "安装", "采购", "物料", "柜子", "展区", "布展", "房东", "邻里"],
    "C 接待与来访": ["接待", "来访", "到访", "区委", "政协", "组织部", "宣传部", "文旅", "科学城", "领导", "区长", "书记", "讲解", "英文", "开街", "动漫谷"],
    "D 制版与工艺": ["丝网", "网版", "制版", "正片", "硫酸纸", "菲林", "晒版", "刮印", "套印", "套色", "油墨", "印制", "印刷", "栗"],
    "E 交互与原型": ["偏移四型", "四型", "MBTI", "八版", "飞鸟", "手势", "MediaPipe", "交互", "原型", "数字"],
    "F 汇报与材料": ["汇报", "中期", "PPT", "讲稿", "答辩", "总结", "成果", "申报", "海报", "宣传"],
    "G 教学与课程": ["课程", "课", "学生", "教学", "同学", "大三", "大四", "研一", "研二"],
}
theme_idx = collections.defaultdict(list)
for r in corpus:
    for th, kws in THEME.items():
        if any(k in r["body"] for k in kws):
            theme_idx[th].append(r)
            break

print("\n主题分布:")
for th in THEME:
    print("  %-14s %d 条" % (th, len(theme_idx[th])))

json.dump(corpus, open(os.path.join(OUT, "_chenye_corpus.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
print("\n已写 _chenye_corpus.json")
