# ARRAY-7 Listening Post

Статический observation terminal. Без backend и без анализа сигнала.

```bash
python3 -m http.server 8765
```

Открыть [http://127.0.0.1:8765/](http://127.0.0.1:8765/).  
Listen to source — крутит текущий `.npy` как звук (тот же waveform, цикл, курсор на осциллографе).

Брифинг для зала: открыть `briefing.html` (стрелки / пробел, `F` — полный экран).  
Desk notes: `docs.html` — Intro / Detectors / DST.

## Выдача раундов

`released` в `data/catalog.json` только прячет пункт в UI. Это **не** контроль доступа: файл в `data/` открывается по URL и живёт в git.

`?all=1` — отладка организатора, не секретность.

Перед живым хаком:

1. Не коммитить будущие `obs_s*.npy` / `.json`, пока раунд не открыт.  
2. `released: true` только у текущего раунда.  
3. После перегенерации в organizer копировать сюда только public `obs_s*` — без GT и playbook.

Порядок: S0 → S1 → S4 → S3 → S2 → S5.
