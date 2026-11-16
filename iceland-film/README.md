# Iceland — A Winter Road Trip

A 37-second cinematic 9:16 travel film cut from 27 clips of drone, camera and phone footage and six photos.

```
iceland-film/
├── edit.py        picture: timeline, speed ramps, reframing, grade, title, transitions
├── score.py       original score + sound design, synthesised with numpy (no samples)
├── assets/        Cormorant Garamond roman + italic (SIL OFL) for the title
├── docs/          01 footage inventory · 02 reference analysis · 03 timeline · 04 QC report
├── output/        iceland_winter_road_trip_9x16.mp4
├── stills/        photos used in the cut (git-ignored; matched by name like the clips)
└── build/         intermediates (git-ignored)
```

## Re-rendering

Needs `ffmpeg`, Python 3 with `numpy` and `Pillow`. Source footage is only read, never modified.

```bash
ICELAND_SRC=/path/to/footage python3 edit.py             # full 1080×1920 render (~10 min)
ICELAND_SRC=/path/to/footage python3 edit.py --preview   # half-res check (~2 min)
ICELAND_SRC=/path/to/footage python3 edit.py --only 14   # re-render one shot, then re-assemble
python3 score.py                                         # rebuild the soundtrack only
```

Clips are matched by name (`*DJI_0127*.mp4` etc.), so the original camera files can be dropped in place of the 720p proxies without changing anything — the crop keyframes are fractions of the frame, not pixels.

## Changing the edit

Everything is in the `SHOTS` list at the top of `edit.py`: order, length in beats, source in/out and speed ramp (`time`), reframing keyframes (`crop`), and per-shot correction (`fix`). The score is on the same 100 BPM grid; if the shot lengths change, move the matching hits in `score.py`.
