# 小鸟连续飞行动画 · Veo 首尾帧提示词

用 Gemini / Veo 3.1 的 **首帧 + 末帧** 功能，把两张版画鸟图变成连贯飞行动画。

---

# 一、先确认能力（官方文档）

| 能力 | 说明 |
|------|------|
| **指定首帧和末帧** | ✅ Veo 3.1 原生支持（specific frame generation） |
| 时长 | 8 秒 |
| 分辨率 | 720p / 1080p / **4K** |
| 画幅 | **16:9**（横）/ 9:16（竖） |
| 音频 | 原生生成 |
| **视频延长** | ✅ 可基于已生成视频继续延长 |
| 参考图 | 最多 3 张用于引导内容 |

来源：[Gemini API · Veo 官方文档](https://ai.google.dev/gemini-api/docs/veo)

---

# 二、准备两张图（这一步最关键）

Veo 是在**首末帧之间插值**。两张图越一致，动画越顺；不一致就会"变形"。

| 要求 | 说明 |
|------|------|
| **同一只鸟** | 头、眼、喙、身体、尾根**必须完全一致** |
| **同一比例** | 鸟的大小不能变 |
| **同一位置网格** | 鸟在画面里的基准位置要一致 |
| **只差翅膀角度** | A 帧翅膀抬到最高 / B 帧翅膀压到最低 |
| **同一画幅** | 两张都要 **16:9 横版**，尺寸一致 |
| **同一底色** | 都是暖纸白，纸纹一致 |

⚠️ **如果两帧的鸟大小或位置差太多，Veo 会让它"飘移"而不是"扇翅"。**

---

# 三、主提示词（首帧 = A，末帧 = B）

```
A flat printed bird silhouette on warm paper, sweeping through one wing-beat.

The shot is locked off. We look straight on at a single sheet of warm paper
that fills the frame edge to edge. Nothing in the frame moves except the bird.
The camera holds perfectly still — the framing, the paper and the light on the
paper are identical from the first frame to the last.

The bird is a solid black silhouette cut in a woodcut idiom, with hard edges
and a coarse printed texture. At the start of the shot its wings are raised to
the highest point of the beat. Across the eight seconds it drives its wings
down through the full stroke, the wing tips travelling through a wide arc,
until the wings reach their lowest point and the whole body has settled a
little higher in the frame. The head, the eye, the beak, the body mass, the
curled spiral on the flank and the root of the tail hold their exact shape
throughout; only the wings travel and only the body position shifts.

The black stays pure, flat and matt. The paper stays warm and still. The
printed dot texture does not shimmer, sharpen or change.
This is a printed image coming to life, not a real bird.

The soundtrack is silent.
```

---

# 四、三种用法（选一个）

## 方案 A ⭐ **推荐 · 无缝循环**

**做法**：首帧 = A，末帧 = A（**同一张图**）

提示词把上面第三段改成：

```
At the start of the shot its wings are raised to the highest point of the
beat. Across the eight seconds it drives its wings down through the full
stroke and then returns them all the way back up, so that the final frame
is identical to the first frame. The head, the eye, the beak, the body mass
and the root of the tail hold their exact shape throughout.
```

**效果**：8 秒一个完整振翅周期，**首尾帧相同 → 可以无限循环播放，看不出接缝**。

---

## 方案 B · 半周期 + 倒放（用你现有的两张图）

**做法**：首帧 = A，末帧 = B → 得到 8 秒"下挥"→ 剪辑时**正放 + 倒放拼接** = 连续扇翅

**剪辑**：
```
[视频正放] + [视频倒放] = 16 秒连续振翅，且首尾无缝
```

**或者**生成两段：A→B 和 B→A，然后拼接。

---

## 方案 C · 延长法（做长视频）

**做法**：先用 A→B 生成 8 秒，再用 **视频延长** 功能接 B→A

官方文档支持基于已生成视频继续延长，可以做成 16 秒、24 秒的连续飞行。

---

# 五、参数设置建议

| 参数 | 建议值 | 原因 |
|------|--------|------|
| 画幅 | **16:9** | 与你的 A4 横版分版一致 |
| 分辨率 | 1080p 起（要投屏就 4K） | 现场投工作站大屏用 4K |
| 时长 | 8 秒 | Veo 固定 8 秒 |
| 音频 | **静音** | 现场要配音或配乐，先出无声素材 |
| 首帧 | 鸟形 A | |
| 末帧 | 鸟形 B（或 A，见方案A） | |

---

# 六、修正提示词

## 如果鸟变形了
```
The bird's shape is drifting between the frames. Hold the head, eye, beak,
body outline and tail exactly as they are in the first frame. Only the wings
move. The bird's overall size and its position in the frame stay constant.
```

## 如果背景/纸面在动
```
The paper is a fixed printed sheet. It does not move, breathe, zoom or shift.
The framing and the paper texture are identical in every frame.
```

## 如果出现了相机运动
```
Remove all camera movement. The camera is locked on a tripod, pointing
straight at a flat sheet of paper. There is no pan, tilt, zoom, dolly,
parallax or handheld drift.
```

## 如果变写实了（出现真羽毛光影）
```
Keep the bird as a flat printed silhouette. Its edges are cut, not feathered.
It shows no photographic detail, no iridescence, no realistic light and no
cast shadow. The image remains a two-colour screen print on paper throughout.
```

## 如果出现文字
```
The sheet carries no lettering. The only marks on the paper are the bird and
the paper's own fibre.
```

---

# 七、现场用法（10/3 领导来）

| 用途 | 做法 |
|------|------|
| **投屏循环** | 方案 A 的 8 秒 GIF/MP4，工作站大屏无限循环 |
| **配合版画体验** | 观众翻动实体两帧纸片 → 大屏同步播放视频，形成"画在纸上、活在屏上"的对照 |
| **讲解词** | "这一块版印的是同一只鸟的两个姿态。把两幅画快速交替，就能看到拍翅——这就是动画最早的样子。" |

---

# 八、⚠️ 两个提醒

**1. 先出静音素材。** Veo 会原生生成音频（鸟叫、环境声），现场不需要——明确写 `The soundtrack is silent.`

**2. 首尾帧必须同尺寸同画幅。** 两张图都是 16:9、同样像素尺寸。如果一张是方图一张是横图，Veo 会裁切并让鸟跳位。

---

# 九、如果要做**马**的版本

把提示词里的 `bird` 换成 `galloping horse`，动作段改成：

```
At the start of the shot the horse's legs are gathered beneath a compressed
body. Across the eight seconds it drives forward into full extension, the
front legs reaching out and the hind legs stretching back, the body
elongating along its axis, until the final frame shows the horse fully
extended. The head, neck, barrel, chest, croup and root of the tail hold
their exact shape throughout; only the legs extend and the body stretches.
```

其余段落一字不改。
