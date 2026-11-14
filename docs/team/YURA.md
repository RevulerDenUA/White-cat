# YURA — дані, API й інтеграція

Головна карта — `docs/DATA_REFERENCE.md`; manifest із розмірами/SHA-256 — `data/package_manifest.json`; усі першоджерела — `data/sources.json`; schema mapping — `schemas/index.json`. Усі runtime paths відносні до package root. Original archive paths у `docs/audit/raw_inventory.json` — аудит, їх не завантажувати браузером. Реалізація всієї гри в цій гілці не створюється.

Стек репозиторію ще не визначено: клієнт читає JSON через `fetch`, uint16 binary через DataView little-endian, GLB через свій GLTF loader, WebP через image loader. SQLite/SQL-server не потрібен. `lib/load.mjs` приймає base URL, підтримує subdirectory deployment. `examples/integration.html` — перевірка integration, не game screen.

```js
import {loadJSON} from '../lib/load.mjs';
const base=new URL('../',import.meta.url);
const specs=await loadJSON(base,'data/rover/rover_specs.json');
console.log(specs.profiles.find(x=>x.id==='science').battery_capacity_wh); // 2400, game
```

Локально: `python -m http.server 8765 --bind 127.0.0.1`,відкрити `http://127.0.0.1:8765/examples/integration.html`. Це HTTP static files; file:// не гарантує ES modules/fetch. Жоден runtime module не звертається до NASA чи CDN.

## Оновлення й відтворення

1. Залиш originals у локальних шляхах з inventory, перевір checksum та реліз. JSON export не є raw authoritative PDS label.
2. Python3.12 venv, `pip install -r tools/requirements.txt`. Node>=22, `npm ci --prefix tools`. `tools/requirements-lock.txt` містить конкретні перевірені Python versions; для точного середовища використовуй його.
3. Лише за потреби Earth API cache: `python tools/fetch_ephemeris.py`;запит399,центр500@10,TDB,Ecliptic J2000,GEOMETRIC,AU-D,1day,2026-11-14..2028-11-15. Повторний fetch — окреме джерельне оновлення. Початковий Mars cache потрібен локально; в package є compact derived ephemeris.
4. `python tools/prepare_data.py`, `python tools/build_catalogs.py`, `node tools/prepare_models.mjs`, `python tools/build_docs.py`, `node tools/create_example.mjs`. Config tuning — `tools/package_config.json`,artist specs — `tools/authoring_specs.json`.
5. Схеми не перебудовувати автоматично при кожній зміні даних: це контракт. Зміна контракту — свідоме редагування schemas/stream_version та відповідного reader. Для первинного створення є `tools/create_schemas.py`.
6. `python tools/validate_package.py` та `node --test tests/runtime.test.mjs`, після зміни binary/model — перевірити browser smoke. `python tools/finalize_manifest.py` перед commit, потім final validation. Не staging усіх data/: лише whitelist через `.gitignore` й manifest.

Вихідні660.26MB у Git не входять. `prepare_data` читає растр вікнами; slope із source halo, ortho reproject на ті самі bounds, heights квантуються до0.02m (помилка<=0.01m), WebP lossy. PLACES lat/lon->CRS->world, не запозичені чужі map pixels. Weather перераховано CSV+XML, фізичні screens і stable WS states, не «середній клімат». Моделі Draco-decode->small simplification->embedded GLB; material consolidation/engine FPS поза перевірками пакета.

## API та офлайн заміни

| API/джерело | Для чого | Офлайн |
|---|---|---|
| NASA Exoplanet TAP | новий snapshot статистики | compact stats + joint anchors; не runtime query|
| JPL Horizons | planetary states,звірка units/center/frame | earth_mars_ephemeris.json,strict bounds|
| NASA PDS PLACES/MEDA | новий реліз координат/калібрувань | routes/weather_samples,source label aliases audit|
| NASA Raw Images | нові gallery images |5 WebP + credits manifest|
| NASA3D/USGS | нові models/maps |готовіGLB/terrain; original hashes audit|

Залежності: VANIA →constants/anchors/config →PASHA orbit/UI; MISHA →model specs/manifest →SASHA collider; SASHA →terrain/routes/profiles →power/data budget; mission UI →launch/EDL/relay +source status. З Trello використані тільки призначення, надані користувачем, актуальну дошку незалежно не синхронізовано.

Для презентації: NASA Exoplanet Archive (observed outcomes),NASA EMAC ExoVista (synthetic architecture),USGS CTX,PDS PLACES/MEDA,NASA instrument/rover pages,JPL mission press kit. SODA —ALMA/CDS partner paper, не NASA; credits/URL не прибирати. Не називати гру схваленою NASA. Challenge transcript користувача не є архівованою офіційною HTML-сторінкою.

Відомі прогалини: немає повного зоряного каталогу/formation tracks,погоджених трьох модифікацій,детального rocket CAD/character mesh,C3 payload curves,usable Wh реальної батареї,validated arbitrary-mass EDL. MVP використовує названі припущення й indeterminate там, де даних бракує. Конкретні тести й обсяг пакета — `docs/VALIDATION.md` та package manifest.
