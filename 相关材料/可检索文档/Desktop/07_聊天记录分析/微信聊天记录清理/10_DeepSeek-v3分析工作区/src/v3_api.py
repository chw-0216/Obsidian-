"""v3 异步 API 客户端：Anthropic 兼容 /v1/messages 与 OpenAI 兼容 /v1/chat/completions。

- Anthropic 兼容：DeepSeek 官方端点（默认，api_style="anthropic"）。
- OpenAI 兼容：NVIDIA 免费层等 OpenAI 风格端点（api_style="openai"）。
- 全局限速：rpm_limit > 0 时用令牌桶保证全部并发调用合计 ≤ rpm 次/分钟（40 RPM 等）。
- Token 只从环境变量读取，由执行器注入；本模块不打印、不写盘、不记录 Token 值。
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional


class RateLimitError(Exception):
    pass


class ApiError(Exception):
    pass


#: aiohttp 回退导入目录（只读；本机无 aiohttp 时使用与执行器一致的 vendor 目录）
_DEFAULT_VENDOR_DIR = str(
    Path(__file__).resolve().parent.parent.parent
    / "09_未迁移脚本与运行依赖" / "runtime" / "vendor"
)


def _ensure_vendor(vendor_dir: Optional[str]) -> None:
    """把 aiohttp 的 vendor 目录加入 sys.path（幂等）。"""
    for cand in (vendor_dir, _DEFAULT_VENDOR_DIR):
        if not cand:
            continue
        if Path(cand).joinpath("aiohttp").exists() and cand not in sys.path:
            sys.path.insert(0, cand)
            return


def extract_text(data: dict) -> str:
    parts = []
    for block in data.get("content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts).strip()


def extract_openai_text(data: dict) -> str:
    """OpenAI 兼容响应解析：choices[0].message.content 可为字符串或内容块数组。
    如果 content 为空，则尝试读取 reasoning_content（某些代理会把长 prompt 的
    输出放到 reasoning_content 字段）。"""
    try:
        msg = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        raise ValueError("响应中没有 choices[0].message")
    content = msg.get("content")
    if content is None or content == "":
        content = msg.get("reasoning_content", "")
    if content is None or content == "":
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts).strip()
    return str(content).strip()


def _extract_json(text: str) -> Any:
    """用括号深度匹配提取最外层 JSON 片段（容忍模型输出前后废话）。"""
    start_idx = -1
    for i, ch in enumerate(text):
        if ch in "[{":
            start_idx = i
            break
    if start_idx < 0:
        raise ValueError("响应中没有 JSON")
    depth = 0
    in_str = False
    escape = False
    for i in range(start_idx, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start_idx:i + 1])
    raise ValueError("JSON 未闭合")


def parse_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[A-Za-z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _extract_json(text)


class TokenBucket:
    """全局限速令牌桶（asyncio）。

    保证所有并发调用合计 ≤ rpm 次/分钟：令牌按 rpm/60 每秒补充，桶容量 = burst
    （默认 2，允许小幅突发但不失控）。acquire() 在令牌不足时 sleep 到有令牌为止。
    """

    def __init__(self, rpm: float, burst: int = 2):
        self.rpm = max(float(rpm), 0.001)
        self.capacity = max(int(burst), 1)
        self._tokens = float(self.capacity)
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                self._tokens = min(
                    self.capacity,
                    self._tokens + (now - self._last) * self.rpm / 60.0,
                )
                self._last = now
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                # 距下一个令牌的时间
                deficit = (1.0 - self._tokens) * 60.0 / self.rpm
                await asyncio.sleep(min(deficit, 5.0))


class ApiClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        model: str,
        max_output_tokens: int,
        api_version: str = "2023-06-01",
        request_timeout: float = 120,
        connect_timeout: float = 15,
        vendor_dir: Optional[str] = None,
        disable_thinking: bool = True,
        api_style: str = "anthropic",
        rpm_limit: Optional[float] = None,
        rate_burst: int = 2,
    ):
        self.base_url = base_url.rstrip("/")
        self.disable_thinking = disable_thinking
        self.token = token
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.api_version = api_version
        self.request_timeout = request_timeout
        self.connect_timeout = connect_timeout
        if api_style not in ("anthropic", "openai"):
            raise ValueError(f"未知 api_style: {api_style!r}")
        self.api_style = api_style
        self.rate_limiter = TokenBucket(rpm_limit, burst=rate_burst) if rpm_limit and rpm_limit > 0 else None

        _ensure_vendor(vendor_dir)
        import aiohttp  # noqa: F401
        self._aiohttp = __import__("aiohttp")
        self._session: Any = None

    @property
    def url(self) -> str:
        if self.api_style == "openai":
            return f"{self.base_url}/chat/completions"
        return f"{self.base_url}/v1/messages"

    async def start(self) -> None:
        timeout = self._aiohttp.ClientTimeout(
            total=self.request_timeout, connect=self.connect_timeout
        )
        connector = self._aiohttp.TCPConnector(limit=16, limit_per_host=16, ttl_dns_cache=120)
        if self.api_style == "openai":
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            }
        else:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.token,
                "Authorization": f"Bearer {self.token}",
                "anthropic-version": self.api_version,
            }
        self._session = self._aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
            trust_env=True,  # 走系统代理(HTTP_PROXY/HTTPS_PROXY/NO_PROXY),直连 IP 已被 NVIDIA 限死
        )

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    def build_body(self, system: str, user_content: str) -> dict:
        if self.api_style == "openai":
            body = {
                "model": self.model,
                "max_tokens": self.max_output_tokens,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
            }
            # 禁用思维链，确保输出落在 content 而非 reasoning_content
            if self.disable_thinking:
                body["thinking"] = {"type": "disabled"}
            return body
        body = {
            "model": self.model,
            "max_tokens": self.max_output_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user_content}],
        }
        # DeepSeek Anthropic 兼容端点默认启用思维链，会耗尽 max_tokens 预算且不产出
        # type=text 块，导致 extract_text 为空。显式禁用，确保输出落在 text 块。
        if self.disable_thinking:
            body["thinking"] = {"type": "disabled"}
        return body

    async def call(self, system: str, user_content: str) -> tuple[Any, int, int]:
        if self.rate_limiter is not None:
            await self.rate_limiter.acquire()
        body = self.build_body(system, user_content)
        data = json.dumps(body, ensure_ascii=False)
        try:
            async with self._session.post(self.url, data=data) as resp:
                if resp.status == 429:
                    text = await resp.text()
                    err = RateLimitError(f"HTTP 429 Rate Limited: {text[:200]}")
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after:
                        try:
                            err.retry_after = float(retry_after)
                        except (TypeError, ValueError):
                            err.retry_after = None
                    raise err
                if resp.status != 200:
                    text = await resp.text()
                    raise ApiError(f"HTTP {resp.status}: {text[:300]}")
                raw = await resp.text()
        except (asyncio.TimeoutError, self._aiohttp.ServerTimeoutError) as exc:
            raise TimeoutError(f"request timeout: {exc}") from exc
        except self._aiohttp.ClientError as exc:
            raise ApiError(f"network error: {type(exc).__name__}: {exc}") from exc

        data = json.loads(raw)
        usage = data.get("usage", {}) or {}
        # Anthropic 格式 input_tokens/output_tokens；OpenAI 兼容格式 prompt_tokens/completion_tokens
        in_tok = int(usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0) or 0)
        out_tok = int(usage.get("output_tokens", 0) or usage.get("completion_tokens", 0) or 0)
        if self.api_style == "openai":
            text = extract_openai_text(data)
        else:
            text = extract_text(data)
        parsed = parse_json(text)
        return parsed, in_tok, out_tok
