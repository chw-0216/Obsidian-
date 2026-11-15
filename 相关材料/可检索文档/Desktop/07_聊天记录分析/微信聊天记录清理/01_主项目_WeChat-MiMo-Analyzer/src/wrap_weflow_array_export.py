from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="把 WeFlow 导出的裸消息数组包装为 MiMo 可导入的私聊 JSON"
    )
    parser.add_argument("--input", type=Path, required=True, help="WeFlow 导出的消息数组 JSON")
    parser.add_argument("--output", type=Path, required=True, help="输出 私聊_*.json 路径")
    parser.add_argument("--wxid", default="", help="对方 wxid（会话标识）")
    parser.add_argument("--display-name", default="", help="显示名（可用代号）")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, list):
        raise SystemExit("输入必须是消息数组")

    session = {
        "wxid": args.wxid,
        "displayName": args.display_name,
        "messageCount": len(payload),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"session": session, "messages": payload}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"wrote {args.output} with {len(payload)} messages")


if __name__ == "__main__":
    main()
