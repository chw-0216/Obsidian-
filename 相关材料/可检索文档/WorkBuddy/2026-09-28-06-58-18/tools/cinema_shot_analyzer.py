#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cinema_shot_analyzer.py —— 运镜（相机运动）分析引擎  v2
=====================================================================
纯本地 · 只用 opencv + numpy · 不联网 · 不上传素材
分类学对齐 CameraBench（NeurIPS 2025 Spotlight, arXiv 2504.15376）

设计原则（对齐 CameraBench 的核心结论）
---------------------------------------------------------------------
CameraBench 实测：SfM 路线强于「几何原语」、弱于「语义原语」；
VLM 路线反之。本引擎走 **几何层**，只回答「机器能证明的」，
语义层（跟拍 / 环绕 / POV / 为什么动）显式标注为「需 VLM」——
不猜、不编。

用法：
    python cinema_shot_analyzer.py <video> [--out DIR] [--debug]

产出：
    shots.csv       逐镜：起止 / 时长 / 运动族 / 原语 / 视差 / 景别 / 各项速率
    summary.json    整片：镜头数 / ASL / 剪辑密度 / 分布
    keyframes/      每镜代表帧

判据（全部可复现）
---------------------------------------------------------------------
1) 镜头切分 —— HSV 直方图 Bhattacharyya 距离 + 灰度均差（双阈值 + 最小镜长）
2) 相机运动 —— Shi-Tomasi 角点 + LK 光流 → 每帧解 (tx,ty,scale,rot)，取**中位数**（抗噪）
3) 变焦 vs 前推 —— ★ 本引擎最关键的一条：
     变焦（intrinsic, 改焦距）→ 全画面等比缩放，**无视差**
     前推（extrinsic, 相机前移）→ 近物放大快于远物，**有视差**
   用「扣除全局平移后的视差残差比」区分。CameraBench 明确指出这是新手最常混的一对。
4) 景别 —— OpenCV Haar 人脸框高 / 画幅高 分档（离线，无需下载模型）
"""
import os, sys, io, json, math, csv, argparse

import cv2
import numpy as np

# ---------------------------------------------------------------- 参数
MOTION_DOWN_W = 320
MIN_SHOT_SEC = 0.35

# 镜头切分（阈值经 87s 实拍样片校准）
HIST_HARD = 0.34        # 直方图距离：单独成立即切
HIST_SOFT = 0.20        # 直方图距离：软阈值
GRAY_SOFT = 26.0        # 灰度均差：与软阈值合用

# 运动判据（三轴统一到「每秒画幅比例变化」后比较 —— 见 classify_motion）
T_MOVE = 0.030          # 任一轴每秒 ≥3% 才算「在动」（噪声底约 0.01~0.02）
DOM = 1.4               # 主导倍数：某轴超过其他轴 1.4 倍才算主导
T_CONSIST = 0.45        # 方向一致性：>= 有明确方向；< 0.30 视为手持
T_PARALLAX = 0.22       # 视差残差比：>= 有视差（真位移）；< 无视差（纯旋转/纯变焦）

# 景别分档（人脸框高 / 画幅高）
SCALE_BINS = [(0.50, "大特写"), (0.28, "特写"), (0.14, "近景"),
              (0.065, "中景"), (0.028, "全景")]

# CameraBench 六族 → 中文
FAMILY_CN = {
    "static": "静止", "translation": "平移", "rotation": "旋转",
    "intrinsic": "变焦", "circular": "环绕", "steadiness": "稳定度",
    "tracking": "跟拍", "unknown": "未判定",
}


def _log(*a):
    print(*a, flush=True)


def _gray_small(frame, w=MOTION_DOWN_W):
    h = max(8, int(frame.shape[0] * w / frame.shape[1]))
    return cv2.cvtColor(cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA),
                        cv2.COLOR_BGR2GRAY)


def _hist(frame):
    small = cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    h = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
    cv2.normalize(h, h)
    return h


# ================================================================ 1. 切分
def detect_shots(path, verbose=True):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError("打不开视频：%s" % path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    min_len = max(2, int(MIN_SHOT_SEC * fps))

    prev_h = prev_g = None
    cuts, idx = [0], 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        h = _hist(fr)
        g = cv2.cvtColor(cv2.resize(fr, (64, 36), interpolation=cv2.INTER_AREA),
                         cv2.COLOR_BGR2GRAY)
        if prev_h is not None:
            hd = cv2.compareHist(prev_h, h, cv2.HISTCMP_BHATTACHARYYA)
            gd = float(np.mean(cv2.absdiff(g, prev_g)))
            hit = (hd > HIST_HARD) or (hd > HIST_SOFT and gd > GRAY_SOFT)
            if hit and idx - cuts[-1] >= min_len:
                cuts.append(idx)
        prev_h, prev_g = h, g
        idx += 1
    cap.release()
    cuts.append(idx)
    if verbose:
        _log("[切分] fps=%.3f 帧=%d 镜头=%d" % (fps, idx, len(cuts) - 1))
    return fps, idx, cuts


# ================================================================ 2. 运动
def analyze_motion(path, i0, i1, fps, debug=False):
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, i0)
    ok, fr = cap.read()
    if not ok:
        cap.release()
        return None
    prev = _gray_small(fr)
    H, W = prev.shape
    diag = math.hypot(W, H)
    pts = cv2.goodFeaturesToTrack(prev, 400, 0.01, 10, blockSize=7)

    tx_l, ty_l, sc_l, rt_l, par_l, mag_l = [], [], [], [], [], []
    cur = i0
    while cur + 1 < i1:
        ok, fr = cap.read()
        if not ok:
            break
        cur += 1
        g = _gray_small(fr)
        if g.shape != prev.shape or pts is None or len(pts) < 8:
            prev = g
            pts = cv2.goodFeaturesToTrack(prev, 400, 0.01, 10, blockSize=7)
            continue
        nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, g, pts, None)
        if nxt is None:
            break
        good = st.ravel() == 1
        if good.sum() < 8:
            prev = g
            pts = cv2.goodFeaturesToTrack(prev, 400, 0.01, 10, blockSize=7)
            continue
        a = pts[good].reshape(-1, 2)
        b = nxt[good].reshape(-1, 2)
        flow = b - a
        t_med = np.median(flow, axis=0)
        # ★ 视差残差比：扣掉全局平移后还剩多少
        resid = flow - t_med
        par = float(np.median(np.hypot(resid[:, 0], resid[:, 1]))) / \
              (float(np.median(np.hypot(flow[:, 0], flow[:, 1]))) + 1e-6)
        mag = float(np.median(np.hypot(flow[:, 0], flow[:, 1]))) / diag
        M, _ = cv2.estimateAffinePartial2D(a, b, method=cv2.RANSAC,
                                           ransacReprojThreshold=2.0)
        if M is not None:
            sc = math.hypot(M[0][0], M[1][0]) - 1.0
            rt = math.degrees(math.atan2(M[1][0], M[0][0]))
            sc_l.append(sc)
            rt_l.append(rt)
        tx_l.append(float(t_med[0]) / W)     # float32 → float（否则 json 序列化失败）
        ty_l.append(float(t_med[1]) / H)
        par_l.append(par)
        mag_l.append(mag)
        prev = g
        pts = nxt[good].reshape(-1, 1, 2)
    cap.release()

    frames = max(1, cur - i0)
    if not mag_l:
        return None

    med = lambda x: float(np.median(x)) if x else 0.0
    trans_rate = med(mag_l)                       # 每帧，归一
    zoom_rate = med(sc_l) if sc_l else 0.0        # 每帧
    rot_rate = med(rt_l) if rt_l else 0.0         # 每帧，度
    parallax = med(par_l)
    consistency = (math.hypot(sum(tx_l), sum(ty_l)) /
                   (sum(abs(x) for x in tx_l) + sum(abs(y) for y in ty_l) + 1e-9))
    net_dx, net_dy = sum(tx_l), sum(ty_l)
    # ★ 净变焦用「求和」而不是「连乘」：连乘在长镜头上会指数溢出（且无物理意义）
    net_zoom = sum(sc_l) * 100 if sc_l else 0.0
    net_rot = sum(rt_l)

    if debug:
        _log("    [raw] trans=%.5f zoom=%.5f rot=%.4f par=%.3f cons=%.3f netdx=%.2f netzoom=%.1f%%"
             % (trans_rate, zoom_rate, rot_rate, parallax, consistency, net_dx, net_zoom))

    return {
        "frames": frames, "sec": round(frames / fps, 3), "fps": fps,
        "trans_rate": float(trans_rate), "zoom_rate": float(zoom_rate),
        "rot_rate": float(rot_rate),
        "parallax": round(parallax, 3), "consistency": round(consistency, 3),
        "net_dx": round(net_dx, 3), "net_dy": round(net_dy, 3),
        "net_zoom_pct": round(float(net_zoom), 1), "net_rot_deg": round(net_rot, 1),
        "trans_ps": round(trans_rate * fps, 4),
        "zoom_ps": round(zoom_rate * 100 * fps, 2),
        "rot_ps": round(abs(rot_rate) * fps, 2),
    }


def classify_motion(m):
    """
    几何层判定：CameraBench 六族 + 中文原语。
    ★ 关键：三轴先换算到**同一货币**——「每秒画幅比例变化」，再比大小，
      否则「对角线比例/秒」和「百分比/秒」不可比（这是 v1 判错的根因）。
    """
    if m is None:
        return "unknown", "未测出", 0.0, ""
    fps = m.get("fps", 25.0)
    t = m["trans_rate"] * fps                    # 平移：对角线 / 秒
    z = abs(m["zoom_rate"]) * fps                # 变焦：比例 / 秒
    r = abs(m["rot_rate"]) / 57.3 * fps          # 滚转：弧度 / 秒（≈ 比例 / 秒）
    par, cons = m["parallax"], m["consistency"]

    # ① 静止：三轴都在噪声底以下
    if max(t, z, r) < T_MOVE:
        return "static", "固定", 0.88, "三轴均低于噪声底（%.3f）" % T_MOVE
    # ② 变焦 / 前推（CameraBench 明确点名新手最常混的一对）
    if z >= T_MOVE and z >= DOM * max(t, r):
        if par >= T_PARALLAX:
            return ("translation", "前推/后拉（相机位移）", 0.74,
                    "视差 %.2f → 有视差，是位移不是变焦" % par)
        return ("intrinsic", "变焦推/拉（改焦距）", 0.76,
                "视差 %.2f → 全画面等比缩放" % par)
    # ③ 滚转
    if r >= T_MOVE and r >= DOM * max(t, z):
        return ("rotation",
                "滚转顺时针" if m["net_rot_deg"] > 0 else "滚转逆时针",
                min(0.9, 0.5 + r / 0.4), "")
    # ④ 平移族
    if t >= T_MOVE:
        horiz = abs(m["net_dx"]) >= abs(m["net_dy"])
        if cons < 0.30:
            return ("steadiness", "手持/抖动",
                    min(0.88, 0.5 + (0.30 - cons) * 2),
                    "方向一致性 %.2f，无主方向" % cons)
        if par >= T_PARALLAX:
            return ("translation",
                    ("横移/侧跟" if horiz else "升降/纵移") + "（有视差）",
                    min(0.9, 0.5 + cons / 2), "视差 %.2f" % par)
        return ("translation",
                ("左右摇" if horiz else "上下俯仰") + "（无视差）",
                min(0.9, 0.5 + cons / 2), "视差 %.2f，旋转式" % par)
    # ⑤ 有运动但都不显著
    return "unknown", "复合/微弱运动", 0.35, ""


# ================================================================ 3. 景别
_CASCADES = None


MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "models", "haarcascades")


def _cascades():
    """cv2 5.x 不再自带 Haar XML → 从本仓库 tools/models/haarcascades/ 读。"""
    global _CASCADES
    if _CASCADES is None:
        names = ("haarcascade_frontalface_default.xml",
                 "haarcascade_profileface.xml",
                 "haarcascade_fullbody.xml",
                 "haarcascade_upperbody.xml")
        out = []
        for n in names:
            for base in (MODEL_DIR, getattr(cv2.data, "haarcascades", "")):
                p = os.path.join(base, n) if base else ""
                if p and os.path.exists(p):
                    cc = cv2.CascadeClassifier(p)
                    if not cc.empty():
                        out.append(cc)
                    break
        _CASCADES = out
    return _CASCADES


def shot_scale(frame):
    """人脸框高 / 画幅高 → 景别。离线 Haar，无需下载模型。"""
    h, w = frame.shape[:2]
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    g = cv2.equalizeHist(g)
    best = 0.0
    for cc in _cascades():
        try:
            faces = cc.detectMultiScale(g, 1.15, 5, minSize=(int(w * 0.03), int(w * 0.03)))
        except Exception:
            continue
        for (x, y, fw, fh) in faces:
            best = max(best, fh / float(h))
    if best <= 0:
        return "无人物/空镜", 0.35, 0.0
    for thr, name in SCALE_BINS:
        if best >= thr:
            return name, 0.7, round(best, 3)
    return "远景", 0.55, round(best, 3)


# ================================================================ 主流程
def analyze(path, outdir=None, debug=False):
    path = os.path.abspath(path)
    stem = os.path.splitext(os.path.basename(path))[0]
    if outdir is None:
        outdir = os.path.join(os.path.dirname(path), "_cinema_" + stem)
    os.makedirs(outdir, exist_ok=True)
    kfdir = os.path.join(outdir, "keyframes")
    os.makedirs(kfdir, exist_ok=True)

    fps, total, cuts = detect_shots(path)
    cap = cv2.VideoCapture(path)
    rows = []
    for k in range(len(cuts) - 1):
        i0, i1 = cuts[k], cuts[k + 1]
        m = analyze_motion(path, i0, i1, fps, debug=debug)
        dur = (i1 - i0) / fps
        fam, prim, conf, note = classify_motion(m)
        cap.set(cv2.CAP_PROP_POS_FRAMES, (i0 + i1) // 2)
        ok, fr = cap.read()
        kf = ""
        scale, sconf, sratio = "未测", 0.0, 0.0
        if ok:
            safe = prim.replace("/", "-").replace("（", "(").replace("）", ")")
            kf = os.path.join(kfdir, "shot%03d_%s.jpg" % (k + 1, safe))
            cv2.imwrite(kf, fr, [cv2.IMWRITE_JPEG_QUALITY, 88])
            scale, sconf, sratio = shot_scale(fr)
        rows.append({
            "shot": k + 1,
            "start_sec": round(i0 / fps, 2), "end_sec": round(i1 / fps, 2),
            "dur_sec": round(dur, 2),
            "family": fam, "family_cn": FAMILY_CN.get(fam, fam),
            "primitive": prim, "conf": round(conf, 2), "note": note,
            "trans_per_sec": (m or {}).get("trans_ps", 0),
            "zoom_pct_per_sec": (m or {}).get("zoom_ps", 0),
            "rot_deg_per_sec": (m or {}).get("rot_ps", 0),
            "net_zoom_pct": (m or {}).get("net_zoom_pct", 0),
            "net_rot_deg": (m or {}).get("net_rot_deg", 0),
            "parallax": (m or {}).get("parallax", 0),
            "consistency": (m or {}).get("consistency", 0),
            "scale": scale, "face_ratio": sratio,
            "keyframe": kf,
        })
        _log("  #%02d %6.2f→%6.2fs (%5.2fs) %-11s %-22s %-9s par=%.2f cons=%.2f"
             % (k + 1, i0 / fps, i1 / fps, dur, FAMILY_CN.get(fam, fam), prim,
                scale, (m or {}).get("parallax", 0), (m or {}).get("consistency", 0)))
    cap.release()

    durs = [r["dur_sec"] for r in rows] or [0]
    fam_d, scale_d, prim_d = {}, {}, {}
    for r in rows:
        fam_d[r["family_cn"]] = fam_d.get(r["family_cn"], 0) + 1
        scale_d[r["scale"]] = scale_d.get(r["scale"], 0) + 1
        prim_d[r["primitive"]] = prim_d.get(r["primitive"], 0) + 1
    moving = sum(1 for r in rows if r["family"] not in ("static", "unknown"))
    summary = {
        "file": path, "fps": round(fps, 3), "total_frames": total,
        "duration_sec": round(total / fps, 2), "shots": len(rows),
        "asl_sec": round(sum(durs) / len(durs), 3),
        "cut_per_sec": round(len(rows) / (sum(durs) or 1), 3),
        "moving_ratio": round(moving / max(1, len(rows)), 3),
        "family_dist": fam_d, "primitive_dist": prim_d, "scale_dist": scale_d,
        "shortest_sec": round(min(durs), 2), "longest_sec": round(max(durs), 2),
    }
    with io.open(os.path.join(outdir, "shots.csv"), "w", encoding="utf-8-sig",
                 newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with io.open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "shots": rows}, f, ensure_ascii=False,
                  indent=2, default=float)

    _log("\n[汇总] 镜头 %d · ASL %.2fs · 密度 %.2f 切/秒 · 运动镜占比 %.0f%%"
         % (summary["shots"], summary["asl_sec"], summary["cut_per_sec"],
            summary["moving_ratio"] * 100))
    _log("[运动族] %s" % fam_d)
    _log("[原语] %s" % prim_d)
    _log("[景别] %s" % scale_d)
    _log("[输出] %s" % outdir)
    return summary, rows, outdir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", default=None)
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args()
    analyze(a.video, a.out, debug=a.debug)


if __name__ == "__main__":
    main()
