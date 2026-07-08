"""
Step 1 (human-in-the-loop): inspect the terrain (zb) elevation distribution
and decide on a ceiling above which cells are treated as bad/sentinel data.

This is the one part of the pipeline that isn't fully automated on purpose -
what counts as "unrealistically high" depends on the model run, so a person
needs to eyeball the gap analysis / histogram / clipped preview before
committing to a number. The choice is then saved to pipeline_state.json and
every other script picks it up automatically.

Usage:
    python 01_diagnose_terrain.py                  # analyse, plot, prompt for a ceiling
    python 01_diagnose_terrain.py --ceiling 260     # skip analysis, just save this value
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt

import config
import io_utils


def analyse(zb, low, high, top_n=5):
    print(f"zb stats: min={np.nanmin(zb):.2f}  max={np.nanmax(zb):.2f}  "
          f"NaNs={np.sum(np.isnan(zb))} ({100*np.mean(np.isnan(zb)):.2f}%)")

    vals = np.sort(np.unique(zb[(zb > low) & (zb < high)]))
    if len(vals) < 2:
        print(f"Fewer than 2 unique values between {low}m and {high}m - try widening --low/--high.")
        return

    diffs = np.diff(vals)
    order = np.argsort(diffs)[::-1][:top_n]
    print(f"\nTop {top_n} value gaps between {low}m and {high}m (candidate cutoffs):")
    for i in sorted(order):
        print(f"  gap {diffs[i]:8.2f}m   between {vals[i]:8.2f}m and {vals[i + 1]:8.2f}m")


def show_histogram(zb, low, high):
    vals = zb[(zb > low) & (zb < high)]
    plt.figure(figsize=(8, 4))
    plt.hist(vals, bins=100)
    plt.xlabel("Elevation (m)")
    plt.ylabel("Cell count")
    plt.title(f"zb distribution between {low}m and {high}m")
    plt.tight_layout()
    plt.show()


def show_clip_preview(zb, ceiling):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    im0 = axes[0].imshow(zb, cmap="terrain")
    axes[0].set_title("zb (raw)")
    fig.colorbar(im0, ax=axes[0], label="Elevation (m)")

    clipped = np.clip(zb, a_min=None, a_max=ceiling)
    im1 = axes[1].imshow(clipped, cmap="terrain")
    axes[1].set_title(f"zb clipped at {ceiling}m")
    fig.colorbar(im1, ax=axes[1], label="Elevation (m)")
    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ceiling", type=float, default=None,
                         help="Skip analysis and directly save this ceiling value.")
    parser.add_argument("--low", type=float, default=150.0,
                         help="Lower bound (m) for the gap-analysis / histogram window.")
    parser.add_argument("--high", type=float, default=700.0,
                         help="Upper bound (m) for the gap-analysis / histogram window.")
    args = parser.parse_args()

    ds = io_utils.load_dataset()
    zb = io_utils.var(ds, "zb").values
    if zb.ndim == 3:
        zb = zb[0]  # terrain is static across time, only need the first frame

    if args.ceiling is not None:
        ceiling = args.ceiling
    else:
        analyse(zb, args.low, args.high)
        show_histogram(zb, args.low, args.high)
        ceiling = float(input("\nEnter the terrain ceiling to use (m): "))
        show_clip_preview(zb, ceiling)
        confirm = input(f"Save ceiling={ceiling}m to {config.STATE_FILE}? [y/N] ").strip().lower()
        if confirm != "y":
            print("Not saved - re-run when you've decided.")
            return

    io_utils.save_state(terrain_ceiling=ceiling)
    print(f"Saved terrain_ceiling={ceiling} to {config.STATE_FILE}")


if __name__ == "__main__":
    main()
