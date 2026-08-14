# HANDOFF — SETI/DST Hack (public)

Документ для продолжения работы в **другом инстансе Cursor** над публичной частью.

**Дата:** 2026-08-14  
**Repo:** https://github.com/LogMaks/seti-hack-public  
**Pages:** https://logmaks.github.io/seti-hack-public/

Полный organizer-handoff (генератор, GT, playbook, hidden message) живёт **только** в отдельном корне `seti-hack-organizer/` и сюда не копируется.

---

## 1. Суть

Образовательный хак: неизвестный сигнал → детекторы → BPA → DST → Bel/Pl/K → decision / HITL.  
Главная цель — решение при неполных и конфликтных свидетельствах.  
Расшифровка скрытых структур — необязательный бонус, не цель baseline.

---

## 2. Два корня

```text
seti-hack-public/      ← этот репозиторий
seti-hack-organizer/   ← отдельный приватный корень / отдельный git
```

В public нельзя: ground truth, playbook ведущего, plaintext скрытого сообщения, параметры кодирования финала.

---

## 3. Архитектура (зафиксировано)

| Решение | Выбор |
|--------|--------|
| Θ | `{signal, noise}` + `m(Θ)` как ключ `unknown` |
| DST | классический Dempster |
| Baselines | majority · mean BPA · DST |
| HITL | K / m(Θ) / Bel → DECIDE \| HUMAN_REVIEW \| OBSERVE_MORE |
| S2 | объяснимый структурированный сигнал, не третий класс в коде |
| Spectrogram на сайте | не нужен в MVP |
| Конфликт | искать кейс, где majority/mean «спокойны», а DST поднимает K / ведёт в HUMAN_REVIEW — не обещать это на каждом файле |

Порядок выдачи observations: **S0 → S1 → S4 → S3 → S2 → S5**.

---

## 4. Что уже в этом репо

### `participant/`
- `dst.py`, `decision.py`, `detectors_a.py`, `detectors_b.py`
- `io_utils.py`, `generator_example.py` (toy noise/sine)
- `main.py` — HITL только с `--human`

```bash
cd participant
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python generator_example.py
python main.py data/example_noise.npy
python main.py data/example_sine.npy
```

### `website/`
- ARRAY-7 terminal: waveform, download `.npy`, status UNCLASSIFIED
- Деплой Pages: `.github/workflows/pages.yml` (артефакт = папка `website/`)
- Выдача раундов: `website/data/catalog.json` → поле `released`
- `?all=1` — показать все observations

```bash
cd website && python3 -m http.server 8765
```

---

## 5. Следующий приоритет

1. `materials/INTRO.md`, `TEAM_A.md`, `TEAM_B.md`, `DST_CHEATSHEET.md`
2. Перед живым хаком: `released:true` только у текущего раунда
3. После перегенерации в organizer — снова копировать только `obs_s*.npy/json` в `website/data/`
4. Не добавлять FastAPI/Docker/тяжёлые DST-frameworks / Θ из трёх гипотез без отдельного решения

---

## 6. Запреты для public

- plaintext скрытого финального сообщения
- «в S5 спрятано сообщение …»
- ground-truth метки наблюдений
- organizer playbook

---

## 7. Промпт для нового Cursor

```text
Продолжаем SETI/DST Hack.
Сначала прочитай HANDOFF.md в корне seti-hack-public и .cursor/rules если есть.
Public repo: participant + website. Organizer-секреты не выдумывать и не коммитить сюда.
Сейчас нужно: [например materials/INTRO+TEAM_A+TEAM_B+DST_CHEATSHEET].
Не усложнять стек. Отвечай по-русски.
```

---

## 8. Критерий

Participant baseline понятен человеку с базовым Python за ~10 минут.  
Новый файл/абстракция — только если нужны для DST, анализа сигнала или проведения хака.
