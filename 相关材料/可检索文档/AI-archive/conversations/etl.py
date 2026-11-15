"""
ETL v5.1: 修复 Claude user 消息 - 包含 tool_result 内容
"""
import sqlite3, json, hashlib, os, glob, re, zstandard
from datetime import datetime, timezone

HOME = os.environ['USERPROFILE']
VAULT = os.path.join(HOME, 'Documents', 'New project gpt', 'AI-archive', 'conversations')
DB = os.path.join(VAULT, 'unified.db')

def hash_content(content):
    return hashlib.sha256(content.encode('utf-8', errors='replace')).hexdigest()[:32]

def insert(conn, source, session_id, session_title, timestamp, role, content, model, token_usage, cwd, metadata):
    if not content or not content.strip():
        return
    try:
        conn.execute('''INSERT OR IGNORE INTO conversations 
            (source, session_id, session_title, timestamp, role, content, model, token_usage, cwd, metadata, content_hash)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
            (source, session_id, session_title, timestamp, role, content, model, token_usage, cwd, metadata,
             hash_content(content)))
    except:
        pass

def extract_claude_content(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content) if content else ''
    texts = []
    for c in content:
        if not isinstance(c, dict):
            continue
        ct = c.get('type', '')
        if ct == 'text':
            t = c.get('text', '')
            if t:
                texts.append(t)
        elif ct == 'thinking':
            t = c.get('thinking', '')
            if t:
                texts.append(f'[thinking] {t}')
        elif ct == 'tool_use':
            name = c.get('name', '')
            texts.append(f'[tool_use: {name}]')
        elif ct == 'tool_result':
            # Extract tool result content (trimmed to avoid noise)
            result_content = c.get('content', '')
            if isinstance(result_content, list):
                result_texts = []
                for rc in result_content:
                    if isinstance(rc, dict) and rc.get('type') == 'text':
                        t = rc.get('text', '')
                        if t:
                            result_texts.append(t)
                result_content = ' '.join(result_texts)
            if result_content and isinstance(result_content, str) and result_content.strip():
                # Trim very long tool results
                if len(result_content) > 2000:
                    result_content = result_content[:2000] + '...'
                texts.append(f'[tool_result] {result_content}')
    return ' '.join(texts)

def import_claude_fixed(conn):
    projects_dir = os.path.join(HOME, '.claude', 'projects')
    jsonl_files = glob.glob(os.path.join(projects_dir, '**', '*.jsonl'), recursive=True)
    print(f"  Found {len(jsonl_files)} Claude project files")
    
    count = 0
    session_titles = {}
    
    # First pass: collect titles
    for fp in jsonl_files:
        try:
            sid = os.path.basename(fp).replace('.jsonl', '')
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        if obj.get('type') in ('ai-title', 'custom-title'):
                            title = obj.get('aiTitle') or obj.get('title') or ''
                            if title: session_titles[sid] = title
                    except: pass
        except: pass
    
    # Second pass: import messages
    for fp in jsonl_files:
        try:
            sid = os.path.basename(fp).replace('.jsonl', '')
            title = session_titles.get(sid, '')
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        otype = obj.get('type', '')
                        ts = obj.get('timestamp', '')
                        
                        if otype == 'user' and 'message' in obj:
                            msg = obj['message']
                            content = extract_claude_content(msg.get('content', ''))
                            # Determine if it's a real user message or tool result
                            role = 'user'
                            raw_content = msg.get('content', '')
                            if isinstance(raw_content, list):
                                has_tool = any(c.get('type') == 'tool_result' for c in raw_content if isinstance(c, dict))
                                has_text = any(c.get('type') == 'text' and c.get('text', '').strip() for c in raw_content if isinstance(c, dict))
                                if has_tool and not has_text:
                                    role = 'tool'  # Pure tool results
                            
                            if content.strip():
                                insert(conn, 'claude', sid, title, ts, role, content, '', 0, obj.get('cwd', ''),
                                       json.dumps(obj.get('origin', {}), ensure_ascii=False))
                                count += 1
                        
                        elif otype == 'assistant' and 'message' in obj:
                            msg = obj['message']
                            content = extract_claude_content(msg.get('content', []))
                            if content.strip():
                                model = msg.get('model', '')
                                usage = msg.get('usage', {})
                                tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
                                insert(conn, 'claude', sid, title, ts, 'assistant', content, model, tokens, '', '')
                                count += 1
                    except: continue
        except: pass
    
    print(f"  Claude: {count} messages, {len(session_titles)} titled sessions")
    return count

# ==================== Reuse v5 imports for other sources ====================

def epoch_ms_to_iso(ms):
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).isoformat()
    except:
        return str(ms)

UUID_RE = re.compile(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})')

def extract_codex_session_id(filepath):
    fname = os.path.basename(filepath)
    m = UUID_RE.search(fname)
    if m: return m.group(1)
    return fname.replace('.jsonl', '')

def build_codex_title_map():
    title_map = {}
    idx_path = os.path.join(HOME, '.codex', 'session_index.jsonl')
    if os.path.exists(idx_path):
        with open(idx_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    title_map[obj['id']] = obj.get('thread_name', '')
                except: pass
    state_db = os.path.join(HOME, '.codex', 'state_5.sqlite')
    if os.path.exists(state_db):
        try:
            src = sqlite3.connect(state_db)
            src.row_factory = sqlite3.Row
            for row in src.execute('SELECT id, title FROM threads WHERE title IS NOT NULL AND title != ""'):
                if row['id'] not in title_map or not title_map[row['id']]:
                    title_map[row['id']] = row['title'] or ''
            src.close()
        except: pass
    return title_map

def import_codex(conn):
    title_map = build_codex_title_map()
    print(f"  Codex title map: {len(title_map)} entries")
    sessions_dir = os.path.join(HOME, '.codex', 'sessions')
    jsonl_files = glob.glob(os.path.join(sessions_dir, '**', '*.jsonl'), recursive=True)
    print(f"  Found {len(jsonl_files)} Codex rollout files")
    count = 0
    for i, filepath in enumerate(jsonl_files):
        if i % 50 == 0 and i > 0:
            print(f"    ... {i}/{len(jsonl_files)}, {count} msgs")
        sid = extract_codex_session_id(filepath)
        title = title_map.get(sid, '')
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        etype = obj.get('type', '')
                        payload = obj.get('payload', {})
                        ts = obj.get('timestamp', '')
                        if etype == 'event_msg':
                            ptype = payload.get('type', '')
                            if ptype == 'user_message':
                                msg = payload.get('message', '')
                                if msg and len(msg) > 2:
                                    insert(conn, 'codex', sid, title, ts, 'user', msg, '', 0, '', '')
                                    count += 1
                            elif ptype == 'agent_message':
                                msg = payload.get('message', '')
                                if msg and len(msg) > 2:
                                    insert(conn, 'codex', sid, title, ts, 'assistant', msg, '', 0, '', '')
                                    count += 1
                        elif etype == 'response_item':
                            ptype = payload.get('type', '')
                            if ptype == 'message':
                                role = payload.get('role', '')
                                if role in ('user', 'assistant'):
                                    texts = []
                                    for c in payload.get('content', []):
                                        if isinstance(c, dict):
                                            ct = c.get('type', '')
                                            txt = c.get('text', '')
                                            if ct in ('output_text', 'input_text') and txt:
                                                texts.append(txt)
                                    content = ' '.join(texts)
                                    if content and len(content) > 3:
                                        insert(conn, 'codex', sid, title, ts, role, content, '', 0, '', '')
                                        count += 1
                    except: continue
        except: pass
    print(f"  Codex: {count} messages")
    return count

def import_zcode(conn):
    zcode_db = os.path.join(HOME, '.zcode', 'cli', 'db', 'db.sqlite')
    if not os.path.exists(zcode_db): return 0
    count = 0
    try:
        src = sqlite3.connect(zcode_db)
        src.row_factory = sqlite3.Row
        sessions = {}
        for row in src.execute('SELECT id, slug, title FROM session'):
            sessions[row['id']] = row['title'] or row['slug'] or ''
        for row in src.execute('SELECT * FROM message ORDER BY time_created'):
            try:
                sid = row['session_id']
                title = sessions.get(sid, '')
                raw_data = row['data'] if row['data'] else '{}'
                data = json.loads(raw_data)
                role = data.get('role', '')
                if not role: continue
                content_raw = data.get('content', '')
                if isinstance(content_raw, list):
                    texts = []
                    for c in content_raw:
                        if isinstance(c, dict):
                            ct = c.get('type', '')
                            if ct == 'text':
                                t = c.get('text', '')
                                if t: texts.append(t)
                            elif ct == 'tool_use':
                                texts.append(f'[tool_use: {c.get("name","")}]')
                            elif ct == 'tool_result':
                                texts.append('[tool_result]')
                        elif isinstance(c, str) and c.strip():
                            texts.append(c)
                    content = ' '.join(texts)
                elif isinstance(content_raw, str):
                    content = content_raw
                else:
                    content = str(content_raw) if content_raw else ''
                ts = epoch_ms_to_iso(row['time_created']) if row['time_created'] else ''
                if content.strip():
                    model = data.get('model', '')
                    insert(conn, 'zcode', sid, title, ts, role, content, model, 0, '', raw_data[:500])
                    count += 1
            except: continue
        for row in src.execute('SELECT * FROM part ORDER BY time_created'):
            try:
                sid = row['session_id']
                title = sessions.get(sid, '')
                raw_data = row['data'] if row['data'] else '{}'
                data = json.loads(raw_data)
                if data.get('type') == 'text':
                    text = data.get('text', '')
                    if text and text.strip():
                        role = data.get('role', 'assistant')
                        ts = epoch_ms_to_iso(row['time_created']) if row['time_created'] else ''
                        insert(conn, 'zcode', sid, title, ts, role, text, '', 0, '', '')
                        count += 1
            except: continue
        for row in src.execute('SELECT * FROM input_history'):
            try:
                sid = row['session_id'] or ''
                text = row['text'] or ''
                if text.strip():
                    ts = epoch_ms_to_iso(row['time_created']) if row['time_created'] else ''
                    insert(conn, 'zcode', sid, '', ts, 'user', text, '', 0, '', '')
                    count += 1
            except: continue
        src.close()
    except Exception as e:
        print(f"  ZCode error: {e}")
    print(f"  ZCode: {count} messages")
    return count

def extract_dsh_content(content):
    if isinstance(content, list):
        texts = []
        for c in content:
            if isinstance(c, dict):
                ct = c.get('type', '')
                if ct == 'text':
                    t = c.get('text', '')
                    if t: texts.append(t)
                elif ct == 'tool-call':
                    texts.append(f'[tool_call: {c.get("name","")}]')
            elif isinstance(c, str) and c.strip():
                texts.append(c)
        return ' '.join(texts)
    elif isinstance(content, str):
        return content
    return str(content) if content else ''

def import_dsh(conn):
    dsh_sessions = os.path.join(HOME, 'Documents', 'New project gpt', 'AI-archive', 'apps', 'deepseek-harness', 'state', 'sessions')
    if not os.path.exists(dsh_sessions): return 0
    zstd_files = glob.glob(os.path.join(dsh_sessions, '**', '*.zstd'), recursive=True)
    print(f"  Processing {len(zstd_files)} DSH sessions...")
    count = 0
    for i, filepath in enumerate(zstd_files):
        if i % 20 == 0 and i > 0: print(f"    {i}/{len(zstd_files)}...")
        try:
            parts_list = filepath.replace(os.sep, '/').split('/')
            session_id = parts_list[-2]
            with open(filepath, 'rb') as f:
                dctx = zstandard.ZstdDecompressor()
                decompressed = dctx.stream_reader(f).read()
            lines = decompressed.decode('utf-8', errors='replace').strip().split('\n')
            session_title = ''
            session_cwd = ''
            for line in lines:
                try:
                    obj = json.loads(line)
                    etype = obj.get('type', '')
                    ts_raw = obj.get('time', '')
                    ts = epoch_ms_to_iso(ts_raw) if ts_raw else ''
                    if etype == 'session': session_cwd = obj.get('cwd', '')
                    if etype == 'session/title': session_title = obj.get('data', {}).get('title', '')
                    if etype in ('user/message', 'agent/inbox/spliced'):
                        data = obj.get('data', {})
                        if etype == 'agent/inbox/spliced':
                            for item in data.get('inserted', []):
                                role = item.get('role', 'user')
                                content = extract_dsh_content(item.get('content', ''))
                                if content.strip():
                                    insert(conn, 'dsh', session_id, session_title, ts, role, content, '', 0, session_cwd, '')
                                    count += 1
                        else:
                            content = extract_dsh_content(data.get('content', ''))
                            if content.strip():
                                insert(conn, 'dsh', session_id, session_title, ts, 'user', content, '', 0, session_cwd, '')
                                count += 1
                    if etype == 'assistant/message':
                        data = obj.get('data', {})
                        message = data.get('message', {})
                        if isinstance(message, dict):
                            content = extract_dsh_content(message.get('content', ''))
                            if content.strip():
                                model = ''
                                source = message.get('source', {})
                                if isinstance(source, dict): model = source.get('model', '')
                                usage = data.get('usage', {})
                                tokens = usage.get('inputTokens', 0) + usage.get('outputTokens', 0)
                                insert(conn, 'dsh', session_id, session_title, ts, 'assistant', content, model, tokens, session_cwd, '')
                                count += 1
                except: continue
        except: pass
    print(f"  DSH: {count} messages from {len(zstd_files)} sessions")
    return count

def import_grok(conn):
    grok_sessions = os.path.join(HOME, '.grok', 'sessions')
    if not os.path.exists(grok_sessions): return 0
    count = 0
    for filepath in glob.glob(os.path.join(grok_sessions, '**', 'prompt_history.jsonl'), recursive=True):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        prompt = obj.get('prompt', '')
                        if prompt:
                            insert(conn, 'grok', obj.get('session_id', ''), '', obj.get('timestamp', ''), 'user', prompt, '', 0, '', '')
                            count += 1
                    except: continue
        except: pass
    print(f"  Grok: {count} prompts")
    return count

# ==================== Main ====================

def main():
    print("=" * 60)
    print("ETL v5.1 - Claude tool_result 修复")
    print(f"目标: {DB}")
    print("=" * 60)
    
    if os.path.exists(DB):
        os.remove(DB)
        print("  (已清除旧数据库)")
    
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
    
    print("\n[1/5] Codex...")
    import_codex(conn)
    conn.commit()
    
    print("\n[2/5] Claude Code (tool_result修复)...")
    import_claude_fixed(conn)
    conn.commit()
    
    print("\n[3/5] ZCode...")
    import_zcode(conn)
    conn.commit()
    
    print("\n[4/5] DSH...")
    import_dsh(conn)
    conn.commit()
    
    print("\n[5/5] Grok...")
    import_grok(conn)
    conn.commit()
    
    total = conn.execute('SELECT COUNT(*) FROM conversations').fetchone()[0]
    by_source = conn.execute('SELECT source, role, COUNT(*) FROM conversations GROUP BY source, role ORDER BY source, role').fetchall()
    titled = conn.execute("SELECT source, COUNT(DISTINCT session_id) FROM conversations WHERE session_title != '' GROUP BY source").fetchall()
    
    print("\n" + "=" * 60)
    print("导入完成！")
    print(f"  总计: {total} 条消息")
    for src, role, cnt in by_source:
        print(f"    {src:8s} | {role:12s} | {cnt:5d}")
    print(f"\n  有标题的会话:")
    for src, cnt in titled:
        print(f"    {src}: {cnt} sessions")
    print(f"\n  数据库: {DB}")
    print(f"  大小: {os.path.getsize(DB) / 1024 / 1024:.1f} MB")
    print("=" * 60)
    conn.close()

if __name__ == '__main__':
    main()