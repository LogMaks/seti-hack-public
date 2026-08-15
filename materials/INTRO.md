# SETI / DST Hack — введение

Два слоя. Сдают оба по желанию, **обязателен только первый**.

**1. Основное — легко.** Это сигнал или шум? Шесть детекторов снимают evidence. Числа сливают через Dempster–Shafer. Решает **сама команда**. Внешнего судьи нет.

**2. Бонус — зашифрованный текст.** В потоке может быть закодированный фрагмент. Найти и прочитать — плюс, не замена baseline. Где лежит и как закодировано — часть задачи, подсказок нет.

На живом хаке соревнуются две группы. Kit один: одна команда в коде, шесть источников.

## Откуда данные

Станция [ARRAY-7](https://logmaks.github.io/seti-hack-public/) показывает waveform и отдаёт `.npy`.  
Анализ — только локально, в `participant/`. Сайт ничего не классифицирует.

Брифинги на станции: [Intro](https://logmaks.github.io/seti-hack-public/docs.html) · [Detectors](https://logmaks.github.io/seti-hack-public/docs.html#detectors) · [DST](https://logmaks.github.io/seti-hack-public/docs.html#dst).  
Зал: [briefing.html](https://logmaks.github.io/seti-hack-public/briefing.html).

Положите скачанный файл в `participant/data/` и запустите:

```bash
cd participant
python main.py data/obs_s0.npy
```

Порядок раундов задаёт организатор (не алфавит ID).

## Что считать ответом (канон)

1. Шесть детекторов независимо получают BPA.  
2. **Канон:** Dempster на всех шести BPA.  
3. Рядом считаются majority и mean — чтобы сравнить, не чтобы заменить DST.

Сдавать по раунду: BPA шести детекторов, majority / mean / DST, Bel, Pl, K, m(Θ), действие политики, вердикт команды, 3–5 предложений «почему».  
Бонус отдельно: если нашли текст — что прочитали и как, без обязаловки.

## Политика

| Действие | Смысл |
|----------|--------|
| `DECIDE` | baseline предлагает метку — команда может согласиться |
| `HUMAN_REVIEW` | высокий K или большое m(Θ); автомат не решает, команда пишет вердикт. При K→1 комбинация **отказана**, не «упала» |
| `OBSERVE_MORE` | слабо / ничья — ждать следующий раунд, отдельного API нет |

Пороги в `decision.py` можно менять, выбор нужно защитить.

## ИИ

Cursor и другие ИИ **разрешены**. Команда должна понимать метод и объяснить результат. ИИ — не ground truth.

Дальше на станции: [Detectors](https://logmaks.github.io/seti-hack-public/docs.html#detectors), [DST](https://logmaks.github.io/seti-hack-public/docs.html#dst).
