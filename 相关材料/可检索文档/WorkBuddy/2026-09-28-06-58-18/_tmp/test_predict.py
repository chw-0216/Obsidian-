# -*- coding: utf-8 -*-
"""test_predict.py —— 在副本上验证「理解判断与校准」全流程（不碰真库）。"""
import os
import sqlite3
import sys
import tempfile

ROOT = r'C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18'
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import selfmodel as SM  # noqa: E402

TMP = tempfile.mkdtemp(prefix='pred_')
db = os.path.join(TMP, 'analysis.sqlite')
s = sqlite3.connect(os.path.join(ROOT, 'analysis.sqlite'))
d = sqlite3.connect(db)
s.backup(d)
d.close()
s.close()
SM.DB = db
vd = os.path.join(TMP, '06_自我模型')
os.makedirs(vd, exist_ok=True)
SM.VIEW_DIR = vd
SM.ROOT = TMP

OK = []


def check(name, cond):
    OK.append(bool(cond))
    print(('  OK  ' if cond else '  XX  ') + name)


def q(sql, *a):
    c = sqlite3.connect(db)
    r = c.execute(sql, a).fetchone()
    c.close()
    return r


print('T1 add 合法')
SM.cmd_predict('add', 'P-T1', '10-13 汇报呈现什么', '他会以过程叙事为主',
               '--basis', 'SC-CON-001', '--conf', 'high')
row = q("select predicted_choice,basis_claims,confidence,match_status "
        "from predictions where pred_id='P-T1'")
check('已写入且待结算', row and row[0] == '他会以过程叙事为主' and row[3] == 'pending')

print('T2 add 非法 basis 应拒绝')
SM.cmd_predict('add', 'P-BAD', 'x', 'y', '--basis', 'SC-NOT-EXIST')
check('非法依据被拒', q("select count(*) from predictions where pred_id='P-BAD'")[0] == 0)

print('T3 resolve 人工判定')
SM.cmd_predict('resolve', 'P-T1', '以过程叙事为主，穿插作品', '--match', 'matched')
row = q("select match_status,match_by from predictions where pred_id='P-T1'")
check('结算为一致/人工', row[0] == 'matched' and row[1] == 'human')

print('T4 自动粗判（不一致）')
SM.cmd_predict('add', 'P-T2', '另一件待决', '他会先做A', '--basis', 'SC-CON-001')
SM.cmd_predict('resolve', 'P-T2', '他完全换了方向先做B')
row = q("select match_status,match_by from predictions where pred_id='P-T2'")
check('粗判为不一致', row[0] == 'mismatched' and row[1] == 'auto')

print('T5 outcome 关联建议')
SM.cmd_predict('add', 'P-T3', '测试关联建议', '预测X',
               '--basis', 'SC-CON-001', '--rec', 'REC-VIDEO-WORKSHOP')
SM.cmd_predict('outcome', 'P-T3', 'failed', '测试')
check('结果已记录', q("select outcome_verdict from predictions where pred_id='P-T3'")[0] == 'failed')

print('T6 calibrate')
SM.cmd_calibrate()

print('T7 render 生成第 6 视图')
SM.cmd_render()
p = os.path.join(vd, '理解判断与校准.md')
check('视图已生成', os.path.exists(p))
txt = open(p, encoding='utf-8').read()
check('含三节结构', '一、待结算' in txt and '二、已结算' in txt and '三、校准小结' in txt)

print('T8 render 幂等（字节数一致）')
b1 = os.path.getsize(p)
SM.cmd_render()
b2 = os.path.getsize(p)
check('字节数一致 %d==%d' % (b1, b2), b1 == b2)

print('T9 _guess_match 边界')
check('完全相同→matched', SM._guess_match('以过程叙事为主', '以过程叙事为主') == 'matched')
check('空值→pending', SM._guess_match('', 'x') == 'pending')
check('完全不同→mismatched', SM._guess_match('他会先做A', '他完全换了方向先做B') == 'mismatched')

print()
print('=' * 52)
print('  通过 %d/%d' % (sum(OK), len(OK)))
print('=' * 52)
print('  真库未动；临时目录 %s' % TMP)
