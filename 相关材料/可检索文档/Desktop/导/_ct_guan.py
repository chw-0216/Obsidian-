import sqlite3, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
DB = r"C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
print("  会话名含『关』的：")
for talker, dn, cnt, last in con.execute(
    "SELECT talker, display_name, message_count, last_ts FROM sessions WHERE display_name LIKE '%关%' OR talker LIKE '%y8f0y4jfthgs21%' ORDER BY last_ts DESC LIMIT 10"):
    import datetime
    t = datetime.datetime.fromtimestamp(last).strftime("%m-%d %H:%M") if last else "?"
    print(f"    {dn}  ({talker})  {cnt}条  最后 {t}")
con.close()
