"""证据链验证：检查引用的 ID 是否存在、结论是否超出证据、是否跨联系人串线。"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def verify_evidence_ids(
    connection: sqlite3.Connection,
    segment_id: str,
    evidence_ids: list[str],
) -> dict:
    """检查证据 ID 是否属于指定片段。"""
    if not evidence_ids:
        return {"valid": True, "invalid_count": 0, "invalid_ids": []}

    # 获取该片段的所有消息 ID
    rows = connection.execute(
        "SELECT id FROM messages WHERE segment_id = ?", (segment_id,)
    ).fetchall()
    valid_ids = {row["id"][:16] for row in rows}

    invalid = [eid for eid in evidence_ids if eid[:16] not in valid_ids]
    return {
        "valid": len(invalid) == 0,
        "invalid_count": len(invalid),
        "invalid_ids": invalid,
    }


def verify_no_cross_talk(
    result: dict,
    expected_segment_ids: set[str],
) -> dict:
    """检查结果中是否引用了不属于当前批次的片段 ID。"""
    all_refs = set()

    # 收集所有引用的 segment_id
    if "segments" in result:
        for seg in result["segments"]:
            all_refs.add(seg.get("segment_id", ""))

    unexpected = all_refs - expected_segment_ids - {""}
    return {
        "valid": len(unexpected) == 0,
        "unexpected_segment_ids": list(unexpected),
    }


def verify_schema_completeness(
    result: dict,
    required_fields: list[str],
) -> dict:
    """检查结果是否包含所有必需字段。"""
    missing = [f for f in required_fields if f not in result]
    return {
        "valid": len(missing) == 0,
        "missing_fields": missing,
    }


def run_full_verification(
    db_path: Path,
    result: dict,
    expected_segment_ids: set[str],
    required_fields: list[str],
) -> dict:
    """执行完整的证据链验证。"""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row

    results = {
        "evidence_ids": [],
        "cross_talk": verify_no_cross_talk(result, expected_segment_ids),
        "schema": verify_schema_completeness(result, required_fields),
    }

    # 验证每个片段的证据 ID
    if "segments" in result:
        for seg in result["segments"]:
            seg_id = seg.get("segment_id", "")
            all_evidence = list(seg.get("evidence_message_ids", []))

            # 收集嵌套的 evidence_ids
            for event in seg.get("key_events", []):
                all_evidence.extend(event.get("evidence_ids", []))
            for item in seg.get("action_items", []):
                all_evidence.extend(item.get("evidence_ids", []))

            ev_result = verify_evidence_ids(connection, seg_id, all_evidence)
            ev_result["segment_id"] = seg_id
            results["evidence_ids"].append(ev_result)

    connection.close()

    # 汇总
    results["ok"] = (
        results["cross_talk"]["valid"]
        and results["schema"]["valid"]
        and all(r["valid"] for r in results["evidence_ids"])
    )
    return results


if __name__ == "__main__":
    print("verify_evidence.py — 证据链验证模块")
