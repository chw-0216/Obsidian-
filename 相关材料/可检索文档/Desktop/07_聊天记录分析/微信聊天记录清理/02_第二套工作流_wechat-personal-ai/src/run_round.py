"""轮次执行器：统一的 R1-R5 执行框架。

继承旧系统的 Claude Code 调用模式：subprocess + JSON Schema + 结构化输出。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def load_prompt_template(round_name: str, prompts_dir: Path) -> str:
    """加载提示词模板。"""
    path = prompts_dir / f"{round_name}.md"
    return path.read_text(encoding="utf-8")


def load_schema(round_name: str, schemas_dir: Path) -> dict:
    """加载 JSON Schema。"""
    schema_map = {
        "round-1-observation": "round-1-observation.schema.json",
        "round-2-relationship": "round-2-relationship.schema.json",
        "round-3-self-pattern": "round-3-self-pattern.schema.json",
        "round-4-coaching": "round-4-coaching.schema.json",
        "round-5-digital-twin": "round-5-digital-twin.schema.json",
    }
    path = schemas_dir / schema_map[round_name]
    return json.loads(path.read_text(encoding="utf-8"))


def call_claude(
    claude_path: str,
    project_root: Path,
    prompt: str,
    schema: dict,
    model: str,
    max_budget_usd: float,
) -> dict:
    """调用 Claude Code + MiMo，返回结构化结果。"""
    command = [
        claude_path,
        "-p",
        "--model", model,
        "--tools", "",
        "--safe-mode",
        "--no-session-persistence",
        "--effort", "low",
        "--output-format", "json",
        "--json-schema", json.dumps(schema, ensure_ascii=False, separators=(",", ":")),
    ]
    if max_budget_usd > 0:
        command.extend(["--max-budget-usd", str(max_budget_usd)])

    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        cwd=project_root,
        timeout=300,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(f"Claude Code 返回退出码 {completed.returncode}")

    outer = json.loads(completed.stdout)
    if outer.get("is_error"):
        raise RuntimeError("MiMo 接口返回错误")

    structured = outer.get("structured_output")
    if structured is None:
        result = outer.get("result")
        structured = json.loads(result) if isinstance(result, str) else result

    return structured


def run_round(
    round_name: str,
    segments: list[dict],
    project_root: Path,
    claude_path: str,
    model: str,
    max_budget_per_batch: float,
    retries: int = 2,
) -> dict:
    """执行单轮分析。"""
    prompts_dir = project_root / "prompts"
    schemas_dir = project_root / "schemas"

    prompt_template = load_prompt_template(round_name, prompts_dir)
    schema = load_schema(round_name, schemas_dir)

    # 构建完整提示词（包含片段数据）
    prompt_parts = [prompt_template, "\n\n## 待分析数据\n"]
    for seg in segments:
        prompt_parts.append(f"\n---\nsegment_id: {seg['id']}\nmessages:\n{seg.get('transcript', '')}")
    full_prompt = "\n".join(prompt_parts)

    # 调用模型
    last_error = None
    for attempt in range(1, retries + 2):
        try:
            result = call_claude(
                claude_path, project_root, full_prompt, schema, model, max_budget_per_batch
            )
            return result
        except Exception as exc:
            last_error = exc
            if attempt <= retries:
                time.sleep(min(2 ** attempt, 8))

    raise last_error or RuntimeError("未知 MiMo 调用错误")


if __name__ == "__main__":
    print("run_round.py — 轮次执行器模块")
    print("用法：python run_round.py --round round-1-observation --database ...")
