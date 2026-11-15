# -*- coding: utf-8 -*-
"""test_selfmodel_sync.py —— 在**副本**上验证「手填区 → 数据库」闭环。

不碰真库、不碰真视图。覆盖：
  T1  填理由 → sync --apply → 库里有值
  T2  幂等：再跑一次 → 0 差异
  T3  render 后：已入库的行从手填区消失，未填的仍在
  T4  非法值（判断写错）→ 跳过 + 报警，且该行**保留**在手填区
  T5  回答 learning_question → status 自动变 answered
  T6  reason 子命令直写
"""
import io
import os
import shutil
import sys
import tempfile

ROOT = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
sys.path.insert(0, os.path.join(ROOT, "tools"))
import selfmodel as SM  # noqa

TMP = tempfile.mkdtemp(prefix="smtest_")
OK = []


def setup():
    import sqlite3
    db = os.path.join(TMP, "analysis.sqlite")
    # ★ 用 SQLite 备份 API（含 WAL 内容），不要直接 copy 主文件
    src = sqlite3.connect(os.path.join(ROOT, "analysis.sqlite"))
    dst = sqlite3.connect(db)
    src.backup(dst)
    dst.close()
    src.close()
    vd = os.path.join(TMP, "06_自我模型")
    os.makedirs(vd, exist_ok=True)
    real_vd = SM.VIEW_DIR
    for fn in os.listdir(real_vd):
        if fn.endswith(".md"):
            shutil.copy2(os.path.join(real_vd, fn), os.path.join(vd, fn))
    SM.DB = db
    SM.VIEW_DIR = vd
    SM.ROOT = TMP          # 备份目录也落在临时区，不污染真工作区
    return vd


def zone_path(vd, name):
    return os.path.join(vd, name)


def fill(vd, name, old_line, new_line):
    p = zone_path(vd, name)
    txt = io.open(p, encoding="utf-8").read()
    assert old_line in txt, "模板里找不到：%r" % old_line
    io.open(p, "w", encoding="utf-8", newline="\n").write(
        txt.replace(old_line, new_line, 1))


def read_db(db, sql, args=()):
    import sqlite3
    c = sqlite3.connect(db)
    r = c.execute(sql, args).fetchone()
    c.close()
    return r


def main():
    vd = setup()
    db = SM.DB

    # ---------- T1 填理由 → sync --apply
    fill(vd, "我的选择与理由.md",
         "[CE-20261013-REPORT]\n理由: ",
         "[CE-20261013-REPORT]\n理由: 【测试】因为材料已成型，改动最小")
    plans, bad = SM._collect_sync_plan()
    assert len(plans) == 1, "T1 期望 1 处改动，实得 %d（bad=%s）" % (len(plans), bad)
    SM.cmd_sync(apply=True, quiet=True)
    got = read_db(db, "select reasons_verbatim from choice_episodes "
                      "where episode_id='CE-20261013-REPORT'")[0]
    assert got == "【测试】因为材料已成型，改动最小", "T1 库值不对：%r" % got
    OK.append("T1 填理由 → 入库 ✅")

    # ---------- T2 幂等
    plans2, _ = SM._collect_sync_plan()
    assert len(plans2) == 0, "T2 期望 0 差异，实得 %d" % len(plans2)
    OK.append("T2 幂等（再跑 0 差异）✅")

    # ---------- T3 render 后：已入库的行消失，未填的保留
    fill(vd, "我的选择与理由.md",
         "[CE-20261010-AIGC-FRAME]\n理由: ",
         "[CE-20261010-AIGC-FRAME]\n理由: 【测试】想把经济学背景用上")
    SM.cmd_render()          # render 会先自动 sync，再重写视图
    z = SM._read_zone(zone_path(vd, "我的选择与理由.md"))
    assert "材料已成型" not in z, "T3 已入库的行没消失"
    assert "想把经济学背景用上" not in z, "T3 已入库的行没消失"
    got2 = read_db(db, "select reasons_verbatim from choice_episodes "
                       "where episode_id='CE-20261010-AIGC-FRAME'")[0]
    assert got2 == "【测试】想把经济学背景用上", "T3 render 未读回：%r" % got2
    assert "[CE-20261011-VIDEO]" in z, "T3 未填的条目丢了"
    OK.append("T3 render 读回 + 手填区清理 ✅")

    # ---------- T4 非法值 → 跳过 + 报警 + 行保留
    fill(vd, "系统当前怎样理解我.md",
         "[SC-CON-005]\n我的判断: ",
         "[SC-CON-005]\n我的判断: 大概吧")
    plans4, bad4 = SM._collect_sync_plan()
    assert any("不合法" in b for b in bad4), "T4 没报警：%s" % bad4
    SM.cmd_render()
    z4 = SM._read_zone(zone_path(vd, "系统当前怎样理解我.md"))
    assert "大概吧" in z4, "T4 非法行被吞了（应保留）"
    OK.append("T4 非法值跳过 + 原样保留 ✅")

    # ---------- T5 回答 learning_question → status=answered
    fill(vd, "值得继续问的问题.md",
         "[LQ-JIHU-SEND]\n回答: ",
         "[LQ-JIHU-SEND]\n回答: 【测试】没发，明天就补发")
    SM.cmd_sync(apply=True, quiet=True)
    st, av, at = read_db(db, "select status,answer_verbatim,answer_time from "
                             "learning_questions where question_id='LQ-JIHU-SEND'")
    assert st == "answered" and av == "【测试】没发，明天就补发" and at, \
        "T5 不对：%r %r %r" % (st, av, at)
    OK.append("T5 答题 → status=answered + 时间 ✅")

    # ---------- T6 reason 子命令
    SM.cmd_reason("CE-20261008-SEPHORA", "【测试】她提的，我不想再吵")
    got6 = read_db(db, "select reasons_verbatim from choice_episodes "
                       "where episode_id='CE-20261008-SEPHORA'")[0]
    assert got6 == "【测试】她提的，我不想再吵", "T6 不对：%r" % got6
    OK.append("T6 reason 子命令 ✅")

    # ---------- T7 render 幂等：连续两次字节数一致
    p1 = zone_path(vd, "系统当前怎样理解我.md")
    SM.cmd_render()
    b1 = os.path.getsize(p1)
    SM.cmd_render()
    b2 = os.path.getsize(p1)
    assert b1 == b2, "T7 render 不幂等：%d → %d" % (b1, b2)
    OK.append("T7 render 幂等（%d 字节不变）✅" % b1)

    print("\n" + "=" * 60)
    for o in OK:
        print("  " + o)
    print("=" * 60)
    print("  %d/%d 通过" % (len(OK), 7))
    print("  真库未动；临时目录：%s" % TMP)


if __name__ == "__main__":
    main()
