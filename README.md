# seti-hack-public

Публичные материалы образовательного хака (анализ неизвестного сигнала + DST + HITL).

**Станция ARRAY-7 (GitHub Pages):** https://logmaks.github.io/seti-hack-public/

```text
seti-hack-public/
├── participant/     # Python baseline
├── website/         # ARRAY-7 observation terminal (static)
└── materials/       # INTRO, TEAM_A/B, DST cheatsheet
```

## Participant

```bash
cd participant
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python generator_example.py
python main.py data/example_noise.npy
python main.py data/example_sine.npy
```

## Website (локально)

```bash
cd website
python3 -m http.server 8765
# http://127.0.0.1:8765/
```

Сайт только показывает waveform и отдаёт `.npy`. Анализ — в `participant/`.

Брифинги: [`website/docs.html`](website/docs.html) (после деплоя — `/docs.html`).  
Зал: [`website/briefing.html`](website/briefing.html).

Организаторские сценарии и ground truth живут в **отдельном** корне и сюда не входят.

Контекст для продолжения в другом Cursor: [`HANDOFF.md`](HANDOFF.md).
