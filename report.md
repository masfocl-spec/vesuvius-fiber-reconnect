# Report: geometry/topology-aware reconnection of broken papyrus fibers

**Experiment.** One cube of the official Vesuvius Challenge
[fiber-skeletons dataset](https://scrollprize.org/data_datasets) (2025-07),
artificial breaks, an **ablation ladder** of reconnection methods on the same
breaks. No training, no GPU, no large downloads (~17 MB). Code:
`run_experiment.py` (see `reproduce.md`).

## Hypothesis

Reconnecting broken papyrus fibers by *nearest endpoints alone* is not
enough: using fiber **direction (tangent)** and **curvature** consistency,
plus a ban on crossing other fibers, should repair more real breaks and —
more importantly — produce **fewer false connections**, especially near
parallel/crossing fibers. (Motivated by topology-aware filament tracing such
as FPicker.)

Because the full method bundles several ingredients (tangent, curvature,
crossing penalty, Hungarian global assignment, one-to-one matching), the
experiment is set up as an **ablation study**: each ingredient is added in
isolation, on identical breaks, so the causal attribution is explicit.

## Data format (what we found)

* Dataset `fiber-skeletons` (2025-07), nnU-Net layout:
  `labelsTr/*.tif` (256³ or 512³ cubes, 0 = background, 1 = fiber),
  `nml/*.nml` — the original manual WEBKNOSSOS skeleton annotations
  (one NML `<thing>` tree = one traced fiber; nodes carry **global**
  x, y, z in voxels; scale 7.91 µm/voxel for scroll 1).
* Cube used: `s1_00497_01497_03997_256` (scroll 1, 256³).
  Mapping verified against the official converter
  (`ScrollPrize/villa/foundation/datasets/fibers-dataset`): tif is saved in
  (z, y, x) order, voxel = `mask[z − 497, y − 1497, x − 3997]`.
* Sanity check: **100 %** of NML nodes land exactly on mask voxels; 99.7 %
  of mask voxels lie within 3 voxels of some polyline. 89 trees → 96
  in-cube chains ≥ 10 voxels (median arc length 277 voxels).
  This NML uses `x=`, `y=`, `z=` attributes per node (not `position="x y z"`).

## Method

1. **Fibers** = NML trees, decomposed into chains, resampled to 1-voxel
   spacing, clipped to the cube.
2. **Artificial breaks**: interior arc segments of length U[8, 20] voxels cut
   perpendicular to the fiber (slab half-width 5 voxels, tube radius 4.5);
   only voxels owned by that fiber are removed; stubs trimmed to the
   surviving mask. 83 breaks (seed 20260926). GT kept separately.
3. **Method-visible world**: remaining pieces + corrupted mask. Dangling
   endpoints get an outward tangent, a local curvature estimate, and two
   GT-free filters (cube-border ends; ends where the mask continues = not a
   tip). 163 of 166 break tips become visible.
4. **Ablation ladder** (same candidate pairs, same τ-acceptance machinery;
   only the pairing rule / cost differs):

| variant | pairing rule | connector |
|---|---|---|
| A0 | greedy nearest endpoint (d ≤ 34 vox) | straight |
| A1 | Hungarian on cost = distance only | Bezier |
| B1a | A1 + hard tangent-direction constraint (a pair is forbidden if either outward tangent points away from the other end, align < −0.15) | Bezier |
| B1b | A1 + soft tangent-alignment cost (W·mean(1 − align), no hard constraint) | Bezier |
| B1c | A1 + hard + soft (= "tangent", the earlier B1) | Bezier |
| B2 | B1c + curvature residual | Bezier |
| B3 | B1c + curvature + crossing penalty (full) | Bezier |

5. **Scoring** against GT: repaired / false cross-fiber / extra same-fiber /
   unrepaired; positional error of the restored segment; subgroup of breaks
   with another fiber within 6 voxels. A τ-sweep (τ ∈ 0.6…2.0, same cost
   matrices) maps each variant's whole repaired-vs-false frontier, so the
   comparison does not depend on one operating point.

On a methodological note: **A0 changes two things at once vs A1** (greedy →
Hungarian *and* straight → Bezier connector). A0 is intended as the simplest
nearest-endpoint baseline; because connector geometry never enters the
pairing score or the pairing metrics (repair/false-link counts), the
**A1 → B1x comparisons isolate the contribution of tangent-aware pairing
cleanly**; the position-error metric is the only one where connector shape
plays a role, and there the differences between variants are small
(1.03–1.21 voxels mean).

All weights/thresholds were fixed a priori (not tuned on the cube). Methods
see no ground-truth identity — only corrupted-mask geometry.

## Results — ablation (83 breaks, seed 20260926, τ = 1.2)

| variant | repaired | false cross-fiber links |
|---|---|---|
| A0 nearest greedy | 48/83 (57.8 %) | 21 |
| A1 distance + Hungarian | 71/83 (85.5 %) | 9 |
| B1a + hard "no backwards" constraint | 76/83 (91.6 %) | 4 |
| **B1b + soft tangent alignment** | **80/83 (96.4 %)** | **0** |
| B1c hard + soft | 80/83 (96.4 %) | 0 |
| B2 + curvature | 71/83 (85.5 %) | 0 |
| B3 + crossing (full) | 69/83 (83.1 %) | 0 |

Same pattern on two more corruption seeds (same cube):

| seed | A0 | A1 | B1a | B1b | B1c | B2 | B3 |
|---|---|---|---|---|---|---|---|
| 7 | 67.9 % / 14 | 82.1 % / 9 | 88.1 % / 4 | **92.9 % / 0** | 92.9 % / 0 | 82.1 % / 0 | 79.8 % / 0 |
| 42 | 53.5 % / 28 | 58.1 % / 31 | 90.7 % / 5 | 93.0 % / 2 | **94.2 % / 2** | 80.2 % / 0 | 80.2 % / 0 |

(entry: repaired % / false cross-fiber links; full data in
`results_seeds.csv`, per-break outcomes in `breaks_per_case.csv`.)

### Tau sweep (who wins is not a threshold artifact)

With the acceptance threshold τ swept (same cost matrices; `tau_sweep.csv`,
`fig7`):

* **A1 saturates at 85.5 % repaired with 9 false links and cannot improve**:
  no τ removes those 9 false pairs — distance alone cannot reject them.
* **B1a (hard constraint only) saturates at 91.6 % / 4 false** — the simple
  rule "never connect backwards" already removes more than half of A1's
  false links, but its frontier stays below B1b's.
* **B1b (soft alignment only) dominates A1 and B1a over the whole frontier**:
  94.0 % / 0 false already at τ = 1.0, ceiling 96.4 % / 0 false.
* **B1c is indistinguishable from B1b at every τ** (and on seeds 7/42 adds at
  most +1 repair): once the soft term is present, the hard constraint is
  nearly redundant at this operating range.
* **B2 reaches exactly B1b/B1c's frontier** (96.4 % / 0 false at τ = 1.5): the
  curvature term only shifts the cost scale, adding no separability.
* **B3 is slightly below that frontier** (94.0 % ceiling): the crossing
  penalty rejects a couple of true connectors — in a dense fiber bundle the
  true connector often passes close to a neighbor.

## Interpretation (revised verdict)

1. **The tangent is the feature that matters — and its soft version carries
   it.** Replacing distance-only costs with distance + soft tangent
   alignment (A1 → B1b) jumps repairs 85.5 % → 96.4 % and cuts false links
   9 → 0 (canonical seed); on seed 42, 31 → 2 while repairs go 58 % → 93 %.
   Operationally this is a one-line rule: *prefer partners that lie roughly
   ahead of both stubs*.
2. **The hard "no backwards" constraint helps but is not the story**
   (B1a: 91.6 % / 4 false), and once the soft term is present it adds
   almost nothing (B1c ≈ B1b).
3. **Global assignment alone is not the key.** Distance + Hungarian (A1)
   improves over greedy A0 on two seeds but *not* on seed 42 (58.1 % vs
   53.5 %, false links 31 vs 28) — with distance-only costs the one-to-one
   constraint has nothing discriminative to work with.
4. **Curvature and crossing, as implemented here and under the tested
   corruption model, provided no additional benefit over tangent-aware
   pairing.** B2 matches but never beats B1b/B1c's frontier; B3 is slightly
   worse. Two plausible mechanisms, both consistent with the data: (a) the
   tested breaks are clean perpendicular cuts, so stub tangents are nearly
   ideal and curvature simply has nothing left to fix; (b) the crossing
   penalty is conceptually too rigid for papyrus — a *correct* connector may
   legitimately pass very close to a neighboring fiber, and indeed B3's
   dropped repairs are exactly such cases. That negative result is itself
   useful: it marks where the simple tangent rule suffices and where the
   model would need to change (slanted/partial breaks, noisy tracers,
   crossing-aware rather than crossing-forbidding costs).
5. Overall, the original hypothesis is **confirmed in a sharper form**:
   local fiber direction, not nearest-neighbor distance, is what makes
   fiber-break reconnection work on this cube; the more elaborate geometry
   cues are redundant here.

## Limitations

* **One cube, one scroll** (s1, 256³, 89 fibers). The dataset has 11 cubes
  (two scrolls); results may differ elsewhere.
* **Artificial breaks** are clean, fully-severing, perpendicular cuts: the
  surviving stubs are straight and their tangents are reliable. The tangent
  feature likely benefits from this the most; real damage (slanted, partial,
  deformed) would make stubs noisier and could shift the balance toward
  curvature terms or a machine-learned combination.
* **Method-visible pieces come from GT polylines** trimmed to the corrupted
  mask, not from an independent tracer on the mask. A real pipeline adds
  tracer errors upstream of reconnection.
* The hard subgroup (another fiber within 6 voxels) is small (8–11 breaks
  per seed); its numbers are indicative only.
* Hyperparameters (weights, D_MAX, ALIGN_FORBID) were fixed a priori; τ is
  handled by the sweep, but the *cost weights* themselves (W_ALIGN = 1.0,
  W_CURV = 0.7, W_CROSS = 3.0) were not tuned — a different weighting might
  let curvature or crossing contribute at B1's level.
* A0 differs from A1 in matching *and* connector shape (see Method §4);
  this does not affect the A1 → B1x attribution but makes the A0 → A1 step
  only loosely interpretable.
* Metrics measure endpoint pairing quality; voxel-level mask completeness
  (painted connectors) is not scored.

## Files

* `outputs/results.csv` — ablation table, 7 variants (canonical seed)
* `outputs/results_seed7.csv`, `results_seed42.csv` — stability runs
* `outputs/results_seeds.csv` — 7 variants × 3 seeds
* `outputs/tau_sweep.csv` (+ `_seed7`, `_seed42`) — frontier data
* `outputs/breaks_per_case.csv` — per-break outcomes for all variants
* `outputs/figures/fig1_gt_vs_corrupted.png` — GT vs corrupted mask
* `outputs/figures/fig2_method_A0_nearest.png`, `fig3_method_B3_geometry_aware.png`
* `outputs/figures/fig4_A0_vs_B3.png` — side-by-side comparison
* `outputs/figures/fig5_hard_cases.png` — zoomed hard (near-parallel) breaks
* `outputs/figures/fig6_ablation.png` — ablation bar chart
* `outputs/figures/fig7_tau_sweep.png` — trade-off frontiers
