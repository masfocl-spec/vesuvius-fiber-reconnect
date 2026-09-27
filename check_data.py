"""Sanity check: do the NML skeletons and the tif label mask of one cube agree?

Checks (per dataset README + official converter ScrollPrize/villa):
  - tif is (size, size, size) in (z, y, x) axis order, labels {0, 1}
  - NML nodes map to local voxel (z - z0, y - y0, x - x0)
  - coverage: how many NML polyline points land on/near mask voxels,
    and how many mask voxels lie near some polyline
"""

import sys

import numpy as np
import tifffile
from scipy.spatial import cKDTree

sys.path.insert(0, "src")
from fiber_reconnect.nml_io import (  # noqa: E402
    chain_decomposition,
    cube_name_to_origin,
    parse_nml,
    resample_polyline,
)

RAW = "data/raw"
CUBE = "s1_00497_01497_03997_256"
NML = f"{RAW}/fibers_s1a_00497z_01497y_03997x_256_v00.nml"
TIF = f"{RAW}/labels_{CUBE}.tif"


def main() -> None:
    mask = tifffile.imread(TIF)
    z0, y0, x0, size = cube_name_to_origin(CUBE)
    print(f"mask shape={mask.shape} dtype={mask.dtype} unique={np.unique(mask)}")
    assert mask.shape == (size, size, size), "unexpected cube size"

    trees, scale = parse_nml(NML)
    print(f"NML: {len(trees)} trees, scale(x,y,z)={scale}")
    print("  nodes per tree:", [len(t.positions) for t in trees])

    # local (z, y, x) coords of every node
    all_pts = []
    n_out = 0
    for t in trees:
        for p in t.positions.values():
            lz, ly, lx = p[2] - z0, p[1] - y0, p[0] - x0
            if 0 <= lz < size and 0 <= ly < size and 0 <= lx < size:
                all_pts.append((lz, ly, lx))
            else:
                n_out += 1
    pts = np.asarray(all_pts)
    print(f"nodes in-cube: {len(pts)}, outside: {n_out}")

    # coverage: fraction of NML nodes whose voxel is inside the mask (or within r=2)
    mask_tree = cKDTree(np.argwhere(mask > 0))
    d, _ = mask_tree.query(pts, k=1, workers=-1)
    for r in (0.0, 1.5, 3.0):
        print(f"  nodes with mask voxel within r={r}: {(d <= r).mean() * 100:.1f}%")

    # reverse coverage: fraction of mask voxels near some NML node
    node_tree = cKDTree(pts)
    mv = np.argwhere(mask > 0)
    d2, _ = node_tree.query(mv, k=1, workers=-1)
    for r in (2.0, 4.0):
        print(f"  mask voxels within r={r} of a node: {(d2 <= r).mean() * 100:.1f}%")

    # chain structure
    n_chains, lens = 0, []
    for t in trees:
        for ch in chain_decomposition(t):
            pp = np.asarray([t.positions[n] for n in ch])
            pp = np.stack([pp[:, 2] - z0, pp[:, 1] - y0, pp[:, 0] - x0], axis=1)
            rs = resample_polyline(pp, 1.0)
            inb = np.all((rs >= 0) & (rs < size), axis=1)
            if inb.sum() >= 8:
                n_chains += 1
                lens.append(int(inb.sum()))
    lens = np.asarray(lens)
    print(f"in-cube chains (>=8 vox): {n_chains}, length min/med/max = "
          f"{lens.min()}/{int(np.median(lens))}/{lens.max()}")


if __name__ == "__main__":
    main()
