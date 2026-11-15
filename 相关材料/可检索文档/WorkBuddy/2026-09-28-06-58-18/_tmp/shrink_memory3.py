# -*- coding: utf-8 -*-
"""第三轮压缩 MEMORY.md —— 目标 <=15,900 字节。"""
import io

p = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18\.workbuddy-ai\memory\MEMORY.md"
s = io.open(p, encoding="utf-8").read()
orig = len(s.encode("utf-8"))


def swap(o, n):
    global s
    if o in s:
        s = s.replace(o, n, 1)
        return True
    print("MISS:", o[:50].replace("\n", " "))
    return False


# ---- §四 数据源行 ----
swap(
    "消息 **394,173** ✅ · `contact.db` 人 42,708 / 群 714 / 标签 52 🟡（`chatroom_member` 5 万＝社交拓扑，未用）· `general.db` FMessage/transfer/redEnvelope/SearchRecent ✅ · `sns.db` 朋友圈 🟡 · `favorite.db` 230 ⬜ · `media_0.db` 语音 2,486 ⬜ · 表情/媒体/头像 ⬜低优先",
    "消息 **395,728** ✅ · `contact.db` 人 42,708 / 群 714 🟡（`chatroom_member` 5 万＝社交拓扑，未用）· `general.db` FMessage/transfer/redEnvelope/SearchRecent ✅ · `sns.db` 🟡 · `favorite.db` 230 ⬜ · `media_0.db` 语音 2,486 ⬜ · 表情/媒体/头像 ⬜低优先",
)

# ---- §五 第 48 行 ----
swap(
    "| 48 | 决策中枢四线（10-07）：① 极狐/安鹏＝三次返款**全未到账**（卡 09-26），10-07 又剐蹭 ② 柯益盈＝锚点「可以结婚的对象」但**空窗 11 个月** ③ Tripo＝群内 0 发言，但 10-06 前确「捏了项目」→「只薅额度」需修正 ④ 何一沙＝美术馆媒体部主任，「拍科普展素材」为**推断** |",
    "| 48 | 决策中枢四线（10-07）：① 极狐/安鹏＝三次返款**全未到账**（卡 09-26），10-07 又剐蹭 ② 柯益盈＝锚点「可以结婚的对象」但**空窗 11 个月** ③ Tripo＝群内 0 发言但确「捏了项目」→「只薅额度」需修正 ④ 何一沙＝美术馆媒体部主任，「拍科普展素材」为**推断** |",
)

# ---- §六 13/14 缩短 ----
swap(
    "13. ★ **不得建议他改任务定义**（《激进构成》§4 路线 E 已否决）：可谈执行细节（出勤天数 / 素材复用），**不可谈目标本身**。理由：导师+党支部书记+「临汾市里领导的指示」的权力结构 + 与「换机会的代价」冲突 + 手上欠 19 天脚本。\n"
    "14. ★ **不得把「已闭环」读成「办完了」**：陈晔线闭环的只是**视频一件**；脚本/群/日期三件仍未动。也不得把「秒回规格」读成「满意」。",
    "13. ★ **不得建议他改任务定义**（《激进构成》§4 路线 E 已否决）：可谈执行细节（出勤天数 / 素材复用），**不可谈目标本身** —— 权力结构不允许 + 与「换机会的代价」冲突 + 欠 19 天脚本。\n"
    "14. ★ **不得把「已闭环」读成「办完了」**（陈晔线只闭环**视频一件**）· **不得把「已兑现行动」读成「问题解决了」**（10-07 的核心不满是「说话做不到」）· 不得把「秒回规格」读成「满意」。",
)

# ---- §七 71/74 缩短 ----
swap(
    "- ✅ `analysis.sqlite`：事件 2,864 / 证据 5,463 / 结论 61 · 可追溯率 51.4% · 结论↔证据绑定 53.3%。年度重建第一轮：8 线×13 月 · 178 候选 · **C1/C2 证伪** · **C3-a 成立 / C3-b 不成立**。",
    "- ✅ `analysis.sqlite`：事件 2,864 / 证据 5,463 / 结论 64 · 年度重建第一轮 8 线×13 月 · 178 候选 · **C1/C2 证伪** · **C3-a 成立 / C3-b 不成立**。",
)
swap(
    "· `aliases` **3,209**。★ 修 3 条 `status`/`cross_domains` 写反 + **修脚本根因**（`build_connective_tissue.py` 原 `delete…like 'hyp:%'` 会静默抹掉人工增量）。",
    "· `aliases` **3,209**。★ 修 3 条 `status` 写反 + **修脚本根因**（`build_connective_tissue.py` 原 `delete…like 'hyp:%'` 会静默抹掉人工增量）。",
)

# ---- §十 运镜行缩短 ----
swap(
    "- **运镜分析**（10-08）：`tools/cinema_shot_analyzer.py`（**判据创新＝视差残差比**）。权威分类学＝CameraBench；易跑方案＝`kandinsky-video-tools`。⬜《绝对者》本体未拿到。",
    "- **运镜分析**（10-08）：`tools/cinema_shot_analyzer.py`（**判据创新＝视差残差比**）。权威分类学＝CameraBench；易跑方案＝`kandinsky-video-tools`。⬜《绝对者》未拿到。",
)

io.open(p, "w", encoding="utf-8").write(s)
print("bytes: %d -> %d" % (orig, len(s.encode("utf-8"))))
