# SETI / DST Hack — participant kit

Неизвестный сигнал. **Основное:** это сигнал или шум? Шесть детекторов дают evidence, DST сливает, команда решает.

**Бонус:** в потоке может быть зашифрованный текст. Найти и прочитать — плюс, не замена сдачи.

## Быстрый старт (~10 минут)

```bash
cd participant
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python generator_example.py
python main.py data/example_noise.npy
python main.py data/example_sine.npy
python main.py data/example_sine.npy --plot
```

Брифинги: [станция /docs.html](https://logmaks.github.io/seti-hack-public/docs.html) или [`../materials/INTRO.md`](../materials/INTRO.md).
Таблица раундов: [Rounds](https://logmaks.github.io/seti-hack-public/scoreboard.html).

## Канон

Θ = {signal, noise}. `unknown` в BPA — это **m(Θ)**, не третий класс.

1. Шесть детекторов → шесть BPA (`detectors.py`).  
2. **Сдача:** majority · mean · DST на этих шести BPA, плюс Bel / Pl / K / политика.  
3. Команда одна. Соревнуются две группы на живом хаке — kit у обеих одинаковый.

При K → 1 комбинация отказана, политика → `HUMAN_REVIEW`: автомат молчит, вердикт пишет команда (не traceback).  
`max K` — максимум последовательных pairwise K, учебный прокси.

Ищите случаи, где majority/mean спокойны, а DST поднимает K — не на каждом файле.

## Pipeline

```text
.npy → 6 detectors → 6 BPA
              majority | mean | DST
              Bel / Pl / K / m(Θ)
              DECIDE | HUMAN_REVIEW | OBSERVE_MORE
```

`OBSERVE_MORE` = ждать следующий раунд. `HUMAN_REVIEW` = команда пишет вердикт, не внешний эксперт. Вердикт: `python main.py FILE --human`.  
Графики BPA и Bel/K после отчёта: `python main.py FILE --plot`.

Бонус (если дошли до структуры в потоке): несущую берут из спектра (`--f0`), длину символа часто ищут так:

```bash
python decode_bonus.py data/obs_s5.npy --f0 YOUR_HZ --scan-spb
python decode_bonus.py data/obs_s5.npy --f0 YOUR_HZ --spb YOUR_SPB
```

`--scan-spb` перебирает длины с целым числом периодов несущей на бит — типичный затык на хаке.

Пороги, признаки, score→BPA можно менять; метод нужно объяснить. ИИ разрешён, ground truth не выдаёт.

Зависимости: Python 3.10+, NumPy, SciPy, Matplotlib. Скачанные наблюдения — в `data/`.
