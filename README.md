# White Cat — науковий пакет Space Mission Design Game

Готові офлайн дані та інженерні правила для команди. Це data/integration package; game engine/UI не обрано. Первинний локальний архів660.26MB збережено поза Git.

Початок: [SASHA](docs/team/SASHA.md) · [MISHA](docs/team/MISHA.md) · [VANIA](docs/team/VANIA.md) · [PASHA](docs/team/PASHA.md) · [YURA](docs/team/YURA.md).

[Карта файлів](docs/DATA_REFERENCE.md) · [Відбір і виправлення](docs/DATA_SELECTION.md) · [Формули](docs/PHYSICS.md) · [Генератор](docs/GENERATION.md) · [Фактична валідація](docs/VALIDATION.md).

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r tools/requirements-lock.txt
npm ci --prefix tools
python tools/validate_package.py
node --test tests/runtime.test.mjs
python -m http.server 8765 --bind 127.0.0.1
# http://127.0.0.1:8765/examples/integration.html
```

Для читання JSON/GLB/WebP браузером Python scientific dependencies не потрібні; вони потрібні для підготовки/повної валідації. JS runtime modules не мають npm dependencies. Детальна інструкція повторного оброблення оригіналів — YURA.md; великі originals і додатковий Earth API response не входять у clone.

Усе з game/synthetic badge є моделлю/припущенням, не вимірюванням. Невідомі характеристики `null`, одиниці в SI або в назві поля, engine-neutral right-handed axes. NASA/PDS/USGS/партнерські джерела і credits збережено. Redistribution of third-party material не змінює його авторських прав; attribution див. `data/sources.json` та manifests. Власні скрипти й технічні нотатки підготовлені для White Cat; жодної нової ліцензії на репозиторій не нав’язано.
