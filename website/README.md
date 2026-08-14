# ARRAY-7 Listening Post

Статический observation terminal. Без backend и без анализа сигнала.

```bash
python3 -m http.server 8765
```

Открыть [http://127.0.0.1:8765/](http://127.0.0.1:8765/).

## Управление выдачей

В `data/catalog.json` поле `released` у каждого observation.  
Перед живым хаком оставьте `true` только у текущего раунда.

`?all=1` в URL показывает все записи (для отладки).

## Данные

После перегенерации в organizer скопируйте сюда только:

```text
obs_s*.npy
obs_s*.json
```

Не копировать `ground_truth.yaml` / manifests / secrets.
