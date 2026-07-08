"""
Step 3 (optional QA): reload an exported EXR and preview it, to sanity-check
pipeline output before importing into Blender.

Usage:
    python 03_visualise_check.py exr_output/terrain_zb.exr
    python 03_visualise_check.py exr_output/exr_zs/frame_0010.exr
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt
import OpenEXR
import Imath


def read_exr_single(path):
    exr = OpenEXR.InputFile(str(path))
    dw = exr.header()["dataWindow"]
    width = dw.max.x - dw.min.x + 1
    height = dw.max.y - dw.min.y + 1
    pt = Imath.PixelType(Imath.PixelType.FLOAT)
    raw = exr.channel("R", pt)
    return np.frombuffer(raw, dtype=np.float32).reshape(height, width)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=str, help="Path to a single-channel EXR file")
    args = parser.parse_args()

    data = read_exr_single(args.path)
    print(f"{args.path}: shape={data.shape} min={data.min():.3f} max={data.max():.3f}")

    plt.imshow(data, cmap="terrain")
    plt.colorbar()
    plt.title(args.path)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
