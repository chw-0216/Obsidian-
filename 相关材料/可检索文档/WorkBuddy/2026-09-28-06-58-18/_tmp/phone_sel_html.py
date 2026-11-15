# -*- coding: utf-8 -*-
"""把「手机可用照片清单」渲染成一页 HTML（逐月分布 + 规则 + 下一步）。"""
import csv, io, os, datetime
from collections import Counter, OrderedDict

WS = r"C:\Users\wardc\WorkBuddy AI\2026-09-28-06-58-18"
CSVP = os.path.join(WS, "手机可用照片清单_2026-10-06.csv")
OUT = os.path.join(WS, "手机可用照片清单_2026-10-06.html")

rows = list(csv.DictReader(io.open(CSVP, encoding="utf-8-sig")))
months = Counter()
for r in rows:
    months[r["date"][:7]] += 1
months = OrderedDict(sorted(months.items()))
mx = max(months.values()) if months else 1
total_mb = sum(int(r["size"]) for r in rows) / 1048576

bars = "".join(
    '<div class="row"><span class="m">%s</span>'
    '<span class="bar" style="width:%.1f%%"></span>'
    '<span class="n">%d</span></div>' % (m, v / mx * 100, v)
    for m, v in months.items())

first, last = rows[0]["date"], rows[-1]["date"]

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>手机可用照片清单 · 2026-10-06</title>
<style>
:root{{--ink:#1F3D2B;--acc:#9E3B2E;--txt:#5A5A5A;--bg:#FAF9F6;--line:#E4E0D8}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--txt);
 font:15px/1.7 "Microsoft YaHei","PingFang SC",system-ui,sans-serif}}
header{{background:var(--ink);color:#fff;padding:32px 40px 26px}}
header h1{{margin:0 0 6px;font-size:25px}}
header p{{margin:2px 0;font-size:13.5px;color:#CFE0D4}}
main{{max-width:900px;margin:0 auto;padding:26px 20px 70px}}
.kpis{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:24px}}
.kpi{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:14px 20px;min-width:140px}}
.kpi b{{display:block;font-size:23px;color:var(--ink)}}
.kpi span{{font-size:12.5px;color:#8A867E}}
.card{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 22px 22px;margin-bottom:20px}}
.card h3{{margin:0 0 12px;font-size:16.5px;color:var(--ink)}}
.row{{display:flex;align-items:center;gap:10px;margin:3px 0}}
.m{{width:74px;font-size:13px;color:#5A5A5A;font-variant-numeric:tabular-nums}}
.bar{{height:15px;background:var(--acc);border-radius:3px;min-width:2px;opacity:.85}}
.n{{font-size:13px;color:var(--ink);font-variant-numeric:tabular-nums}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}
th,td{{text-align:left;padding:7px 8px;border-bottom:1px solid #EFECE6}}
th{{color:var(--ink);font-weight:600}}
code{{background:#F1EEE8;padding:1px 5px;border-radius:4px;font-size:12.5px}}
.warn{{background:#FDF4F2;border-left:5px solid var(--acc);border-radius:8px;padding:14px 18px;margin-bottom:20px}}
.warn b{{color:var(--acc)}}
</style></head><body>
<header>
  <h1>手机可用照片清单</h1>
  <p>荣耀 X60 Pro ｜ DCIM/Camera ｜ 2025-09-01 起（考上央美之后）</p>
  <p>生成 2026-10-06 ｜ 数据源：MediaStore 影像元数据（8,605 条索引）</p>
</header>
<main>
  <div class="kpis">
    <div class="kpi"><b>{len(rows)}</b><span>选中照片</span></div>
    <div class="kpi"><b>{total_mb:.0f} MB</b><span>预计体积</span></div>
    <div class="kpi"><b>{len(months)}</b><span>覆盖月份</span></div>
    <div class="kpi"><b>{first[:7]} → {last[:7]}</b><span>时间跨度</span></div>
  </div>

  <div class="warn">
    <b>口径：先筛后取，不是全量拉取。</b><br>
    手机里共 <b>8,605 张</b>影像，其中 <b>3,999 张是截图</b>、还有大量缓存与表情。
    下面这份是按「可用」筛出来的 <b>{len(rows)} 张</b> —— 只取这些，不把手机整个拷出来。
  </div>

  <div class="card">
    <h3>筛选规则（四条）</h3>
    <table>
      <tr><th style="width:34%">规则</th><th>说明</th><th style="width:22%">剔掉</th></tr>
      <tr><td>相册命中 <code>Camera</code></td><td>只要手机相机拍的；截图 / 表情 / 微信转发 / 缓存全部不要</td><td>5,282 张</td></tr>
      <tr><td>单张 ≥ 0.8 MB</td><td>太小的是缩略图、表情包、缓存图</td><td>116 张</td></tr>
      <tr><td>拍摄时间 ≥ 2025-09-01</td><td>「考上央美之后」这段；更早的属于本科/格拉斯哥时期</td><td>531 张</td></tr>
      <tr><td>去重</td><td>同名同体积只留一条</td><td>—</td></tr>
    </table>
  </div>

  <div class="card">
    <h3>逐月分布（{first[:7]} → {last[:7]}）</h3>
    {bars}
  </div>

  <div class="card">
    <h3>为什么值得取这一批</h3>
    <p style="margin:0 0 8px">微信库里的 68,158 张图<b>被剥掉了 EXIF</b>，拍摄日期结构性拿不到；
    这批手机原片带<b>真实拍摄时间</b>（精确到秒）和原始分辨率，是目前唯一能还原「什么时候在哪拍了什么」的一层。</p>
    <p style="margin:0">可直接补上的缺口：<b>06 厦门</b>（现无可用图）· <b>07 北京台</b>（全库仅 3 张）·
    <b>主 PPT 第 15 页</b>（AI 与交互技术，现 0 图）。</p>
  </div>

  <div class="card">
    <h3>下一步：需要你做一个动作</h3>
    <p style="margin:0 0 8px">手机 USB 调试已经开了（系统里能看到 <code>Android Composite ADB Interface</code>），
    但 <b>HonorSuite 正占着 USB</b>，adb 看不到设备；它以后台管理员权限运行，程序层面杀不掉。</p>
    <p style="margin:0"><b>请在任务栏右下角托盘找到 HonorSuite 图标 → 右键 → 退出</b>（确认窗口全关）。
    退出后我立刻执行取回，只取上面这 {len(rows)} 张。</p>
  </div>
</main>
<footer style="text-align:center;color:#A8A49C;font-size:12.5px;padding:18px">
清单文件：<code>手机可用照片清单_2026-10-06.csv</code> ｜ 工具：<code>tools\\phone_photos.py</code>
</footer>
</body></html>"""

io.open(OUT, "w", encoding="utf-8").write(html)
print("→", OUT, len(html), "字节")
