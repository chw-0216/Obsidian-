import sqlite3, json, urllib.parse
src = r'C:\Users\wardc\AppData\Roaming\@deepseek-ai\dsh-desktop\Network\Cookies'
uri = 'file:' + src.replace('\\','/') + '?mode=ro&immutable=1'
try:
    con = sqlite3.connect(uri, uri=True, timeout=2)
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("select name from sqlite_master where type='table'")]
    print('tables:', tables)
    cols = [r[1] for r in cur.execute('pragma table_info(cookies)')]
    print('cookies cols:', cols)
    rows = cur.execute("select host_key,name,length(encrypted_value),hex(substr(encrypted_value,1,3)),length(value) from cookies").fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print('ERR', type(e).__name__, e)
