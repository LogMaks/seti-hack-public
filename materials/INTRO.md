# SETI / DST Hack — введение

Два слоя. Сдают оба по желанию, **обязателен только первый**.

**1. Основное — легко.** Это сигнал или шум? Команда A смотрит спектр, команда B — структуру. Числа сливают через Dempster–Shafer. Решают **сами команды**. Внешнего судьи нет.

**2. Бонус — зашифрованный текст.** В потоке может быть закодированный фрагмент. Найти и прочитать — плюс, не замена baseline. Где лежит и как закодировано — часть задачи, подсказок нет.

## Откуда данные

Станция [ARRAY-7](https://logmaks.github.io/seti-hack-public/) показывает waveform и отдаёт `.npy`.  
Анализ — только локально, в `participant/`. Сайт ничего не классифицирует.

Брифинги на станции: [Intro](https://logmaks.github.io/seti-hack-public/docs.html) · [Team A](https://logmaks.github.io/seti-hack-public/docs.html#team-a) · [Team B](https://logmaks.github.io/seti-hack-public/docs.html#team-b) · [DST](https://logmaks.github.io/seti-hack-public/docs.html#dst).  
Зал: [briefing.html](https://logmaks.github.io/seti-hack-public/briefing.html).

Положите скачанный файл в `participant/data/` и запустите:

```bash
cd participant
python main.py data/obs_s0.npy
```

Порядок раундов задаёт организатор (не алфавит ID).

## Что считать ответом (канон)

1. Team A и Team B независимо получают BPA детекторов.  
2. Внутри команды — среднее BPA (`mean`, это не DST).  
3. **Канон:** Dempster на двух team means (A vs B).  
4. Рядом считаются majority и mean — чтобы сравнить, не чтобы заменить DST.  
5. Прогон по всем 6 детекторам — диагностика, не сдача.

Сдавать по раунду: BPA (или team means), majority / mean / DST, Bel, Pl, K, m(Θ), действие политики, вердикт команд, 3–5 предложений «почему».  
Бонус отдельно: если нашли текст — что прочитали и как, без обязаловки.

## Политика

| Действие | Смысл |
|----------|--------|
| `DECIDE` | baseline предлагает метку — команда может согласиться |
| `HUMAN_REVIEW` | спор A vs B: высокий K или большое m(Θ); автомат не решает, команды пишут вердикт. При K→1 комбинация **отказана**, не «упала» |
| `OBSERVE_MORE` | слабо / ничья — ждать следующий раунд, отдельного API нет |

Пороги в `decision.py` можно менять, выбор нужно защитить.

## ИИ

Cursor и другие ИИ **разрешены**. Команда должна понимать метод и объяснить результат. ИИ — не ground truth.

Дальше на станции: [Team A](https://logmaks.github.io/seti-hack-public/docs.html#team-a), [Team B](https://logmaks.github.io/seti-hack-public/docs.html#team-b), [DST](https://logmaks.github.io/seti-hack-public/docs.html#dst).
