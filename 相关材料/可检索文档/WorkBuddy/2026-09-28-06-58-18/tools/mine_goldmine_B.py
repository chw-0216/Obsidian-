# -*- coding: utf-8 -*-
"""榨干剩余数据源：收藏 / 朋友圈 / 评论 / 语音 / 社交拓扑"""
import sqlite3, os, io, datetime, collections, re, struct

DEC = r'C:\Users\wardc\AppData\Local\ChatTrace\accounts\wxid_zn4ozsnn8esr21_db45\decrypted'
WS = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
IDX = r'C:\Users\wardc\Desktop\_im_tmp\wechat-mcp\index.sqlite'
SELF = 'wxid_zn4ozsnn8esr21'

name = {}
con = sqlite3.connect(f'file:{os.path.join(DEC, "contact", "contact.db")}?mode=ro', uri=True)
for u, rm, nk, al in con.execute('select username, remark, nick_name, alias from contact'):
    name[u] = rm or nk or al or u
# 群名
for rid, un in con.execute('select id, username from chat_room'):
    pass
con.close()
con = sqlite3.connect(f'file:{IDX}?mode=ro', uri=True)
for t, n in con.execute('select talker, display_name from sessions'):
    name.setdefault(t, n or t)
con.close()


def t2s(ts):
    try:
        v = int(ts)
        if v > 10_000_000_000:
            v //= 1000
        return datetime.datetime.fromtimestamp(v).strftime('%Y-%m-%d')
    except Exception:
        return str(ts)


def nm(x):
    return '【我】' if x == SELF else name.get(x, x)


out = io.StringIO()

# ============ 1. 收藏 ============
p = os.path.join(DEC, 'favorite', 'favorite.db')
con = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
cur = con.cursor()
rows = list(cur.execute('select local_id, type, update_time, content, fromusr, realchatname from fav_db_item order by update_time desc'))
out.write('=' * 84 + '\n')
out.write(f'一、★ 收藏 favorite.db —— 共 {len(rows)} 条\n')
out.write('=' * 84 + '\n')
tc = collections.Counter(r[1] for r in rows)
out.write(f'type 分布：{dict(tc)}\n\n')
for lid, ty, ut, content, fu, rc in rows:
    c = content if isinstance(content, str) else (content or b'').decode('utf-8', 'ignore')
    c = re.sub(r'<[^>]+>', ' ', c)
    c = re.sub(r'\s+', ' ', c).strip()
    out.write(f'[{t2s(ut)}] type={ty:<3} from={nm(fu)[:14]:<16} {c[:110]}\n')
con.close()

# ============ 2. 朋友圈 ============
p = os.path.join(DEC, 'sns', 'sns.db')
con = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
con.text_factory = lambda b: b.decode('utf-8', 'ignore')   # 容忍二进制字段
cur = con.cursor()
out.write('\n' + '=' * 84 + '\n')
out.write('二、★ 朋友圈 SnsTimeLine（他/别人的时间线缓存）\n')
out.write('=' * 84 + '\n')
tl = list(cur.execute('select tid, user_name, content from SnsTimeLine order by tid desc'))
out.write(f'共 {len(tl)} 条\n\n')
for tid, u, c in tl[:25]:
    c = c if isinstance(c, str) else (c or b'').decode('utf-8', 'ignore')
    c = re.sub(r'<[^>]+>', ' ', c)
    c = re.sub(r'\s+', ' ', c).strip()
    out.write(f'{nm(u)[:16]:<18} {c[:120]}\n')

out.write('\n' + '=' * 84 + '\n')
out.write('三、★ 朋友圈评论/点赞 SnsMessage_tmp3\n')
out.write('=' * 84 + '\n')
ms = list(cur.execute('select create_time, type, from_username, from_nickname, to_username, content, is_relative_me from SnsMessage_tmp3 order by create_time desc'))
out.write(f'共 {len(ms)} 条\n\n')
for ct, ty, fu, fn, tu, c, rel in ms[:60]:
    c = c if isinstance(c, str) else (c or b'').decode('utf-8', 'ignore')
    c = re.sub(r'<[^>]+>', ' ', c)
    c = re.sub(r'\s+', ' ', c).strip()
    out.write(f'[{t2s(ct)}] {"★我" if rel else "  "} {nm(fu)[:14]:<16}->{nm(tu)[:14]:<16} {c[:80]}\n')

# SnsTopItem 的 summary 非空项
out.write('\n' + '=' * 84 + '\n')
out.write('四、朋友圈条目 SnsTopItem_1（summary 非空）\n')
out.write('=' * 84 + '\n')
n = 0
for tid, u, s, ct in cur.execute('select tid, username, summary, create_time from SnsTopItem_1 where summary is not null and length(summary)>2 order by create_time desc'):
    s = s if isinstance(s, str) else (s or b'').decode('utf-8', 'ignore')
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    out.write(f'[{t2s(ct)}] {nm(u)[:16]:<18} {s[:100]}\n')
    n += 1
    if n > 40:
        break
out.write(f'（summary 非空共 {n}+ 条）\n')

# 发布者频次
cnt = collections.Counter()
for u, in cur.execute('select username from SnsTopItem_1'):
    cnt[u] += 1
out.write('\n★ 朋友圈里出现最多的人（TOP30）：\n')
for u, v in cnt.most_common(30):
    out.write(f'   {v:>4}  {nm(u)}\n')
con.close()

# ============ 3. 语音 ============
p = os.path.join(DEC, 'message', 'media_0.db')
con = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
cur = con.cursor()
n2id = {i: u for i, u in cur.execute('select rowid, user_name from Name2Id')}
vc = collections.Counter()
for cn, ct, lid, sv, vd, di in cur.execute('select chat_name_id, create_time, local_id, svr_id, voice_data, data_index from VoiceInfo'):
    vc[cn] += 1
out.write('\n' + '=' * 84 + '\n')
out.write(f'五、★ 语音 VoiceInfo 共 {sum(vc.values())} 条 · {len(vc)} 个会话\n')
out.write('=' * 84 + '\n')
for cn, v in vc.most_common(30):
    u = n2id.get(cn, str(cn))
    out.write(f'   {v:>4} 条  {nm(u)}\n')
con.close()

# ============ 4. 社交拓扑 ============
p = os.path.join(DEC, 'contact', 'contact.db')
con = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
cur = con.cursor()
room_name = {}
for rid, un in cur.execute('select id, username from chat_room'):
    room_name[rid] = un
mem = collections.defaultdict(set)   # person -> rooms
room = collections.defaultdict(set)  # room -> persons
for rid, mid in cur.execute('select room_id, member_id from chatroom_member'):
    mem[mid].add(rid)
    room[rid].add(mid)
out.write('\n' + '=' * 84 + '\n')
out.write(f'六、★ 社交拓扑 chatroom_member：{sum(len(v) for v in mem.values())} 条 · {len(mem)} 人 · {len(room)} 群\n')
out.write('=' * 84 + '\n')
# 哪些人横跨最多群（潜在「桥」）
top = sorted(mem.items(), key=lambda kv: -len(kv[1]))[:35]
out.write('★ 横跨最多群的人（潜在「桥」）：\n')
for mid, rs in top:
    out.write(f'   {len(rs):>4} 群  {nm(mid)}\n')
con.close()

open(os.path.join(WS, '_tmp', 'mine_B.txt'), 'w', encoding='utf-8').write(out.getvalue())
print('ok', len(out.getvalue()))
