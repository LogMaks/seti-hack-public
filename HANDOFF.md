# HANDOFF — SETI/DST Hack (public)

Документ для продолжения работы в **другом инстансе Cursor** над публичной частью.

**Дата:** 2026-08-14  
**Repo:** https://github.com/LogMaks/seti-hack-public  
**Pages:** https://logmaks.github.io/seti-hack-public/

Полный organizer-handoff (генератор, GT, playbook, hidden message) живёт **только** в отдельном корне `seti-hack-organizer/` и сюда не копируется.

---

## 1. Суть

Образовательный хак в два слоя: (1) сигнал или шум, DST, решение команд; (2) бонус — зашифрованный текст в потоке.  
Внешнего судьи нет. В public нельзя писать plaintext и «где / как закодировано».

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
| Политика | K / m(Θ) / Bel → DECIDE \| HUMAN_REVIEW (спор команд) \| OBSERVE_MORE |
| Канон | DST на team-mean A vs B; все 6 детекторов — диагностика |
| K→1 | комбинация отказана → HUMAN_REVIEW (вердикт команд), не traceback |
| S2 | объяснимый структурированный сигнал, не третий класс в коде |
| Spectrogram на сайте | не нужен в MVP |
| Конфликт | искать кейс, где majority/mean «спокойны», а DST поднимает K / ведёт в HUMAN_REVIEW — не обещать это на каждом файле |

Порядок выдачи observations: **S0 → S1 → S4 → S3 → S2 → S5**.

---

## 4. Что уже в этом репо

### `participant/`
- `dst.py`, `decision.py`, `detectors_a.py`, `detectors_b.py`
- `io_utils.py`, `generator_example.py` (toy noise/sine)
- `main.py` — вердикт команд через `--human`

```bash
cd participant
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python generator_example.py
python main.py data/example_noise.npy
python main.py data/example_sine.npy
```

### `website/`
- ARRAY-7: waveform, Listen to source, download `.npy`, docs, briefing
- Pages: `.github/workflows/pages.yml` (артефакт = `website/`)
- `released` прячет пункт в UI, **не** прячет файл. Живой хак: не пушить будущие `.npy`
- `?all=1` — отладка организатора

### `materials/`
- `INTRO.md`, `TEAM_A.md`, `TEAM_B.md`, `DST_CHEATSHEET.md`

```bash
cd website && python3 -m http.server 8765
```

---

## 5. Следующий приоритет

1. Перед живым хаком: не держать будущие `obs_s*.npy` в Pages; `released:true` только у текущего раунда
2. Pre-flight: `main.py` на каждом obs — найти хотя бы один кейс «majority спокоен, DST поднимает K»
3. После перегенерации в organizer — копировать в `website/data/` только public `obs_s*`
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
Сейчас нужно: [например pre-flight baseline на всех obs / процедура выдачи раундов].
Не усложнять стек. Отвечай по-русски.
```

---

## 8. Критерий

Participant baseline понятен человеку с базовым Python за ~10 минут.  
Новый файл/абстракция — только если нужны для DST, анализа сигнала или проведения хака.
