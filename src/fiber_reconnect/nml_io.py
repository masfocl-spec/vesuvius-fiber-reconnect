"""Parsing of WEBKNOSSOS NML skeleton files from the Vesuvius fiber-skeletons dataset.

NML format (https://docs.webknossos.org/webknossos/data/concepts.html#nml-files):
  <things>
    <parameters>... <scale x=.. y=.. z=../> ...</parameters>
    <thing id="N" ...>            <- one annotated "tree" = one traced fiber (or fragment)
      <nodes>
        <node id="i" position="x y z" radius=".." .../>
      </nodes>
      <edges>
        <edge source="i" target="j"/>
      </edges>
    </thing>
    ... (things may live under <groups> as well)
  </things>

Node positions are GLOBAL volume coordinates in webknossos (x, y, z) order.
The official converter (ScrollPrize/villa fibers-dataset-generator.py) paints voxels at
(z - z0, y - y0, x - x0) and saves the volume transposed to (z, y, x) axis order,
so for a cube named "..._{z0}z_{y0}y_{x0}x_{size}" the tif voxel is
mask[z - z0, y - y0, x - x0].
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np


@dataclass
class NmlTree:
    """One WEBKNOSSOS <thing>: a graph of nodes+edges = one traced fiber."""

    tree_id: int
    name: str
    positions: dict[int, np.ndarray] = field(default_factory=dict)  # global x,y,z floats
    edges: set[tuple[int, int]] = field(default_factory=set)

    def adjacency(self) -> dict[int, list[int]]:
        adj: dict[int, list[int]] = defaultdict(list)
        for a, b in self.edges:
            adj[a].append(b)
            adj[b].append(a)
        return adj


def parse_nml(path: str) -> tuple[list[NmlTree], tuple[float, float, float]]:
    """Parse an NML file -> (list of trees, voxel scale (x, y, z))."""
    root = ET.parse(path).getroot()

    scale = (1.0, 1.0, 1.0)
    params = root.find("parameters")
    if params is not None:
        sc = params.find("scale")
        if sc is not None:
            scale = (
                float(sc.get("x", "1")),
                float(sc.get("y", "1")),
                float(sc.get("z", "1")),
            )

    trees: list[NmlTree] = []
    for thing in root.iter("thing"):
        tid = int(thing.get("id"))
        name = thing.get("name", f"tree{tid}")
        tree = NmlTree(tree_id=tid, name=name)
        for node in thing.iter("node"):
            # both NML writer variants occur: position="x y z" or x=,y=,z=
            if node.get("position") is not None:
                pos = tuple(float(c) for c in node.get("position").split())
            else:
                pos = (float(node.get("x")), float(node.get("y")),
                       float(node.get("z")))
            tree.positions[int(node.get("id"))] = np.asarray(pos, dtype=float)
        for edge in thing.iter("edge"):
            a, b = int(edge.get("source")), int(edge.get("target"))
            if a in tree.positions and b in tree.positions:
                tree.edges.add((min(a, b), max(a, b)))
        if tree.positions:
            trees.append(tree)
    return trees, scale


def chain_decomposition(tree: NmlTree) -> list[list[int]]:
    """Split a tree graph into maximal chains between nodes of degree != 2.

    Returns a list of chains, each a list of node ids in traversal order.
    Isolated single nodes are dropped.
    """
    adj = tree.adjacency()
    junctions = {n for n, nbrs in adj.items() if len(nbrs) != 2}

    visited_edges: set[tuple[int, int]] = set()
    chains: list[list[int]] = []

    def edge_key(a: int, b: int) -> tuple[int, int]:
        return (min(a, b), max(a, b))

    # chains starting at junction nodes / leaves
    for start in list(adj.keys()):
        if start not in junctions:
            continue
        for nbr in adj[start]:
            e = edge_key(start, nbr)
            if e in visited_edges:
                continue
            chain = [start, nbr]
            visited_edges.add(e)
            prev, cur = start, nbr
            while cur not in junctions:
                nxt = [v for v in adj[cur] if v != prev]
                if not nxt:  # dead end (should not happen for degree-2)
                    break
                v = nxt[0]
                e = edge_key(cur, v)
                if e in visited_edges:
                    break
                visited_edges.add(e)
                chain.append(v)
                prev, cur = cur, v
            if len(chain) >= 2:
                chains.append(chain)

    # remaining edges = closed loops not touching any junction
    for a, b in tree.edges:
        e = edge_key(a, b)
        if e not in visited_edges:
            chain = [a, b]
            visited_edges.add(e)
            prev, cur = a, b
            while cur != a:
                nxt = [v for v in adj[cur] if v != prev]
                if not nxt:
                    break
                v = nxt[0]
                e2 = edge_key(cur, v)
                if e2 in visited_edges:
                    break
                visited_edges.add(e2)
                chain.append(v)
                prev, cur = cur, v
            chains.append(chain)

    return chains


def cube_name_to_origin(cube_name: str) -> tuple[int, int, int]:
    """'s1_00497_01497_03997_256' -> (z0, y0, x0) per the dataset naming."""
    m = re.match(r"s(\d+)_(\d+)_(\d+)_(\d+)_(\d+)$", cube_name)
    if not m:
        raise ValueError(f"unexpected cube name: {cube_name}")
    _, z0, y0, x0, size = m.groups()
    return int(z0), int(y0), int(x0), int(size)


def resample_polyline(points: np.ndarray, spacing: float = 1.0) -> np.ndarray:
    """Resample a polyline to roughly uniform arc-length spacing.

    points: (N, 3) float array. Returns (M, 3) with M ~ arc_length / spacing.
    """
    if len(points) < 2:
        return points.copy()
    seg = np.linalg.norm(np.diff(points, axis=0), axis=1)
    keep = seg > 1e-9
    if not keep.any():
        return points[:1].copy()
    pts = np.vstack([points[:-1][keep], points[-1:]])
    seg = seg[keep]
    s = np.concatenate([[0.0], np.cumsum(seg)])
    total = s[-1]
    if total < spacing:
        return np.vstack([points[0], points[-1]])
    n = max(2, int(round(total / spacing)) + 1)
    targets = np.linspace(0.0, total, n)
    out = np.empty((n, 3), dtype=float)
    for d in range(3):
        out[:, d] = np.interp(targets, s, pts[:, d])
    return out
