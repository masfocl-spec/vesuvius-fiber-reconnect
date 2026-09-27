"""Load eval_fibers JSON annotations (VC3D fiber format) as GT polylines.

Coordinates: eval fiber JSON positions are (x, y, z) in BASE volume voxels
(2.4 um) of PHercParis4/20260411134726@L0. We convert to level-3 voxels
(19.2 um, base/8) and shift to region-local (z, y, x) order matching the
region cubes saved by run_real_experiment.py.
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np

# default region constants — must match data_plan.md / region_*.npy
REG_BASE = dict(x=(16384, 18432), y=(9216, 11264), z=(44544, 46592))
REG_L3_ORIGIN = (2048, 1152, 5568)      # (x, y, z) level-3 voxels
REGION_SHAPE = (256, 256, 256)          # (z, y, x)


def load_eval_fibers(data_dir: str = "data/spiral/eval_fibers",
                     origin_l3=(2048, 1152, 5568)) -> list[dict]:
    """Return [{name, pts (N,3) region-local (z,y,x) L3 voxels, hv_tag}].

    origin_l3 = (x, y, z) level-3 voxel coords of the region corner.
    Fibers contribute only their polylines; points outside the region are kept
    (scoring clips by distance), caller decides.
    """
    ox, oy, oz = origin_l3
    out = []
    for fp in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        try:
            d = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        lp = np.asarray(d["line_points"], dtype=float)      # (N,3) (x,y,z) base
        z = lp[:, 2] / 8.0 - oz
        y = lp[:, 1] / 8.0 - oy
        x = lp[:, 0] / 8.0 - ox
        pts = np.stack([z, y, x], axis=1)
        hv = d.get("hv_classification", {}).get("automatic_tag")
        out.append({"name": d.get("filename", os.path.basename(fp)),
                    "pts": pts, "hv_tag": hv})
    return out


def in_region(pts: np.ndarray, margin: float = 0.0) -> np.ndarray:
    lo = np.array([-margin, -margin, -margin])
    hi = np.array([256 + margin] * 3)
    return np.all((pts >= lo) & (pts < hi), axis=1)
