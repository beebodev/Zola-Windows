# P3PRE Audit 02 — GLB Capability Map

Read-only parse of `C:\Users\test\Dev\zola-assets\zola.glb`. Script: `C:\Users\test\Dev\zola-spikes\p3pre-helix\parse_glb.py`. Interpreter: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe` (no packages added). SHA-256 matched in Phase 1.

## 1. Inventory against K3

| K3 claim | Measured | Label |
|---|---|---|
| 33,972,240 bytes | file length 33,972,240; GLB `length` field 33,972,240 | [MATCH] |
| generator Khronos glTF Blender I/O v5.1.20 | `asset.generator` is that string | [MATCH] |
| one scene, one node, one mesh, one primitive | `scenes` 1, `nodes` 1, `meshes` 1, `primitives` 1 | [MATCH] |
| node translation `[-1.752, 0, 0]` | exact `[-1.752037525177002, 0, 0]` | [MATCH] (K3 rounded) |
| 90,489 vertices, 330,753 indices | POSITION accessor `count` 90489; indices accessor `count` 330753, componentType 5125 (UNSIGNED_INT) | [MATCH] |
| no skins, bones, animations, cameras | those arrays are absent | [MATCH] |
| one material, double-sided, opaque, emissiveFactor [1,1,1] | `doubleSided: true`, `emissiveFactor: [1,1,1]`. `alphaMode` is omitted, which the glTF 2.0 spec defines as `OPAQUE` | [MATCH] |
| four 2048×2048 JPEGs | four images, each JPEG SOF 2048×2048 | [MATCH] |
| 15 morph targets, POSITION + NORMAL, names only in `extras.targetNames` | 15 targets, each keys `POSITION` and `NORMAL` only. Names only under `meshes[0].extras.targetNames`. `meshes[0].weights` is 15 zeros | [MATCH] |

`P3PRE-AUD-07` [MATCH]. K3's numbers hold. The node is not at the origin.

JSON chunk 10,536 bytes. BIN chunk 33,961,676 bytes. 34 accessors, 53 buffer views, 1 buffer, 1 sampler.

`materials[0]` has no `alphaMode`, no `baseColorFactor`, no `metallicFactor`, no `roughnessFactor`. glTF defaults apply: opaque, base color factor `[1,1,1,1]`, metallic 1, roughness 1. Sampler 0: `magFilter` 9729 (`LINEAR`), `minFilter` 9987 (`LINEAR_MIPMAP_LINEAR`).

Texture assignment:

| glTF image | bufferView | BIN offset | bytes | Role |
|---|---|---|---|---|
| `Image_3` | 4 | 4,218,660 | 76,676 | emissive (`textures[0]`) |
| `Image_2` | 5 | 4,295,336 | 3,592,637 | normal (`textures[1]`) |
| `Image_0` | 6 | 7,887,976 | 4,134,247 | base color (`textures[2]`) |
| `Image_1` | 7 | 12,022,224 | 1,490,005 | metallic-roughness (`textures[3]`) |

`meshes[0]` (accessor arrays omitted; target accessors are indices 4–33):

```json
{
  "name": "Mesh_0.001",
  "extras": { "targetNames": [
    "Blink left", "Blink right", "Blink both", "Squint Eyes",
    "Wide / alert Eyes", "Brow raise", "Brow furrow / concern",
    "Nostril flare", "Jaw open", "Open AH", "Mid-open EH/UH",
    "Closed M/B/P", "Round OO/W", "Wide EE/ smile-adjacent",
    "Teeth showing F/V"
  ]},
  "weights": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  "primitives": [{
    "attributes": { "POSITION": 0, "NORMAL": 1, "TEXCOORD_0": 2 },
    "indices": 3,
    "material": 0,
    "targets": [ { "POSITION": 4, "NORMAL": 5 }, "... through ...", { "POSITION": 32, "NORMAL": 33 } ]
  }]
}
```

`nodes[0]`:

```json
{ "mesh": 0, "name": "Mesh_0.001", "translation": [-1.752037525177002, 0, 0] }
```

`samplers`:

```json
[{ "magFilter": 9729, "minFilter": 9987 }]
```

Order of `targetNames` is the morph index order. Names are not on the target objects themselves.

## 2. Bounds and camera (spike must confirm facing)

POSITION accessor min/max (mesh-local, before the node translation):

| Axis | min | max | size | local center |
|---|---|---|---|---|
| X | -0.6735854744911194 | 0.6716906428337097 | 1.345276117 | -0.000947416 |
| Y | -0.950559675693512 | 0.9484301209449768 | 1.898989797 | -0.001064777 |
| Z | -0.5125954151153564 | 0.5114091634750366 | 1.024004579 | -0.000593126 |

World center after translation `[-1.752037525177002, 0, 0]`:

**(-1.752984941, -0.001064777, -0.000593126)**

The visible center is about 1.75 units left of the world origin. A camera aimed at the origin misses the bust.

Proposed frame, for the whole mesh (there is no separate head mesh, so "head and upper torso" is this AABB):

- Look-at: that world center. Up: +Y.
- Vertical FOV: 35°.
- Distance along +Z from the center: ` (1.898989797 / 2) * 1.12 / tan(17.5°) ` = **3.372**. The 1.12 is a 12% margin so the bust is not clipped. `tan(17.5°) = 0.315299`.
- Eye: `(-1.752984941, -0.001064777, 3.3714)`.
- Near 0.05, far 50.

Which way the face points is not in the file (no camera, no node rotation). If the face looks toward -Z, this camera sees the back of the head. **Spike confirmation required.**

## 3. Morph target → document behavior

One mesh. Motion is morph weights plus the node transform. Nothing else exists.

| Doc behavior | Target that can express it | Label |
|---|---|---|
| §5 BlinkController | index 0 `Blink left`, 1 `Blink right`, 2 `Blink both` | [MATCH] `P3PRE-AUD-08` |
| Blink suppression (`blinkSuppression` > 0.8 stops the timer) | No target. Suppression is "do not drive blink weights". `Wide / alert Eyes` (4) can hold the lids open if a blink target is also at 0. | [GAP] `P3PRE-AUD-09` |
| `browTension` | `Brow furrow / concern` (6). `Brow raise` (5) is the opposite direction, not a tension scalar. | [MATCH] as furrow only |
| `eyelidOpenness` | `Wide / alert Eyes` (4) opens; `Squint Eyes` (3) and the blink targets close. No single 0–1 openness target. | [MATCH] by combining those |
| `mouthCurve` | `Wide EE/ smile-adjacent` (13) is the only smile-direction target. No frown / negative-curve target. | [GAP] `P3PRE-AUD-10` for a signed curve |
| `eyeSoftness` | none | [GAP] `P3PRE-AUD-11` |
| `projectionStability` | none. No pixel-block geometry. | [GAP] `P3PRE-AUD-12` |
| IDLE pose (low brow, lids 0.75, slight smile) | weights near 0 are the neutral face. Slight `Wide EE/ smile-adjacent`. | [MATCH] neutral; smile is approximate |
| LISTENING (lids 0.90) | `Wide / alert Eyes` | [MATCH] approximate |
| THINKING (brow 0.35, mouth -0.05) | `Brow furrow / concern`. Negative mouth curve has no target. | [GAP] on the mouth term |
| SPEAKING | `Jaw open` plus a viseme below | [MATCH] |
| ALERT (brow 0.55, lids 1.0, mouth -0.12) | `Wide / alert Eyes` and `Brow furrow / concern` or `Brow raise`. Negative mouth has no target. | [GAP] on the mouth term |
| §10 mouth open | `Jaw open` (8) | [MATCH] |
| §10 visemes | `Open AH` (9), `Mid-open EH/UH` (10), `Closed M/B/P` (11), `Round OO/W` (12), `Wide EE/ smile-adjacent` (13), `Teeth showing F/V` (14) | [MATCH] for this set. No signal drives them (K5, `S17`). |
| §5 micro-saccade | none. No separate eye geometry to translate. | [GAP] `P3PRE-AUD-13` |
| §12 hair energy / per-strand shimmer | none. No hair mesh, no strand list. | [GAP] `P3PRE-AUD-14` |
| §13 pixel projection and hologram | none as geometry. Edge pixels, if present, are texels on this one primitive. | [GAP] `P3PRE-AUD-15` |
| §3 breathing (chest glow only) | no chest sub-mesh. See §4. | [GAP] `P3PRE-AUD-16` |
| §3 attention lean | node rotation. The node has a translation and no rotation. A whole-node Y rotation is the available stand-in. | [MATCH] as a transform, not a morph |

`Nostril flare` (7) has no doc behavior.

## 4. Emissive map

One material, one emissive texture (`Image_3`, 2048×2048 JPEG, 76,676 bytes). Full-pixel scan of that JPEG (`System.Drawing.Bitmap.LockBits`, Format24bppRgb):

| Measure | Value |
|---|---|
| Peak average channel | 31, at pixel (84, 1603), RGB (29, 30, 34) |
| Pixels with average ≥ 1 | 14,580 of 4,194,304 (0.35%) |
| Pixels with average ≥ 8 | 867 |
| Pixels with average ≥ 20 | 57 |
| Bounding box of average ≥ 8 | (19, 164) to (2047, 2043) — almost the whole sheet |

Those ≥8 pixels are scattered. The busiest 128×128 cells are (4,5), (14,1), (10,13), (1,13), (12,8), (5,16), (4,15). That is not one island for eyes, one for a centre line, one for a chest diamond, one for shoulder blocks, or one for hair.

`emissiveFactor` is `[1,1,1]`, so the GPU adds this dim texture as-is. Eyes, centre line, chest diamond, shoulder pixels, and hair cannot be separated by material (there is only `Material_0`) or by a contiguous emissive UV island. A mask derived from this texture would be a speckled, low-value image, not a chest-only region.

Whether the bright gold in the reference images comes from the base-color JPEG instead is measured in Phase 4 Q11. This section does not change K7.

[RISK] `P3PRE-AUD-16`. §3 chest-only breathing and §6 per-layer glow cannot address separate regions of this asset. One emissive intensity moves every emissive texel together, and those texels are already near black.

## 5. Asset storage

33,972,240 bytes is under GitHub's 50 MB warning and under the 100 MB hard limit. Plain git can store it. This repo has no `.gitattributes` and no Git LFS patterns (search for `.gitattributes` returned none). The audit does not copy the GLB in. [MATCH] `P3PRE-AUD-17` as a fact: both storage choices are inside GitHub's file limit; LFS is not set up.

## Findings in this document

| ID | Severity | Label | Summary |
|---|---|---|---|
| P3PRE-AUD-07 | — | [MATCH] | K3 inventory confirmed, including 15 named morph targets and the off-origin node. |
| P3PRE-AUD-08 | — | [MATCH] | Blink, jaw, and the six viseme names exist as morph targets. |
| P3PRE-AUD-09 | LOW | [GAP] | Blink suppression is a timer rule, not a morph target. |
| P3PRE-AUD-10 | MEDIUM | [GAP] | No negative mouth-curve / frown target. `Wide EE/ smile-adjacent` only bends one way. |
| P3PRE-AUD-11 | MEDIUM | [GAP] | `eyeSoftness` has no target. |
| P3PRE-AUD-12 | MEDIUM | [GAP] | `projectionStability` has no geometry. |
| P3PRE-AUD-13 | HIGH | [GAP] | Micro-saccade cannot target eyes. One mesh, no eye node. |
| P3PRE-AUD-14 | HIGH | [GAP] | Hair shimmer cannot target strands. No hair mesh. |
| P3PRE-AUD-15 | HIGH | [GAP] | Pixel-projection and hologram layers have no separate geometry. |
| P3PRE-AUD-16 | HIGH | [RISK] | One material and a near-black, scattered emissive JPEG. Chest-only glow is not separable. |
| P3PRE-AUD-17 | — | [MATCH] | 34.0 MB file is under GitHub's 100 MB limit. The repo does not use LFS. |
