"""冒烟测试：1 次极小调用验证端点/模型/token/格式，再启动长跑。

只打印是否成功 + usage token 数，不打印 token 值、不打印响应正文。
用法：python diag/smoke_test.py [--model deepseek-v4-pro[1m]] [--style anthropic|openai]
"""
import argparse, asyncio, json, os, sys
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WS))

def get_token():
    t = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if t:
        return t
    s = Path.home() / ".claude" / "settings.json"
    if s.exists():
        try:
            t = json.load(open(s, encoding="utf-8")).get("env", {}).get("ANTHROPIC_AUTH_TOKEN", "")
        except Exception:
            t = ""
    return t

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="deepseek-v4-pro[1m]")
    ap.add_argument("--style", default="anthropic", choices=["anthropic", "openai"])
    args = ap.parse_args()

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")
    token = get_token()
    if not token:
        print("❌ 未找到 token")
        sys.exit(2)

    from src.v3_api import ApiClient

    async def go():
        client = ApiClient(base_url, token, args.model, max_output_tokens=64,
                           api_style=args.style, disable_thinking=True)
        await client.start()
        try:
            system = "你是一个测试助手。只输出一个合法 JSON 对象。"
            user = '回复 {"ok": true}'
            result, in_tok, out_tok = await client.call(system, user)
            print(f"✅ 冒烟成功 model={args.model} style={args.style}")
            print(f"   usage in={in_tok} out={out_tok}")
            print(f"   parsed keys: {list(result.keys()) if isinstance(result, dict) else type(result).__name__}")
        except Exception as e:
            print(f"❌ 冒烟失败: {type(e).__name__}: {e}")
            sys.exit(1)
        finally:
            await client.close()

    asyncio.run(go())

if __name__ == "__main__":
    main()