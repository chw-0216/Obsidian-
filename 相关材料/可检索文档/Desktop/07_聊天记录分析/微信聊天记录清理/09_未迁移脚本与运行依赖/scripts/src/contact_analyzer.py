"""WeChat-MiMo-Analyzer 联系人优先分析模块 (v2)"""

from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.error
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
import sqlite3
from common import connect_database, utc_now, display_time, redact_for_model

# Schema
CONTACT_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS contact_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    total_messages INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    received_count INTEGER DEFAULT 0,
    first_ts INTEGER DEFAULT 0,
    last_ts INTEGER DEFAULT 0,
    active_months INTEGER DEFAULT 0,
    is_bidirectional INTEGER DEFAULT 0,
    avg_chars_per_message REAL DEFAULT 0,
    contact_type TEXT DEFAULT 'unknown',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contact_timeline_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    time_layer TEXT NOT NULL,
    time_range TEXT,
    summary TEXT,
    key_events TEXT,
    relationship_signals TEXT,
    tone_shifts TEXT,
    open_items TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    UNIQUE(conversation_id, time_layer)
);

CREATE TABLE IF NOT EXISTS contact_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    relationship_type TEXT,
    closeness_score REAL DEFAULT 0,
    communication_style TEXT,
    sentiment_balance TEXT,
    dominant_topics TEXT,
    tone_distribution TEXT,
    core_tensions TEXT,
    shared_history TEXT,
    growth_trajectory TEXT,
    confidence REAL DEFAULT 0,
    evidence_segment_ids TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

def create_contact_tables(db_path: Path) -> None:
    conn = connect_database(db_path)
    conn.executescript(CONTACT_TABLES_SQL)
    conn.commit()
    conn.close()
    print("[OK] Contact tables created")

def get_contact_stats(db_path: Path) -> list[dict]:
    conn = connect_database(db_path)
    sql = """
    SELECT c.id as conversation_id, c.display_name,
           COUNT(m.id) as total_messages,
           SUM(CASE WHEN m.is_send=1 THEN 1 ELSE 0 END) as sent_count,
           SUM(CASE WHEN m.is_send=0 THEN 1 ELSE 0 END) as received_count,
           MIN(m.create_ts) as first_ts, MAX(m.create_ts) as last_ts,
           AVG(LENGTH(m.clean_content)) as avg_chars
    FROM conversations c LEFT JOIN messages m ON m.conversation_id = c.id
    WHERE c.display_name NOT IN ('文件传输助手','微信团队','服务通知')
      AND c.display_name NOT LIKE '%美团%' AND c.display_name NOT LIKE '%饿了么%'
      AND c.display_name NOT LIKE '%淘宝%' AND c.display_name NOT LIKE '%京东%'
      AND c.display_name NOT LIKE '%快递%' AND c.display_name NOT LIKE '%银行%'
    GROUP BY c.id HAVING total_messages >= 10 ORDER BY total_messages DESC
    """
    rows = conn.execute(sql).fetchall()
    results = []
    for row in rows:
        r = dict(row)
        if r['first_ts'] and r['last_ts']:
            fd = datetime.fromtimestamp(r['first_ts'])
            ld = datetime.fromtimestamp(r['last_ts'])
            r['active_months'] = max(1, (ld.year-fd.year)*12 + ld.month-fd.month + 1)
        else:
            r['active_months'] = 0
        r['is_bidirectional'] = 1 if r['total_messages']>0 and 0.2 <= r['sent_count']/r['total_messages'] <= 0.8 else 0
        r['contact_type'] = 'personal'
        results.append(r)
    conn.close()
    return results

def save_contact_summary(db_path: Path, contacts: list[dict]) -> int:
    conn = connect_database(db_path)
    now = utc_now()
    saved = 0
    for c in contacts:
        conn.execute("""INSERT OR REPLACE INTO contact_summary 
            (conversation_id,display_name,total_messages,sent_count,received_count,
             first_ts,last_ts,active_months,is_bidirectional,avg_chars_per_message,
             contact_type,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (c['conversation_id'],c['display_name'],c['total_messages'],
             c['sent_count'],c['received_count'],c['first_ts'],c['last_ts'],
             c['active_months'],c['is_bidirectional'],c['avg_chars'],
             c['contact_type'],now,now))
        saved += 1
    conn.commit()
    conn.close()
    return saved

def get_contact_messages(db_path: Path, conversation_id: str, days: Optional[int] = None, limit_chars: int = 40000) -> str:
    conn = connect_database(db_path)
    time_filter = f"AND m.create_ts >= {int((datetime.now()-timedelta(days=days)).timestamp())}" if days else ""
    sql = f"SELECT m.create_ts,m.is_send,m.clean_content FROM messages m WHERE m.conversation_id=? {time_filter} AND m.message_type='文本消息' AND LENGTH(m.clean_content)>0 ORDER BY m.create_ts"
    rows = conn.execute(sql, (conversation_id,)).fetchall()
    conn.close()
    lines = []
    total = 0
    for row in rows:
        ts = display_time(row[0])
        spk = "我" if row[1] else "对方"
        txt, _ = redact_for_model(row[2])
        line = f"[{ts}] {spk}: {txt}"
        if total + len(line) > limit_chars:
            lines.append("... (截断) ...")
            break
        lines.append(line)
        total += len(line)
    return "\n".join(lines)

def aggregate_contact_corpus(db_path: Path, cid: str) -> dict[str, str]:
    return {
        'recent_30d': get_contact_messages(db_path, cid, days=30),
        'recent_6m': get_contact_messages(db_path, cid, days=180),
        'full': get_contact_messages(db_path, cid),
    }

class MiMoClient:
    def __init__(self, api_base=None, api_key=None, model=None):
        self.api_base = api_base or os.environ.get("MIMO_API_BASE", "https://token-plan-cn.xiaomimimo.com/anthropic")
        self.api_key = api_key or os.environ.get("MIMO_API_KEY", "")
        self.model = model or os.environ.get("MIMO_MODEL", "mimo-v2.5-pro")
    
    def call(self, sys_prompt: str, user_prompt: str, retries: int = 3) -> dict[str, Any]:
        url = f"{self.api_base}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000,
            "reasoning_effort": "none"
        }
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read())
                    content = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})
                    
                    # 清理 markdown 代码块
                    clean = content.strip()
                    if clean.startswith("`"):
                        clean = re.sub(r"^`(?:json)?\s*\n?", "", clean)
                        clean = re.sub(r"\n?`\s*$", "", clean)
                    
                    # 解析 JSON
                    try:
                        parsed = json.loads(clean)
                    except:
                        m = re.search(r"\{.*\}", clean, re.DOTALL)
                        parsed = json.loads(m.group()) if m else {}
                    
                    return {
                        "data": parsed,
                        "input_tokens": usage.get("prompt_tokens", 0),
                        "output_tokens": usage.get("completion_tokens", 0)
                    }
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise

def extract_field(data: dict, *keys, default=None):
    """从嵌套字典中提取字段"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data if data is not default else default

def run_contact_analysis(db_path: Path, top_n: int = 10, dry_run: bool = False) -> dict:
    print("=" * 60)
    print("WeChat-MiMo-Analyzer 联系人优先分析")
    print("=" * 60)
    
    print("\n[阶段 1] 联系人盘点...")
    create_contact_tables(db_path)
    contacts = get_contact_stats(db_path)
    saved = save_contact_summary(db_path, contacts)
    print(f"  -> 发现 {len(contacts)} 个有效联系人，已保存 {saved} 个")
    
    # 筛选有近期消息的双向联系人
    recent_contacts = []
    for c in contacts:
        if c['is_bidirectional'] and c['last_ts']:
            days_since = (datetime.now().timestamp() - c['last_ts']) / 86400
            if days_since <= 60:  # 最近60天有消息
                recent_contacts.append(c)
    
    top_contacts = recent_contacts[:top_n]
    print(f"  -> 选择 TOP {len(top_contacts)} 双向联系人（最近60天有消息）")
    
    if dry_run:
        print("\n[Dry Run] 跳过大模型调用")
        for c in top_contacts:
            print(f"    - {c['display_name']}: {c['total_messages']} 条消息")
        return {"contacts": top_contacts, "timelines": {}, "profiles": {}}
    
    client = MiMoClient()
    timelines = {}
    profiles = {}
    
    for i, contact in enumerate(top_contacts, 1):
        cid = contact['conversation_id']
        name = contact['display_name']
        print(f"\n[{i}/{len(top_contacts)}] 分析联系人: {name}")
        
        print("  [阶段 2] 聚合语料...")
        corpus = aggregate_contact_corpus(db_path, cid)
        
        print("  [阶段 3] 生成时间线摘要...")
        tl_results = {}
        for layer, text in corpus.items():
            if not text.strip() or len(text) < 100:
                print(f"    跳过 {layer}: 语料不足 ({len(text)} 字符)")
                continue
            
            prompt = f"""分析与「{name}」的聊天记录（{layer}）：

{text[:15000]}

请输出JSON格式的时间线摘要，包含以下字段：
- time_range: 时间范围
- summary: 总结（100字以内）
- key_events: 关键事件列表（最多5个，每个包含 date, event, impact）
- relationship_signals: 关系信号（最多3个字符串）
- tone_shifts: 语气变化（最多2个字符串）
- open_items: 未完成事项（最多3个字符串）"""
            
            result = client.call("你是关系分析师。分析聊天记录，输出严格JSON格式。", prompt)
            tl_results[layer] = result['data']
            
            # 保存到数据库
            conn = connect_database(db_path)
            conn.execute("""INSERT OR REPLACE INTO contact_timeline_summaries
                (conversation_id, time_layer, time_range, summary, key_events,
                 relationship_signals, tone_shifts, open_items, input_tokens, output_tokens, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (cid, layer,
                 result['data'].get('time_range'),
                 result['data'].get('summary'),
                 json.dumps(result['data'].get('key_events', []), ensure_ascii=False),
                 json.dumps(result['data'].get('relationship_signals', []), ensure_ascii=False),
                 json.dumps(result['data'].get('tone_shifts', []), ensure_ascii=False),
                 json.dumps(result['data'].get('open_items', []), ensure_ascii=False),
                 result['input_tokens'], result['output_tokens'], utc_now()))
            conn.commit()
            conn.close()
            print(f"    {layer}: {result['data'].get('summary', '(无)')[:50]}...")
        
        timelines[cid] = tl_results
        
        if not tl_results:
            print("    跳过阶段4: 无时间线数据")
            continue
        
        print("  [阶段 4] 生成关系画像...")
        prompt = f"""根据与「{name}」的时间线摘要，生成关系画像：

{json.dumps(tl_results, ensure_ascii=False, indent=2)[:5000]}

请输出JSON格式，包含以下字段：
- relationship_type: 关系类型（家人/密友/朋友/同事/业务关系/服务关系/其他）
- closeness_score: 亲密度（0-10分）
- communication_style: 沟通风格（50字以内）
- dominant_topics: 主要话题（最多3个字符串）
- growth_trajectory: 发展趋势（递增/稳定/递减/波动）
- confidence: 置信度（0-1）"""
        
        prof_result = client.call("你是关系画像分析师。根据时间线摘要生成关系画像，输出严格JSON。", prompt)
        profiles[cid] = prof_result['data']
        
        # 保存到数据库
        conn = connect_database(db_path)
        conn.execute("""INSERT OR REPLACE INTO contact_profiles
            (conversation_id, display_name, relationship_type, closeness_score,
             communication_style, dominant_topics, growth_trajectory,
             confidence, input_tokens, output_tokens, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (cid, name,
             prof_result['data'].get('relationship_type'),
             prof_result['data'].get('closeness_score', 0),
             prof_result['data'].get('communication_style'),
             json.dumps(prof_result['data'].get('dominant_topics', []), ensure_ascii=False),
             prof_result['data'].get('growth_trajectory'),
             prof_result['data'].get('confidence', 0),
             prof_result['input_tokens'], prof_result['output_tokens'],
             utc_now(), utc_now()))
        conn.commit()
        conn.close()
        
        print(f"    -> 关系类型: {prof_result['data'].get('relationship_type')}")
        print(f"    -> 亲密度: {prof_result['data'].get('closeness_score')}/10")
        print(f"    -> 置信度: {prof_result['data'].get('confidence')}")
    
    total_in = sum(p.get('input_tokens', 0) for p in profiles.values())
    total_out = sum(p.get('output_tokens', 0) for p in profiles.values())
    
    print("\n" + "=" * 60)
    print(f"分析完成！联系人: {len(top_contacts)}, Token: {total_in}+{total_out}")
    print("=" * 60)
    
    return {"contacts": top_contacts, "timelines": timelines, "profiles": profiles, "token_usage": {"input": total_in, "output": total_out}}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, default=Path("data/wechat-private-v2.sqlite3"))
    p.add_argument("--top-n", type=int, default=10)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    run_contact_analysis(args.db, args.top_n, args.dry_run)
