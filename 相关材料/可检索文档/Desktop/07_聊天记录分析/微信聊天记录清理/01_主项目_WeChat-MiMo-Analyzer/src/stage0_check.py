"""
Stage 0: Pre-flight checks for aggressive annotation pipeline.
Verifies database, API, disk, and existing progress.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen


DB_PATH = Path(r"C:\Users\wardc\Documents\New project gpt\AI-archive\apps\WeChat-MiMo-Analyzer\data\wechat-private-v2.sqlite3")
WEFLOW_ROOT = Path(r"C:\Users\wardc\Desktop\微信完整导出_2026-07-24\01_WeFlow可读导出")
API_BASE = "https://token-plan-cn.xiaomimimo.com/anthropic"


def check_database():
    """Check database state."""
    print("\n=== 1. 数据库检查 ===")
    if not DB_PATH.exists():
        print("❌ 数据库不存在！")
        return False

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Basic counts
    conv_count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    msg_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    seg_count = conn.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
    old_ann = conn.execute("SELECT COUNT(*) FROM annotations").fetchone()[0]

    print(f"✅ 数据库存在: {DB_PATH}")
    print(f"   会话数: {conv_count}")
    print(f"   消息数: {msg_count}")
    print(f"   片段数: {seg_count}")
    print(f"   旧标注: {old_ann} ({old_ann/seg_count*100:.1f}%)")

    # Check aggressive schema
    try:
        agg_count = conn.execute("SELECT COUNT(*) FROM aggressive_annotations").fetchone()[0]
        msg_ann = conn.execute("SELECT COUNT(*) FROM aggressive_message_annotations").fetchone()[0]
        ent_count = conn.execute("SELECT COUNT(*) FROM aggressive_entities").fetchone()[0]
        evt_count = conn.execute("SELECT COUNT(*) FROM aggressive_events").fetchone()[0]
        print(f"\n   激进标注已有: {agg_count} 片段 ({agg_count/seg_count*100:.1f}%)")
        print(f"   消息级标注: {msg_ann}")
        print(f"   实体提取: {ent_count}")
        print(f"   事件提取: {evt_count}")
    except sqlite3.OperationalError:
        print("\n   激进标注表尚未创建（首次运行会自动创建）")

    conn.close()
    return True


def check_weflow_data():
    """Check WeFlow export data."""
    print("\n=== 2. WeFlow 数据检查 ===")
    if not WEFLOW_ROOT.exists():
        print(f"❌ WeFlow 导出目录不存在: {WEFLOW_ROOT}")
        return False

    private_chats = list(WEFLOW_ROOT.glob("私聊_*.json"))
    print(f"✅ WeFlow 导出目录: {WEFLOW_ROOT}")
    print(f"   私聊 JSON 文件: {len(private_chats)}")

    # Sample check a few files
    errors = 0
    for f in private_chats[:3]:
        try:
            with open(f, "r", encoding="utf-8-sig") as fh:
                data = json.load(fh)
            msgs = data.get("messages", [])
            session = data.get("session", {})
            name = session.get("displayName") or session.get("nickname") or f.stem
            print(f"   ✓ {name}: {len(msgs)} 条消息")
        except Exception as e:
            print(f"   ✗ {f.name}: {e}")
            errors += 1

    if errors > 0:
        print(f"   ⚠️  {errors} 个文件解析失败")
    return True


def check_api():
    """Test API connectivity."""
    print("\n=== 3. MiMo API 检查 ===")

    # Read API key
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if not api_key:
        settings_path = Path.home() / ".claude" / "settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
                api_key = settings.get("env", {}).get("ANTHROPIC_AUTH_TOKEN", "")

    if not api_key:
        print("❌ 未找到 API Key")
        return False

    print(f"✅ API Key 已配置 (前10字符: {api_key[:10]}...)")

    # Test connection
    try:
        start = time.time()
        body = json.dumps({
            "model": "mimo-v2.5-pro",
            "max_tokens": 50,
            "messages": [{"role": "user", "content": "说一个字：好"}]
        }).encode("utf-8")

        req = Request(f"{API_BASE}/v1/messages", data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("x-api-key", api_key)
        req.add_header("anthropic-version", "2023-06-01")

        resp = urlopen(req, timeout=30)
        data = json.loads(resp.read().decode("utf-8"))
        latency = time.time() - start

        usage = data.get("usage", {})
        print(f"✅ API 连接成功 (延迟: {latency:.2f}s)")
        print(f"   模型: {data.get('model', 'unknown')}")
        print(f"   Token: 输入 {usage.get('input_tokens', '?')} / 输出 {usage.get('output_tokens', '?')}")
        return True

    except Exception as e:
        print(f"❌ API 连接失败: {type(e).__name__}: {e}")
        return False


def check_disk():
    """Check available disk space."""
    print("\n=== 4. 磁盘空间检查 ===")
    total, used, free = shutil.disk_usage(DB_PATH.parent)
    print(f"✅ C: 盘")
    print(f"   总空间: {total // (1024**3)} GB")
    print(f"   已使用: {used // (1024**3)} GB")
    print(f"   可用: {free // (1024**3)} GB")
    if free < 30 * (1024**3):
        print("⚠️  可用空间不足 30GB，可能不够用")
    return True


def check_existing_progress():
    """Check existing annotation progress."""
    print("\n=== 5. 已有进度检查 ===")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    try:
        runs = conn.execute("""
            SELECT * FROM aggressive_run_stats ORDER BY started_at DESC LIMIT 5
        """).fetchall()
        if runs:
            print(f"已有 {len(runs)} 次运行记录:")
            for run in runs:
                print(f"  Run {run['run_id']}: {run['status']} | "
                      f"完成 {run['completed_segments']}/{run['total_segments']} | "
                      f"失败 {run['failed_segments']} | "
                      f"API调用 {run['total_api_calls']} | "
                      f"开始于 {run['started_at']}")
        else:
            print("无已有运行记录（首次运行）")
    except sqlite3.OperationalError:
        print("激进标注表尚未创建")

    # Count already annotated
    try:
        annotated = conn.execute("SELECT COUNT(*) FROM aggressive_annotations").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
        remaining = total - annotated
        print(f"\n标注进度: {annotated}/{total} ({annotated/total*100:.1f}%)")
        print(f"剩余: {remaining} 个片段")
    except sqlite3.OperationalError:
        total = conn.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
        print(f"\n待标注: {total} 个片段（全部）")

    conn.close()
    return True


def estimate_time():
    """Estimate completion time."""
    print("\n=== 6. 时间估算 ===")
    conn = sqlite3.connect(str(DB_PATH))
    try:
        annotated = conn.execute("SELECT COUNT(*) FROM aggressive_annotations").fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
        remaining = total - annotated

        # Estimate based on ~3 segments/batch, ~10s per API call, 4 workers
        batches = remaining // 3 + 1
        seconds_per_batch = 12  # average including overhead
        parallel_factor = 4  # initial workers
        est_seconds = batches * seconds_per_batch / parallel_factor

        print(f"剩余片段: {remaining}")
        print(f"预估批次: {batches}")
        print(f"预估耗时 (4 workers): {est_seconds/60:.0f} 分钟 ({est_seconds/3600:.1f} 小时)")
        print(f"预估耗时 (16 workers): {est_seconds/4/60:.0f} 分钟")
        print(f"预估耗时 (32 workers): {est_seconds/8/60:.0f} 分钟")
    except:
        print("无法估算（表未创建）")
    conn.close()


def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     WeChat-MiMo Aggressive Annotation Pipeline - Stage 0       ║")
    print("║                    启动前检查                                    ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    checks = [
        ("数据库", check_database),
        ("WeFlow数据", check_weflow_data),
        ("API连接", check_api),
        ("磁盘空间", check_disk),
        ("已有进度", check_existing_progress),
        ("时间估算", estimate_time),
    ]

    results = {}
    for name, check_fn in checks:
        try:
            results[name] = check_fn()
        except Exception as e:
            print(f"❌ {name} 检查失败: {e}")
            results[name] = False

    print(f"\n{'='*60}")
    print("检查总结:")
    all_ok = True
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\n✅ 所有检查通过！可以启动全量标注。")
        print("\n启动命令:")
        print(f'  python "{Path(__file__).parent / "aggressive_executor.py"}" --workers 4')
        print(f"\n或使用启动脚本:")
        print(f'  powershell -ExecutionPolicy Bypass -File "{DB_PATH.parent.parent / "run.ps1"}"')
    else:
        print("\n❌ 部分检查未通过，请先解决问题。")


if __name__ == "__main__":
    main()
