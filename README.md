# NetCDF-files-cleaning-and-organising
This repository contains code which will turn a NetCDF file (.nc) with flood modelling output data into OpenEXR (.exr) files for visualising these outputs in Virtual Reality. 

# BG Flood → EXR pipeline

Consolidated from the earlier one-off scripts. Run in this order:

```
1. python 01_diagnose_terrain.py      # human-in-the-loop: pick the terrain ceiling
2. python 02_export_all.py            # automated: exports terrain_zb.exr + h/u/v/zs frames
3. python 03_visualise_check.py <exr>  # optional: spot-check any output frame
```

## Why terrain cleaning stays manual

`zb` contains sentinel/artifact values far above the real DEM max. What counts
as "too high" depends on the model run, so `01_diagnose_terrain.py` prints a
gap analysis (biggest jumps in the sorted unique elevation values — usually
the real cutoff), shows a histogram, then lets you type in a ceiling and
preview the clipped result before committing. That value is saved to
`pipeline_state.json`, so you only redo this when you get a new model run.

If you already know the right ceiling (e.g. from a previous run), skip the
interactive step entirely:
```
python 01_diagnose_terrain.py --ceiling 260
```

## Everything else is automated

`02_export_all.py` reads the saved ceiling and:
- clips + writes the static terrain to `exr_output/terrain_zb.exr`
- writes one EXR per timestep for `h`, `u`, `v` (raw, NaN→0) into
  `exr_output/exr_h/`, `exr_u/`, `exr_v/`
- writes one EXR per timestep for `zs` into `exr_output/exr_zs/`, clipped at
  `terrain_ceiling + ZS_CEILING_MARGIN` (default +5m) since water surface can
  sit a bit above the (already-clipped) ground

Each variable is single-channel (R only), which is what you want for a
Blender Displace-modifier texture — no need to pack h/u/v/zs into RGBA
channels of one file unless you specifically want to save texture slots.

## Config

Everything path/setting-related lives in `config.py`:
- `NCFILE` — path to the model output
- `RESOLUTION_LEVEL` — `"P1"` by default; switch to `"P0"` to process that
  grid instead (variable names are built as `{name}_{RESOLUTION_LEVEL}`,
  e.g. `zb_P1`, `h_P0`)
- `ZS_CEILING_MARGIN` — extra headroom above the terrain ceiling for `zs`

## What got dropped / merged

- `check_time.py` — retired, as agreed (input DEM only needs checking once,
  and isn't part of the per-run pipeline).
- `clean_terrain_zb.py`, `visualise_terrain_zb.py`, `binary_dilation.py` —
  their useful bits (gap analysis, histogram, clipped preview) were merged
  into `01_diagnose_terrain.py`.
- `exporting.py`, `exr_frame_clean.py` — two overlapping generations of the
  same export logic, merged into `02_export_all.py` (kept the later
  single-channel-per-variable approach, since that's simplest for Blender's
  Displace modifier).
- `postie.py` — this was a separate DEM-heightmap-PNG experiment on the raw
  input DEM (not BG Flood output), so it wasn't folded into this pipeline.
  Say the word if you still want that flow wired in/updated too.

## Adding more variables later

`export_dynamic()` in `02_export_all.py` works for any `(time, y, x)`
variable — just add its name to `DYNAMIC_VARS` (or pass `--vars`).
