# SETI / DST Hack — participant kit

Неизвестный зашумлённый сигнал. Две команды извлекают evidence, объединяют его через Dempster–Shafer (DST) и принимают решение — в том числе *воздержаться* или передать человеку.

Главный вопрос хака: **какова природа наблюдения при неполных и противоречивых свидетельствах?**  
Расшифровка скрытых структур — необязательный бонус, не цель baseline.

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

Ожидайте: для `example_noise` политика чаще уходит в шум / review / observe; для `example_sine` — согласие детекторов на `signal`.

## Pipeline

```text
observation (.npy)
      ↓
Team A: FFT / PSD / SNR          Team B: autocorr / entropy / periodicity
      ↓                                    ↓
     BPA                                  BPA
      └──────────────┬─────────────────────┘
                     ↓
         majority | mean score | DST
                     ↓
         Bel / Pl / conflict K / m(Θ)
                     ↓
         DECIDE | HUMAN_REVIEW | OBSERVE_MORE
```

## Пространство гипотез (DST)

Бинарный frame:

```text
Θ = {signal, noise}
```

Каждый детектор отдаёт basic probability assignment:

```python
{"signal": 0.60, "noise": 0.15, "unknown": 0.25}  # sum == 1
```

`unknown` — это **m(Θ)** (масса незнания), не третий класс.

Модуль `dst.py`: `validate_bpa`, `belief`, `plausibility`, `conflict`, `combine` (правило Демпстера).

## Две команды

| Команда | Вопрос | Файлы |
|--------|--------|--------|
| **A** | Есть ли физически выделяемый сигнал? | `detectors_a.py` |
| **B** | Есть ли неслучайная структура? | `detectors_b.py` |

Можно менять пороги, добавлять признаки, переписывать отображение score→BPA. Нужно уметь объяснить метод и результат.

## Baseline для сравнения

На одном и том же наборе BPA `decision.py` считает:

1. **majority** — голоса hard-label  
2. **mean score** — среднее BPA  
3. **DST** — комбинация Демпстера  

Плюс простая HITL-политика по `K`, `m(Θ)`, `Bel`.

Имеет смысл искать (и обсуждать) случаи, где majority/mean выглядят «спокойно», а DST подсвечивает высокий конфликт `K` или большое незнание `m(Θ)`. Это не обязано случаться на каждом файле — это исследовательский критерий.

## AI-assisted development

Использование Cursor, ChatGPT и других ИИ-инструментов **разрешено**. Их можно применять для разбора кода, реализации методов, визуализации и проверки гипотез. Команда должна понимать метод и уметь объяснить результат. ИИ — инструмент разработки, не источник ground truth.

## Структура

```text
participant/
├── main.py                 # один прогон
├── detectors_a.py          # спектральные baseline
├── detectors_b.py          # структурные baseline
├── dst.py                  # DST
├── decision.py             # majority / mean / DST + HITL
├── io_utils.py             # load/save .npy (+ json)
├── generator_example.py    # toy noise / sine
├── requirements.txt
├── data/                   # кладите скачанные наблюдения
└── README.md
```

Зависимости: Python 3.10+, NumPy, SciPy, Matplotlib.

## Что сдать по observation

- BPA детекторов (или team means)  
- сравнение majority / mean / DST  
- Bel, Pl, K, m(Θ)  
- действие политики и (если было) решение человека  
- 3–5 предложений обоснования  

Подробные брифинги команд — в материалах мероприятия (`TEAM_A.md` / `TEAM_B.md`), когда их выдаст организатор.
