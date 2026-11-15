"""审核导出：生成待用户确认的审核文件。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def export_for_review(
    result: dict,
    round_name: str,
    output_dir: Path,
) -> Path:
    """将分析结果导出为待审核文件。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"review-{round_name}-{timestamp}.json"

    review = {
        "round": round_name,
        "exported_at": utc_now(),
        "status": "pending_review",
        "result": result,
        "user_decisions": [],
    }

    output_path.write_text(
        json.dumps(review, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def confirm_fact(
    fact_id: str,
    fact_content: str,
    reviews_dir: Path,
) -> None:
    """记录用户确认的事实。"""
    path = reviews_dir / "user-confirmed-facts.jsonl"
    entry = {
        "id": fact_id,
        "content": fact_content,
        "confirmed_at": utc_now(),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def reject_inference(
    inference_id: str,
    reason: str,
    reviews_dir: Path,
) -> None:
    """记录用户否决的推断。"""
    path = reviews_dir / "rejected-inferences.jsonl"
    entry = {
        "id": inference_id,
        "reason": reason,
        "rejected_at": utc_now(),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def add_correction(
    target_type: str,
    target_id: str,
    correction: str,
    reviews_dir: Path,
) -> None:
    """记录用户的纠正。"""
    path = reviews_dir / "corrections.jsonl"
    entry = {
        "target_type": target_type,
        "target_id": target_id,
        "correction": correction,
        "corrected_at": utc_now(),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    print("export_review.py — 审核导出模块")
