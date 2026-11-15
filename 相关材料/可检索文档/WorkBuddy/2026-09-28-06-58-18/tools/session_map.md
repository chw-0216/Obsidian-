# 会话名对照表（wxid ↔ 真名）

> 从 `MEMORY.md` §十一 迁出（2026-10-11 晚，为腾出容量）。
> 用途：索引库 / 解密库里 `talker`、`username` 都是 wxid，查人先来这张表。
> 维护：新人进档时补一行。**本表只是索引，定性一律看引擎 `04-人际地图.md`。**

## 一、核心人物（常查）

| wxid / 会话名 | 真名 | 备注 |
|---|---|---|
| `deerluna` | **陈晔** | 导师 · 央美副教授 |
| `wxid_wdnk6ue9kiyn22` | **笑一** | 现任女友 |
| `wxid_0gb0smyjaoyk22` | **陈昶文** | 大一学妹 · 07-09 归零 → 10-08 复活 |
| `wxid_1wa75s1kze3o22` | **刘丽萍** | 母亲（央美版画系教授） |
| `a35599192` | **王利敏** | 中传老师 · 工号 **1146** |
| `guo647789` | **李老师**（海燕） | 中传交互技术课 |
| `zhouran68` | **周冉** | 格拉斯哥北京校友会 **会长**（文案终审） |
| `Darwin480015` | **Darwin / 曹总** | 校友会 **活动负责人**（18 家跨校友会资源） |
| `wxid_id1nfp5f20e122` | **沐茜妍**（林立娜） | 09-16 由本人终止 |
| `wxid_5049180491911` | **柯益盈** | 情感锚点 · 空窗 11 月 |
| `huxiaomi123` | **何一莎** | 央美美术馆媒体部主任 |
| `wxid_0ejd54z34nmv32` | **舒泽林** | |
| `wxid_y8f0y4jfthgs21` | **关宇佳** | |

## 二、本科圈 · 首经贸城院（2026-10-11 新增）

| wxid | 真名 | 备注 |
|---|---|---|
| `wxid_4yurl8wrbi4a22` | **李博文**（bownbown / St-reborn） | 3班 + 城院 · 体制内在职 · 档位待复核 |
| `wxid_uhulgmrvfq4a12` | **周雯娟**（Sora / sora4811） | 城院 · 库内零消息 |

## 三、其他已定位

| wxid / 会话名 | 真名 | 备注 |
|---|---|---|
| — | 程颂孟秋 | 前本科室友 · 带标签 37=城院 |
| — | 林茂 | 央美**院长** · 旧识 |
| — | 旭峰 | 母亲的朋友 · 曾在人事处 |

## 四、怎么用

```python
import sqlite3
c = sqlite3.connect('file:C:/Users/wardc/Desktop/_im_tmp/wechat-mcp/index.sqlite?mode=ro', uri=True)
c.execute("select count(*) from messages where session_key=?", ('wxid_uhulgmrvfq4a12',)).fetchone()
```

- 索引库 `sessions.display_name` 为空时 → 查解密库 `contact.db` 按 `username='xxx@chatroom'` 取 `nick_name`。
- ★ **时间窗只覆盖 2024-11-10 起** —— 早于此**不得读成没关系**。
