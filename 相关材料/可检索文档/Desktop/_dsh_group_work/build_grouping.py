# -*- coding: utf-8 -*-
"""DSH 会话主题分组方案生成器（2026-10-23）
单一数据源：members-catalog.csv + 重要性排序层级 + 本脚本内映射表
输出：DSH工作区\00_DSH会话主题分组_20261023.md
      DSH工作区\00_DSH会话分组清单_20261023.csv
      _dsh_group_work\reconciliation.json
只读输入；不触碰 DSH state；不删除/改名/归档任何会话。
"""
import csv
import hashlib
import json
import re
from collections import Counter, OrderedDict
from datetime import datetime
from pathlib import Path

DESKTOP = Path(r"C:\Users\wardc\Desktop")
WORK = DESKTOP / "_dsh_group_work"
OUT = DESKTOP / "DSH工作区"

CATALOG = WORK / "members-catalog.csv"
RANKING = OUT / "00_DSH会话重要性排序_20261023.md"
DOC_OUT = OUT / "00_DSH会话主题分组_20261023.md"
CSV_OUT = OUT / "00_DSH会话分组清单_20261023.csv"
RECON_OUT = WORK / "reconciliation.json"

GROUPS = [
    "家庭事务",
    "人物与沟通",
    "学业/导师与课程",
    "艺术创作与三维",
    "校友会与公益",
    "AI平台与开发",
    "微信与WeFlow",
    "电脑/网络与文件",
    "清理候选",
]

# 上一轮 130 条口径（任务书给定）
PREV_130 = {
    "家庭事务": 3,
    "人物与沟通": 10,
    "学业/导师与课程": 12,
    "艺术创作与三维": 12,
    "校友会与公益": 5,
    "AI平台与开发": 37,
    "微信与WeFlow": 9,
    "电脑/网络与文件": 25,
    "清理候选": 17,
}

# 相对 130 口径新增的会话（c8634800 于 23:11 建立；3ec7e7f1 于 20:12 建立，已含在 130 内）
POST_130 = {"c8634800"}

# 清理候选细分（任务书给定 7 + 4 + 6）
CLEANUP_KIND = {
    # 问候 7
    "0eb2e8b3": "问候",
    "1f0b9e50": "问候",
    "5827a765": "问候",
    "c42d903c": "问候",
    "8e63796a": "问候",
    "ded4545a": "问候",
    "e486acb6": "问候",
    # 连接测试 4
    "21b86e63": "连接测试",
    "462b05a2": "连接测试",
    "b3dacc62": "连接测试",
    "cc9f1164": "连接测试",
    # Arduino 无回复重试 6
    "49d8f9de": "Arduino 重试",
    "551ca214": "Arduino 重试",
    "66eafaf7": "Arduino 重试",
    "6e97fb86": "Arduino 重试",
    "99247e2b": "Arduino 重试",
    "e804e95c": "Arduino 重试",
}

KEEP6 = {"db5d2b39", "f957f9f8", "bb0a3305", "7e808edf", "1d5f7c4c", "68437449"}

# 分组映射（id8 -> (组名, 理由)）
ASSIGN = OrderedDict()


def put(group, items):
    for id8, reason in items:
        if id8 in ASSIGN:
            raise SystemExit(f"重复映射: {id8}")
        ASSIGN[id8] = (group, reason)


put("家庭事务", [
    ("20b2071d", "母亲线核心事务：博导申报回执与书籍延期（S 层，置顶）"),
    ("bcfdf9b6", "母亲线：博士论文评审·刘丽萍（S 层，置顶）"),
    ("db5d2b39", "母亲两事务的实质整理副本（5/2 消息），保留并归回家庭事务"),
])
put("人物与沟通", [
    ("0019f76f", "笑一早期分析与 WeFlow 修复起点（S 层，置顶）"),
    ("c8aa2e21", "笑一最新聊天分析与回话（S 层，置顶，357 条用户消息）"),
    ("081f3489", "李媛（火山雪0号）相处策略（人物线）"),
    ("38c353e1", "米雪·延期回复（人物线）"),
    ("4737b514", "天天·生日问候与画像（人物线）"),
    ("931c4cf0", "舒泽林·语音回复策略（人物线）"),
    ("ae244605", "李梓燏·深度侧写（人物线）"),
    ("c1b92f69", "林映雯·关系分析（人物线）"),
    ("c2ec030c", "刘华赞·人物分析（人物线）"),
    ("7e808edf", "李梓燏深度侧写副本（43/153 消息），保留并归回人物与沟通"),
])
put("学业/导师与课程", [
    ("309b3e8d", "陈晔线：中期汇报内容浏览（A 层）"),
    ("70ac5f3b", "陈晔导师线·视频/论文/中传（S 层，置顶，最大单会话）"),
    ("caedb662", "陈晔要求日志优化（A 层，归档保留）"),
    ("0791acb2", "导师线：中秋祝福（王利敏等）（A 层）"),
    ("1b2f3a44", "姜涛（导师）回应与改 PPT（A 层，归档保留）"),
    ("7d9ea0bc", "姜涛（导师）教师节导出与祝福（A 层，归档保留）"),
    ("d506c42f", "姜涛（导师）云南行程报备与意图分析（A 层，按对象归导师线）"),
    ("50e487d7", "学业：中期汇报聊天检索（A 层）"),
    ("347a74e0", "中传王利敏·交互课加课（S 层，置顶）"),
    ("641f676f", "中传课程群·交互盒子与问候（S 层，归档+置顶）"),
    ("5e7ef0c1", "CAFA 缴费平台白屏（校园事务，归学业线）（C 层）"),
    ("4752a83a", "表格格式与信息填写（9-15 与中期汇报同批的提交材料）（B 层）"),
])
put("艺术创作与三维", [
    ("3ec7e7f1", "yifei 聊天记录分析+美术馆（新增会话；标题含“美术馆”，归艺术线；未分层）"),
    ("0ac6ecc8", "腾讯文档读取整理（内容创作与文档交付）（A 层）"),
    ("281e5c71", "Hyper3D/Rodin 接入与项目复现（三维）（B 层）"),
    ("4d85bb7f", "Tripo 群面讨论整理（三维工具）（B 层）"),
    ("9abb3ff0", "开源剪辑项目调研（视频创作工作流）（A 层）"),
    ("cea65051", "美术馆寻星展08·种草视频（S 层，置顶）"),
    ("07ebc97c", "双手成曲×井邻·投影交接（A 层）"),
    ("44631390", "宣传视觉图与宣发稿（B 层，归档保留）"),
    ("5d99e1ed", "植物染·零基础方法与采购（B 层）"),
    ("e84090ea", "植物染·信息分析建议（A 层）"),
    ("bb0a3305", "双手成曲副本1（5/1 消息），保留并归回艺术组"),
    ("f957f9f8", "双手成曲副本2（5/3 消息），保留并归回艺术组"),
])
put("校友会与公益", [
    ("57316a4c", "校友会公众号三长图·标题文案（S 层，置顶）"),
    ("ed0d665e", "格拉斯哥北京校友会任务（A 层）"),
    ("019884c1", "知行计划·立项群照片导出（公益项目）（A 层）"),
    ("5c5baab3", "知行计划·文件查找（公益项目）（A 层）"),
    ("da0752e8", "韩云峰·项目分析（业务项目线，按项目/公益归组）（A 层）"),
])
put("AI平台与开发", [
    ("c8634800", "本次运行中的治理会话（23:11 建立；标题取自 23:16 投影缓存，可能变化；未分层）"),
    ("68437449", "超算 Flash 连接记录（原测试项，保留并归模型接入线）"),
    ("5a06d5c8", "AI 使用画像与偏好（A 层）"),
    ("6bbe679f", "双 Codex 账号登录（A 层）"),
    ("76fe02d5", "DSH Agent 接入微信（A 层）"),
    ("7cc06066", "Codex 使用优化建议（B 层）"),
    ("8847ec4b", "荣耀X60 控制 Claude Code（B 层）"),
    ("c595451f", "升级 zcode 领 token（B 层）"),
    ("c662e786", "ChatGPT 权限无法开启（B 层）"),
    ("c6b12960", "Codex 文件下载失败（B 层）"),
    ("d1b71597", "恢复丢失的 Codex 会话（B 层）"),
    ("e5b85d98", "Workbuddy 未完成任务（B 层）"),
    ("06a166a7", "Claude Code 桌面入口（C 层，归档保留）"),
    ("1626894a", "zcode 模型加载排查（C 层，归档保留）"),
    ("1c1511c4", "小米 MiMo Token 接入（C 层）"),
    ("25109098", "禁用 Kimi 浏览器弹窗（C 层，归档保留）"),
    ("2aa9e71b", "Codex 变 Claude Router（C 层，归档保留）"),
    ("38f8b86d", "中转站 API 接入测试（C 层，归档保留）"),
    ("4cc61add", "Codex 404 修复（C 层，归档保留）"),
    ("5f4dc8a5", "OpenCode 接 DeepSeek 评估（C 层）"),
    ("68cd809e", "本地部署 zcode（C 层）"),
    ("702d00af", "国家超算中心 API 接入（C 层，归档保留）"),
    ("abe9ebb9", "小米 MiMo 与 DS 价格对比（C 层）"),
    ("cb5a8f1c", "中转站状态与可用模型（C 层，归档保留）"),
    ("d2b94fa7", "ChatGPT 重置额度查询（C 层，归档保留）"),
    ("e52943f0", "模型扩额·英伟达 token（C 层）"),
    ("efe870e5", "Codex 接 DeepSeek 回顾（C 层）"),
    ("0d6ca434", "Codex 全局 MCP Hyper3D 配置（B 层）"),
    ("57df6d73", "对话文件整理方案（工作区治理）（A 层）"),
    ("b047e18b", "DeepSeek 模型更新配置（A 层，归档保留）"),
    ("c699f4db", "09-01 工作区检查点（B 层，归档保留）"),
    ("cc98c129", "新会话读 CHECKPOINT 提示（B 层）"),
    ("f9c10ed5", "Workbuddy ENOENT 修复（A 层）"),
    ("fffdef06", "DSH 工作区整理方案（A 层）"),
    ("b5a080a6", "customer-profile Demo 重建（开发项目）（B 层）"),
    ("1d5f7c4c", "Workbuddy 报错副本（12/107 消息），保留并归 AI 组"),
    ("1e06d42a", "全部文件地图总览（工作区治理分析）（B 层）"),
    ("7aca91f6", "全盘文件与配置分析（工作区治理分析）（B 层）"),
])
put("微信与WeFlow", [
    ("0dfc3e46", "WeFlow 接 DeepSeek API（B 层）"),
    ("10730a98", "WeFlow 工具调用 ID 异常（B 层，归档保留）"),
    ("2e6509e9", "WeFlow 导出进展检查（B 层）"),
    ("544600eb", "WeFlow 锚点漂移修复1（B 层）"),
    ("75d87208", "WeFlow 工作进程查询（B 层）"),
    ("894e23bf", "WeFlow 锚点漂移修复2（B 层）"),
    ("89608bf1", "WeFlow 数据总检索（A 层，98 条）"),
    ("ac5d70df", "WeFlow 高效使用方案（B 层）"),
    ("4fc162c1", "新微信聊天记录自动化导出（C 层，归档保留）"),
])
put("电脑/网络与文件", [
    ("0bc0d756", "桌面文件与目录整理（B 层）"),
    ("8101c6f5", "Obsidian 空间清理（A 层）"),
    ("87ebf90d", "临时文件扫描与转移（S 层，置顶）"),
    ("d12472ae", "清理10GB·方案与执行（A 层）"),
    ("07936b69", "反重力打不开（软件排查）（B 层）"),
    ("33112222", "Arduino IDE 实操（B 层，归档保留）"),
    ("375b8ab4", "网络安全软件信息查找（B 层）"),
    ("3f1d24e9", "VPN 代理问题排查（A 层，归档保留）"),
    ("4b794c32", "CMCC 与华为增强器网络（B 层）"),
    ("53e59600", "文件转 PDF（B 层，归档保留）"),
    ("683a99c1", "连接校园网（B 层）"),
    ("81611fd6", "交互文件定位（B 层）"),
    ("9e98c1cd", "电脑不删文件清理（B 层，归档保留）"),
    ("afd0ee55", "查找我的头像位置（B 层，归档保留）"),
    ("b490edb2", "Arduino 红外传感器亮灯（B 层）"),
    ("c626d09c", "文件传输助手内容查找（B 层，归档保留）"),
    ("cce82c7e", "电脑卡顿原因排查（A 层）"),
    ("f6b4407e", "查找一寸面试证件照（B 层，归档保留）"),
    ("0cd20d82", "安装 Flash 4.1（C 层，归档保留）"),
    ("0fde647c", "蓝屏负荷分析（C 层，归档保留）"),
    ("1863fb4d", "spacedesk 投屏（C 层，归档保留）"),
    ("1c04aa1e", "快速截屏方法（C 层，归档保留）"),
    ("4c68c3f9", "外接硬盘检测（C 层，归档保留）"),
    ("739e1750", "异常进程关停（C 层，归档保留）"),
    ("8953dc4d", "手机连接电脑调试（C 层，归档保留）"),
])
put("清理候选", [
    ("0eb2e8b3", "问候测试：仅问候语、无业务内容（D 层）"),
    ("1f0b9e50", "问候测试：仅问候语、无业务内容（D 层，当前可见）"),
    ("5827a765", "问候测试：仅问候语、无业务内容（D 层）"),
    ("c42d903c", "问候测试：仅问候语、无业务内容（D 层）"),
    ("8e63796a", "问候测试：仅问候语、无业务内容（D 层）"),
    ("ded4545a", "问候测试：仅问候语、无业务内容（D 层）"),
    ("e486acb6", "问候测试：仅问候语、无业务内容（D 层）"),
    ("21b86e63", "连接冒烟测试：一次性连接验证（D 层）"),
    ("462b05a2", "连接冒烟测试：仅“套餐 Flash 已连接”（D 层）"),
    ("b3dacc62", "连接冒烟测试：5.3 连接验证（D 层）"),
    ("cc9f1164", "连接冒烟测试：仅“套餐 Flash 已连接”（D 层）"),
    ("49d8f9de", "Arduino 亮灯无回复重试副本4：同题无独立内容（D 层）"),
    ("551ca214", "Arduino 亮灯无回复重试副本1：同题无独立内容（D 层）"),
    ("66eafaf7", "Arduino 亮灯无回复重试副本2：同题无独立内容（D 层）"),
    ("6e97fb86", "Arduino 亮灯无回复重试副本3：同题无独立内容（D 层）"),
    ("99247e2b", "Arduino 亮灯无回复重试副本6：同题无独立内容（D 层）"),
    ("e804e95c", "Arduino 亮灯无回复重试副本5：同题无独立内容（D 层）"),
])

GROUP_KEYWORDS = {
    "家庭事务": "母亲（博导申报·书籍延期、博士论文评审）、母亲两事务副本",
    "人物与沟通": "笑一、李媛、米雪、天天、舒泽林、李梓燏、林映雯、刘华赞",
    "学业/导师与课程": "陈晔、王利敏、中传课程群、姜涛（导师）、中期汇报、CAFA 缴费、表格材料",
    "艺术创作与三维": "美术馆寻星展、双手成曲×井邻、植物染、宣传视觉、Hyper3D/Rodin、Tripo、开源剪辑、腾讯文档",
    "校友会与公益": "校友会公众号、格拉斯哥北京校友会、知行计划、韩云峰项目",
    "AI平台与开发": "Codex/zcode/Workbuddy/ChatGPT、DeepSeek/MiMo/超算/中转站接入、配置与工作区治理、customer-profile、治理会话",
    "微信与WeFlow": "WeFlow 数据检索/锚点修复/导出/API/进程、微信记录导出",
    "电脑/网络与文件": "存储与清理、文件定位/PDF/照片、校园网/VPN/网络、蓝屏/进程/软件、Arduino 实操、历史系统维护",
    "清理候选": "问候 7、连接测试 4、Arduino 无回复重试 6",
}

LAYER_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4, "未分层": 5}
CLEANUP_ORDER = {"问候": 0, "连接测试": 1, "Arduino 重试": 2}
PREFIX_ORDER = ["母亲", "笑一", "陈晔", "姜涛", "中传", "美术馆", "校友会", "存储", "人物",
                "导师", "学业", "项目", "工具", "配置", "历史", "测试", "重复", "(无前缀)"]


def load_members():
    with open(CATALOG, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        rid = r["id"].strip()
        out.append({
            "id": rid,
            "id8": rid[:8],
            "title": r["title"].strip(),
            "prefix": r["prefix"].strip(),
            "archived": r["archived"].strip() == "True",
            "pinned": r["pinned"].strip() == "True",
            "mtime": datetime.strptime(r["mtime"].strip(), "%Y/%m/%d %H:%M:%S"),
        })
    return out


def load_layers():
    layers = {}
    cur = None
    with open(RANKING, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^## ([SABCD]) ·", line)
            if m:
                cur = m.group(1)
                continue
            if line.startswith("## "):
                cur = None
                continue
            if cur is None:
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 7 and re.fullmatch(r"[0-9a-f]{8}", cells[-1]):
                layers[cells[-1]] = cur
    return layers


def recommendation(member):
    id8 = member["id8"]
    group = ASSIGN[id8][0]
    if group == "清理候选":
        return "归档观察·不删除"
    if id8 in KEEP6:
        return "保留·归回主题"
    if id8 in POST_130:
        return "保留·运行中"
    if member["pinned"]:
        return "保留·置顶"
    if member["archived"]:
        return "保留归档（不删除）"
    return "保留·可见"


def main():
    members = load_members()
    layers = load_layers()

    # ---- 校验输入 ----
    ids = [m["id"] for m in members]
    assert len(members) == 131, f"成员数 {len(members)} != 131"
    assert len(set(ids)) == 131, "ID 不唯一"
    assert sum(1 for m in members if m["archived"]) == 54, "归档数 != 54"
    assert sum(1 for m in members if m["pinned"]) == 10, "置顶数 != 10"
    layer_counts = Counter(layers.values())
    assert layer_counts == Counter({"S": 10, "A": 34, "B": 38, "C": 24, "D": 23}), layer_counts

    # ---- 校验映射 ----
    member_ids8 = {m["id8"] for m in members}
    assigned = set(ASSIGN)
    missing = member_ids8 - assigned
    extra = assigned - member_ids8
    assert not missing, f"未分组: {sorted(missing)}"
    assert not extra, f"映射多余: {sorted(extra)}"
    group_counts = Counter(g for g, _ in ASSIGN.values())
    for g in GROUPS:
        assert group_counts[g] > 0, f"空组 {g}"
    assert sum(group_counts.values()) == 131
    cleanup_counts = Counter(CLEANUP_KIND.values())
    assert cleanup_counts == Counter({"问候": 7, "连接测试": 4, "Arduino 重试": 6}), cleanup_counts
    assert set(CLEANUP_KIND) == {i for i, (g, _) in ASSIGN.items() if g == "清理候选"}
    assert KEEP6 == {i for i in KEEP6 if ASSIGN[i][0] != "清理候选" and i in member_ids8}

    # 上一轮 130 口径断言
    base130 = Counter()
    for id8, (g, _) in ASSIGN.items():
        if id8 not in POST_130:
            base130[g] += 1
    for g in GROUPS:
        assert base130[g] == PREV_130[g], f"{g}: 130口径 {base130[g]} != 上一轮 {PREV_130[g]}"

    # ---- 输出数据行 ----
    recs = []
    for m in members:
        g, reason = ASSIGN[m["id8"]]
        recs.append({**m, "group": g, "layer": layers.get(m["id8"], "未分层"),
                     "recommendation": recommendation(m), "reason": reason})

    def sort_key(r):
        gidx = GROUPS.index(r["group"])
        if r["group"] == "清理候选":
            return (gidx, CLEANUP_ORDER[CLEANUP_KIND[r["id8"]]], 0.0, r["title"])
        return (gidx, LAYER_ORDER[r["layer"]], -r["mtime"].timestamp(), r["title"])

    recs.sort(key=sort_key)

    # ---- 写 CSV ----
    with open(CSV_OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "current_name", "prefix", "group", "archived", "pinned", "layer", "recommendation", "reason"])
        for r in recs:
            w.writerow([r["id"], r["title"], r["prefix"], r["group"],
                        "True" if r["archived"] else "False",
                        "True" if r["pinned"] else "False",
                        r["layer"], r["recommendation"], r["reason"]])
    csv_sha = hashlib.sha256(CSV_OUT.read_bytes()).hexdigest()

    # ---- 汇总 ----
    now = datetime.now()
    gen_time = now.strftime("%Y-%m-%d %H:%M")
    def gstats(g):
        rows = [r for r in recs if r["group"] == g]
        return rows, sum(1 for r in rows if not r["archived"]), sum(1 for r in rows if r["archived"]), sum(1 for r in rows if r["pinned"])

    total_visible = sum(1 for r in recs if not r["archived"])
    total_archived = sum(1 for r in recs if r["archived"])
    total_pinned = sum(1 for r in recs if r["pinned"])

    # 前缀分布
    prefix_dist = OrderedDict()
    for r in recs:
        prefix_dist.setdefault(r["prefix"], Counter())[r["group"]] += 1
    ordered_prefixes = [p for p in PREFIX_ORDER if p in prefix_dist] + \
                       [p for p in prefix_dist if p not in PREFIX_ORDER]

    # 130 口径逐组
    base130_rows = [r for r in recs if r["id8"] not in POST_130]

    # 每组明细表
    def detail_table(g):
        rows, vis, arc, pin = gstats(g)
        lines = ["| ID（8 位） | 当前名称 | 状态 | 置顶 | 层级 | 建议 |",
                 "| --- | --- | --- | --- | --- | --- |"]
        for r in rows:
            lines.append("| {id8} | {title} | {status} | {pin} | {layer} | {rec} |".format(
                id8=r["id8"], title=r["title"], status="归档" if r["archived"] else "可见",
                pin="是" if r["pinned"] else "", layer=r["layer"], rec=r["recommendation"]))
        lines.append("")
        lines.append(f"> 小计：{len(rows)} 条（可见 {vis} / 归档 {arc}，置顶 {pin}）。")
        return "\n".join(lines)

    cleanup_rows = [r for r in recs if r["group"] == "清理候选"]
    cleanup_table = ["| ID（8 位） | 当前名称 | 状态 | 归类原因 | 建议 |",
                     "| --- | --- | --- | --- | --- |"]
    for r in cleanup_rows:
        cleanup_table.append("| {} | {} | {} | {} | {} |".format(
            r["id8"], r["title"], "归档" if r["archived"] else "可见",
            CLEANUP_KIND[r["id8"]], "归档观察·不删除"))
    cleanup_table = "\n".join(cleanup_table)

    keep_rows = [r for r in recs if r["id8"] in KEEP6]
    keep_table = ["| ID（8 位） | 当前名称 | 归入组 | 理由 |",
                  "| --- | --- | --- | --- |"]
    for r in keep_rows:
        keep_table.append("| {} | {} | {} | {} |".format(r["id8"], r["title"], r["group"], r["reason"]))
    keep_table = "\n".join(keep_table)

    # 汇总表
    summary_rows = ["| 组名 | 条数 | 可见 | 归档 | 置顶 | 主要对象/关键词 |",
                    "| --- | --- | --- | --- | --- | --- |"]
    for g in GROUPS:
        rows, vis, arc, pin = gstats(g)
        summary_rows.append(f"| {g} | {len(rows)} | {vis} | {arc} | {pin} | {GROUP_KEYWORDS[g]} |")
    summary_rows.append(f"| **合计** | **{len(recs)}** | **{total_visible}** | **{total_archived}** | **{total_pinned}** | 8 主题组 + 清理候选 |")
    summary_table = "\n".join(summary_rows)

    # 差异表
    diff_rows = ["| 组名 | 上一轮 130 口径 | 本方案 130 口径 | 本方案 131（含治理会话） | 差值 | 原因 |",
                 "| --- | --- | --- | --- | --- | --- |"]
    for g in GROUPS:
        cur = group_counts[g]
        b = base130[g]
        diff = cur - b
        reason = "—"
        if diff:
            reason = "本方案 130 口径不含 c8634800（23:11 建立）；本轮新增治理会话归入本组"
        diff_rows.append(f"| {g} | {PREV_130[g]} | {b} | {cur} | {'+' if diff > 0 else ''}{diff if diff else '0'} | {reason} |")
    diff_rows.append(f"| **合计** | **130** | **{len(base130_rows)}** | **{len(recs)}** | **+1** | 新增本次运行中的治理会话 c8634800 |")
    diff_table = "\n".join(diff_rows)

    # 前缀分布表
    prefix_table = ["| 前缀 | 条数 | 主要落组（条数） |", "| --- | --- | --- |"]
    for p in ordered_prefixes:
        cnt = prefix_dist[p]
        parts = "、".join(f"{g} {n}" for g, n in cnt.most_common())
        prefix_table.append(f"| {p} | {sum(cnt.values())} | {parts} |")
    prefix_table = "\n".join(prefix_table)

    # 在办入口（置顶 10 条）
    pin_rows = [r for r in recs if r["pinned"]]
    pin_table_lines = ["| # | ID（8 位） | 当前名称 | 组 | 状态 |", "| --- | --- | --- | --- | --- |"]
    for i, r in enumerate(pin_rows, 1):
        pin_table_lines.append("| {} | {} | {} | {} | {} |".format(
            i, r["id8"], r["title"], r["group"], "归档" if r["archived"] else "可见"))
    pin_table = "\n".join(pin_table_lines)

    # 清理候选中仍可见的
    cleanup_visible = [r for r in cleanup_rows if not r["archived"]]

    # 一致性与交叉校验数字
    group_counts_line = " / ".join(f"{g} {group_counts[g]}" for g in GROUPS)

    doc = f"""# DSH 会话主题分组方案（2026-10-23）

> **生成时间**：北京时间 {gen_time}（由 `_dsh_group_work/build_grouping.py` 从单一数据源生成；文档数字与同名 CSV 一致）
> **数据口径**：**131 条侧栏成员会话**（`_dsh_group_work/members-catalog.csv`，2026-10-23 23:14:58 生成）。只读标题与元数据（ID／标题／前缀／归档／置顶／修改时间）；**未读取任何会话消息正文**；本轮**未修改侧栏、未删除、未改名、未归档**任何会话，实际删除 0 条。
> **层级依据**：`00_DSH会话重要性排序_20261023.md`（129 条快照的 S/A/B/C/D 层）；本轮 2 条新增会话不在快照内，标“未分层”。
> **与 129 条文档快照的关系**：+2——`3ec7e7f1`“分析yifei聊天记录与美术馆”（会话目录 20:12 建立、21:41 最后活动）与 `c8634800`“# DSH 会话治理交接：修订稿已”（**本次运行中的治理会话**，23:11 建立；标题取自 23:16 投影缓存，可能变化）。
> **状态基线**：可见 {total_visible} / 归档 {total_archived}；置顶 {total_pinned}；S/A/B/C/D = 10/34/38/24/23，另 2 条未分层。归档数与旧快照同为 54。

## 一、结论（先看这里）

1. **131 条成员全部落位**：8 个主题组 114 条 + 清理候选 17 条 = 131，ID 无重复、无遗漏。
2. **相对上一轮 130 条口径，8 组计数逐组一致**，唯一 +1 是 **AI平台与开发 37 → 38**：本轮运行中的治理会话 `c8634800` 于 23:11 建立，必然不在上一轮 130 条盘点内；另一条新增 `3ec7e7f1` 于 20:12 建立，已含在 130 口径中。
3. **以“分组”为主，不删会话**：清理候选 17 条只建议“归档观察、不删除”；用户此前口头允许删除不必要的会话，但**本轮实际删除 0 条**，侧栏零改动。
4. **落地靠三层手段**：标题前缀搜索（17 个前缀）、置顶 10 条（在办入口）、归档 54 条（历史沉底）。DSH 原生“分组”以工作目录为键，131 条侧栏成员 `cwd` 均为 `C:\\Users\\wardc\\Desktop`，无法拆成多个原生分组，详见第八节。

## 二、数据口径与边界

- **成员口径**：131 条 = 129 条文档快照成员 + 2 条新会话（`3ec7e7f1`、`c8634800`）。43 条非成员目录不计入，见附录。
- **状态口径**：可见/归档、置顶取自 2026-10-23 23:14 的 workspace 投影（已含在 members-catalog.csv）；本轮未改动状态。
- **层级口径**：S/A/B/C/D 来自 2026-10-23 09:28 的重要性排序文档（129 条），不是本轮重新评定；`3ec7e7f1`、`c8634800` 未收录，标“未分层”。
- **标题口径**：标题为当前名称，未改名；`c8634800` 标题可能随会话继续变化。
- **组内排序**：S → A → B → C → D → 未分层；同层按修改时间倒序。
- **只读边界**：本轮只读标题/元数据与既有治理文档（含会话目录建立时间，仅用于区分新增），未读取消息正文、未调用归档/改名 API、未触碰 DSH state 目录。

## 三、8 组汇总

{summary_table}

## 四、分组明细

### 1. 家庭事务（{group_counts['家庭事务']}）

母亲线与两件母亲事务的实质副本；S 层 2 条均置顶。

{detail_table('家庭事务')}

### 2. 人物与沟通（{group_counts['人物与沟通']}）

笑一主线 + 7 条人物分析/沟通策略 + 李梓燏副本；笑一 2 条 S 层置顶。

{detail_table('人物与沟通')}

### 3. 学业/导师与课程（{group_counts['学业/导师与课程']}）

陈晔、王利敏、中传课程、姜涛（导师）与中期汇报/学业事务；S 层 2 条。

{detail_table('学业/导师与课程')}

### 4. 艺术创作与三维（{group_counts['艺术创作与三维']}）

美术馆、双手成曲、植物染、宣传视觉、Hyper3D/Rodin、Tripo、开源剪辑与文档交付；新会话 `3ec7e7f1` 因标题含“美术馆”归入本组（如更偏向人物线可改归“人物与沟通”，见第七节备注）。

{detail_table('艺术创作与三维')}

### 5. 校友会与公益（{group_counts['校友会与公益']}）

校友会公众号、格拉斯哥北京校友会、知行计划与韩云峰项目。

{detail_table('校友会与公益')}

### 6. AI平台与开发（{group_counts['AI平台与开发']}）

Codex/zcode/Workbuddy/ChatGPT 等工具链、DeepSeek/MiMo/超算/中转站模型接入、配置与工作区治理、开发 Demo，以及**本次运行中的治理会话 `c8634800`**（{group_counts['AI平台与开发']} 条中含 1 条运行中会话）。

{detail_table('AI平台与开发')}

### 7. 微信与WeFlow（{group_counts['微信与WeFlow']}）

WeFlow 数据检索、锚点修复、导出、API 与进程，及微信记录导出历史条目。

{detail_table('微信与WeFlow')}

### 8. 电脑/网络与文件（{group_counts['电脑/网络与文件']}）

存储与清理、文件定位/转换/照片、校园网与 VPN、蓝屏/进程/软件安装、Arduino 实操与历史系统维护。

{detail_table('电脑/网络与文件')}

## 五、清理候选（17 条，建议归档观察、不删除）

口径：**17 = 问候 7 + 连接测试 4 + Arduino 无回复重试 6**，全部为总目 D 层“测试与重复”。其中 **15 条已归档、2 条仍可见**（`1f0b9e50` 测试｜问候·1、`0eb2e8b3` 测试｜问候·2）；建议只对仍可见的 2 条做手工归档观察。**不删除**：删除会话不可逆，且用户偏好以分组为主。

{cleanup_table}

> 小计：17 条（问候 7 / 连接测试 4 / Arduino 重试 6；可见 {len(cleanup_visible)} / 归档 {17 - len(cleanup_visible)}）。

## 六、原测试/重复但有业务内容、建议保留（6 条）

这 6 条在旧分层里被标为“测试/重复”（D 层），但按任务书口径与其旧名/消息量，存在业务内容或作为同主题副本有保留价值，**建议保留并归回主题**，不放入清理候选。其中 5 条当前已归档、1 条可见（`7e808edf`）。

{keep_table}

> 备注：`7e808edf` 当前可见且有 43/153 条消息，是李梓燏深度侧写的实质副本；若用户只想留一份，可自行归档，本方案不主动处理。

## 七、与上一轮 130 条口径的差异

**回推依据**：会话目录只读时间戳显示 `3ec7e7f1` 于 20:12 建立、`c8634800` 于 23:11 建立；文档快照 129 条写于 09:28。因此上一轮“130 条”= 129 条快照 + `3ec7e7f1`，本轮 131 条 = 上一轮 130 + `c8634800`。

{diff_table}

**说明**：

- 上一轮未留下逐 ID 机器清单，上表“本方案 130 口径”是本轮把 `c8634800` 剔除后复算的结果；能逐组对齐，说明分组口径稳定，差异仅来自新增治理会话。
- 若用户更希望 `3ec7e7f1` 按“人物聊天记录分析”归入人物与沟通，可把它从艺术组移到人物组：艺术 12→11、人物 10→11，其余不变（**两可，供用户确认**）。
- 清理候选 17 条的口径与上一轮完全一致：问候 7、连接测试 4、Arduino 重试 6。

## 八、落地方式与限制

### 8.1 为什么侧栏无法直接按主题分组

- **DSH 原生“分组”绑定工作目录（cwd）**：同一 cwd 的会话落在同一个原生分组里。当前 131 条成员会话的 cwd 均为 `C:\\Users\\wardc\\Desktop`，无法拆成 8 个原生分组。
- **旧会话 cwd 不可迁移**：迁移会改变会话归属与检索范围，且需要改 DSH 状态，风险高、不可逆。
- **本会话对 DSH state 无写权限**：状态目录 `C:\\Users\\wardc\\Documents\\New project gpt\\AI-archive\\apps\\deepseek-harness\\state` 不在本会话可写范围；本轮也按要求不修改 DSH 状态。
- 因此本方案只产出“方案 + 清单”，侧栏保持原样：**未置顶、未归档、未改名、未删除；实际删除 0 条**。

### 8.2 替代手段：用“前缀 + 置顶 + 归档”模拟分组

**① 标题前缀搜索**：17 个前缀均可直接在侧栏搜索框按“前缀｜”过滤（如 `人物｜`、`工具｜WeFlow`），比翻 131 条快得多。前缀与落组关系：

{prefix_table}

上表中的 2 条无前缀会话（`3ec7e7f1`、`c8634800`）只能按标题关键词或 ID 搜索；建议后续改名为“美术馆｜yifei·聊天记录与美术馆”“配置｜DSH 会话治理交接”以便前缀检索（**未执行**，仅建议）。

**② 置顶 10 条 = 在办入口**（当前状态，无需调整）：

{pin_table}

**③ 归档 54 条**：历史/测试/重复已沉底；清理候选中再归档仍可见的 2 条（`1f0b9e50`、`0eb2e8b3`）即可让侧栏更干净。

### 8.3 用户手工操作步骤

- **置顶/取消置顶**：侧栏会话条目的“更多/右键”菜单 → 置顶（或取消置顶）。置顶后该会话固定在侧栏顶部，跨重启保留。
- **归档**：右键 → 归档；归档后从主列表消失，可在归档区找回。建议先只归档“清理候选”中仍可见的 2 条（`1f0b9e50`、`0eb2e8b3`）。
- **按主题筛选**：侧栏搜索框输入前缀片段（如 `陈晔｜`、`配置｜`）即可过滤；组合对象名（如 `WeFlow`、`知行计划`）可进一步缩小。
- **若未来 DSH 支持标签/自定义分组**：可直接以本清单 CSV 为数据源批量导入分组（`group` 列即目标分组）。

### 8.4 本次实际变化与未执行清单

- **实际变化**：仅新增 2 个交付文件——本方案文档与 `DSH工作区\\00_DSH会话分组清单_20261023.csv`；另在 `_dsh_group_work` 下新增生成脚本 `build_grouping.py` 与对账文件 `reconciliation.json`（临时核对用，可删除）。DSH 状态与侧栏**零改动**。
- **未执行**：清理候选 17 条未归档；6 条保留项未移动；置顶未调整；未改名；未删除任何会话或文件。

## 九、自检与对账

- 数据行：**131 行**（不含表头），ID 唯一（131/131），无重复、无遗漏。
- 分组求和：{group_counts_line}，合计 **131**。
- 状态一致：可见 **{total_visible}** / 归档 **{total_archived}** / 置顶 **{total_pinned}**，与 CSV 汇总一致；归档 54 与旧快照一致。
- 清理候选：**17 条 = 问候 7 + 连接测试 4 + Arduino 重试 6**，与任务书一致。
- 6 条保留项：`db5d2b39`、`f957f9f8`、`bb0a3305`、`7e808edf`、`1d5f7c4c`、`68437449`，全部已归回主题组。
- 与上一轮 130 口径：8 组逐组一致，仅 AI平台与开发 +1（`c8634800`）；合计 130 → 131，差 +1。
- 文件校验：`00_DSH会话分组清单_20261023.csv` SHA-256 = `{csv_sha}`；本文件 SHA-256 在生成后回填到 `_dsh_group_work/reconciliation.json` 与交付回报（正文内嵌自身哈希会造成自指，故不内嵌）。

## 附录：43 条非成员目录

这 43 条是会话库目录中**不属于侧栏成员**的目录（42 条子代理转录 + 1 条未加入工作区的 `f936f3c5`），不计入 131 条成员，也不做主题归类；本轮未移动、未归档、未删除它们。详见 `00_DSH会话总目_20261023.md` 的非成员附录。
"""
    DOC_OUT.write_text(doc, encoding="utf-8", newline="\n")
    doc_sha = hashlib.sha256(DOC_OUT.read_bytes()).hexdigest()

    # ---- 对账 JSON（含两文件 SHA-256） ----
    recon = {
        "generatedAt": now.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "inputs": {
            "membersCatalog": str(CATALOG),
            "rankingSnapshot": str(RANKING),
            "memberCount": len(members),
            "catalogGeneratedAt": "2026-10-23T23:14:58+08:00",
        },
        "outputs": {
            "doc": {"path": str(DOC_OUT), "sha256": doc_sha},
            "csv": {"path": str(CSV_OUT), "sha256": csv_sha},
        },
        "checks": {
            "rows": len(recs),
            "uniqueIds": len({r["id"] for r in recs}),
            "groupCounts": {g: group_counts[g] for g in GROUPS},
            "groupSum": sum(group_counts.values()),
            "visible": total_visible,
            "archived": total_archived,
            "pinned": total_pinned,
            "cleanup": {
                "total": len(cleanup_rows),
                "greetings": cleanup_counts["问候"],
                "connectionTests": cleanup_counts["连接测试"],
                "arduinoRetries": cleanup_counts["Arduino 重试"],
            },
            "keep6": sorted(KEEP6),
            "base130MatchesPrevious": all(base130[g] == PREV_130[g] for g in GROUPS),
        },
        "previousRound130": PREV_130,
        "base130": {g: base130[g] for g in GROUPS},
        "current131": {g: group_counts[g] for g in GROUPS},
    }
    RECON_OUT.write_text(json.dumps(recon, ensure_ascii=False, indent=2), encoding="utf-8")

    print("OK")
    print("groupCounts:", dict((g, group_counts[g]) for g in GROUPS))
    print("visible/archived/pinned:", total_visible, total_archived, total_pinned)
    print("cleanup:", cleanup_counts)
    print("base130:", dict((g, base130[g]) for g in GROUPS))
    print("doc:", DOC_OUT, doc_sha)
    print("csv:", CSV_OUT, csv_sha)


if __name__ == "__main__":
    main()
