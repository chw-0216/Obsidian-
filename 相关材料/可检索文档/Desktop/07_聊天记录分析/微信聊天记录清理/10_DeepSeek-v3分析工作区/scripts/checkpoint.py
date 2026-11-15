"""checkpoint.py — 强制上下文续接检查点：原子更新 SESSION-HANDOFF.md 与 RUN-STATE.json。

用法（PowerShell）：
  python scripts/checkpoint.py `
    --milestone "MILESTONE-ID" `
    --phase "event-center-phase1" `
    --status "running|completed|paused" `
    --note "一句话说明" `
    --done "已完成项（可重复）" --pending "未完成项（可重复）" `
    --next "下一步命令（可重复）" --risk "风险（可重复）" `
    [--recovery "恢复命令（可重复）"]

行为：
  1. 读 .checkpoint/state.json（规范状态，不存在则从现有 SESSION-HANDOFF.md 初始化背景叙事）。
  2. 追加一条检查点记录到 state 与 .checkpoint/log.jsonl。
  3. 从模板重新生成 SESSION-HANDOFF.md（保留历史背景）。
  4. 合并更新 RUN-STATE.json（保留既有全部字段，新增/覆盖 phase/status/next_step/context_continuation）。
  5. 全部通过「临时文件 + os.replace」原子写入。

本脚本自身不调用 API、不触碰数据库、只写工作区内的状态文件。
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / ".checkpoint" / "state.json"
LOG_FILE = ROOT / ".checkpoint" / "log.jsonl"
HANDOFF = ROOT / "SESSION-HANDOFF.md"
RUN_STATE = ROOT / "RUN-STATE.json"

#: 固定约束清单（与 CLAUDE.md / CONTEXT-PROTOCOL.md 保持一致）
CONSTRAINTS = [
    "只写本工作区 10_DeepSeek-v3分析工作区；01_主项目 / 09_未迁移脚本 / WeFlow 导出 / 原始库只读。",
    "只新建 _v3 版本化表；不覆盖 annotations / aggressive_* / contact_* 历史表。",
    "事件候选必须同时具备 时间 + 实体/项目词 + 任务/语义 三类信号，禁止只按日期合并。",
    "候选/证据/联系人/复核/最终判断全部回链 message_id / segment_id / candidate_id。",
    "API Token 只从环境变量读取；不打印不落盘。当前阶段不调用任何 API。",
    "不自动发送微信/外部消息；不删除原始导出。试运行并发 ≤8。",
]

DEFAULT_RECOVERY = [
    'python -m unittest discover -s tests -v',
    'python -m src.v3_events discover --db data/wechat-analysis-v3.sqlite3',
    'python -m src.v3_events bundle --db data/wechat-analysis-v3.sqlite3 --limit 30',
    'python -m src.v3_events dryrun --db data/wechat-analysis-v3.sqlite3',
]


def _utc_cn_now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")


def _load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _atomic_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _init_state() -> dict:
    state = _load_json(STATE_FILE, {})
    if not state:
        state = {
            "project": "wechat-v3-event-center",
            "phase": "event-center-phase1",
            "status": "running",
            "next_step": "",
            "recovery_commands": list(DEFAULT_RECOVERY),
            "constraints": list(CONSTRAINTS),
            "checkpoints": [],
            "background_md": "",
        }
        old = _read_text(HANDOFF)
        if old:
            state["background_md"] = old
    return state


def _next_prompt(state: dict, latest: dict) -> str:
    if latest.get("next"):
        cmd = " && ".join(latest["next"][:1]) or "（见检查点日志）"
    else:
        cmd = "（见检查点日志）"
    return (
        "请先读 CLAUDE.md、CONTEXT-PROTOCOL.md、SESSION-HANDOFF.md、RUN-STATE.json，"
        "运行「恢复命令」验证未回退，然后继续下一步：\n\n  " + cmd
        + "\n\n任何 API 或扩大范围的动作先经用户确认。"
    )


def _render_handoff(state: dict, latest: dict) -> str:
    cps = list(state.get("checkpoints", []))
    log_rows = []
    for cp in reversed(cps):
        rows = [f"### {cp.get('milestone')} @ {cp.get('at')}"]
        if cp.get("note"):
            rows.append("> " + cp["note"])
        for label, key in (("已完成", "done"), ("未完成", "pending"),
                           ("风险", "risks"), ("下一步", "next")):
            items = cp.get(key) or []
            if items:
                rows.append("- **" + label + "**：" + "；".join(items))
        log_rows.append("\n".join(rows))
    log_section = "\n\n".join(log_rows) if log_rows else "（暂无）"

    rec = state.get("recovery_commands") or []
    rec_block = "\n".join("```\n" + c + "\n```" for c in rec)

    return (
        "# SESSION-HANDOFF · 微信分析 v3 工作区\n\n"
        f"更新：{state.get('updated_at')} · 阶段：{state.get('phase')} · 状态：{state.get('status')}\n\n"
        "## 新会话启动提示\n\n" + _next_prompt(state, latest) + "\n\n"
        "## 恢复命令（新会话从这里开始）\n\n" + rec_block + "\n\n"
        "## 当前状态\n\n" + (state.get("next_step") or "（见检查点日志）") + "\n\n"
        "## 检查点日志（最新在前）\n\n" + log_section + "\n\n"
        "## 项目约束\n\n" + "\n".join("- " + c for c in state.get("constraints", [])) + "\n\n"
        "## 历史背景\n\n" + (state.get("background_md") or "（无）") + "\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="写入强制上下文续接检查点（0 API）")
    ap.add_argument("--milestone", required=True, help="里程碑/检查点标识")
    ap.add_argument("--phase", default="event-center-phase1")
    ap.add_argument("--status", default="running", choices=["running", "completed", "paused"])
    ap.add_argument("--note", default="")
    ap.add_argument("--done", action="append", default=[])
    ap.add_argument("--pending", action="append", default=[])
    ap.add_argument("--next", action="append", default=[])
    ap.add_argument("--risk", action="append", default=[])
    ap.add_argument("--recovery", action="append", default=[])
    args = ap.parse_args()

    state = _init_state()
    now = _utc_cn_now()
    record = {
        "at": now,
        "milestone": args.milestone,
        "note": args.note,
        "done": args.done,
        "pending": args.pending,
        "risks": args.risk,
        "next": args.next,
    }
    state["checkpoints"].append(record)
    state["phase"] = args.phase
    state["status"] = args.status
    state["updated_at"] = now
    if args.note:
        state["next_step"] = args.note
    if args.recovery:
        state["recovery_commands"] = list(dict.fromkeys(state.get("recovery_commands", []) + args.recovery))
    if args.next:
        state["recovery_commands"] = list(dict.fromkeys(state.get("recovery_commands", []) + args.next))

    latest = record
    handoff = _render_handoff(state, latest)

    # 更新 RUN-STATE.json（保留既有字段）
    run = _load_json(RUN_STATE, {})
    run.update({
        "schema_version": run.get("schema_version", "1.2"),
        "phase": args.phase,
        "status": args.status,
        "updated_at": now,
        "next_step": state.get("next_step") or "",
        "next_step_explanation": args.note or "",
        "api_runs_in_progress": False,
    })
    ctx = run.setdefault("context_continuation", {})
    ctx.update({
        "protocol": "CONTEXT-PROTOCOL.md",
        "last_checkpoint": record["milestone"],
        "updated_at": now,
        "recovery_commands": state.get("recovery_commands"),
        "checkpoint_log": state.get("checkpoints"),
        "constraints": state.get("constraints"),
    })
    run["next_commands"] = list(dict.fromkeys(
        (run.get("next_commands") or []) + (state.get("recovery_commands") or [])))

    # 原子写入三个文件
    _atomic_write_json(STATE_FILE, state)
    _atomic_write_text(HANDOFF, handoff)
    _atomic_write_json(RUN_STATE, run)

    # 追加 log.jsonl
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"[checkpoint] {record['milestone']} @ {now} -> SESSION-HANDOFF.md + RUN-STATE.json 已原子更新")
    print(f"[checkpoint] 检查点总数：{len(state['checkpoints'])}")


if __name__ == "__main__":
    main()
