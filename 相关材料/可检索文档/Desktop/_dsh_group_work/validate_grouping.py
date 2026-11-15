# -*- coding: utf-8 -*-
"""独立校验：不依赖 build_grouping.py 的映射，仅比对输出与输入/任务口径。"""
import csv
import json
import re
from pathlib import Path

DESKTOP = Path(r"C:\Users\wardc\Desktop")
WORK = DESKTOP / "_dsh_group_work"
OUT = DESKTOP / "DSH工作区"
CAT = WORK / "members-catalog.csv"
CSV_OUT = OUT / "00_DSH会话分组清单_20261023.csv"
DOC_OUT = OUT / "00_DSH会话主题分组_20261023.md"
RECON = WORK / "reconciliation.json"

GROUPS = ["家庭事务", "人物与沟通", "学业/导师与课程", "艺术创作与三维", "校友会与公益",
          "AI平台与开发", "微信与WeFlow", "电脑/网络与文件", "清理候选"]
EXPECT = {"家庭事务": 3, "人物与沟通": 10, "学业/导师与课程": 12, "艺术创作与三维": 12,
          "校友会与公益": 5, "AI平台与开发": 38, "微信与WeFlow": 9, "电脑/网络与文件": 25,
          "清理候选": 17}
CLEANUP = {
    "问候": {"0eb2e8b3", "1f0b9e50", "5827a765", "c42d903c", "8e63796a", "ded4545a", "e486acb6"},
    "连接测试": {"21b86e63", "462b05a2", "b3dacc62", "cc9f1164"},
    "Arduino 重试": {"49d8f9de", "551ca214", "66eafaf7", "6e97fb86", "99247e2b", "e804e95c"},
}
KEEP6 = {"db5d2b39", "f957f9f8", "bb0a3305", "7e808edf", "1d5f7c4c", "68437449"}
problems = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ((" :: " + detail) if detail and not cond else ""))
    if not cond:
        problems.append(name + " " + detail)


cat = {r["id"]: r for r in csv.DictReader(open(CAT, encoding="utf-8-sig", newline=""))}
rows = list(csv.DictReader(open(CSV_OUT, encoding="utf-8-sig", newline="")))
doc = DOC_OUT.read_text(encoding="utf-8")

check("131 data rows (no header)", len(rows) == 131, f"got {len(rows)}")
check("ID unique", len({r["id"] for r in rows}) == 131)
check("all catalog IDs covered", set(r["id"] for r in rows) == set(cat), "missing/extra ids")
check("id is full UUID", all(re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", r["id"]) for r in rows))
check("current_name matches catalog",
      all(r["current_name"] == cat[r["id"]]["title"] for r in rows))
check("prefix matches catalog",
      all(r["prefix"] == cat[r["id"]]["prefix"] for r in rows))
check("archived matches catalog",
      all(r["archived"] == cat[r["id"]]["archived"] for r in rows))
check("pinned matches catalog",
      all(r["pinned"] == cat[r["id"]]["pinned"] for r in rows))

groups = {}
for r in rows:
    groups.setdefault(r["group"], []).append(r)
check("group names exact set", set(groups) == set(GROUPS), str(set(groups)))
check("group counts match expected",
      all(len(groups[g]) == EXPECT[g] for g in GROUPS),
      json.dumps({g: len(groups.get(g, [])) for g in GROUPS}, ensure_ascii=False))
check("group sum 131", sum(len(v) for v in groups.values()) == 131)

cleanup_ids = {r["id"][:8] for r in groups.get("清理候选", [])}
check("cleanup total 17", len(cleanup_ids) == 17)
for kind, ids in CLEANUP.items():
    check(f"cleanup {kind} = {len(ids)}", ids <= cleanup_ids and
          {r["id"][:8] for r in groups.get("清理候选", []) if r["id"][:8] in ids} == ids)
check("cleanup kinds sum 17", sum(len(v) for v in CLEANUP.values()) == 17)

archived = sum(1 for r in rows if r["archived"] == "True")
pinned = sum(1 for r in rows if r["pinned"] == "True")
check("archived 54", archived == 54, f"got {archived}")
check("pinned 10", pinned == 10, f"got {pinned}")
check("visible 77", 131 - archived == 77)

check("keep6 all present and not cleanup", all(k in {r["id"][:8] for r in rows} for k in KEEP6)
      and all(not ({r["id"][:8] for r in rows if r["id"][:8] == k} <= cleanup_ids) for k in KEEP6))
check("keep6 recommendation 保留·归回主题",
      all(r["recommendation"] == "保留·归回主题" for r in rows if r["id"][:8] in KEEP6))

layers = {r["id"][:8]: r["layer"] for r in rows}
check("layer values valid", set(layers.values()) <= {"S", "A", "B", "C", "D", "未分层"})
check("layers S10 A34 B38 C24 D23",
      {k: sum(1 for v in layers.values() if v == k) for k in "SABCD"} ==
      {"S": 10, "A": 34, "B": 38, "C": 24, "D": 23})
check("unlayered = 2 (new sessions)", sum(1 for v in layers.values() if v == "未分层") == 2)

# 文档覆盖：131 个 8 位 ID 都应出现在正文中
missing_in_doc = [i[:8] for i in cat if i[:8] not in doc]
check("131 IDs all appear in doc", not missing_in_doc, str(missing_in_doc[:5]))
check("doc mentions 131 rows", "131" in doc)
check("doc mentions archived 54", "归档 54" in doc or "54" in doc)
check("doc mentions cleanup 7/4/6", "问候 7" in doc and "连接测试 4" in doc and "Arduino 重试 6" in doc)
check("doc mentions no-delete statement", "实际删除 0 条" in doc)
check("doc mentions cwd limit", "cwd" in doc and "Desktop" in doc)
check("doc has 8 group summary rows",
      all(f"| {g} | {EXPECT[g]} |" in doc for g in GROUPS[:8]))
check("doc has cleanup table 17 rows",
      len(re.findall(r"\| 归档观察·不删除 \|", doc)) == 17)
check("doc diff row AI 37->38", "| AI平台与开发 | 37 | 37 | 38 | +1 |" in doc)

recon = json.loads(RECON.read_text(encoding="utf-8"))
check("recon checks rows 131", recon["checks"]["rows"] == 131)
check("recon checks sum 131", recon["checks"]["groupSum"] == 131)
check("recon checks archived 54", recon["checks"]["archived"] == 54)
check("recon checks pinned 10", recon["checks"]["pinned"] == 10)
check("recon base130 matches previous", recon["checks"]["base130MatchesPrevious"] is True)
check("recon csv sha present", bool(recon["outputs"]["csv"]["sha256"]))
check("recon doc sha present", bool(recon["outputs"]["doc"]["sha256"]))

print()
print("PROBLEMS:", len(problems))
for p in problems:
    print(" -", p)
