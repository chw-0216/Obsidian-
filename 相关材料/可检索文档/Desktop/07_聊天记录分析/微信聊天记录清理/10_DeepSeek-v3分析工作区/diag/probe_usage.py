"""测量 DeepSeek usage.input_tokens 的构成：对比 (a) user_content 含 system 文本 vs (b) 不含。
只读 token 环境变量，不打印 token 值。
"""
import asyncio, json, os, sys
from pathlib import Path
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))
try:
    import aiohttp  # noqa
except ImportError:
    sys.path.insert(0, str(Path(r"C:\Users\wardc\Desktop\微信聊天记录清理\09_未迁移脚本与运行依赖\runtime\vendor")))

CONFIG = json.loads((WORKSPACE_ROOT / "config" / "v3_config.json").read_text(encoding="utf-8"))
PROMPT = (WORKSPACE_ROOT / "prompts" / "base_annotation.md").read_text(encoding="utf-8")

# 两个极短单元（真实消息），模拟合批
from src.v3_core import Unit, build_units
import sqlite3
conn = sqlite3.connect(f"file:{WORKSPACE_ROOT / 'data' / 'wechat-analysis-v3.sqlite3'}?mode=ro", uri=True)
rows = conn.execute("SELECT id, transcript FROM segments WHERE message_count BETWEEN 2 AND 3 LIMIT 2").fetchall()
conn.close()
units = []
for seg_id, transcript in rows:
    built = build_units(seg_id, transcript, "", "", 15, 0)
    if built: units.append(built[0])

# (a) 像 build_group_prompt 一样：system 文本放进 user_content
def prompt_with_system(u):
    return "\n".join([PROMPT.strip(), "", f"输入包含以下 {len(u)} 个标注单元。", "",
                      "[UNIT_START]", f"segment_id={u[0].segment_id}", "window_idx=0", "---",
                      u[0].render_for_prompt(), "[UNIT_END]", "", "只输出 JSON 数组。"])

def prompt_units_only(u):
    return "\n".join([f"[UNIT_START]", f"segment_id={u[0].segment_id}", "window_idx=0", "---",
                      u[0].render_for_prompt(), "[UNIT_END]", "", "只输出 JSON 数组。"])

async def call(session, user_content):
    body = {"model": CONFIG["model"], "max_tokens": 512,
            "thinking": {"type": "disabled"},
            "system": PROMPT,
            "messages": [{"role": "user", "content": user_content}]}
    async with session.post(f"{os.environ.get('ANTHROPIC_BASE_URL','https://api.deepseek.com/anthropic').rstrip('/')}/v1/messages",
                            data=json.dumps(body, ensure_ascii=False)) as resp:
        data = json.loads(await resp.text())
        return resp.status, (data or {}).get("usage")

async def main():
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    headers = {"Content-Type": "application/json", "x-api-key": token,
               "Authorization": f"Bearer {token}", "anthropic-version": CONFIG["api"]["api_version"]}
    async with aiohttp.ClientSession(headers=headers) as s:
        pa, ua = await call(s, prompt_with_system(units))
        pb, ub = await call(s, prompt_units_only(units))
    print(f"user_content (a) 含system: chars={len(prompt_with_system(units))} usage_in={ua.get('input_tokens') if ua else None}")
    print(f"user_content (b) 不含system: chars={len(prompt_units_only(units))} usage_in={ub.get('input_tokens') if ub else None}")
    print(f"system 文本 chars={len(PROMPT)}")
    print(f"差值（system 重复计入成本）: {ua.get('input_tokens') - ub.get('input_tokens') if ua and ub else '?'}")
    print(f"status a={pa} b={pb}")

if __name__ == "__main__":
    asyncio.run(main())
