"""
统一 ETL 脚本：将 Codex、Claude Code、ZCode、Grok 的对话数据导入统一 SQLite 数据仓库。
运行方式：python etl_unified.py
"""
import sqlite3
import json
import hashlib
import os
import glob
import sys

HOME = os.environ['USERPROFILE']
VAULT = os.path.join(HOME, 'Documents', 'New project gpt', 'AI-archive', 'conversations')
DB = os.path.join(VAULT, 'unified.db')

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT NOT NULL,
        session_id TEXT NOT NULL,
        session_title TEXT,
        timestamp TEXT,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        model TEXT,
        token_usage INTEGER,
        cwd TEXT,
        metadata TEXT,
        content_hash TEXT UNIQUE
    )''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON conversations(source)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_session ON conversations(source, session_id)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON conversations(timestamp)')
    conn.commit()
    return conn

def hash_content(content):
    return hashlib.sha256(content.encode('utf-8', errors='replace')).hexdigest()[:32]

def insert(conn, source, session_id, session_title, timestamp, role, content, model, token_usage, cwd, metadata):
    try:
        conn.execute('''INSERT OR IGNORE INTO conversations 
            (source, session_id, session_title, timestamp, role, content, model, token_usage, cwd, metadata, content_hash)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (source, session_id, session_title, timestamp, role, content, model, token_usage, cwd, metadata,
             hash_content(content)))
    except Exception as e:
        pass  # UNIQUE 约束自动去重

def import_codex_index(conn):
    """导入 Codex session_index.jsonl 作为元数据"""
    index_path = os.path.join(HOME, '.codex', 'session_index.jsonl')
    if not os.path.exists(index_path):
        print("  [SKIP] session_index.jsonl not found")
        return 0
    count = 0
    with open(index_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                obj = json.loads(line)
                insert(conn, 'codex', obj['id'], obj.get('thread_name', ''),
                       obj.get('updated_at', ''), 'meta',
                       json.dumps(obj, ensure_ascii=False), '', 0, '', '')
                count += 1
            except:
                pass
    print(f"  Codex index: {count} sessions indexed")
    return count

def import_codex_rollouts(conn, limit_per_session=50):
    """导入 Codex rollout JSONL 文件中的实际对话"""
    sessions_dir = os.path.join(HOME, '.codex', 'sessions')
    if not os.path.exists(sessions_dir):
        print("  [SKIP] Codex sessions dir not found")
        return 0
    
    count = 0
    jsonl_files = glob.glob(os.path.join(sessions_dir, '**', '*.jsonl'), recursive=True)
    print(f"  Found {len(jsonl_files)} Codex rollout files")
    
    for filepath in jsonl_files:
        try:
            fname = os.path.basename(filepath)
            # 从文件名提取 session_id: rollout-...-<uuid>.jsonl
            parts = fname.rsplit('-', 1)
            sid = parts[-1].replace('.jsonl', '') if len(parts) > 1 else fname
            
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                line_count = 0
                for line in f:
                    if line_count >= limit_per_session:
                        break
                    try:
                        obj = json.loads(line)
                        etype = obj.get('type', '')
                        payload = obj.get('payload', {})
                        ts = obj.get('timestamp', '')
                        
                        if etype == 'event_msg':
                            ptype = payload.get('type', '')
                            if ptype == 'user_message':
                                msg = payload.get('message', '')
                                if msg:
                                    insert(conn, 'codex', sid, '', ts, 'user', msg, '', 0, '', '')
                                    line_count += 1
                            elif ptype == 'agent_message':
                                msg = payload.get('message', '')
                                if msg:
                                    insert(conn, 'codex', sid, '', ts, 'assistant', msg, '', 0, '', '')
                                    line_count += 1
                        elif etype == 'response_item':
                            ptype = payload.get('type', '')
                            if ptype == 'message':
                                role = payload.get('role', '')
                                content_items = payload.get('content', [])
                                texts = []
                                for c in content_items:
                                    if isinstance(c, dict) and c.get('type') in ('output_text', 'input_text'):
                                        texts.append(c.get('text', ''))
                                content = ' '.join(texts)
                                if content and role in ('user', 'assistant'):
                                    insert(conn, 'codex', sid, '', ts, role, content, '', 0, '', '')
                                    line_count += 1
                    except:
                        continue
                count += 1
        except Exception as e:
            pass
    
    print(f"  Codex rollouts: processed {count} files")
    return count

def import_claude(conn):
    """导入 Claude Code projects/*.jsonl"""
    projects_dir = os.path.join(HOME, '.claude', 'projects')
    if not os.path.exists(projects_dir):
        print("  [SKIP] Claude projects dir not found")
        return 0
    
    count = 0
    jsonl_files = glob.glob(os.path.join(projects_dir, '**', '*.jsonl'), recursive=True)
    print(f"  Found {len(jsonl_files)} Claude project files")
    
    for filepath in jsonl_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if obj.get('type') == 'user' and 'message' in obj:
                            msg = obj['message']
                            content = msg.get('content', '')
                            if isinstance(content, list):
                                content = ' '.join([
                                    c.get('text', '') for c in content
                                    if isinstance(c, dict) and c.get('type') == 'text'
                                ])
                            if content:
                                sid = obj.get('sessionId', '')
                                insert(conn, 'claude', sid, '', obj.get('timestamp', ''),
                                       'user', content, '', 0, obj.get('cwd', ''),
                                       json.dumps(obj.get('origin', {}), ensure_ascii=False))
                                count += 1
                        elif obj.get('type') == 'assistant' and 'message' in obj:
                            msg = obj['message']
                            texts = []
                            for c in msg.get('content', []):
                                if isinstance(c, dict):
                                    if c.get('type') == 'text':
                                        texts.append(c.get('text', ''))
                            content = ' '.join(texts)
                            if content:
                                sid = obj.get('sessionId', '')
                                model = msg.get('model', '')
                                usage = msg.get('usage', {})
                                tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                                insert(conn, 'claude', sid, '', obj.get('timestamp', ''),
                                       'assistant', content, model, tokens, '', '')
                                count += 1
                    except:
                        continue
        except Exception as e:
            pass
    
    print(f"  Claude: {count} messages imported")
    return count

def import_claude_history(conn):
    """导入 Claude history.jsonl（用户消息摘要）"""
    history_path = os.path.join(HOME, '.claude', 'history.jsonl')
    if not os.path.exists(history_path):
        return 0
    count = 0
    with open(history_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            try:
                obj = json.loads(line)
                display = obj.get('display', '')
                if display:
                    sid = obj.get('sessionId', '')
                    insert(conn, 'claude', sid, '', obj.get('timestamp', ''),
                           'user', display, '', 0, obj.get('project', ''),
                           json.dumps({'pastedContents': obj.get('pastedContents', {})}, ensure_ascii=False))
                    count += 1
            except:
                continue
    print(f"  Claude history: {count} user prompts")
    return count

def import_zcode(conn):
    """导入 ZCode db.sqlite 中的对话"""
    zcode_db = os.path.join(HOME, '.zcode', 'cli', 'db', 'db.sqlite')
    if not os.path.exists(zcode_db):
        print("  [SKIP] ZCode db.sqlite not found")
        return 0
    
    count = 0
    try:
        src = sqlite3.connect(zcode_db)
        src.row_factory = sqlite3.Row
        
        # 先获取 session 标题
        sessions = {}
        for row in src.execute('SELECT id, slug, title FROM session'):
            sessions[row['id']] = row['title'] or row['slug'] or ''
        
        # 导入消息
        for row in src.execute('SELECT * FROM message ORDER BY time_created'):
            try:
                sid = row['session_id']
                title = sessions.get(sid, '')
                data = json.loads(row['data'])
                role = data.get('role', '')
                content = data.get('content', '')
                
                if isinstance(content, list):
                    texts = []
                    for c in content:
                        if isinstance(c, dict):
                            if c.get('type') == 'text':
                                texts.append(c.get('text', ''))
                            elif c.get('type') == 'tool_use':
                                texts.append(f"[tool: {c.get('name', '')}]")
                    content = ' '.join(texts)
                elif not isinstance(content, str):
                    content = str(content)
                
                if content.strip():
                    model = data.get('model', '')
                    insert(conn, 'zcode', sid, title, row['time_created'],
                           role, content, model, 0, '', '')
                    count += 1
            except:
                continue
        
        # 导入 input_history
        for row in src.execute('SELECT * FROM input_history'):
            try:
                sid = row['session_id'] or ''
                text = row['text'] or ''
                if text.strip():
                    insert(conn, 'zcode', sid, '', row['time_created'],
                           'user', text, '', 0, '', '')
                    count += 1
            except:
                continue
        
        src.close()
    except Exception as e:
        print(f"  ZCode error: {e}")
        return 0
    
    print(f"  ZCode: {count} messages imported")
    return count

def import_grok(conn):
    """导入 Grok prompt_history.jsonl（仅用户输入）"""
    grok_sessions = os.path.join(HOME, '.grok', 'sessions')
    if not os.path.exists(grok_sessions):
        return 0
    
    count = 0
    jsonl_files = glob.glob(os.path.join(grok_sessions, '**', 'prompt_history.jsonl'), recursive=True)
    
    for filepath in jsonl_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        prompt = obj.get('prompt', '')
                        if prompt:
                            sid = obj.get('session_id', '')
                            insert(conn, 'grok', sid, '', obj.get('timestamp', ''),
                                   'user', prompt, '', 0, '', '')
                            count += 1
                    except:
                        continue
        except:
            pass
    
    print(f"  Grok: {count} prompts imported (user-only, no AI responses)")
    return count


def main():
    print("=" * 60)
    print("AI 对话统一 ETL 导入")
    print(f"目标数据库: {DB}")
    print("=" * 60)
    
    conn = init_db()
    
    print("\n[1/5] 导入 Codex 会话索引...")
    import_codex_index(conn)
    
    print("\n[2/5] 导入 Codex 对话内容 (每会话前50条消息)...")
    import_codex_rollouts(conn, limit_per_session=50)
    
    print("\n[3/5] 导入 Claude Code 对话...")
    import_claude(conn)
    import_claude_history(conn)
    
    print("\n[4/5] 导入 ZCode 对话...")
    import_zcode(conn)
    
    print("\n[5/5] 导入 Grok 提示词...")
    import_grok(conn)
    
    conn.commit()
    
    # 统计
    total = conn.execute('SELECT COUNT(*) FROM conversations').fetchone()[0]
    by_source = conn.execute(
        'SELECT source, COUNT(*) FROM conversations GROUP BY source'
    ).fetchall()
    
    print("\n" + "=" * 60)
    print(f"导入完成！总计 {total} 条记录")
    for src, cnt in by_source:
        print(f"  {src}: {cnt} 条")
    print(f"数据库: {DB}")
    print(f"大小: {os.path.getsize(DB) / 1024 / 1024:.1f} MB")
    print("=" * 60)
    
    conn.close()


if __name__ == '__main__':
    main()