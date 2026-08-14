# Observation data

Put downloaded observations here (from the station website or organizer handout).

Expected files per observation:

- `obs_XX.npy` — waveform (`float` array)
- `obs_XX.json` — optional public metadata (`id`, `fs`, `round`, …)

No ground-truth labels are provided.

Generate local toys:

```bash
python generator_example.py
```
