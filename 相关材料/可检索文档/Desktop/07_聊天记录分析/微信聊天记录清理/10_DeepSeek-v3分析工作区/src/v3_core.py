"""v3 核心逻辑：transcript 解析、清理、窗口、合批、校验、抽样。

本模块不发起任何网络请求，也不访问真实数据库（只接受内存/临时连接），
便于在不调用 API 的情况下做结构化测试。
"""
from __future__ import annotations

import hashlib
import html
import re
import random
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Optional


# ─── Transcript parsing ────────────────────────────────────────────────────────

# 每行格式：[id=msg_xxx][时间戳][我/对方][类型] 内容
# 类型可缺失；内容可跨行，直到下一个 [id= 行。
_HEADER_RE = re.compile(
    r"^\[id=([A-Za-z0-9_]+)\]\[([^\]]*)\]\[([^\]]*)\](?:\[([^\]]*)\])?",
    re.MULTILINE,
)


@dataclass
class ParsedMessage:
    evidence_id: str
    timestamp: str
    sender: str
    msg_type: str
    content: str      # 清理后（HTML 实体反转义、空白规整）
    redacted: str     # 送去模型前的 PII 脱敏文本
    pii_count: int = 0


def clean_text(text: str) -> str:
    """清理消息内容：HTML 实体反转义、换行规整、控制字符剔除。"""
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = "".join(ch for ch in text if ch in "\n\t" or unicodedata.category(ch) != "Cc")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("EMAIL", re.compile(r"(?i)(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+?86[- ]?)?1[3-9]\d{9}(?!\d)")),
    ("ID", re.compile(r"(?<!\d)\d{6}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[0-9Xx](?!\d)")),
    ("BANK", re.compile(r"(?<!\d)(?:\d[ -]?){16,19}(?!\d)")),
    ("IP", re.compile(r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\d)")),
)


def stable_hash8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:8]


def redact_for_model(text: str) -> tuple[str, int]:
    """将电话/邮箱/证件号/银行卡/IP 替换为 <LABEL:hash8>。返回 (脱敏文本, 替换数)。"""
    replacements = 0

    def make(label: str):
        def _repl(match: re.Match[str]) -> str:
            nonlocal replacements
            replacements += 1
            return f"<{label}:{stable_hash8(match.group(0))}>"
        return _repl

    out = text
    for label, pattern in _PII_PATTERNS:
        out = pattern.sub(make(label), out)
    return out, replacements


def parse_transcript(transcript: str) -> list[ParsedMessage]:
    """把 transcript 文本解析为消息列表。内容可跨行；找不到任何消息头时返回 []。"""
    matches = list(_HEADER_RE.finditer(transcript))
    messages: list[ParsedMessage] = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(transcript)
        raw = transcript[m.end():end].lstrip(" ")
        cleaned = clean_text(raw)
        redacted, pii_count = redact_for_model(cleaned)
        messages.append(
            ParsedMessage(
                evidence_id=m.group(1),
                timestamp=m.group(2),
                sender=m.group(3),
                msg_type=(m.group(4) or "").strip(),
                content=cleaned,
                redacted=redacted,
                pii_count=pii_count,
            )
        )
    return messages


# ─── Unit / 窗口 ───────────────────────────────────────────────────────────────

@dataclass
class Unit:
    """一个可独立调用的标注单元：整段短片段，或长片段的一个窗口。"""
    segment_id: str
    window_idx: int
    messages: list[ParsedMessage]
    segment_sha256: str = ""
    conversation_id: str = ""
    segment_message_count: int = 0  # 原始片段的总消息数（窗口单元保留，供按段统计）

    @property
    def unit_key(self) -> str:
        return f"{self.segment_id}:{self.window_idx}"

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def char_count(self) -> int:
        return sum(len(m.content) for m in self.messages)

    @property
    def expected_ids(self) -> tuple[str, ...]:
        return tuple(m.evidence_id for m in self.messages)

    @property
    def content_sha256(self) -> str:
        """单元内容哈希：用于（模型+提示词版本）去重。基于清理后的渲染文本。"""
        payload = "\n".join(
            f"[id={m.evidence_id}][{m.timestamp}][{m.sender}][{m.msg_type}] {m.content}"
            for m in self.messages
        )
        return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()

    def render_for_prompt(self) -> str:
        lines = [
            f"[id={m.evidence_id}][{m.timestamp}][{m.sender}][{m.msg_type}] {m.redacted}"
            for m in self.messages
        ]
        return "\n".join(lines)


def chunk_messages(messages: list[ParsedMessage], window_size: int) -> list[list[ParsedMessage]]:
    return [messages[i:i + window_size] for i in range(0, len(messages), window_size)]


def build_units(
    segment_id: str,
    transcript: str,
    segment_sha256: str,
    conversation_id: str = "",
    window_size: int = 15,
    segment_message_count: int = 0,
) -> list[Unit]:
    """短片段 → 单个单元；长片段 → 多个窗口单元（每个窗口只含对应文本）。"""
    msgs = parse_transcript(transcript)
    if not msgs:
        return []
    if len(msgs) <= window_size:
        return [
            Unit(
                segment_id=segment_id,
                window_idx=0,
                messages=msgs,
                segment_sha256=segment_sha256,
                conversation_id=conversation_id,
                segment_message_count=segment_message_count or len(msgs),
            )
        ]
    units = []
    for idx, window in enumerate(chunk_messages(msgs, window_size)):
        units.append(
            Unit(
                segment_id=segment_id,
                window_idx=idx,
                messages=window,
                segment_sha256=segment_sha256,
                conversation_id=conversation_id,
                segment_message_count=segment_message_count or len(msgs),
            )
        )
    return units


# ─── 合批 ──────────────────────────────────────────────────────────────────────

def estimate_output_tokens(msg_count: int) -> int:
    """根据消息数粗估单单元输出 Token（用于合批预算）。"""
    return 900 + 231 * msg_count


def make_batches(
    units: list[Unit],
    max_output_tokens: int = 6550,
    max_units_per_batch: int = 8,
    max_msgs_per_batch: int = 30,
    max_input_chars_per_batch: int = 40000,
) -> list[list[Unit]]:
    """贪心合批：短单元真正合并进同一个 API 请求；超预算的单元独占一批。

    max_input_chars_per_batch 防止长单条（如 5 万字符转发记录）拖爆上下文。
    """
    ordered = sorted(units, key=lambda u: (u.message_count, u.segment_id, u.window_idx))
    batches: list[list[Unit]] = []
    current: list[Unit] = []
    cur_tok = 0
    cur_msgs = 0
    cur_chars = 0
    for unit in ordered:
        tok = estimate_output_tokens(unit.message_count)
        if current and (
            len(current) >= max_units_per_batch
            or cur_msgs + unit.message_count > max_msgs_per_batch
            or cur_tok + tok > max_output_tokens
            or cur_chars + unit.char_count > max_input_chars_per_batch
        ):
            batches.append(current)
            current = []
            cur_tok = 0
            cur_msgs = 0
            cur_chars = 0
        current.append(unit)
        cur_tok += tok
        cur_msgs += unit.message_count
        cur_chars += unit.char_count
    if current:
        batches.append(current)
    return batches


def build_group_prompt(system: str, units: list[Unit]) -> str:
    """把多个单元渲染进同一个提示词（每个单元独立标记，长片段窗口只含自身文本）。

    system 参数仅保留兼容性，不再把系统提示词文本拼进 user 内容——
    系统提示词已通过 API 的 `system` 参数单独下发，重复拼接只会浪费输入 Token
    （且 DeepSeek 兼容端点对合批请求会把重复文本计入 usage.input_tokens）。
    """
    parts = [
        f"输入包含以下 {len(units)} 个标注单元。每个单元由 [UNIT_START] 与 [UNIT_END] 包裹。",
        "",
    ]
    for unit in units:
        parts.append("[UNIT_START]")
        parts.append(f"segment_id={unit.segment_id}")
        parts.append(f"window_idx={unit.window_idx}")
        parts.append(f"消息数: {unit.message_count}")
        parts.append("---")
        parts.append(unit.render_for_prompt())
        parts.append("[UNIT_END]")
        parts.append("")
    parts.append("请为每个单元输出一个 JSON 对象，并把所有对象放入一个 JSON 数组返回。")
    parts.append("只输出 JSON 数组，不要其他文本。")
    return "\n".join(parts)


# ─── 响应解析与拆分 ────────────────────────────────────────────────────────────

def extract_unit_results(payload: object) -> list[dict]:
    """从模型返回的解析结果中提取单元对象列表（兼容数组 / 包裹数组 / 单个对象）。"""
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        if "segment_id" in payload:
            return [payload]
        lists = [
            v for v in payload.values()
            if isinstance(v, list) and v and isinstance(v[0], dict)
        ]
        if lists:
            return max(lists, key=len)
    return []


def collect_referenced_ids(obj: dict) -> set[str]:
    """收集对象内所有引用的 evidence_id（顶层 evidence_ids 及各列表项的 evidence_ids/evidence_id）。"""
    ids: set[str] = set()
    for key in (
        "evidence_ids", "requests", "commitments", "events", "entities",
        "relationship_signals", "memory_candidates", "alternative_explanations",
    ):
        val = obj.get(key)
        if key == "evidence_ids" and isinstance(val, list):
            ids.update(x for x in val if isinstance(x, str))
        elif isinstance(val, list):
            for item in val:
                if not isinstance(item, dict):
                    continue
                for inner in ("evidence_ids", "evidence_id"):
                    v = item.get(inner)
                    if isinstance(v, list):
                        ids.update(x for x in v if isinstance(x, str))
                    elif isinstance(v, str):
                        ids.add(v)
    return ids


_STRUCT_FIELDS = (
    "requests", "commitments", "events", "entities",
    "relationship_signals", "memory_candidates", "alternative_explanations",
)


def validate_unit(obj: dict, unit: Unit) -> tuple[bool, list[str], set[str]]:
    """严格校验单个单元结果。返回 (通过?, 错误列表, 引用的证据ID集合)。"""
    errors: list[str] = []
    if not isinstance(obj, dict):
        return False, ["结果不是 JSON 对象"], set()

    if obj.get("segment_id") != unit.segment_id:
        errors.append(f"segment_id 不一致: {obj.get('segment_id')!r} != {unit.segment_id!r}")

    msgs = obj.get("messages")
    if not isinstance(msgs, list):
        errors.append("messages 不是数组")
        return False, errors, collect_referenced_ids(obj)

    returned: list[str] = []
    for idx, m in enumerate(msgs):
        if not isinstance(m, dict):
            errors.append(f"messages[{idx}] 不是对象")
            continue
        eid = m.get("evidence_id")
        if not isinstance(eid, str) or not eid:
            errors.append(f"messages[{idx}] 缺少 evidence_id")
        else:
            returned.append(eid)

    expected = set(unit.expected_ids)
    ret_set = set(returned)
    missing = expected - ret_set
    extra = ret_set - expected
    if missing:
        errors.append(f"缺少证据ID: {sorted(missing)[:8]} (共{len(missing)})")
    if extra:
        errors.append(f"多余证据ID: {sorted(extra)[:8]} (共{len(extra)})")
    if len(returned) != len(ret_set):
        errors.append("messages 中存在重复 evidence_id")

    for fname in _STRUCT_FIELDS:
        v = obj.get(fname)
        if v is not None and not isinstance(v, list):
            errors.append(f"{fname} 不是数组")

    conf = obj.get("confidence")
    if not isinstance(conf, (int, float)):
        errors.append("缺少数值型 confidence")

    referenced = collect_referenced_ids(obj)
    bogus = referenced - expected
    if bogus:
        errors.append(f"引用了输入中不存在的证据ID: {sorted(bogus)[:8]} (共{len(bogus)})")

    ok = not errors
    return ok, errors, referenced


def validate_group(results: list[dict], units: list[Unit]) -> dict[str, tuple[bool, list[str], set[str]]]:
    """按 unit_key 对整批结果分组并逐一校验。返回 {unit_key: (ok, errors, referenced)}。"""
    by_key: dict[str, dict] = {}
    for obj in results:
        seg = obj.get("segment_id")
        widx = obj.get("window_idx", 0)
        if isinstance(seg, str):
            by_key.setdefault(f"{seg}:{widx}", obj)
    out: dict[str, tuple[bool, list[str], set[str]]] = {}
    for unit in units:
        obj = by_key.get(unit.unit_key)
        if obj is None:
            out[unit.unit_key] = (False, [f"未返回 {unit.unit_key} 的结果"], set())
        else:
            out[unit.unit_key] = validate_unit(obj, unit)
    return out


def split_units(units: list[Unit], depth: int) -> list[list[Unit]]:
    """校验失败时把批次对半拆分，便于定位坏单元（最多拆分 depth 层）。"""
    if len(units) <= 1:
        return [units]
    half = (len(units) + 1) // 2
    return [units[:half], units[half:]]


# ─── 分层抽样 ──────────────────────────────────────────────────────────────────

_BUCKET_SQL = {
    "1": "s.message_count = 1",
    "2-3": "s.message_count BETWEEN 2 AND 3",
    "4-10": "s.message_count BETWEEN 4 AND 10",
    "11-30": "s.message_count BETWEEN 11 AND 30",
    "31+": "s.message_count >= 31",
}


def stratified_sample(
    conn,
    seed: int,
    per_bucket: int,
    buckets: Iterable[tuple[str, int]],
    max_total: Optional[int] = None,
) -> list[dict]:
    """按尺寸分层抽样。优先选未标注片段（annotations ∪ aggressive_annotations ∪ v3 成功）。"""
    import sqlite3
    if not isinstance(conn, sqlite3.Connection) or conn.row_factory is None:
        conn.row_factory = sqlite3.Row  # 兼容调用方未设置 row_factory 的情况
    rng = random.Random(seed)
    annotated_ids = _annotated_id_set(conn)
    selected: list[dict] = []
    for label, _min_mc in buckets:
        condition = _BUCKET_SQL[label]
        rows = conn.execute(
            f"""
            SELECT s.id, s.conversation_id, s.message_count, s.char_count,
                   s.transcript, s.content_sha256 AS segment_sha256
            FROM segments s
            WHERE {condition}
            ORDER BY s.id
            """
        ).fetchall()
        unannotated = [dict(r) for r in rows if r["id"] not in annotated_ids]
        annotated = [dict(r) for r in rows if r["id"] in annotated_ids]
        pool = unannotated if len(unannotated) >= per_bucket else unannotated + annotated
        pool = sorted(pool, key=lambda d: d["id"])
        picked = rng.sample(pool, min(per_bucket, len(pool)))
        selected.extend(picked)
        if max_total and len(selected) >= max_total:
            break
    return selected


def _annotated_id_set(conn) -> set[str]:
    ids: set[str] = set()
    for r in conn.execute("SELECT segment_id FROM annotations UNION SELECT segment_id FROM aggressive_annotations"):
        ids.add(r[0])
    for r in conn.execute("SELECT DISTINCT segment_id FROM v3_annotations WHERE status='success'"):
        ids.add(r[0])
    return ids


# ─── 重试预算 ──────────────────────────────────────────────────────────────────

@dataclass
class RetryBudget:
    max_attempts: int = 3

    def exhausted(self, attempts: int) -> bool:
        return attempts >= self.max_attempts


def compute_backoff(kind: str, attempts: int, base: float, cap: float) -> float:
    """指数退避：base * 2^(attempts-1)，封顶 cap。"""
    return min(base * (2 ** (attempts - 1)), cap)
