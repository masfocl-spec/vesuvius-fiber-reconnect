# Reproduce: fiber-break reconnection experiment (Vesuvius fiber-skeletons)

Small CPU-only experiment on ONE cube of the official
[fiber-skeletons dataset](https://scrollprize.org/data_datasets) (2025-07):
does geometry/topology-aware endpoint reconnection beat plain
nearest-endpoint pairing when repairing artificial breaks in papyrus fibers?

No training, no GPU, no large downloads (~17 MB for one cube), no neural nets.

## 1. Requirements

* Python 3.10+ (tested on 3.14)
* `pip install numpy scipy matplotlib tifffile` (scikit-image not required)

## 2. Data

We use cube `s1_00497_01497_03997_256` (scroll 1, 256^3 voxels) of
`Dataset001_sk-fibers-20250124`:

* label mask: `https://dl.ash2txt.org/datasets/fiber-skeletons/Dataset001_sk-fibers-20250124/labelsTr/s1_00497_01497_03997_256.tif`
* manual WEBKNOSSOS skeletons (one NML tree = one traced fiber):
  `https://dl.ash2txt.org/datasets/fiber-skeletons/Dataset001_sk-fibers-20250124/nml/fibers_s1a_00497z_01497y_03997x_256_v00.nml`

Both files go into `data/raw/` (the exact local names used by the code:

```
data/raw/labels_s1_00497_01497_03997_256.tif
data/raw/fibers_s1a_00497z_01497y_03997x_256_v00.nml
```

`download_parallel.sh` automates the download (the server throttles and
resets connections aggressively; the script fetches small byte ranges in
parallel and appends them):

```bash
bash download_parallel.sh          # ~17 MB total, verify sizes with ls
```

Expected sizes: tif = 16,819,802 bytes; nml = 693,533 bytes.

### Format notes (from the dataset README + official converter)

* The dataset follows the nnU-Net layout (`labelsTr/`, `imagesTr/`, `nml/`),
  labels are {0 = background, 1 = fiber}; cubes are 256^3 or 512^3.
* NML node positions are **global** (x, y, z) in voxels. The cube name
  `s1_00497_01497_03997_256` encodes the origin (z0=497, y0=1497, x0=3997)
  and size. A node maps to tif voxel `mask[z - z0, y - y0, x - x0]`
  (the saved tif is in (z, y, x) axis order — verified against the official
  converter `ScrollPrize/villa/foundation/datasets/fibers-dataset`).
* The volumetric labels were produced from these same skeletons
  (interpolation + EDT <= 3 + Frangi binarization), so NML polylines are the
  fiber centerlines of the mask.

## 3. Sanity check

```bash
python check_data.py
```

Prints mask stats, number of NML trees/chains, and how well NML polylines
and the label mask agree (coverage both ways).

## 4. Self-test (no data needed)

```bash
python test_synthetic.py
```

Two synthetic scenes: (1) a single broken curved fiber + straight decoy,
(2) an adversarial scene where the nearest tip is a *decoy* cut at a fiber
crossing. Method A (nearest) makes a false cross-fiber link there; method B
does not.

## 5. Run the experiment

```bash
python run_experiment.py --cube s1_00497_01497_03997_256 --seed 20260926
```

Outputs:

* `outputs/results.csv` — ablation ladder for all 5 variants (canonical seed)
* `outputs/results_seeds.csv` — 5 variants x 3 corruption seeds
* `outputs/tau_sweep.csv` — repaired/false-links trade-off vs acceptance
  threshold tau for A1/B1/B2/B3 (also saved per seed as `tau_sweep_seed*.csv`)
* `outputs/breaks_per_case.csv` — per-break outcomes (all variants)
* `outputs/figures/fig1_gt_vs_corrupted.png` — GT vs artificially corrupted mask
* `outputs/figures/fig2_method_A0_nearest.png` — greedy nearest baseline
* `outputs/figures/fig3_method_B3_geometry_aware.png` — full method
* `outputs/figures/fig4_A0_vs_B3.png` — side-by-side comparison
* `outputs/figures/fig5_hard_cases.png` — zoom on breaks near parallel fibers
* `outputs/figures/fig6_ablation.png` — ablation bar chart
* `outputs/figures/fig7_tau_sweep.png` — trade-off frontiers per variant

## 6. What the experiment does

1. **Pieces.** NML trees are decomposed into maximal chains, resampled to
   1-voxel spacing, clipped to the cube -> fiber polylines.
2. **Corruption.** For each eligible fiber (>= 50 voxels) with prob. 0.75 one
   interior arc segment of length U[8, 20] voxels is removed (long fibers may
   get a second gap with prob. 0.35). The cut is PERPENDICULAR to the fiber
   (like a real break): a slab of half-width 5 voxels around the gap arc is
   removed from the mask, restricted to voxels within 4.5 of the fiber
   centerline AND whose nearest centerline is that fiber (other fibers keep
   their voxels). Piece stubs are then trimmed to the surviving mask so tips
   sit exactly on the corrupted mask boundary.
3. **Method-visible world.** Remaining piece polylines + corrupted mask.
   Dangling endpoints get an outward tangent (6-voxel average), a curvature
   estimate (local circular fit, clamped to 0.12 rad/voxel), and are filtered
   by two GT-free rules: border ends (within 3 voxels of a cube face) and
   non-tip ends (mask continues 3 voxels beyond the end along the tangent).
4. **Ablation ladder** (all on the SAME corruption; only pairing differs):

   * **A0** — greedy nearest-endpoint pairing (d <= 34 voxels), straight
     connectors (the naive baseline; note it differs from A1 in matching
     AND connector shape).
   * **A1** — Hungarian assignment on distance-only cost.
   * **B1a** — A1 + hard tangent-direction constraint: a pair is forbidden
     if either endpoint's outward tangent points away from the other end.
   * **B1b** — A1 + soft tangent-alignment cost term (no hard constraint).
   * **B1c** — A1 + hard + soft (= the tangent feature, full).
   * **B2** — B1c + curvature-residual term (circular extrapolation from
     both ends must land near the other tip).
   * **B3** — B1c + curvature + crossing penalty (+3.0 if the smooth Bezier
     connector touches other fibers' voxels in the corrupted mask). Full
     method.

   All scored variants share one acceptance threshold tau = 1.2 (a cost
   above tau leaves the endpoint unpaired) and one-to-one matching;
   `tau_sweep.csv` / fig7 cover tau in 0.6..2.0 so conclusions do not hinge
   on the operating point. Connector geometry (straight vs Bezier) never
   enters the pairing score or the pairing metrics.
5. **Metrics** (against GT): repaired breaks, false cross-fiber links,
   extra same-fiber links, unrepaired breaks, positional error of the
   restored segment (mean / p95 / max distance from the true deleted arc to
   the predicted connector), subgroup analysis for breaks with another fiber
   within 6 voxels (near-parallel / crossing).

All hyperparameters were fixed a priori and not tuned on the evaluation cube.
The default seed is 20260926; `--seed 7` and `--seed 42` were run as a
stability check on the same cube (see `outputs/results_seeds.csv`).
