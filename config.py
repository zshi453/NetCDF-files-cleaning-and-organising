"""
Shared configuration for the BG Flood -> EXR pipeline.

Edit the values below to point at your model output. Everything downstream
(01_diagnose_terrain.py, 02_export_all.py) reads from here so there is a
single source of truth for paths and settings.
"""
from pathlib import Path

# ---- Input ----
NCFILE = r"R:\ENGSCI\Flooding\bg_flood\model_for_uoa\01_model_0.65Qin\BGout_RoseDEM_refined_v4_riv65_dual_layer_1.nc"

# Resolution level suffix used in the NetCDF variable names, e.g. "zb_P1",
# "h_P1", "u_P1", "v_P1", "zs_P1". Switch to "P0" to process that grid instead.
RESOLUTION_LEVEL = "P1"

# ---- Output ----
OUTPUT_DIR = Path("exr_output")

# ---- Terrain cleaning ----
# 01_diagnose_terrain.py writes the chosen ceiling here so it persists across
# runs/machines. Delete this file (or pass --ceiling again) to redo the call.
STATE_FILE = Path("pipeline_state.json")

# Optional: hardcode a known-good ceiling to skip the interactive diagnostic
# step entirely (e.g. once you've settled on a value for a given model run).
DEFAULT_TERRAIN_CEILING = None  # e.g. 260.0

# Margin added on top of the terrain ceiling when clamping water-surface
# elevation (zs) frames, since the real water surface can sit a little above
# the (already clamped) ground.
ZS_CEILING_MARGIN = 5.0
