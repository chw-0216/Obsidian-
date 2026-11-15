# Bird Flight Loop — Veo First/Last-Frame Prompts (EN)
## Paste-ready

---

# SETUP

Veo 3.1 "specific frame generation": supply a **first frame** and a **last frame**.
The model interpolates the 8 seconds between them.

**Your two frames must match on:**
- the same bird — head, eye, beak, body mass, tail root identical
- the same scale and the same position grid
- only the wing angle differs
- the same 16:9 landscape canvas, same pixel dimensions
- the same warm paper ground and the same paper texture

If the two frames disagree on scale or position, the bird will drift across the
shot instead of beating its wings.

---

# PROMPT 1 — A → B (downstroke)

First frame: bird form A (wings up)
Last frame: bird form B (wings down)

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

# PROMPT 2 — A → A (seamless loop) ★ recommended

First frame: bird form A
Last frame: **the same bird form A**

```
A flat printed bird silhouette on warm paper, sweeping through one complete
wing-beat and returning to where it began.

The shot is locked off. We look straight on at a single sheet of warm paper
that fills the frame edge to edge. Nothing in the frame moves except the bird.
The camera holds perfectly still — the framing, the paper and the light on the
paper are identical in every frame.

The bird is a solid black silhouette cut in a woodcut idiom, with hard edges
and a coarse printed texture. It begins with its wings raised to the highest
point of the beat. Across the eight seconds it drives them down through the
full stroke, then lifts them all the way back up, so that the last frame is
identical to the first. The head, the eye, the beak, the body mass, the curled
spiral on the flank and the root of the tail hold their exact shape
throughout; only the wings travel.

The black stays pure, flat and matt. The paper stays warm and still. The
printed dot texture does not shimmer, sharpen or change.

This is a printed image coming to life, not a real bird.

The soundtrack is silent.
```

**Why this one:** the first and last frames are identical, so the eight seconds
loop forever with no visible seam. This is the version to put on the
workstation screen.

---

# PROMPT 3 — B → A (upstroke)

First frame: bird form B (wings down)
Last frame: bird form A (wings up)

```
A flat printed bird silhouette on warm paper, lifting through one wing-beat.

The shot is locked off. We look straight on at a single sheet of warm paper
that fills the frame edge to edge. Nothing in the frame moves except the bird.
The camera holds perfectly still — the framing, the paper and the light on the
paper are identical from the first frame to the last.

The bird is a solid black silhouette cut in a woodcut idiom, with hard edges
and a coarse printed texture. At the start of the shot its wings rest at the
lowest point of the beat. Across the eight seconds it lifts them up through
the full return stroke, the wing tips travelling through a wide arc, until
they reach their highest point and the body has settled slightly lower in the
frame. The head, the eye, the beak, the body mass and the root of the tail
hold their exact shape throughout; only the wings travel.

The black stays pure, flat and matt. The paper stays warm and still. The
printed dot texture does not shimmer, sharpen or change.

The soundtrack is silent.
```

Generate this one alongside Prompt 1, then butt-join the two clips —
A→B followed by B→A — for a clean 16-second continuous flap.

---

# RECOMMENDED SETTINGS

| Setting | Value | Why |
|---------|-------|-----|
| Aspect ratio | **16:9** | matches your A4 landscape separation |
| Resolution | 1080p minimum, **4K** if it goes on the workstation screen | |
| Duration | 8 s | Veo's fixed length |
| Audio | **silent** | add your own sound later |
| First frame | bird form A | |
| Last frame | bird form B, or A for the loop version | |

---

# CORRECTION PROMPTS

**Bird deforming:**
```
The bird's shape is drifting between frames. Hold the head, eye, beak, body
outline and tail exactly as they are in the first frame. Only the wings move.
The bird's overall size and its position in the frame stay constant.
```

**Paper or background moving:**
```
The paper is a fixed printed sheet. It does not move, breathe, zoom or shift.
The framing and the paper texture are identical in every frame.
```

**Camera movement appearing:**
```
Remove all camera movement. The camera is locked on a tripod, pointing
straight at a flat sheet of paper. There is no pan, tilt, zoom, dolly,
parallax or handheld drift.
```

**Turning photographic:**
```
Keep the bird as a flat printed silhouette. Its edges are cut, not feathered.
It shows no photographic detail, no iridescence, no realistic light and no
cast shadow. The image remains a two-colour screen print on paper throughout.
```

**Lettering appearing:**
```
The sheet carries no lettering. The only marks on the paper are the bird and
the paper's own fibre.
```

---

# HORSE VARIANT

Swap `bird` for `galloping horse` and replace the action paragraph with:

```
At the start of the shot the horse's legs are gathered beneath a compressed
body. Across the eight seconds it drives forward into full extension, the
front legs reaching out and the hind legs stretching back, the body
elongating along its axis, until the final frame shows the horse fully
extended. The head, neck, barrel, chest, croup and root of the tail hold
their exact shape throughout; only the legs extend and the body stretches.
```

Every other paragraph stays word for word.

---

# ON-SITE USE

| Use | How |
|-----|-----|
| Screen loop | Prompt 2's 8-second clip, looping on the workstation display |
| Paired with the print demo | visitor flips the physical two-frame card while the screen plays the same motion |
| Talk track | "Both frames show the same bird in two positions. Flip them quickly and you see the wing-beat — the earliest form of animation." |
