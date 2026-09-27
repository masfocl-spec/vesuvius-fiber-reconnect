"""Auto-pilot: wait for S3 recovery, then run the hard-region benchmark chain.

1. Poll S3 every 2 min until a test chunk downloads (max 6 h).
2. Probe the 9 fiber-rich windows (hunt_hard_region.stage_b) -> hole density.
3. Winner = max holes>=3vox per 100 GT points (ties: higher wander).
4. Download the full minimal set for the winner (presence/nx/ny 4^3 chunks
   + CT 2^3 chunks) and assemble region cubes -> data/pred/hard/.
5. Run run_real_experiment.py --world gt on the winner.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time

import numpy as np
import requests
from numcodecs import Blosc

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, "..", "data"))
S3 = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/"
PRESENCE = (S3 + "PHercParis4/representations/predictions/fibers/"
            "20260411134726-fibers-20260915212757-L1/"
            "PHercParis4-20260411134726-las-sd1-7ff0ce6c_presence.ome.zarr/3/")
NY = PRESENCE.replace("presence", "ny")
NX = PRESENCE.replace("presence", "nx")
CT = S3 + "PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/3/"
TEST_CHUNK = PRESENCE + "87/19/32"

sys.path.insert(0, os.path.join(HERE, "src"))
sys.stdout.reconfigure(line_buffering=True)


def wait_for_s3(max_wait_s: int = 6 * 3600) -> bool:
    t0 = time.time()
    n = 0
    while time.time() - t0 < max_wait_s:
        n += 1
        try:
            r = requests.get(TEST_CHUNK, timeout=(10, 30))
            if r.status_code == 200:
                print(f"S3 recovered after {n} polls "
                      f"({(time.time() - t0) / 60:.0f} min).")
                return True
        except Exception:
            pass
        print(f"poll {n}: S3 unreachable, waiting 120s...")
        time.sleep(120)
    return False


def fetch_all(jobs, workers=16):
    import concurrent.futures as cf
    got = {}

    def one(job):
        url, path = job
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path, "cached"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for a in range(6):
            try:
                r = requests.get(url, timeout=(15, 60))
                if r.status_code == 200:
                    open(path, "wb").write(r.content)
                    return path, "ok"
                if r.status_code == 404:
                    return path, "404"
            except Exception:
                pass
            time.sleep(2 + a)
        return path, "FAIL"

    with cf.ThreadPoolExecutor(workers) as ex:
        for path, status in ex.map(one, jobs):
            got[path] = status
            if status == "FAIL":
                print("FAIL", path)
    return got


def main():
    max_h = float(sys.argv[sys.argv.index("--max-hours") + 1]) if "--max-hours" in sys.argv else 12.0
    if not wait_for_s3(max_wait_s=int(max_h * 3600)):
        print("S3 did not recover in time; aborting.")
        return
    # warm-up double-check
    ok = 0
    for _ in range(3):
        try:
            if requests.get(TEST_CHUNK, timeout=(10, 30)).status_code == 200:
                ok += 1
        except Exception:
            pass
    if ok < 2:
        print("S3 flaky right now; aborting to avoid partial data.")
        return

    sys.path.insert(0, os.path.join(HERE, "src"))
    from hunt_hard_region import load_fibers, stage_b
    fibers = load_fibers()
    rich = json.load(open(os.path.join(HERE, "rich_windows.json")))
    wins = [(r[0], 0.0, r[2], r[3], r[4], r[5], r[6]) for r in rich]
    res = stage_b(fibers, wins, max_windows=9)
    res.sort(key=lambda r: (-r["holes100"], -r["wander"]))
    print("\nprobe ranking:")
    for r in res:
        print(f"  x[{r['x0']},{r['x0']+2048}] y[{r['y0']},{r['y0']+2048}] "
              f"z[{r['z0']},{r['z0']+2048}]: holes100={r['holes100']:.2f} "
              f"cov={r['cov100']:.1f}% fibers={r['nfib']}")
    win = res[0]
    ox, oy, oz = win["x0"], win["y0"], win["z0"]
    print(f"\nWINNER: x[{ox},{ox+2048}] y[{oy},{oy+2048}] z[{oz},{oz+2048}] "
          f"holes100={win['holes100']:.2f}")

    # full minimal set for the winner
    tag = f"hard_{ox}_{oy}_{oz}"
    outdir = os.path.join(DATA, "pred", tag)
    jobs = []
    for ch_url, ch_name in ((PRESENCE, "presence"), (NX, "nx"), (NY, "ny")):
        for cz in range(oz // 512, oz // 512 + 4):
            for cy in range(oy // 512, oy // 512 + 4):
                for cx in range(ox // 512, ox // 512 + 4):
                    jobs.append((f"{ch_url}{cz}/{cy}/{cx}",
                                 os.path.join(outdir, ch_name,
                                              f"{cz}_{cy}_{cx}.chunk")))
    for cz in range(oz // 1024, oz // 1024 + 2):
        for cy in range(oy // 1024, oy // 1024 + 2):
            for cx in range(ox // 1024, ox // 1024 + 2):
                jobs.append((f"{CT}{cz}/{cy}/{cx}",
                             os.path.join(DATA, "ct", "hard",
                                          f"{cz}_{cy}_{cx}.chunk")))
    got = fetch_all(jobs)
    n_fail = sum(1 for s in got.values() if s == "FAIL")
    print(f"downloaded {len(jobs)} files, failures={n_fail}")
    if n_fail:
        print("aborting: incomplete download")
        return

    # assemble region cubes
    codec = Blosc(cname="zstd", clevel=3, shuffle=1, blocksize=0)
    for ch in ("presence", "nx", "ny"):
        cube = np.zeros((256, 256, 256), dtype=np.uint8)
        for fp in glob.glob(os.path.join(outdir, ch, "*.chunk")):
            name = os.path.basename(fp).replace(".chunk", "")
            cz, cy, cx = map(int, name.split("_"))
            arr = np.frombuffer(codec.decode(open(fp, "rb").read()),
                                dtype=np.uint8).reshape(64, 64, 64)
            z0 = cz * 64 - oz // 8
            y0 = cy * 64 - oy // 8
            x0 = cx * 64 - ox // 8
            cube[z0:z0 + 64, y0:y0 + 64, x0:x0 + 64] = arr
        np.save(os.path.join(outdir, f"region_{ch}.npy"), cube)
        print(f"assembled region_{ch}.npy "
              f"(nonzero {(cube > 0).mean() * 100:.1f}%)")

    # run the benchmark on the winner
    r = subprocess.run(
        [sys.executable, os.path.join(HERE, "run_real_experiment.py"),
         "--world", "gt", "--ox", str(ox), "--oy", str(oy), "--oz", str(oz),
         "--region-prefix", outdir, "--tau", "1.2"],
        cwd=HERE)
    print("benchmark exit code:", r.returncode)
    print("AUTO_PILOT_DONE")


if __name__ == "__main__":
    main()
