# SETI / DST Hack — введение

Неизвестный зашумлённый сигнал. Две команды собирают evidence, сливают его через Dempster–Shafer и решают: принять гипотезу, воздержаться или отдать человеку.

Главный вопрос: **какова природа наблюдения при неполных и конфликтных свидетельствах?**  
Расшифровка скрытых структур — необязательный бонус, не цель baseline.

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

Сдавать: BPA (или team means), majority / mean / DST, Bel, Pl, K, m(Θ), действие политики, если было — решение человека, 3–5 предложений «почему».

## Политика

| Действие | Смысл |
|----------|--------|
| `DECIDE` | достаточно Bel, конфликт невысокий |
| `HUMAN_REVIEW` | высокий K или большое m(Θ); при K→1 комбинация **отказана**, не «упала» |
| `OBSERVE_MORE` | слабо / ничья — ждать следующий раунд, отдельного API нет |

Пороги в `decision.py` можно менять, выбор нужно защитить.

## ИИ

Cursor и другие ИИ **разрешены**. Команда должна понимать метод и объяснить результат. ИИ — не ground truth.

Дальше на станции: [Team A](https://logmaks.github.io/seti-hack-public/docs.html#team-a), [Team B](https://logmaks.github.io/seti-hack-public/docs.html#team-b), [DST](https://logmaks.github.io/seti-hack-public/docs.html#dst).
