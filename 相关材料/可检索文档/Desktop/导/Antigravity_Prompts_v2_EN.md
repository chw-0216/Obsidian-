# Antigravity Image Prompts — v2
## Tuned for Gemini Pro-class image generation (high reasoning)

**What changed from v1 and why** — see the notes at the end.

---

# THE SIX RULES THIS VERSION FOLLOWS

1. **Composition first.** Framing and format go at the top, not the end.
2. **Positive description only.** Never "no gradients" — instead "flat areas of
   solid ink". Negative wording is largely ignored by these models.
3. **"Keep unchanged" sentences are mandatory** on any pair or edit.
4. **Natural prose, not keyword stacks.** Write sentences; the model is a
   reasoner, not a tag matcher.
5. **Reference images get named roles** — "use image 1 for X, image 2 for Y".
6. **Repeat identity details in text** even when a reference image carries them.

---

# MASTER PROMPT — paste this first

```
You are a screen-print separation designer working in a woodcut and
paper-cut idiom. Before generating anything, open and study these reference
images. Each one has a specific job.

REFERENCE FILES AND THEIR ROLES

Use for overall design language and composition feel:
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_飞鸟木刻语言_新标修订_v21\00_飞鸟_主视觉.png
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_飞鸟木刻语言_新标修订_v21\00_飞鸟_设计语言总览.png

Use as the exact style target for how a two-frame pair is built:
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_飞鸟木刻语言_新标修订_v21\03_动态\动画帧_A.png
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_飞鸟木刻语言_新标修订_v21\03_动态\动画帧_B.png
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_飞鸟两帧_新增孔版_v20\00_新增鸟版_视觉总览.png

Use as source material for the workstation interior:
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_共印与栗影_视觉提案_v12\assets\取材_工作站院落.jpg
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_共印与栗影_视觉提案_v12\assets\取材_共同印制现场.jpg

Place these two logo files into the layout exactly as supplied. Their job is
to appear unaltered — same letterforms, same arch curvature, same
proportions. Do not redraw, restyle or re-letter them:
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_飞鸟木刻语言_新标修订_v21\04_原标与参考\工作站新标_统一墨色.png
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_飞鸟木刻语言_新标修订_v21\04_原标与参考\悲鸿红标_统一墨色.png

Use as the approved visual tone — the level of simplification, the courage
of the negative space, the density of the cut marks:
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_飞鸟木刻语言_新标修订_v21\04_原标与参考\用户风格参考_卷曲留白.png
C:\Users\wardc\Documents\Codex\2026-09-30\new-chat-6\outputs\悲鸿YOUNG_飞鸟木刻语言_新标修订_v21\04_原标与参考\用户风格参考_群马.png


THE PROJECT

Theme: JINGLIN | CO-PRINTING A VILLAGE
Place: a rural art-education workstation in Dongtai Village, Bohaizhen,
Huairou District, Beijing. The building has grey brick walls, old timber
doors with worn paint, lattice windows, and long wooden tables.

Every image is a hand-pulled screen print on warm paper. The sheet is a
physical object: it carries paper fibre, a faint deckle at the edge, and
the slight colour misregistration that comes from registering layers by eye.

THE INKS

The palette is exactly three printing inks, plus the paper itself:
- Warm paper white #F2EDE3 — this is the paper. It is never printed.
- Deep forest green #1F4A3C — carries the structure and the large Chinese type.
- Vermilion red #D93A22 — carries the leaf masses and one bold accent block.

Any area that is not green or red is bare paper showing through. There is no
fourth colour, no tint, no wash, no tonal blend.

THE PRINT LANGUAGE

Forms are cut, not drawn. Each shape is a flat area of solid ink with a hard
edge. Texture comes from coarse halftone dots, large enough that you can
count them individually. Where the two inks overlap, one sits slightly off
register from the other, the way a hand-pulled two-colour print does.

The tonal range is high: solid ink or bare paper, with the dot screen
providing the only intermediate step. There is no soft shadow, no modelled
volume, no light source within the picture.

The cuts are confident. Where a line is too fine to survive the screen it is
removed entirely, leaving a gap of bare paper instead.


TECHNICAL OUTPUT SPEC

A4 portrait, 210 by 297 millimetres, at 300 dpi.
Finished image area about 180 by 240 millimetres, with generous margins.
Registration crosses at the four corners and a 100 mm test line at the foot.
One image per plate, output separately.


WORK ORDER

Generate in this sequence and show me plate 01 before continuing:
  01  Jinglin scene, deep green      A4 portrait, halftone
  02  Jinglin scene, vermilion       A4 portrait, flat masses
  03  Bird, two frames               A4 landscape, pure black
  04  Horse, two frames              A4 landscape, pure black
  05  Squirrel and chestnut, two frames  A4 landscape, pure black

Whenever a plate is a pair of frames, remember that the two frames must be
able to sit one over the other and register exactly. The drawing that does
not move is locked; only the named part changes.
```

---

# PER-PLATE PROMPTS

## 01 — Jinglin scene, deep green

```
An A4 portrait sheet, finished image area about 180 by 240 millimetres,
centred with generous margins.

The picture shows the inside of a rural art-education workstation, seen
straight on. On the left an old timber door stands open. On the right a
lattice window. Across the lower third runs the edge of a long wooden table.
On the table rest a stretched silk-screen frame and a rubber squeegee.
Above, a taut line carries four or five finished prints, clipped and hanging.

The doorway on the left is left as bare paper — a clean vertical rectangle
of empty sheet, roughly one third of the image width, running from the table
edge to the top margin. Nothing is printed there.

Everything is cut as flat shapes in deep forest green #1F4A3C. The brickwork
behind, the grain of the tabletop and the mesh of the screen are each
rendered as coarse halftone dots, large and countable, never as smooth
gradient. The architecture reads as bold printed silhouette: door frame,
lattice grid, wall courses, table edge.

The sheet is warm paper white #F2EDE3 and its fibre shows through in every
unprinted area. Registration crosses sit at the four corners, a 100 mm test
line at the foot.

This is one separation from a two-colour hand-pulled screen print. It is a
printed sheet, flat and matt, with no light source, no cast shadow and no
modelled volume.
```

## 02 — Jinglin scene, vermilion

```
An A4 portrait sheet matching plate 01 exactly in size, margins and
registration, so the two can be printed one over the other.

This sheet carries only vermilion red #D93A22 on warm paper white. Every
area left unprinted here is bare paper.

The picture shows branches and leaves entering through the open doorway and
through the lattice window, then reaching across toward the table edge.
The foliage is cut as a handful of large flat masses — perhaps five or six
shapes in total — with the leaf edges reduced to simple angular cuts. One
bold rectangular block of solid red sits in the lower right as an accent.

The red layer sits a few millimetres off perfect register from where plate 01
would place it, the way a second colour lands when it is pulled by hand.

The sheet is warm paper white, its fibre visible throughout. Registration
crosses at the four corners, a 100 mm test line at the foot.

This is a flat printed sheet in a single ink: hard-edged areas of solid
colour, no outline, no tonal blend, no shading.
```

## 03 — Bird, two frames

```
An A4 landscape sheet, 297 by 210 millimetres, holding two square-ish panels
side by side. Each panel is 100 by 120 millimetres, and they are separated by
a clear gutter of bare paper. Registration crosses sit between and around
them, with a 100 mm test line at the foot.

This sheet is printed in a single ink: pure black on warm paper white.

Panel one, on the left: a bird in full silhouette, its wings raised to the
highest point of the beat. The body tilts up and to the right, angled as
though it has just launched out of an open doorway. The bird is built from
flat black masses — a solid body, a curled negative-space spiral cut into the
flank, the tail reduced to three slashed feathers, a round eye hole rather
than a drawn eye, the head and beak cut as one clean profile.

Panel two, on the right: the same bird, with its wings brought down to the
lowest point of the beat, and the whole body shifted a little to the right
and a little higher, as though it has now cleared the doorway.

Keep the head, the eye, the beak, the body mass, the curled spiral on the
flank and the root of the tail exactly as they are in panel one. Change only
the angle of the wings and the position of the whole bird within its panel.

Both panels are flat areas of solid black with hard cut edges. The finest
line anywhere on the sheet is about one millimetre, and the eye hole is about
two millimetres across. Everything else is bare paper.

This is a film positive for a silk screen: pure black and pure paper, printed
as a flat matt sheet.
```

## 04 — Horse, two frames ★

```
An A4 landscape sheet, 297 by 210 millimetres, holding two square-ish panels
side by side. Each panel is 100 by 120 millimetres, separated by a clear
gutter of bare paper. Registration crosses sit between and around them, with
a 100 mm test line at the foot.

This sheet is printed in a single ink: pure black on warm paper white.

Panel one, on the left: a horse at full gallop, in complete silhouette. All
four legs are gathered up beneath a compressed body, the head is low and
thrust forward, and the mane and tail stream back along the line of travel.
The horse is built from flat black masses — a solid barrel, a strong neck, a
tapered head, the legs cut as clearly separated blades with visible gaps of
bare paper between them, the tail reduced to three or four swept strokes.

Panel two, on the right: the same horse with all four legs extended — the
front legs reaching out ahead, the hind legs stretched back behind, the body
elongated along its axis, the mane and tail flying. The whole animal sits a
little further right in its panel than in panel one.

Keep the head, the neck, the barrel of the body, the chest, the croup and the
root of the tail exactly as they are in panel one. Change only the extension
of the four legs and the stretch of the body between them.

Both panels are flat areas of solid black with hard cut edges. Interior
description is carried by negative-space cuts, not by tone: two or three
clean lines describe the shoulder and the flank, and no line is thinner than
one millimetre. There is no interior grey.

This is a film positive for a silk screen: pure black and pure paper, printed
as a flat matt sheet.
```

## 05 — Squirrel and chestnut, two frames

```
An A4 landscape sheet, 297 by 210 millimetres, holding two square-ish panels
side by side. Each panel is 100 by 120 millimetres, separated by a clear
gutter of bare paper. Registration crosses between and around them, a 100 mm
test line at the foot.

Single ink: pure black on warm paper white.

Panel one, on the left: a squirrel sitting upright on a branch, its tail
curled high and forward over its back, both forepaws cradling a spiky
chestnut burr. The animal is a solid black mass with a clear profile — a
rounded head, one small ear, a hunched back, and a bushy tail cut as a single
curved blade shape.

Panel two, on the right: the same squirrel leaning forward and down along the
branch, its tail flicked straight out behind it, one forepaw reaching down
toward a fallen chestnut on the branch below.

Keep the head, the ear, the back and the haunch exactly as they are in panel
one. Change only the posture of the body and the direction of the tail.

The chestnut burr is reduced to a small oval with five or six bold spikes.
Negative-space gaps are left around the paws so the limbs read separately
from the body. The finest line on the sheet is about one millimetre.

This is a film positive for a silk screen: pure black and pure paper, flat
and matt.
```

---

# CORRECTION PROMPT — when a result misses

```
Keep the overall composition and the framing. Rebuild the rendering with
these changes:

Push the image further toward a woodcut print. Where there is currently fine
detail, replace it with a single flat mass. Where a line is thinner than one
millimetre, remove it and leave bare paper in its place.

Increase the empty paper. The finished sheet should read as roughly sixty per
cent blank.

Use exactly three inks and nothing else: warm paper white #F2EDE3 as the
paper, deep forest green #1F4A3C, and vermilion red #D93A22.

Make the halftone dots larger and more visible, so they read as a coarse
printed screen rather than a smooth photographic tone.

Flatten the light. The sheet should look like ink pressed onto paper under
even light, with no shadow inside the picture and no sense of a light source.
```

---

# TWO HARD CONSTRAINTS TO STATE

```
1. The two logo files must appear in the layout exactly as supplied — same
   letterforms, same arch curvature, same proportions, unaltered.

2. These images are composition and style studies. The production artwork
   will be rebuilt from my own site photography, so keep the scene elements
   simplified enough that they can be substituted later.
```

---

# WHY THIS VERSION IS DIFFERENT FROM v1

| v1 wrote | v2 writes | Reason |
|----------|-----------|--------|
| `no gradients, no shading` | "flat areas of solid ink with hard edges… bare paper showing through" | These models respond to positive scene description; semantic negatives outperform literal ones |
| `Head, body and tail are identical` | "**Keep** the head, the eye, the beak, the body mass… exactly as they are. **Change only** the angle of the wings" | The mandatory Keep/Change pair is what prevents the model redrawing both frames as different animals |
| Format spec at the bottom | "An A4 portrait sheet…" as the **first line** | Framing stated early is followed more reliably |
| Keyword list: `silkscreen print, risograph, halftone dots, limited palette…` | Full sentences describing a physical printed sheet | Pro-class models are reasoners; prose carries intent that tags do not |
| `No extra text` | (omitted entirely — no text is described, so none appears) | Describing the absence invites the model to consider text |
| `Do not redraw the logos` | "Place these two files into the layout exactly as supplied… same letterforms, same arch curvature" | Positive instruction with role assignment |
| Reference images listed flat | Each file given an explicit **job** | Multi-reference prompts need assigned roles |
