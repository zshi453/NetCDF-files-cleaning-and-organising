"""
Step 0 (sanity check): inspect a .nc file's structure and confirm the data
actually varies over time, before spending time on terrain cleaning/export.

Covers what check_time.py used to do (dims/coords/vars, time range) plus a
frame-to-frame change check on a chosen variable (default: h, water depth) -
useful for catching a run that silently produced duplicate/near-static
frames, or a variable that isn't updating.

Usage:
    python 00_sanity_check.py                    # structure + h_P1 change check
    python 00_sanity_check.py --var zs            # check a different variable
    python 00_sanity_check.py --var h --plot      # also plot mean depth over time
    python 00_sanity_check.py --threshold 0.01    # tune the "stuck frame" sensitivity
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt

import config
import io_utils


def show_structure(ds):
    print("--- Dimensions ---")
    print(ds.dims)
    print("\n--- Coordinates ---")
    print(list(ds.coords))
    print("\n--- Data variables ---")
    print(list(ds.data_vars))


def show_time_range(ds):
    if "time" not in ds.coords:
        print("\nNo 'time' coordinate found - skipping time range check.")
        return
    t = ds["time"].values
    print(f"\n--- Time ---")
    print(f"First: {t[0]}")
    print(f"Last:  {t[-1]}")
    print(f"Steps: {len(t)}")
    if len(t) > 1:
        print(f"Range: {t[-1] - t[0]}")


def check_time_variation(ds, name, threshold, plot):
    data = io_utils.var(ds, name).values  # (time, y, x)
    if data.ndim != 3:
        print(f"\n{name} is not time-varying (shape={data.shape}) - nothing to check.")
        return

    n_time = data.shape[0]
    means = np.nanmean(data, axis=(1, 2))
    maxes = np.nanmax(data, axis=(1, 2))

    print(f"\n--- Frame-to-frame check: {name} ({n_time} timesteps) ---")
    print(f"{'step':>5} {'mean':>10} {'max':>10} {'mean|delta| vs prev':>20}")
    print(f"{0:>5} {means[0]:>10.4f} {maxes[0]:>10.4f} {'--':>20}")

    stuck_steps = []
    for t in range(1, n_time):
        diff = np.abs(data[t] - data[t - 1])
        mean_abs_diff = np.nanmean(diff)
        print(f"{t:>5} {means[t]:>10.4f} {maxes[t]:>10.4f} {mean_abs_diff:>20.6f}")
        if mean_abs_diff < threshold:
            stuck_steps.append(t)

    if stuck_steps:
        print(f"\nWARNING: {len(stuck_steps)} timestep(s) show almost no change "
              f"(mean|delta| < {threshold}) vs the previous frame: {stuck_steps}")
        print("This can mean duplicate frames, a stalled write, or a genuinely static period.")
    else:
        print(f"\nAll {n_time - 1} frame-to-frame diffs are above the {threshold} threshold - looks healthy.")

    if plot:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        axes[0].plot(means, marker="o")
        axes[0].set_title(f"Mean {name} per timestep")
        axes[0].set_xlabel("timestep")

        diffs = [np.nanmean(np.abs(data[t] - data[t - 1])) for t in range(1, n_time)]
        axes[1].plot(range(1, n_time), diffs, marker="o", color="tab:orange")
        axes[1].axhline(threshold, color="red", linestyle="--", label="threshold")
        axes[1].set_title(f"Mean |delta {name}| vs previous frame")
        axes[1].set_xlabel("timestep")
        axes[1].legend()

        plt.tight_layout()
        plt.show()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--var", type=str, default="h",
                         help="Variable to check for time variation (default: h, water depth).")
    parser.add_argument("--threshold", type=float, default=0.005,
                         help="Mean absolute frame-to-frame diff below which a step is flagged as 'stuck'.")
    parser.add_argument("--plot", action="store_true",
                         help="Show mean-value and frame-diff plots over time.")
    args = parser.parse_args()

    ds = io_utils.load_dataset()

    show_structure(ds)
    show_time_range(ds)
    check_time_variation(ds, args.var, args.threshold, args.plot)


if __name__ == "__main__":
    main()
