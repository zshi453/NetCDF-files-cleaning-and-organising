# NetCDF-files-cleaning-and-organising
This repository contains code which will turn a NetCDF file (.nc) with flood modelling output data into OpenEXR (.exr) files for visualising these outputs in Virtual Reality. 

# BG Flood → EXR pipeline

Run in this order:

```
0. python 00_sanity_check.py           # structure + confirm data actually changes over time
1. python 01_diagnose_terrain.py       # human-in-the-loop: pick the terrain ceiling
2. python 02_export_all.py             # automated: exports terrain_zb.exr + h/u/v/zs frames
3. python 03_visualise_check.py <exr>  # optional: spot-check any output frame
```

## 0. One-time environment setup

```
pip install xarray netcdf4 numpy matplotlib OpenEXR
```

`OpenEXR` on Windows can be awkward via pip (needs a compiled wheel). If
`pip install OpenEXR` fails, use a prebuilt wheel (Christoph Gohlke's
collection) or `conda install -c conda-forge openexr-python`.

Keep all pipeline files in the same folder — they import each other by
relative path.

## 1. Point the pipeline at your .nc file

Edit `config.py`:
- `NCFILE` — full path to the `.nc` file
- `RESOLUTION_LEVEL` — `"P1"` or `"P0"` (suffix on variable names, e.g. `zb_P1`)

Everything else reads from here — no other script needs editing for a new run.

## 2. Sanity-check the raw file

```
python 00_sanity_check.py
```

Prints dims/coords/data variables and the time range (what `check_time.py`
used to do), then checks a chosen variable (default `h`, water depth) for
frame-to-frame change — flags any timestep whose mean absolute difference
from the previous frame falls below a threshold, which usually means a
duplicate/stuck frame rather than real model output.

```
python 00_sanity_check.py --var zs             # check a different variable
python 00_sanity_check.py --plot               # also plot mean value + Δ over time
python 00_sanity_check.py --threshold 0.01     # tune stuck-frame sensitivity
```

Run this once per new model output, before trusting the rest of the pipeline
on it.

## 3. Run the terrain diagnostic (human-in-the-loop)

```
python 01_diagnose_terrain.py
```

1. Opens the `.nc` file, pulls out `zb` (terrain).
2. Prints min/max/NaN stats and the top 5 biggest gaps in sorted elevation
   values between 150m–700m — a large isolated gap usually marks the
   boundary between real terrain and sentinel/artifact values.
3. Shows a histogram of that range. Close it to continue.
4. Prompts: `Enter the terrain ceiling to use (m):` — type a value based on
   what you saw (e.g. `260`).
5. Shows a side-by-side raw-vs-clipped preview. Close it when happy.
6. Prompts: `Save ceiling=260.0m to pipeline_state.json? [y/N]` — type `y`.

This writes `pipeline_state.json`, e.g. `{"terrain_ceiling": 260.0}`, which
every later step reads automatically.

```
python 01_diagnose_terrain.py --low 0 --high 1000   # widen the gap-analysis window
python 01_diagnose_terrain.py --ceiling 260          # skip interactivity, just save this value
```

## 4. Run the export (fully automated)

```
python 02_export_all.py
```

1. Reads `terrain_ceiling` from `pipeline_state.json`.
2. Clips `zb`, NaN→0, writes `exr_output/terrain_zb.exr`.
3. For each of `h`, `u`, `v`, `zs`, writes one single-channel EXR per
   timestep into `exr_output/exr_<name>/frame_0000.exr`, `frame_0001.exr`, …
   (`zs` clipped at `terrain_ceiling + ZS_CEILING_MARGIN`, default +5m).

```
python 02_export_all.py --vars h zs                  # export a subset
python 02_export_all.py --out D:/blender_project/textures
```

## 5. Spot-check the output (optional but recommended)

```
python 03_visualise_check.py exr_output/terrain_zb.exr
python 03_visualise_check.py exr_output/exr_zs/frame_0010.exr
```

Prints shape/min/max and shows a `terrain`-colormap preview. Check for no
spikes in `terrain_zb.exr`, and a plausible (non-flat, non-empty) flood
extent in a mid-sequence `zs` frame.

## 6. Into Blender

`exr_output/` now has:
- `terrain_zb.exr` → base terrain displacement
- `exr_zs/frame_NNNN.exr` → per-frame water-surface displacement
- `exr_h/`, `exr_u/`, `exr_v/` → depth/velocity, for shading (e.g.
  color-by-depth, flow-mapped normals) rather than geometry

Load as Image Sequences in Blender's image texture nodes; point the terrain
one at a Displace modifier. Displacement-strength scaling for that modifier
is still an open step — flag it if you want to work through it next.

## Re-running for a new model output

Steps 1–3 (edit `NCFILE`, sanity-check, re-diagnose terrain) are required per
new file, since a different run may have different time behaviour and
sentinel values. Step 4 is always just `python 02_export_all.py`.

## Config

Everything path/setting-related lives in `config.py`:
- `NCFILE` — path to the model output
- `RESOLUTION_LEVEL` — `"P1"` by default; switch to `"P0"` for that grid
  (variable names built as `{name}_{RESOLUTION_LEVEL}`, e.g. `zb_P1`, `h_P0`)
- `ZS_CEILING_MARGIN` — extra headroom above the terrain ceiling for `zs`

## What got dropped / merged

- `check_time.py` — superseded by `00_sanity_check.py`, which does the same
  structural inspection plus the frame-to-frame change check.
- `clean_terrain_zb.py`, `visualise_terrain_zb.py`, `binary_dilation.py` —
  merged into `01_diagnose_terrain.py` (gap analysis, histogram, clipped
  preview).
- `exporting.py`, `exr_frame_clean.py` — merged into `02_export_all.py`
  (kept the single-channel-per-variable approach — simplest for Blender's
  Displace modifier).
- `postie.py` — separate DEM-heightmap-PNG experiment on the raw input DEM
  (not BG Flood output), not folded into this pipeline. Say the word if you
  still want that flow wired in/updated too.

## Adding more variables later

`export_dynamic()` in `02_export_all.py` and `check_time_variation()` in
`00_sanity_check.py` both work for any `(time, y, x)` variable — just pass
`--vars` / `--var` or extend the defaults.
