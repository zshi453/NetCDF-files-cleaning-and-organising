"""
Step 2 (fully automated): export cleaned terrain + all dynamic variables to
per-frame EXR files, using the ceiling saved by 01_diagnose_terrain.py.

Usage:
    python 02_export_all.py
    python 02_export_all.py --vars h u v zs        # subset of dynamic vars
    python 02_export_all.py --out my_exr_folder
"""
import argparse
from pathlib import Path

import numpy as np

import config
import io_utils

DYNAMIC_VARS = ["h", "u", "v", "zs"]  # zs gets the same ceiling treatment as terrain


def export_terrain(ds, ceiling, out_dir):
    zb = io_utils.var(ds, "zb").values
    if zb.ndim == 3:
        zb = zb[0]
    zb_clipped = np.clip(zb, a_min=None, a_max=ceiling)
    out_dir.mkdir(parents=True, exist_ok=True)
    io_utils.write_exr_single(out_dir / "terrain_zb.exr", zb_clipped)
    print(f"Wrote terrain_zb.exr (clipped at {ceiling}m)")


def export_dynamic(ds, name, out_dir, ceiling=None):
    data = io_utils.var(ds, name).values  # (time, y, x)
    n_time = data.shape[0]
    var_dir = out_dir / f"exr_{name}"
    var_dir.mkdir(parents=True, exist_ok=True)

    for t in range(n_time):
        frame = data[t]
        if ceiling is not None:
            frame = np.clip(frame, a_min=None, a_max=ceiling)
        io_utils.write_exr_single(var_dir / f"frame_{t:04d}.exr", frame)

    print(f"Wrote {n_time} frames for {name} -> {var_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vars", nargs="+", default=DYNAMIC_VARS,
                         help=f"Dynamic variables to export (default: {DYNAMIC_VARS})")
    parser.add_argument("--out", type=Path, default=config.OUTPUT_DIR)
    args = parser.parse_args()

    ceiling = io_utils.get_terrain_ceiling()
    zs_ceiling = ceiling + config.ZS_CEILING_MARGIN

    ds = io_utils.load_dataset()
    export_terrain(ds, ceiling, args.out)

    for name in args.vars:
        var_ceiling = zs_ceiling if name == "zs" else None
        export_dynamic(ds, name, args.out, ceiling=var_ceiling)

    print("\nDone.")


if __name__ == "__main__":
    main()
