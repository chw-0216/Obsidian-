# -*- coding: utf-8 -*-
"""brief.py — 会话速览：每个会话取首尾若干行，快速了解是谁、在谈什么"""
import os
import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DIR = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\_tmp\readable"
TARGETS = sys.argv[1:] if len(sys.argv) > 1 else None

for fn in sorted(os.listdir(DIR)):
    if not fn.endswith(".txt"):
        continue
    name = fn[:-4]
    if TARGETS and not any(t in name for t in TARGETS):
        continue
    lines = open(os.path.join(DIR, fn), encoding="utf-8").read().split("\n")
    head = lines[0] if lines else ""
    body = [l for l in lines if l.startswith("[") or l.startswith("═══")]
    print(f"\n{'='*70}")
    print(head)
    print("── 开头 ──")
    for l in body[:18]:
        print("  " + l[:120])
    if len(body) > 34:
        print("── 结尾 ──")
        for l in body[-12:]:
            print("  " + l[:120])
