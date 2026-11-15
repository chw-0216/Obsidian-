# wxq — 微信实时查询工具（ChatTrace 版）

**不依赖 WeFlow、不改系统时钟。** 数据全部来自已解密的微信库 + 本地索引。

## 数据链路

```
微信客户端（已登录）
   │  ChatTrace 解密（DPAPI 密钥，永久有效）
   ▼
%LOCALAPPDATA%\ChatTrace\accounts\wxid_..._db45\decrypted\
   ├─ message_0.db / message_1.db   聊天消息
   ├─ sns/sns.db                    朋友圈（含赞与评论）
   └─ contact/contact.db            联系人
   │  index-incremental.py
   ▼
_im_tmp\wechat-mcp\index.sqlite     1826 会话 / 31.9 万条 / FTS5 全文索引
```

## 一键用法

双击 `一键刷新看新消息.cmd` → 刷新三层 + 打印最近 3 小时新消息。

## 命令行

```powershell
$t = "C:\Users\wardc\Desktop\07_聊天记录分析\tools\wxq.py"

python $t refresh                          # 三层刷新（解密→索引→JSON，约 35 秒）
python $t sessions -n 30                   # 最近活跃会话
python $t sessions --type private -n 20    # 只看私聊
python $t new -m 180                       # 最近 3 小时新消息（跨全部会话）
python $t dump 火山雪 -n 40                 # 导出某会话（支持名字片段）
python $t moments wxid_j2be9no47ur822      # 导出某人朋友圈（含赞/评论）
python $t search 关键词 --moments           # 全文检索（可同时搜朋友圈）
python $t resolve 火山雪                    # 名字 → wxid
python $t export 火山雪 --out "输出目录" --with-moments   # 导出 JSON+MD 数据包
```

## 为什么快

- 查询全走 `index.sqlite`（SQLite + FTS5），**毫秒~秒级**，不重新扫 1GB 的消息库
- `refresh` 是**增量**的：数据库没变就 skip，实测解密 27s + 索引 4s + JSON 0.4s
- `new` 走时间戳索引，跨 1826 个会话只查新增部分

## 已知情况

- `gen_live_json.py` 只导出 `_sync_state.json` 里登记的会话（当前：笑一、Ealthy 李梓燏）；
  要看别的会话用 `wxq dump`，不要动那个水位文件
- `index.sqlite` 在 2026-10-01 做过一次去重修复（约 34.5 万 → 31.9 万条），
  备份在 `index.sqlite.bak-before-repair-20261001_205601`
- 朋友圈只包含**本机同步到过的**内容；对方设置"仅三天可见"或已删除的帖子不会出现

## 文件

| 文件 | 说明 |
|---|---|
| `wxq.py` | 本工具 |
| `一键刷新看新消息.cmd` | 双击即用 |
| `..\weflow_extract\read_lilian.py` | 早期单会话读取脚本（已被 wxq 取代） |
| `..\weflow_extract\probe_lilian.py` | 库结构探查脚本 |
