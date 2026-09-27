# fiber-reconnect: a measured baseline for reconnecting broken papyrus fibers

Quantitative baseline study for **automatic reconnection of fragmented papyrus fiber
traces** in Vesuvius Challenge CT volumes (Herculaneum scrolls). This addresses the
officially open problem of *fiber tracing* / *winding constraints* — the Vesuvius
Challenge spiral fitter consumes whole fibers and manually linked same-winding
constraints, while fiber linking today is done **by hand**.

This is **not** a claim of a novel method. It is the first *measured* post-hoc
reconnection baseline on official Vesuvius data, an ablation that decouples each
geometric ingredient (with a negative result for hand-tuned geometry on real noise),
a regime analysis of *when* tangent cues help, and an evaluation of proposal
filtering for human-in-the-loop review. See **Attributions** — several of the core
ideas were articulated earlier by others; our contribution is the measurement.

## Results in one table (repaired% / false cross-fiber links, best τ)

| Regime | Events | A0 greedy | A1 dist+Hungarian | B1a hard tangent | B1b soft tangent | B2 +curvature | B3 +crossing |
|---|---|---|---|---|---|---|---|
| Synthetic, seed 20260926 | 83 | 57.8% / 21 | 85.5% / 9 | 91.6% / 4 | **96.4% / 0** | 85.5% / 0 | 83.1% / 0 |
| Synthetic, seed 7 | 83 | 67.9% / 14 | 82.1% / 9 | 88.1% / 4 | **92.9% / 0** | 82.1% / 0 | 79.8% / 0 |
| Synthetic, seed 42 | 83 | 53.5% / 28 | 58.1% / 31 | 90.7% / 5 | 93.0% / 2 | **94.2% / 2** | 80.2% / 0 |
| Real, easy region (GT world) | 18 addressable | 8/8 / 0 | 8/8 / 0 | 8/8 / 0 | 7/8 / 0 | 3/8 / 0 | 3/8 / 0 |
| Real, hard region (GT world) | 28 addressable | **14/14 / 0** | **14/14 / 0** | 7/14 / 0 | 6/14 / 0 | 3/14 / 0 | 2/14 / 0 |
| Real, easy region (full region, 7255 ends) | — | 5 true / 3068 props | 3 / 3296 | — | **7 true / 1830 props** | — | 2 / 621 |

## Main findings

1. **The winner depends on the regime — this is the point of the study.**
   On synthetic corruption (long clean cuts, competing distractors) soft-tangent
   alignment is the causal factor (85.5→96.4% repaired, 9→0 false). On real
   official fiber predictions the hierarchy **inverts**: plain endpoint distance +
   one-to-one assignment (Hungarian + τ threshold) reaches the full achievable
   ceiling (8/8 and 14/14) with zero false links, and *every* geometric term
   strictly reduces recall (hard tangent constraint kills half of the true pairs;
   curvature/crossing penalties reject true pairs outright).
2. **Mechanism, not anecdote:** real holes along annotated fibers are short
   (median ≈ 4 voxels), so there is no distractor competition in the matching
   window — distance is already unambiguous — while endpoint tangents on the torn
   19.2 µm prediction mask are noisy enough that alignment penalties fire on true
   pairs. τ-sweeps show the result is not a threshold artifact (A1 saturates at
   τ=1.0; B-variants never catch up at any τ).
3. **Dominant fragmentation source on real data is weave crossings** (H×V), not
   holes: ~2/3 of breaks sit at crossings where "the mask continues" (correctly)
   filters the ends out of the hole-bridging contract. Crossing resolution is the
   open next problem, not more hole-bridging.
4. **Surviving practical value of the geometric variant is proposal filtering:**
   in a full noisy region (7,255 dangling ends) soft-tangent costs yield 45% fewer
   proposals while recovering *more* true links than greedy/distance — fewer
   clicks for human reviewers in a pending/approved workflow.
5. **Practical recommendation:** start any automatic fiber stitching from
   distance + one-to-one assignment; add geometric terms only after recalibration
   on real noise (learned weights), not hand-tuned ones. Independently, the only
   joining heuristic inside the official `villa` codebase (the VC3D tracer's
   forward/reverse fusion) is also purely distance-based — see `docs/villa_audit.md`.

## What is here

```
src/fiber_reconnect/     core: corruption, endpoint features, cost ladder,
                         Hungarian assignment + τ, Bezier connectors, scoring
run_experiment.py        synthetic benchmark (fiber-skeletons NML cube)
run_real_experiment.py   real benchmark (official Paris4 fiber prediction)
hunt_hard_region.py      region selection by GT-guided presence probing
auto_hard_region.py      autopilot for the hard-region chain
test_synthetic.py        self-test incl. adversarial decoy-at-crossing scene
report.md                synthetic benchmark report
real_region_report.md    real-data report (easy + hard regions, inversion)
reproduce.md             reproduction commands
outputs/, outputs_real/  all result CSVs and figures
docs/                    villa code audit, site audit, data plan, roadmap,
                         MASTER_INDEX (knowledge map of the project)
```

## Data sources (not redistributed here)

* Official fiber prediction for PHerc.Paris.4, layer 20260915212757-L1
  (`presence`/`nx`/`ny` OME-Zarr, 19.2 µm L3) —
  `s3://vesuvius-challenge-open-data/PHercParis4/representations/predictions/fibers/`
* `eval_fibers` manual VC3D annotations (65 fibers) —
  `dl.ash2txt.org/datasets/spiral_datasets/PHercParis4/eval_fibers/`
* fiber-skeletons Dataset001 (manual NML cubes, 7.91 µm) —
  `dl.ash2txt.org/datasets/fiber-skeletons/`

Vesuvius Challenge data is licensed **CC-BY-NC 4.0**; cite the dataset per its
data agreement.

## Reproduce

See `reproduce.md` (synthetic) and the header of `run_real_experiment.py` (real;
downloads a few dozen MB of presence/nx/ny chunks). Python 3.10+, numpy, scipy,
scikit-image, tifffile.

## Status / roadmap

In progress (see `docs/ROADMAP.md`): adversarial corruption stress-test of the
"distance suffices" claim, fragmentation census (holes vs crossings vs
unaddressable), compressed-region regime (the one regime where a parallel
distractor is systematic and distance *should* fail), and an integration probe
as a top-k suggestion layer over the manual linking workflow.

## Attributions

We are not first to any single core idea — several were articulated publicly
before this work. We measure; where prior formulations exist we cite them. The
registry below is normative for any derived write-up.

| Idea / fact | Author | When, where | Note |
|---|---|---|---|
| "Bridging gaps between fibers" framed as an official open problem | Vesuvius Challenge | Open Problems 2026, scrollprize.org | task framing |
| Predictive model for missing/erroneous fiber connections | Stephen (alumni) | 31.07.2024, VC Discord | first public formulation of the task |
| Vertex matching between strokes to choose continuation | Kyle | 03.10.2024, VC Discord | matching precedent |
| Gap-closing as linear assignment (LAP) | Jaqaman et al. 2008; Kreshuk et al. 2015 | literature | assignment formulation |
| Cost = endpoint distance + tangent + threshold (coronary vessels) | Guo 2025; Yang 2011/2012; Bates 2018 | literature | closest cost precedent |
| FPicker: geometry-aware filament tracing, endpoint regression | Zhao, ECCV 2026 (arXiv:2609.08305) | literature | general idea only; FPicker does not do reconnection |
| Automatic fiber linking via graph traversal | thehja | ~2025 / Aug 2026, VC Discord | CPU linking attempt, abandoned |
| Assignment optimization over fiber pieces (loopy belief propagation) | waldkauz (Hendrik Schilling) | 21.09.2026, VC Discord #unrolling-vc3d | "kind of works, needs less errors"; not published as code — different formulation (global constraint optimization vs our post-hoc endpoint matching) |
| "Fiberlets" (discrete optimization of short traces) | waldkauz | 16.08.2026, VC Discord | announced, no code |
| Fiber fingerprint (re-identification by neighborhood across gaps) | bruniss (Sean Johnson), djosey | 21.09.2026, VC Discord | alternative mechanism to endpoint matching |
| Semi-automatic fiber tracing (Trace2CP, beam search, distance-only fusion) | waldkauz / villa codebase | 2026, ScrollPrize/villa | our upstream and comparison point |
| bracket_fiber_links (automated H/V same-sheet links) | bruniss | ScrollPrize/villa | consumes *whole* fibers — beneficiary of reconnection |
| Same-winding mapping across breaks via fibers | djosey | 28.07.2026, VC Discord | motivation |
| Re-identification along fibers at large distance | waldkauz | 08.07.2026, VC Discord | motivation |
| H/V crossing graph as same-winding skeleton | jrudolph (design), team (VC3D) | 28.01.2025 / 2026 | `branches` format |
| Synthetic scrolls/surfaces with controlled defects | willstevens, maxim_xyz, bruniss | 20.07.2026, VC Discord | corruption methodology kinship |
| Intersection areas as topology map | tomweidig | 09.10.2024, VC Discord | historical |
| Sealed-benchmark / constraint-gauge evaluation methodology | pscamillo | Jul–Sep 2026, GitHub | evaluation protocol inspiration |
| Seam detection for sheet-switch (labelscope) | rodriguescarson | Aug 2026, GitHub | candidate reject-rule |
| Geometric split-leak control (spiralcheck) | pxnet | 03.08.2026, GitHub | applied to our GT splits |
| "Flags ≠ filter" (check downstream effect) | iluss (fiber-patch-continuity) | 24.09.2026, GitHub | applied to our proposals |

**Not included in this repository:** raw Discord dumps (private community
content). Only short attributed references above. The full internal knowledge
map (including data inventories and experiment log) is `docs/MASTER_INDEX.md`.

## License

Code: MIT (see LICENSE). This project uses Vesuvius Challenge data licensed
CC-BY-NC 4.0; it is not affiliated with the Vesuvius Challenge.
