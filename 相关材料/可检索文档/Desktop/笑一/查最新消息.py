# 极速查看会话最新消息
# 用法:
#   python 查最新消息.py              -> 默认会话(笑一) 最新20条，秒级(不刷新)
#   python 查最新消息.py -r           -> 先增量刷新(约30秒)再查看
#   python 查最新消息.py -r 30        -> 刷新后显示30条
#   python 查最新消息.py wxid_xxx 30  -> 指定会话
import sqlite3, sys, datetime, subprocess, os

DB = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
DEFAULT_TALKER = 'wxid_wdnk6ue9kiyn22'
ME = 'wxid_zn4ozsnn8esr21'

def do_refresh():
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    subprocess.run(['python', '-m', 'chattrace.cli', 'data', 'decrypt',
                    '--account-dir', r'C:\Users\wardc\xwechat_files\wxid_zn4ozsnn8esr21_db45'],
                   cwd=r'C:\Users\wardc\Desktop\_im_tmp\chattrace', env=env,
                   capture_output=True, timeout=180)
    subprocess.run(['python', 'index-incremental.py'],
                   cwd=r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp', env=env,
                   capture_output=True, timeout=120)

def show(talker, limit):
    c = sqlite3.connect(f'file:{DB}?mode=ro', uri=True)
    cur = c.cursor()
    cur.execute("SELECT role, ts, content FROM messages WHERE session_key LIKE ? ORDER BY ts DESC, id DESC LIMIT ?",
                (f'%{talker}%', limit * 4))
    rows = cur.fetchall()
    c.close()
    seen, out = set(), []
    for role, ts, content in rows:
        key = (ts, content)
        if key in seen: continue
        seen.add(key); out.append((role, ts, content))
        if len(out) >= limit: break
    print(f"=== {talker} 最新 {len(out)} 条 ===")
    for role, ts, content in reversed(out):
        who = '我' if role == 'me' else ('系统' if role == 'system' else '她')
        try: dt = datetime.datetime.fromtimestamp(int(ts)).strftime('%m-%d %H:%M:%S')
        except Exception: dt = str(ts)
        text = (content or '').replace('\n', ' ')
        if len(text) > 120: text = text[:117] + '...'
        print(f"[{dt}] {who}: {text}")

if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    refresh = '-r' in args or '--refresh' in args
    args = [a for a in args if not a.startswith('-')]
    # 纯数字参数 = 条数；否则 = 会话 wxid
    talker, limit = DEFAULT_TALKER, 20
    for a in args:
        if a.isdigit():
            limit = int(a)
        else:
            talker = a
    if refresh: do_refresh()
    show(talker, limit)
