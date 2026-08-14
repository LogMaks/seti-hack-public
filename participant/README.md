# SETI / DST Hack — participant kit

Неизвестный зашумлённый сигнал. Две команды извлекают evidence, сливают через Dempster–Shafer и решают — в том числе воздержаться или отдать человеку.

Главный вопрос: **какова природа наблюдения при неполных и противоречивых свидетельствах?**  
Расшифровка скрытых структур — бонус, не цель baseline.

## Быстрый старт (~10 минут)

```bash
cd participant
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python generator_example.py
python main.py data/example_noise.npy
python main.py data/example_sine.npy
```

Брифинги: [`../materials/INTRO.md`](../materials/INTRO.md).

## Канон

Θ = {signal, noise}. `unknown` в BPA — это **m(Θ)**, не третий класс.

1. Team A / Team B → свои BPA (`detectors_a.py` / `detectors_b.py`).  
2. Внутри команды — mean BPA.  
3. **Сдача:** majority · mean · DST на двух team means (A vs B), плюс Bel / Pl / K / политика.  
4. Все 6 детекторов в выводе `main.py` — диагностика.

При K → 1 комбинация отказана, политика → `HUMAN_REVIEW` (не traceback).  
`max K` — максимум последовательных pairwise K, учебный прокси.

Ищите случаи, где majority/mean спокойны, а DST поднимает K — не на каждом файле.

## Pipeline

```text
.npy → A: SNR/FFT/band     B: autocorr/entropy/periodicity
         BPA                      BPA
              mean A  +  mean B  →  majority | mean | DST
                                  Bel / Pl / K / m(Θ)
                                  DECIDE | HUMAN_REVIEW | OBSERVE_MORE
```

`OBSERVE_MORE` = ждать следующий раунд, отдельного API нет. HITL: `python main.py FILE --human`.

Пороги, признаки, score→BPA можно менять; метод нужно объяснить. ИИ разрешён, ground truth не выдаёт.

Зависимости: Python 3.10+, NumPy, SciPy, Matplotlib. Скачанные наблюдения — в `data/`.
