# seti-hack-public

Публичные материалы образовательного хака (анализ неизвестного сигнала + DST + HITL).

```text
seti-hack-public/
├── participant/     # Python baseline
└── website/         # ARRAY-7 observation terminal (static)
```

## Participant

```bash
cd participant
pip install -r requirements.txt
python generator_example.py
python main.py data/example_noise.npy
python main.py data/example_sine.npy
```

## Website

```bash
cd website
python3 -m http.server 8765
# http://127.0.0.1:8765/
```

Сайт только показывает waveform и отдаёт `.npy`. Анализ — в `participant/`.

Организаторские сценарии и ground truth — в отдельном корне `seti-hack-organizer/` (не здесь).

Полный контекст для продолжения разработки: корневой `HANDOFF.md`.
