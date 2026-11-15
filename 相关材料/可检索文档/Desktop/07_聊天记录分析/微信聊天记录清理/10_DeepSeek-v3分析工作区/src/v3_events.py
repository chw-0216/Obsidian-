"""v3 事件中心 · 第一阶段：全库无 API 事件候选发现 + 时间窗口 / 跨联系人检索基础设施。

原则（本模块强制）：
- 每个事件候选**必须同时**具备三类信号：时间 + 实体/项目词 + 任务/语义线索，禁止只按日期合并；
- 时间窗口 = 证据消息时间戳聚簇 + 相对时间词解析（今天/明天/周X/X月X日…）；
- 跨联系人检索 = 强实体（人名/项目/地点词）在不同会话中的合并；
- 一切可回链：candidate_id / message_id / segment_id / conversation_id。

零 API。只读源表，写入新建的 `_v3_event_*` 表。

运行：
  python -m src.v3_events dryrun   --db data/wechat-analysis-v3.sqlite3   # 只读统计+报告
  python -m src.v3_events discover --db data/wechat-analysis-v3.sqlite3   # 计算并落库
  python -m src.v3_events bundle   --db data/wechat-analysis-v3.sqlite3 --limit 30
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from .v3_io import utc_now, write_json_atomic

# ─────────────────────────────────────────────────────────────────────────────
# 常量与词汇
# ─────────────────────────────────────────────────────────────────────────────

#: 排除的噪声/系统/自我传输会话（微信自身通道）
EXCLUDE_CONVERSATIONS: tuple[str, ...] = (
    "文件传输助手", "美团", "微信团队", "微信公众平台", "公众平台安全助手",
    "微信ClawBot", "我", "公众号", "订阅号", "服务号",
)

#: 高价值上下文词（命中即强信号 + 加分；扩范围复核优先覆盖对象）
KEY_CONTEXT_TERMS: tuple[str, ...] = (
    "陈老师", "舒泽林", "舒哥", "格拉斯哥", "格拉", "Glasgow",
    "井邻", "周冉", "校友会", "协会",
)

#: 特定专有项目词 = 可作跨会话/跨日「合并键」的项目词（防止 上海/中介/公众号 等通用词过度合并）
STRONG_PROJECT_GLOSSARY: tuple[str, ...] = (
    "格拉斯哥", "格拉", "Glasgow", "井邻", "校友会", "协会", "学生会",
    "宣发", "社团", "招生", "迎新",
)

#: 人名（显式）+ 项目/组织词（显式）
PEOPLE_GLOSSARY: tuple[str, ...] = (
    "陈老师", "舒泽林", "舒哥", "周冉", "马姐", "马慧楠", "龙彦西", "陈昶文",
    "薛伟东", "王若彤", "甘泉", "沐茜妍", "小苹果", "张宝", "陈飞老师", "杨丁懿",
    "巩世峰", "金钰", "汪伊俊", "李紫懿", "郑英泽", "张雅婷", "李佳杨", "蔡峰峰",
)
PROJECT_GLOSSARY: tuple[str, ...] = (
    "格拉斯哥", "格拉", "Glasgow", "校友会", "协会", "井邻", "学生会", "社团",
    "宣发", "海报", "公众号", "推文", "场地", "赞助", "义卖", "迎新", "讲座",
    "招生", "报名表", "活动", "论文", "答辩", "开题", "终稿", "初稿", "查重",
    "盲审", "实习", "毕业", "签证", "机票", "酒店", "宿舍", "房东", "中介",
    "项目", "方案", "合同", "报价", "交付", "对接",
)
PLACES_GLOSSARY: tuple[str, ...] = (
    "英国", "伦敦", "格拉斯哥", "爱丁堡", "曼彻斯特", "北京", "上海", "广州",
    "深圳", "杭州", "武汉", "成都", "重庆", "南京", "苏州", "香港", "澳门",
    "央美", "湖北", "湖南", "广东",
)

#: 常见姓氏（用于从联系人名派生 姓氏+称谓 词）
COMMON_SURNAMES: str = (
    "张王李赵刘陈杨黄周吴徐孙马胡朱郭何罗高林郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤"
)

#: 姓氏+称谓 派生词权重（中等强度）
HONORIFICS: tuple[str, ...] = ("老师", "姐", "哥", "总", "学长", "学姐", "教授", "经理", "医生")

#: 时间引用模式：(正则, 类型, 权重)
TIME_PATTERNS: tuple[tuple[re.Pattern, str, float], ...] = (
    (re.compile(r"今天|今日|今晚|今天上午|今天下午|今天中午"), "today", 4.0),
    (re.compile(r"明天|明日|明晚|明早|明天上午|明天下午"), "tomorrow", 4.0),
    (re.compile(r"后天"), "day+2", 3.0),
    (re.compile(r"大后天"), "day+3", 3.0),
    (re.compile(r"昨天|昨日|昨晚|昨天晚上"), "day-1", 3.0),
    (re.compile(r"前天"), "day-2", 2.0),
    (re.compile(r"这周|本周|这礼拜|这星期"), "this_week", 3.0),
    (re.compile(r"下周|下礼拜|下星期"), "next_week", 3.0),
    (re.compile(r"上周|上礼拜|上星期"), "last_week", 2.0),
    (re.compile(r"[周星期礼拜][一二三四五六日天]"), "weekday", 3.0),
    (re.compile(r"(\d{1,2})\s*月\s*(\d{1,2})\s*(?:日|号)?"), "month_day", 5.0),
    (re.compile(r"(\d{1,2})\s*月(?:份|底|初|中)?"), "month", 2.0),
    (re.compile(r"凌晨|清晨|早上|上午|中午|下午|傍晚|晚上|夜里|半夜|深夜"), "time_of_day", 2.0),
    (re.compile(r"(\d{1,2})\s*[点时](?:\s*(\d{1,2})\s*分?|半|一刻|整)?"), "hour", 2.5),
    (re.compile(r"过年|春节|除夕|元宵|中秋|端午|清明|五一|国庆|元旦|圣诞|跨年|暑假|寒假"), "holiday", 3.0),
)

#: 任务/语义线索模式：(正则, 类别, 权重)
TASK_PATTERNS: tuple[tuple[re.Pattern, str, float], ...] = (
    (re.compile(r"约(?:好|了|一下|个|时间)?|见面|碰面|赴约|聚餐|聚会|吃饭|吃个饭|喝茶|咖啡|约饭"), "appoint", 3.0),
    (re.compile(r"出发|起飞|落地|航班|机票|高铁|火车票|船票|签证|托运|行李额|行李|回国|出国|返程|去机场|接机|送机|酒店|住宿|订房"), "travel", 3.0),
    (re.compile(r"看房|租房|租房子|搬家|搬|入住|退租|房东|中介|押金|房租|合租|拼住|室友|装修"), "house", 3.0),
    (re.compile(r"转账|转钱|报销|付款|收款|发红包|红包|收款码|支付宝|定金|尾款|AA"), "money", 2.5),
    (re.compile(r"论文|答辩|开题|终稿|初稿|查重|盲审|pre-|presentation|毕设|毕论"), "thesis", 3.0),
    (re.compile(r"面试|offer|入职|简历|笔试|实习|秋招|春招|转正|内推|投递|招聘"), "job", 3.0),
    (re.compile(r"完成|搞定|弄完|办完|提交|交付|写完|做完|弄好|通过|报完|交完"), "done", 2.0),
    (re.compile(r"商量|讨论|沟通|确认|同步|对齐|碰一下|过一下|对一下|对接"), "discuss", 2.5),
    (re.compile(r"安排|计划|打算|准备|筹备|策划|定下来|敲定|规划"), "plan", 2.5),
    (re.compile(r"体检|看病|医院|牙|药|检查|复诊|挂号|医生|发烧|咳嗽|手术|住院"), "health", 3.0),
    (re.compile(r"上课|考试|作业|复习|成绩|选课|课表|课程|考完|期中|期末"), "study", 2.5),
    (re.compile(r"开会|会议|例会|腾讯会议|会议链接|zoom|汇报|present"), "meeting", 3.0),
    (re.compile(r"报名|申请|投递|递交|报名表|名额|占位"), "apply", 2.5),
)

#: 常用词停用列表（递归词发现时排除）
BIGRAM_STOP: set[str] = {
    "我们", "你们", "他们", "她们", "自己", "大家", "一个", "一些", "什么", "怎么",
    "这样", "那样", "这个", "那个", "这里", "那里", "现在", "已经", "还是", "就是",
    "不是", "因为", "所以", "如果", "然后", "但是", "而且", "虽然", "不过", "可以",
    "应该", "知道", "觉得", "感觉", "真的", "非常", "特别", "时候", "时间", "事情",
    "问题", "东西", "地方", "今天", "明天", "后天", "昨天", "前天", "晚上", "上午",
    "下午", "中午", "早上", "凌晨", "以后", "之前", "这些", "那些", "别人", "其他",
    "另外", "还有", "或者", "之后", "先不", "不会", "不要", "没有", "有点", "一些",
    "出来", "回去", "过来", "一起", "一下", "一点", "一个", "的话", "的人", "的事",
    "我了", "了你", "来了", "去啊", "好的", "是的", "行吧", "好吧", "哈哈", "嗯嗯",
    "哦哦", "哎呀", "这样子", "那种", "这种", "每个", "每次", "很快", "赶紧", "随便",
    "反正", "其实", "虽然", "甚至", "只是", "比如", "比如", "包括", "关于", "根据",
    "通过", "由于", "以及", "并且", "或者", "因而", "为此", "因此", "所以",
    "老师", "感谢", "需要", "朋友", "同学", "学习", "开始", "可能", "不用", "没事",
    "给你", "收到", "咱们", "都是", "你的", "我的", "他的", "她的", "回来", "出去",
    "进去", "过来", "起来", "上去", "下去", "回去", "看看", "了解", "继续", "已经",
    "这么", "那么", "怎么", "为什么", "什么样", "一下", "一下下", "谢谢", "客气",
}

#: 聚类参数
RUN_GAP_SECONDS = 12 * 3600        # 同一会话内信号消息成「活动段」的最大间隔
LINK_GAP_SECONDS = 7 * 86400       # 同一强实体跨段/跨会话合并的最大间隔
MIN_MSGS_PER_CANDIDATE = 2         # 候选最少信号消息数
DISCOVER_TERM_MIN_CONVS = 3        # 递归项目词最少会话数
DISCOVER_TERM_MIN_MSGS = 8         # 递归项目词最少消息数
DISCOVER_TERM_TOP = 60

#: DEEP-REVIEW-SPEC：稳定人格/关系/沟通模式所需的最小独立已确认事件数。
#: 未达到时，该结论只能标为「暂定假设」（tentative），不得当作稳定结论。
STABILITY_REQUIRED_EVENTS = 3

#: 深度分析状态机（无 API 阶段只允许前两种，绝不假装已完成模型级深度推理）。
ANALYSIS_STATUS_RETRIEVAL_READY = "retrieval_ready"        # 证据包+槽位已就绪，待深度分析
ANALYSIS_STATUS_PENDING_DEEP = "pending_deep_analysis"     # 已入深度分析队列（待用户确认 token 预算后执行）

#: 结论条目的事实/推测/未知状态
FACT_STATUS_FACT = "fact"
FACT_STATUS_INFERRED = "inferred"
FACT_STATUS_UNKNOWN = "unknown"

#: 深度分析槽位键（预填档案中这些键在无 API 阶段必须为空/占位）
DEEP_ANALYSIS_SLOTS: tuple[str, ...] = (
    "deep_hypotheses", "alternative_hypotheses", "relationship_profile",
    "value_assumptions", "communication_advice",
)


@dataclass
class MsgSignal:
    message_id: str
    conversation_id: str
    segment_id: Optional[str]
    create_ts: int
    text: str
    is_send: int
    sender_name: Optional[str]
    time_signals: list[dict] = field(default_factory=list)
    entity_signals: list[dict] = field(default_factory=list)
    task_signals: list[dict] = field(default_factory=list)
    score: float = 0.0


@dataclass
class Run:
    conversation_id: str
    display_name: str
    msgs: list[MsgSignal] = field(default_factory=list)
    start_ts: int = 0
    end_ts: int = 0
    strong_entities: set[str] = field(default_factory=set)
    all_entities: set[str] = field(default_factory=set)
    tasks: set[str] = field(default_factory=set)
    time_types: set[str] = field(default_factory=set)
    resolved_dates: set[str] = field(default_factory=set)
    time_ref_texts: set[str] = field(default_factory=set)

    def finish(self) -> "Run":
        self.start_ts = min(m.create_ts for m in self.msgs)
        self.end_ts = max(m.create_ts for m in self.msgs)
        for m in self.msgs:
            for e in m.entity_signals:
                self.all_entities.add(e["term"])
                # 强合并键 = 特定人名 或 特定专有项目词；通用地点/通用项目词不作为合并键
                if (e["kind"] == "person" and e["weight"] >= 3.0) or e["term"] in STRONG_PROJECT_GLOSSARY:
                    self.strong_entities.add(e["term"])
            for t in m.task_signals:
                self.tasks.add(t["category"])
            for t in m.time_signals:
                self.time_types.add(t["type"])
                self.time_ref_texts.add(t["text"])
                if t.get("resolved"):
                    self.resolved_dates.add(t["resolved"])
        return self


# ─────────────────────────────────────────────────────────────────────────────
# 信号提取
# ─────────────────────────────────────────────────────────────────────────────

_CJK = re.compile(r"[一-鿿]")


def _is_cjk(ch: str) -> bool:
    return "一" <= ch <= "鿿"


def derive_honorifics(display_name: str) -> list[str]:
    """从联系人名派生「姓氏+称谓」词（如 陈昶文 → 陈老师/陈姐/陈哥/陈总）。"""
    name = re.sub(r"[^一-鿿]", "", display_name)
    if not (2 <= len(name) <= 4):
        return []
    if name[0] not in COMMON_SURNAMES:
        return []
    return [name[0] + h for h in HONORIFICS]


def _clean_text(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"\[[^\]]*\]", " ", text)          # [表情] [位置] 等占位
    t = re.sub(r"[｜|、。；，：！？·…（）()《》<>\"'“”‘’\s]+", " ", t)
    return t.strip()


def extract_time_signals(text: str) -> list[dict]:
    """返回 [{type, text, weight, resolved}]，resolved 为可解析的绝对日期(YYYY-MM-DD)。"""
    out: list[dict] = []
    for pat, ttype, weight in TIME_PATTERNS:
        for m in pat.finditer(text):
            resolved = None
            if ttype == "month_day" and m.group(1) and m.group(2):
                resolved = "%04d-%02d-%02d" % (2000, int(m.group(1)), int(m.group(2)))
            out.append({
                "type": ttype,
                "text": m.group(0),
                "weight": weight,
                "resolved": resolved,
            })
    return out


def resolve_single(sig: dict, ts: int) -> Optional[str]:
    """把单个时间信号解析成消息时间戳附近的绝对日期字符串。"""
    t = sig["type"]
    dt = datetime.fromtimestamp(ts).date()
    if t == "today":
        return dt.isoformat()
    if t == "tomorrow":
        return (dt + timedelta(days=1)).isoformat()
    if t in ("day+2", "day+3"):
        return (dt + timedelta(days=int(t.split("+")[1]))).isoformat()
    if t in ("day-1", "day-2"):
        return (dt - timedelta(days=int(t.split("-")[1]))).isoformat()
    if t in ("this_week",):
        return dt.isoformat()
    if t == "next_week":
        return (dt + timedelta(days=7)).isoformat()
    if t == "last_week":
        return (dt - timedelta(days=7)).isoformat()
    if t == "weekday":
        wmap = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
        for ch, w in wmap.items():
            if ch in sig["text"]:
                return (dt + timedelta(days=(w - dt.weekday()) % 7)).isoformat()
        return None
    if t == "month_day":
        m = re.match(r"(\d{1,2})月(\d{1,2})", sig["text"])
        if not m:
            return None
        mm, dd = int(m.group(1)), int(m.group(2))
        for y in (dt.year - 1, dt.year, dt.year + 1):
            try:
                d = datetime(y, mm, dd).date()
            except ValueError:
                continue
            if abs((d - dt).days) <= 365:
                return d.isoformat()
        return None
    if t == "month":
        m = re.search(r"(\d{1,2})\s*月", sig["text"])
        if m:
            for y in (dt.year - 1, dt.year, dt.year + 1):
                if abs((datetime(y, int(m.group(1)), 1).date() - dt).days) <= 365:
                    return f"{y}-{int(m.group(1)):02d}-01"
        return None
    return None


def resolve_time_refs(time_signals: list[dict], ts: int) -> tuple[list[str], str]:
    """返回 (resolved_dates, certainty)。certainty: fact(有绝对日期) / inferred(相对) / unknown。"""
    dates: set[str] = set()
    has_abs = False
    has_rel = False
    for s in time_signals:
        r = resolve_single(s, ts)
        if r:
            dates.add(r)
            if s["type"] == "month_day":
                has_abs = True
            else:
                has_rel = True
    if has_abs:
        return sorted(dates), "fact"
    if has_rel:
        return sorted(dates), "inferred"
    return [], "unknown"


def extract_entity_signals(text: str, derived_honorifics: list[str]) -> list[dict]:
    """返回 [{term, kind, weight}]。person/project/place 来自词汇表，派生称谓为 person。"""
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def push(term: str, kind: str, weight: float) -> None:
        key = (term, kind)
        if key in seen:
            return
        seen.add(key)
        out.append({"term": term, "kind": kind, "weight": weight})

    for term in PEOPLE_GLOSSARY:
        if term in text:
            push(term, "person", 4.0)
    for term in PROJECT_GLOSSARY:
        if term in text:
            push(term, "project", 3.0)
    for term in PLACES_GLOSSARY:
        if term in text:
            push(term, "place", 3.0)
    for term in derived_honorifics:
        if term in text:
            push(term, "person", 3.0)
    # 泛用「姓氏+称谓」：仅单姓氏字 + 称谓（避免 万吗老师/丁堡总 这类噪声）
    for m in re.finditer(
        r"([" + COMMON_SURNAMES + r"])(老师|姐|哥|总|学长|学姐|教授|经理|医生)",
        text,
    ):
        push(m.group(1) + m.group(2), "person", 3.0)
    return out


def extract_task_signals(text: str) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for pat, category, weight in TASK_PATTERNS:
        if pat.search(text) and category not in seen:
            seen.add(category)
            m = pat.search(text)
            out.append({"category": category, "keyword": m.group(0) if m else "", "weight": weight})
    return out


def extract_message_signals(
    message_id: str,
    conversation_id: str,
    segment_id: Optional[str],
    create_ts: int,
    text: str,
    is_send: int,
    sender_name: Optional[str],
    derived_honorifics: list[str],
    discovered_terms: list[str],
) -> MsgSignal:
    sig = MsgSignal(
        message_id=message_id,
        conversation_id=conversation_id,
        segment_id=segment_id,
        create_ts=create_ts,
        text=text,
        is_send=is_send,
        sender_name=sender_name,
    )
    cleaned = _clean_text(text)
    if not cleaned:
        return sig

    time_signals = extract_time_signals(cleaned)
    for s in time_signals:
        s["resolved"] = resolve_single(s, create_ts)

    sig.time_signals = time_signals
    sig.entity_signals = extract_entity_signals(cleaned, derived_honorifics)
    sig.task_signals = extract_task_signals(cleaned)

    # 递归发现的低权重项目词
    for term in discovered_terms:
        if term in cleaned:
            sig.entity_signals.append({"term": term, "kind": "discovered", "weight": 1.5})

    sig.score = (
        sum(s["weight"] for s in sig.time_signals)
        + sum(s["weight"] for s in sig.entity_signals)
        + sum(s["weight"] for s in sig.task_signals)
    )
    return sig


# ─────────────────────────────────────────────────────────────────────────────
# 递归项目词发现（跨会话频繁字词，低权重）
# ─────────────────────────────────────────────────────────────────────────────

def discover_recurring_terms(conn: sqlite3.Connection) -> list[str]:
    """统计跨会话高频 CJK 双字词（排除停用词），返回 top 列表。

    过滤：去掉表情占位；双字均须为汉字；出现在中等数量的会话（≥3 且 ≤30）；
    每会话平均消息数 ≤6（太普遍的词视为功能词）；排除停用词与助词尾字。
    """
    conv_counter: Counter[str] = Counter()
    msg_counter: Counter[str] = Counter()
    cur = conn.execute(
        """
        SELECT conversation_id, clean_content FROM messages
        WHERE message_type='文本消息' AND clean_content IS NOT NULL AND length(clean_content) > 0
        """
    )
    tail_chars = set("的了着呢吧吗啊呀哦嗯嘛")
    func_chars = set("你我他她它们这那哪些么什来来去就又还在都要会把让给跟对从为以于和或但而如之其候吧呢先也再全很真")
    for conv_id, text in cur:
        text = re.sub(r"\[[^\]]*\]", "", text or "")       # 去掉 [旺柴] 等表情占位
        text = re.sub(r"[^一-鿿]", "", text)
        if not text:
            continue
        seen_in_msg: set[str] = set()
        for i in range(len(text) - 1):
            bg = text[i:i + 2]
            if bg in BIGRAM_STOP or bg[0] in tail_chars or bg[1] in tail_chars:
                continue
            if bg[0] in func_chars or bg[1] in func_chars:
                continue
            seen_in_msg.add(bg)
        for bg in seen_in_msg:
            conv_counter[bg] += 1
            msg_counter[bg] += 1
    out = [
        bg for bg, c in conv_counter.items()
        if c >= DISCOVER_TERM_MIN_CONVS and c <= 30
        and msg_counter[bg] >= DISCOVER_TERM_MIN_MSGS
        and msg_counter[bg] / c <= 6
    ]
    out.sort(key=lambda bg: (conv_counter[bg], msg_counter[bg]), reverse=True)
    return out[:DISCOVER_TERM_TOP]


# ─────────────────────────────────────────────────────────────────────────────
# 活动段聚类 → 候选链接
# ─────────────────────────────────────────────────────────────────────────────

def build_runs(signals: list[MsgSignal], conversation_id: str, display_name: str) -> list[Run]:
    """把某会话的信号消息按时间间隔聚成活动段。"""
    runs: list[Run] = []
    current: list[MsgSignal] = []
    for m in signals:
        if not current or m.create_ts - current[-1].create_ts <= RUN_GAP_SECONDS:
            current.append(m)
        else:
            runs.append(Run(conversation_id, display_name, msgs=current).finish())
            current = [m]
    if current:
        runs.append(Run(conversation_id, display_name, msgs=current).finish())
    return runs


def link_candidates(runs: list[Run]) -> list[dict]:
    """跨段/跨会话合并 → 事件候选。

    合并规则（同时满足）：
      1. 共享 ≥1 个强实体（person/project/place，weight≥3）；
      2. 时间窗口间隔 ≤ LINK_GAP，或共享某个解析出的绝对日期。
    同一强实体组内按时间顺序游走，间隔超过 LINK_GAP 则另起候选（避免跨月大杂烩）。
    """
    by_entity: dict[str, list[Run]] = {}
    for r in runs:
        for e in r.strong_entities:
            by_entity.setdefault(e, []).append(r)

    groups: list[list[Run]] = []
    for runs_for_entity in by_entity.values():
        runs_for_entity.sort(key=lambda r: r.start_ts)
        chain: list[Run] = []
        for r in runs_for_entity:
            if not chain:
                chain = [r]
                continue
            prev = chain[-1]
            gap_ok = r.start_ts - prev.end_ts <= LINK_GAP_SECONDS
            share_date = bool(r.resolved_dates & prev.resolved_dates)
            if gap_ok or share_date:
                chain.append(r)
            else:
                groups.append(chain)
                chain = [r]
        if chain:
            groups.append(chain)

    candidates: list[dict] = []
    seen_sig: set[tuple] = set()
    for chain in groups:
        msgs: list[MsgSignal] = []
        for r in chain:
            for m in r.msgs:
                msgs.append(m)
        msgs.sort(key=lambda m: m.create_ts)
        if len(msgs) < MIN_MSGS_PER_CANDIDATE:
            continue

        strong: set[str] = set()
        all_ent: set[str] = set()
        tasks: set[str] = set()
        time_types: set[str] = set()
        resolved_dates: set[str] = set()
        time_ref_texts: set[str] = set()
        for r in chain:
            strong |= r.strong_entities
            all_ent |= r.all_entities
            tasks |= r.tasks
            time_types |= r.time_types
            resolved_dates |= r.resolved_dates
            time_ref_texts |= r.time_ref_texts

        # 候选必须三类信号齐全（时间 + 实体 + 任务）
        if not (time_types and all_ent and tasks):
            continue

        start_ts = msgs[0].create_ts
        end_ts = msgs[-1].create_ts
        sig = (tuple(sorted(strong)), start_ts, msgs[0].message_id)
        if sig in seen_sig:
            continue
        seen_sig.add(sig)

        cand = {
            "candidate_id": _cand_id(strong, start_ts, msgs[0].message_id),
            "strong_entities": sorted(strong),
            "entity_terms": sorted(all_ent),
            "task_categories": sorted(tasks),
            "time_types": sorted(time_types),
            "time_ref_texts": sorted(time_ref_texts),
            "resolved_dates": sorted(resolved_dates),
            "start_ts": start_ts,
            "end_ts": end_ts,
            "msgs": msgs,
            "conv_ids": sorted({m.conversation_id for m in msgs}),
            "day_span": round((end_ts - start_ts) / 86400, 2),
            "msg_count": len(msgs),
        }
        cand.update(score_candidate(cand))
        candidates.append(cand)
    return candidates


def _cand_id(strong: set[str], start_ts: int, first_msg_id: str) -> str:
    h = hashlib.sha256("|".join(sorted(strong) + [str(start_ts), first_msg_id]).encode("utf-8"))
    return "evc_" + h.hexdigest()[:16]


def score_candidate(cand: dict) -> dict:
    strong = set(cand["strong_entities"])
    tasks = set(cand["task_categories"])
    time_types = set(cand["time_types"])
    msg_count = cand["msg_count"]
    day_span = cand["day_span"]
    conv_count = len(cand["conv_ids"])
    key_hit = any(t in strong for t in KEY_CONTEXT_TERMS)
    project_terms = {e for e in cand["entity_terms"] if e in PROJECT_GLOSSARY or e in PLACES_GLOSSARY}
    discovered = {e for e in cand["entity_terms"] if e not in PROJECT_GLOSSARY and e not in PLACES_GLOSSARY and e not in PEOPLE_GLOSSARY}

    score = (
        5.0 * len(strong)
        + 2.0 * len(project_terms)
        + 1.0 * len(discovered & set(cand["entity_terms"]))
        + 3.0 * len(tasks)
        + 1.5 * len(time_types)
        + 1.0 * min(msg_count, 10)
        + (3.0 if day_span >= 2 else 0.0)
        + 4.0 * (conv_count - 1)
        + (6.0 if key_hit else 0.0)
    )
    return {
        "signal_score": round(score, 2),
        "project_terms": sorted(project_terms),
        "discovered_terms": sorted(discovered),
        "conversation_count": conv_count,
        "key_context": key_hit,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 展示辅助
# ─────────────────────────────────────────────────────────────────────────────

CATEGORY_LABELS: dict[str, str] = {
    "appoint": "约/见面", "travel": "出行/旅行", "house": "租房/搬家", "money": "财务/转账",
    "thesis": "论文/学业", "job": "求职/实习", "done": "事项完成", "discuss": "沟通/讨论",
    "plan": "计划/筹备", "health": "健康/就医", "study": "学习/考试", "meeting": "会议",
    "apply": "报名/申请",
}


def dominant_task(cand: dict) -> str:
    """按证据消息的任务信号权重取主导任务类别（避免按字母序显示）。"""
    weights: dict[str, float] = {}
    for m in cand["msgs"]:
        for t in m.task_signals:
            weights[t["category"]] = weights.get(t["category"], 0.0) + t["weight"]
    if not weights:
        return (cand["task_categories"][:1] or [""])[0]
    return max(weights, key=weights.get)


def make_title(cand: dict) -> str:
    strong = cand["strong_entities"]
    head = " · ".join(strong[:2]) if strong else "（无强实体）"
    cat = dominant_task(cand)
    label = CATEGORY_LABELS.get(cat, cat) if cat else "事项"
    return f"{head} · {label}"


def make_description(cand: dict) -> str:
    parts = []
    if cand.get("resolved_dates"):
        parts.append("提到日期 " + "/".join(cand["resolved_dates"][:4]))
    if cand.get("time_ref_texts"):
        parts.append("时间词 " + "、".join(cand["time_ref_texts"][:6]))
    if cand.get("task_categories"):
        parts.append("线索 " + "、".join(cand["task_categories"][:5]))
    return "；".join(parts)


def time_certainty_of(cand: dict) -> str:
    ttypes = set(cand["time_types"])
    if ttypes & {"month_day"}:
        return "fact"
    if ttypes & {"today", "tomorrow", "weekday", "day+2", "day+3", "day-1", "day-2"}:
        return "inferred"
    return "unknown"


def _ts_iso(ts: int) -> str:
    """把 Unix 秒时间戳转成本地可读时间（仅展示）。"""
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except (OSError, OverflowError, ValueError):
        return str(ts)


def _ds_iso(ts: int) -> str:
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
    except (OSError, OverflowError, ValueError):
        return str(ts)


def assess_stability(supporting_event_count: int) -> dict:
    """稳定结论判定：稳定的人格/关系/沟通模式至少需要 3 个独立已确认事件。

    返回 {status: 'tentative'|'stable', required, supporting_events}。
    未达到 3 个时只能写为「暂定假设」，不得当成稳定结论。
    """
    required = STABILITY_REQUIRED_EVENTS
    status = "stable" if supporting_event_count >= required else "tentative"
    return {
        "status": status,
        "required": required,
        "supporting_events": int(supporting_event_count or 0),
    }


def build_analysis_profile(cand: dict, display_names: dict[str, str]) -> dict:
    """生成无 API 阶段的深度预填判断档案（analysis_profile）。

    诚实边界（DEEP-REVIEW-SPEC 改动一）：
    - `facts`：只含确定性证据可推导的事实（时间范围、参与者、主导任务、解析日期、强实体），
      每条带 evidence_ids 回链与 fact/inferred/unknown 状态、置信度。
    - 深度槽位（deep_hypotheses / alternative_hypotheses / relationship_profile /
      value_assumptions / communication_advice）：无 API 阶段一律为空列表或 None，
      analysis_status=retrieval_ready，明示「待深度分析阶段填充」，绝不假装模型已推理。
    - `counter_evidence`：反证槽位，本阶段为空数组，但 schema 与展示均保留该槽位。
    - `conclusion_stability`：无 API 阶段没有已确认事件，一律 tentative。
    """
    cid = cand["candidate_id"]
    ev_ids = {m.message_id: _evidence_id_for(m.message_id, cid) for m in cand["msgs"]}

    facts: list[dict] = []

    # 1. 时间范围（确定性事实，来自消息时间戳）
    facts.append({
        "statement": f"消息时间范围 {_ts_iso(cand['start_ts'])} ~ {_ts_iso(cand['end_ts'])}"
                     f"（{int(cand['day_span'])} 天跨度，{cand['msg_count']} 条信号消息）",
        "status": FACT_STATUS_FACT,
        "confidence": 1.0,
        "evidence_ids": [ev_ids[cand["msgs"][0].message_id], ev_ids[cand["msgs"][-1].message_id]],
        "kind": "event_time",
    })

    # 2. 参与者（确定性事实，来自跨会话回链）
    conv_names = [display_names.get(c, c) for c in cand["conv_ids"]]
    facts.append({
        "statement": f"涉及联系人：{'、'.join(conv_names)}（{cand['conversation_count']} 个会话）",
        "status": FACT_STATUS_FACT,
        "confidence": 1.0,
        "evidence_ids": [ev_ids[m.message_id] for m in cand["msgs"][:3]],
        "kind": "participants",
    })

    # 3. 主导任务类别（确定性，来自任务信号；但「具体做了什么」需深度分析）
    cat = dominant_task(cand)
    cat_label = CATEGORY_LABELS.get(cat, cat) or "事项"
    task_msgs = [m for m in cand["msgs"] if m.task_signals]
    facts.append({
        "statement": f"主导任务线索：{cat_label}",
        "status": FACT_STATUS_FACT,
        "confidence": 0.8,
        "evidence_ids": [ev_ids[m.message_id] for m in task_msgs[:3]] or [ev_ids[cand["msgs"][0].message_id]],
        "kind": "dominant_task",
    })

    # 4. 解析出的日期（确定性事实，若 resolve_single 解析成功）
    if cand.get("resolved_dates"):
        facts.append({
            "statement": "提到日期：" + "、".join(cand["resolved_dates"][:5]),
            "status": FACT_STATUS_FACT,
            "confidence": 0.7,
            "evidence_ids": [ev_ids[m.message_id] for m in cand["msgs"] if m.time_signals][:3],
            "kind": "resolved_dates",
        })

    # 5. 强实体（确定性，来自实体信号）
    if cand.get("strong_entities"):
        ent_msgs = [m for m in cand["msgs"] if m.entity_signals]
        facts.append({
            "statement": "关键实体：" + "、".join(cand["strong_entities"][:6]),
            "status": FACT_STATUS_FACT,
            "confidence": 0.8,
            "evidence_ids": [ev_ids[m.message_id] for m in ent_msgs[:3]] or [ev_ids[cand["msgs"][0].message_id]],
            "kind": "entities",
        })

    profile = {
        "schema_version": "prefill-profile-1.0",
        "candidate_id": cid,
        "analysis_status": ANALYSIS_STATUS_RETRIEVAL_READY,
        "analysis_note": (
            "无 API 阶段：仅生成确定性可追溯证据包与推断/反证槽位；"
            "模型级深度推理未执行，待深度分析（需用户确认 token 预算）后进行。"
        ),
        "confidence": None,
        "facts": facts,
        "deep_hypotheses": [],            # 槽位：深度分析阶段填充
        "alternative_hypotheses": [],     # 槽位：备选解释
        "counter_evidence": [],           # 反证槽位：本阶段保留为空
        "relationship_profile": None,     # 槽位：关系定位/角色/互惠/期待
        "value_assumptions": [],          # 槽位：成长/合作/情感/资源/风险/边界
        "communication_advice": [],       # 槽位：下一步沟通建议
        "conclusion_stability": assess_stability(0),
    }
    return profile


# ─────────────────────────────────────────────────────────────────────────────
# 候选选择（~30 高信号，优先跨联系人/多日/关键上下文）
# ─────────────────────────────────────────────────────────────────────────────

def _span_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    ov = max(0, min(a_end, b_end) - max(a_start, b_start))
    a_len = max(1, a_end - a_start)
    b_len = max(1, b_end - b_start)
    return ov / min(a_len, b_len)


def select_candidates(candidates: list[dict], limit: int = 30) -> list[dict]:
    """按 跨联系人 > 多日 > 分数 排序，并用「共享强实体 + 时间重叠>50%」去重，
    避免复核包出现大量同一项目的近似重复。"""
    if not candidates:
        return []
    ranked = sorted(
        candidates,
        key=lambda c: (int(c["conversation_count"] >= 2), int(c["day_span"] >= 2), c["signal_score"]),
        reverse=True,
    )
    picked: list[dict] = []
    used_ids: set[str] = set()
    for c in ranked:
        if c["candidate_id"] in used_ids:
            continue
        dup = any(
            set(c["strong_entities"]) & set(p["strong_entities"])
            and _span_overlap(c["start_ts"], c["end_ts"], p["start_ts"], p["end_ts"]) > 0.5
            for p in picked
        )
        if dup:
            continue
        used_ids.add(c["candidate_id"])
        picked.append(c)
        if len(picked) >= limit:
            break

    # 关键上下文覆盖：确保四大上下文各至少 1 个
    for ctx in ("陈老师", "舒泽林", "格拉斯哥", "井邻"):
        have = any(any(ctx in e or (ctx == "格拉斯哥" and "格拉" in e) for e in c["strong_entities"]) for c in picked)
        if not have:
            best = next(
                (c for c in ranked if c["candidate_id"] not in used_ids
                 and any(ctx in e or (ctx == "格拉斯哥" and "格拉" in e) for e in c["strong_entities"])),
                None,
            )
            if best:
                # 用最低分非上下文候选替换
                non_ctx = [c for c in picked if not c["key_context"]]
                if non_ctx and len(picked) >= limit:
                    swap = non_ctx[-1]
                    picked.remove(swap)
                    used_ids.discard(swap["candidate_id"])
                used_ids.add(best["candidate_id"])
                picked.append(best)
                picked.sort(key=lambda c: (int(c["conversation_count"] >= 2), int(c["day_span"] >= 2), c["signal_score"]), reverse=True)
    return picked[:limit]


# ─────────────────────────────────────────────────────────────────────────────
# Schema 与持久化
# ─────────────────────────────────────────────────────────────────────────────

EVENT_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS _v3_event_candidates (
  candidate_id TEXT PRIMARY KEY,
  title TEXT,
  category TEXT,
  description TEXT,
  start_ts INTEGER, end_ts INTEGER,
  time_certainty TEXT,            -- fact / inferred / unknown
  fact_status TEXT DEFAULT 'unknown',   -- 待复核：fact / inferred / unknown
  strong_entities TEXT,           -- JSON 数组
  project_terms TEXT,             -- JSON 数组
  task_categories TEXT,           -- JSON 数组
  time_ref_texts TEXT,            -- JSON 数组
  resolved_dates TEXT,            -- JSON 数组
  conversation_count INTEGER DEFAULT 0,
  day_span REAL DEFAULT 0,
  msg_count INTEGER DEFAULT 0,
  signal_score REAL DEFAULT 0,
  key_context INTEGER DEFAULT 0,
  status TEXT DEFAULT 'draft',    -- draft / reviewed / merged / split
  analysis_status TEXT DEFAULT 'retrieval_ready',  -- retrieval_ready / pending_deep_analysis / analyzed
  analysis_profile_json TEXT,     -- 深度预填判断档案（facts+槽位+结论稳定性）
  confidence REAL,                -- 无 API 阶段为 NULL；深度分析后填充
  candidate_json TEXT,            -- 完整结构（含证据快照）
  created_at TEXT, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS _v3_event_evidence (
  evidence_id TEXT PRIMARY KEY,
  candidate_id TEXT NOT NULL,
  message_id TEXT NOT NULL,
  segment_id TEXT,
  conversation_id TEXT,
  create_ts INTEGER,
  quote TEXT,
  signal_types TEXT,              -- JSON 数组
  match_terms TEXT,               -- JSON 数组
  created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_v3_ev_ev_cand ON _v3_event_evidence(candidate_id);
CREATE TABLE IF NOT EXISTS _v3_event_contacts (
  candidate_id TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  display_name TEXT,
  message_count INTEGER DEFAULT 0,
  role_hint TEXT,                 -- 用户确认的角色（复核后填）
  role_certainty TEXT,            -- fact / inferred / unknown
  created_at TEXT,
  PRIMARY KEY(candidate_id, conversation_id)
);
CREATE TABLE IF NOT EXISTS _v3_event_review (
  candidate_id TEXT PRIMARY KEY,
  review_status TEXT,             -- pending / confirmed / corrected / merged / split / rejected
  user_verdict TEXT,              -- confirmed / partial / incorrect / rejected
  user_correction_json TEXT,      -- {field: {guess, corrected, reason}} 模型猜测与用户修正并存
  model_guess_json TEXT,          -- 预填档案快照（原模型猜测，供并存对照）
  title_override TEXT,
  start_ts INTEGER, end_ts INTEGER,
  time_certainty TEXT,
  fact_status TEXT,
  roles_json TEXT,                -- {conversation_id: {role, certainty}}
  merge_into TEXT,
  split_parts_json TEXT,          -- [{name, evidence_note}]
  expectation TEXT,               -- 用户自己的期待
  value_score INTEGER,
  value_tags TEXT,                -- JSON 数组
  note TEXT,
  reviewed_at TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS _v3_event_judgments (
  event_id TEXT PRIMARY KEY,      -- 最终确认的事件 id（可能是原候选或合并/拆分产物）
  source_candidate_ids TEXT,      -- JSON 数组
  title TEXT,
  start_ts INTEGER, end_ts INTEGER,
  time_certainty TEXT, fact_status TEXT,
  roles_json TEXT, expectation TEXT,
  value_score INTEGER, value_tags TEXT,
  keep_recommendation TEXT,       -- keep / pending / cleanup
  note TEXT,
  created_at TEXT
);
"""


_EVENT_COLUMN_MIGRATIONS: tuple[tuple[str, str, str], ...] = (
    # (table, column, ddl) —— 对已存在的表幂等补列
    ("_v3_event_candidates", "analysis_status", "TEXT DEFAULT 'retrieval_ready'"),
    ("_v3_event_candidates", "analysis_profile_json", "TEXT"),
    ("_v3_event_candidates", "confidence", "REAL"),
    ("_v3_event_review", "user_verdict", "TEXT"),
    ("_v3_event_review", "user_correction_json", "TEXT"),
    ("_v3_event_review", "model_guess_json", "TEXT"),
)


def _ensure_event_columns(conn: sqlite3.Connection) -> None:
    """对已存在的 _v3_event_* 表幂等补列（老库升级，不重建表）。"""
    for table, column, ddl in _EVENT_COLUMN_MIGRATIONS:
        has = conn.execute(
            f"SELECT 1 FROM pragma_table_info('{table}') WHERE name=?", (column,)
        ).fetchone()
        if not has:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def ensure_event_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(EVENT_SCHEMA_SQL)
    _ensure_event_columns(conn)
    conn.commit()


def _evidence_id_for(message_id: str, candidate_id: str) -> str:
    """证据 id = 消息 + 候选的确定性哈希（跨模块一致，可回链）。"""
    return "eve_" + hashlib.sha256((message_id + "|" + candidate_id).encode()).hexdigest()[:16]


def _evidence_rows(cand: dict) -> list[dict]:
    rows = []
    for m in cand["msgs"]:
        signal_types = []
        if m.time_signals:
            signal_types.append("time")
        if m.entity_signals:
            signal_types.append("entity")
        if m.task_signals:
            signal_types.append("task")
        match_terms = (
            [s["term"] for s in m.entity_signals]
            + [s["category"] for s in m.task_signals]
            + [s["text"] for s in m.time_signals]
        )
        rows.append({
            "evidence_id": _evidence_id_for(m.message_id, cand["candidate_id"]),
            "candidate_id": cand["candidate_id"],
            "message_id": m.message_id,
            "segment_id": m.segment_id,
            "conversation_id": m.conversation_id,
            "create_ts": m.create_ts,
            "quote": (("[我] " if m.is_send else "[对方] ") + (m.text or "")[:140]),
            "signal_types": signal_types,
            "match_terms": match_terms,
        })
    return rows


def _contact_rows(cand: dict, display_names: dict[str, str]) -> list[dict]:
    counts: Counter = Counter()
    for m in cand["msgs"]:
        counts[m.conversation_id] += 1
    rows = []
    for conv_id in sorted(counts):
        rows.append({
            "candidate_id": cand["candidate_id"],
            "conversation_id": conv_id,
            "display_name": display_names.get(conv_id),
            "message_count": counts[conv_id],
            "role_hint": None,
            "role_certainty": None,
        })
    return rows


def write_candidates(conn: sqlite3.Connection, candidates: list[dict], display_names: dict[str, str]) -> None:
    now = utc_now()
    for cand in candidates:
        title = make_title(cand)
        cand["title"] = title
        cand["description"] = make_description(cand)
        cand["time_certainty"] = time_certainty_of(cand)
        profile = build_analysis_profile(cand, display_names)
        cand["analysis_status"] = profile["analysis_status"]
        conn.execute(
            """
            INSERT INTO _v3_event_candidates(
              candidate_id, title, category, description, start_ts, end_ts,
              time_certainty, fact_status, strong_entities, project_terms,
              task_categories, time_ref_texts, resolved_dates,
              conversation_count, day_span, msg_count, signal_score, key_context,
              status, analysis_status, analysis_profile_json, confidence,
              candidate_json, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(candidate_id) DO UPDATE SET
              title=excluded.title, category=excluded.category, description=excluded.description,
              start_ts=excluded.start_ts, end_ts=excluded.end_ts,
              time_certainty=excluded.time_certainty,
              strong_entities=excluded.strong_entities, project_terms=excluded.project_terms,
              task_categories=excluded.task_categories, time_ref_texts=excluded.time_ref_texts,
              resolved_dates=excluded.resolved_dates,
              conversation_count=excluded.conversation_count, day_span=excluded.day_span,
              msg_count=excluded.msg_count, signal_score=excluded.signal_score,
              key_context=excluded.key_context,
              analysis_status=excluded.analysis_status,
              analysis_profile_json=excluded.analysis_profile_json,
              confidence=excluded.confidence,
              candidate_json=excluded.candidate_json,
              updated_at=excluded.updated_at
            """,
            (
                cand["candidate_id"], title, dominant_task(cand),
                cand["description"], cand["start_ts"], cand["end_ts"],
                cand["time_certainty"], "unknown",
                json.dumps(cand["strong_entities"], ensure_ascii=False),
                json.dumps(cand["project_terms"], ensure_ascii=False),
                json.dumps(cand["task_categories"], ensure_ascii=False),
                json.dumps(cand["time_ref_texts"], ensure_ascii=False),
                json.dumps(cand["resolved_dates"], ensure_ascii=False),
                cand["conversation_count"], cand["day_span"], cand["msg_count"],
                cand["signal_score"], 1 if cand["key_context"] else 0,
                "draft",
                cand["analysis_status"],
                json.dumps(profile, ensure_ascii=False),
                profile["confidence"],
                json.dumps(_candidate_snapshot(cand, profile=profile), ensure_ascii=False),
                now, now,
            ),
        )
        for ev in _evidence_rows(cand):
            conn.execute(
                """
                INSERT INTO _v3_event_evidence(
                  evidence_id, candidate_id, message_id, segment_id, conversation_id,
                  create_ts, quote, signal_types, match_terms, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(evidence_id) DO UPDATE SET
                  quote=excluded.quote, signal_types=excluded.signal_types,
                  match_terms=excluded.match_terms
                """,
                (
                    ev["evidence_id"], ev["candidate_id"], ev["message_id"], ev["segment_id"],
                    ev["conversation_id"], ev["create_ts"], ev["quote"],
                    json.dumps(ev["signal_types"], ensure_ascii=False),
                    json.dumps(ev["match_terms"], ensure_ascii=False),
                    now,
                ),
            )
        for ct in _contact_rows(cand, display_names):
            conn.execute(
                """
                INSERT INTO _v3_event_contacts(
                  candidate_id, conversation_id, display_name, message_count,
                  role_hint, role_certainty, created_at
                ) VALUES (?,?,?,?,?,?,?)
                ON CONFLICT(candidate_id, conversation_id) DO UPDATE SET
                  message_count=excluded.message_count, display_name=excluded.display_name
                """,
                (ct["candidate_id"], ct["conversation_id"], ct["display_name"],
                 ct["message_count"], ct["role_hint"], ct["role_certainty"], now),
            )
    conn.commit()


def _candidate_snapshot(cand: dict, profile: Optional[dict] = None) -> dict:
    """不含 MsgSignal 对象的可 JSON 化快照（含证据精简与可选预填档案）。"""
    snap = {
        "candidate_id": cand["candidate_id"],
        "title": make_title(cand),
        "description": make_description(cand),
        "category": dominant_task(cand),
        "start_ts": cand["start_ts"],
        "end_ts": cand["end_ts"],
        "time_certainty": time_certainty_of(cand),
        "strong_entities": cand["strong_entities"],
        "entity_terms": cand["entity_terms"],
        "project_terms": cand["project_terms"],
        "task_categories": cand["task_categories"],
        "time_types": cand["time_types"],
        "time_ref_texts": cand["time_ref_texts"],
        "resolved_dates": cand["resolved_dates"],
        "conversation_count": cand["conversation_count"],
        "day_span": cand["day_span"],
        "msg_count": cand["msg_count"],
        "signal_score": cand["signal_score"],
        "key_context": cand["key_context"],
        "evidence": _evidence_rows(cand),
    }
    if profile is not None:
        snap["analysis_status"] = profile["analysis_status"]
        snap["analysis_profile"] = profile
    return snap


# ─────────────────────────────────────────────────────────────────────────────
# 主流水线
# ─────────────────────────────────────────────────────────────────────────────

def _load_display_names(conn: sqlite3.Connection) -> dict[str, str]:
    return dict(conn.execute("SELECT id, display_name FROM conversations"))


def discover_pipeline(conn: sqlite3.Connection, exclude: tuple[str, ...] = EXCLUDE_CONVERSATIONS) -> dict:
    """全库事件候选发现：返回 {candidates, display_names, stats, signals_by_conv}。"""
    conn.row_factory = sqlite3.Row
    display_names = _load_display_names(conn)
    name_set = set(display_names.values())
    derived: dict[str, list[str]] = {}
    for cid, name in display_names.items():
        derived[cid] = derive_honorifics(name)

    discovered = discover_recurring_terms(conn)
    excl_set = set(exclude)

    # 载入文本消息信号
    signals_by_conv: dict[str, list[MsgSignal]] = {}
    cur = conn.execute(
        """
        SELECT id, conversation_id, segment_id, create_ts, clean_content, is_send, sender_name
        FROM messages
        WHERE message_type='文本消息' AND clean_content IS NOT NULL AND length(clean_content) > 0
        ORDER BY conversation_id, create_ts
        """
    )
    n_signal_msg = 0
    for row in cur:
        conv_id = row["conversation_id"]
        name = display_names.get(conv_id, "")
        if name in excl_set:
            continue
        sig = extract_message_signals(
            row["id"], conv_id, row["segment_id"], row["create_ts"],
            row["clean_content"], row["is_send"], row["sender_name"],
            derived.get(conv_id, []), discovered,
        )
        if sig.score > 0:
            n_signal_msg += 1
            signals_by_conv.setdefault(conv_id, []).append(sig)

    runs: list[Run] = []
    for conv_id, sigs in signals_by_conv.items():
        runs.extend(build_runs(sigs, conv_id, display_names.get(conv_id, "")))

    candidates = link_candidates(runs)
    stats = {
        "conversations_scanned": sum(1 for cid in display_names if display_names[cid] not in excl_set),
        "conversations_excluded": sum(1 for cid in display_names if display_names[cid] in excl_set),
        "text_messages_scanned": 0,
        "signal_messages": n_signal_msg,
        "runs": len(runs),
        "candidates_raw": len(candidates),
        "discovered_terms": len(discovered),
        "top_discovered_terms": discovered[:20],
    }
    cur2 = conn.execute("SELECT COUNT(*) FROM messages WHERE message_type='文本消息' AND clean_content IS NOT NULL AND length(clean_content) > 0")
    stats["text_messages_scanned"] = cur2.fetchone()[0]

    return {
        "candidates": candidates,
        "display_names": display_names,
        "stats": stats,
        "signals_by_conv": signals_by_conv,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 复核包（供 v3_event_review 渲染 event_review.html）
# ─────────────────────────────────────────────────────────────────────────────

def build_bundle(candidates: list[dict], display_names: dict[str, str], limit: int = 30) -> dict:
    picked = select_candidates(candidates, limit=limit)
    items = []
    for c in picked:
        profile = build_analysis_profile(c, display_names)
        snap = _candidate_snapshot(c, profile=profile)
        snap["conversations"] = [
            {
                "conversation_id": cid,
                "display_name": display_names.get(cid, cid),
                "message_count": sum(1 for m in c["msgs"] if m.conversation_id == cid),
                "role_hint": None,
            }
            for cid in c["conv_ids"]
        ]
        snap["fact_status"] = "unknown"
        snap["analysis_status"] = profile["analysis_status"]
        snap["analysis_profile"] = profile
        items.append(snap)
    return {
        "schema_version": "event-review-1.1",
        "generated_at": utc_now(),
        "candidate_count": len(items),
        "candidates": items,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _db_connect(db: str, ro: bool = False) -> sqlite3.Connection:
    if ro:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(db, timeout=30)
    return conn


def cmd_dryrun(args: argparse.Namespace) -> int:
    conn = _db_connect(args.db, ro=True)
    try:
        res = discover_pipeline(conn)
    finally:
        conn.close()
    cands = res["candidates"]
    stats = res["stats"]
    picked = select_candidates(cands, limit=args.limit)
    print("=== 事件候选发现 · 只读 dry-run ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"  候选总数: {len(cands)}")
    print(f"  跨联系人候选: {sum(1 for c in cands if c['conversation_count'] >= 2)}")
    print(f"  多日候选: {sum(1 for c in cands if c['day_span'] >= 2)}")
    print(f"  关键上下文候选: {sum(1 for c in cands if c['key_context'])}")
    print()
    print(f"=== 复核包 top {len(picked)} ===")
    for i, c in enumerate(picked, 1):
        conv = "跨联系人" if c["conversation_count"] >= 2 else "单联系人"
        md = "多日" if c["day_span"] >= 2 else "单日"
        ctx = "★" if c["key_context"] else " "
        print(f"{i:2d}. {ctx} [{conv}/{md}] score={c['signal_score']:.1f} 时段 {c['start_ts']}..{c['end_ts']} ({c['msg_count']}条/{c['conversation_count']}会话) {make_title(c)}")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    conn = _db_connect(args.db)
    try:
        ensure_event_schema(conn)
        res = discover_pipeline(conn)
        write_candidates(conn, res["candidates"], res["display_names"])
    finally:
        conn.close()
    print(f"[discover] 已写入 {len(res['candidates'])} 个事件候选到 _v3_event_* 表（0 API）")
    return 0


def cmd_bundle(args: argparse.Namespace) -> int:
    conn = _db_connect(args.db, ro=True)
    try:
        res = discover_pipeline(conn)
    finally:
        conn.close()
    bundle = build_bundle(res["candidates"], res["display_names"], limit=args.limit)
    bundle["run_id"] = Path(args.outdir).name
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(out_dir / "event_review_bundle.json", bundle)
    print(f"[bundle] {len(bundle['candidates'])} 个候选 -> {out_dir / 'event_review_bundle.json'}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="v3 事件中心：无 API 事件候选发现")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_dry = sub.add_parser("dryrun", help="只读统计")
    p_dry.add_argument("--db", default="data/wechat-analysis-v3.sqlite3")
    p_dry.add_argument("--limit", type=int, default=30)
    p_dry.set_defaults(func=cmd_dryrun)

    p_dis = sub.add_parser("discover", help="计算并落库")
    p_dis.add_argument("--db", default="data/wechat-analysis-v3.sqlite3")
    p_dis.set_defaults(func=cmd_discover)

    p_bun = sub.add_parser("bundle", help="生成复核包 JSON")
    p_bun.add_argument("--db", default="data/wechat-analysis-v3.sqlite3")
    p_bun.add_argument("--limit", type=int, default=30)
    p_bun.add_argument("--outdir", default="runs/event_review_p1")
    p_bun.set_defaults(func=cmd_bundle)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
