"""
Shared IO helpers for the BG Flood -> EXR pipeline.
"""
import json

import numpy as np
import xarray as xr
import OpenEXR
import Imath

import config


def load_dataset():
    """Open the configured NetCDF file. Open once per script and reuse the handle."""
    return xr.open_dataset(config.NCFILE, engine="netcdf4")


def var(ds, name):
    """
    Fetch a variable at the configured resolution level.
    e.g. var(ds, "zb") -> ds["zb_P1"] when config.RESOLUTION_LEVEL == "P1".
    """
    key = f"{name}_{config.RESOLUTION_LEVEL}"
    if key not in ds:
        raise KeyError(f"{key!r} not found in dataset. Available: {list(ds.data_vars)}")
    return ds[key]


def load_state():
    if config.STATE_FILE.exists():
        return json.loads(config.STATE_FILE.read_text())
    return {}


def save_state(**kwargs):
    state = load_state()
    state.update(kwargs)
    config.STATE_FILE.write_text(json.dumps(state, indent=2))
    return state


def get_terrain_ceiling():
    """Resolve the terrain ceiling: state file > config default > error."""
    state = load_state()
    ceiling = state.get("terrain_ceiling", config.DEFAULT_TERRAIN_CEILING)
    if ceiling is None:
        raise RuntimeError(
            "No terrain ceiling set yet. Run 01_diagnose_terrain.py first, "
            "or set config.DEFAULT_TERRAIN_CEILING manually."
        )
    return float(ceiling)


def write_exr_single(path, array, nan_fill=0.0):
    """Write a single-channel (R) float32 EXR."""
    frame = np.nan_to_num(array, nan=nan_fill).astype(np.float32)
    ny, nx = frame.shape
    header = OpenEXR.Header(nx, ny)
    header["channels"] = {"R": Imath.Channel(Imath.PixelType(Imath.PixelType.FLOAT))}
    exr = OpenEXR.OutputFile(str(path), header)
    exr.writePixels({"R": frame.tobytes()})
    exr.close()
