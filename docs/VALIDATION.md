# Фактична перевірка

Дата: 2026-11-14. Середовище: Python3.12.15, Node26.13.1, rasterio1.5.2/GDAL, pyproj3.8.0, Pillow12.3.0, jsonschema4.26.0. Точні Python/npm dependencies зафіксовано lock-файлами. CI налаштовано на Python3.12 і Node22; його результат оцінювати окремо від локальних запусків.

## Виконані автоматичні перевірки

`python tools/validate_package.py` — **11/11 passed локально**, без skipped checks:

- 24 JSON ресурси перевірено конкретними JSON Schema2020-12; NaN/Infinity заборонено.
- 31 числовий приклад повторно обчислено; незалежні rounded-reference checks для Earth gravity, Hohmann time/C3, AU light-time.
- 64 парні mass/radius anchors, густини, межі типів і суми атмосферних mole fractions.
- Height PNG відповідає uint16 binary; розміри binary, маски, край grid, nodata та vertical datum перевірені.
- Forward/inverse CRS для всіх211 PLACES points; NED→scene handedness; фактичний початок карти й pixel/world mapping.
- 733 одночасні Earth/Mars TDB epochs, step1day, distance Euclidean й delay=d/c.
- Усі PNG/WebP відкрито,5 gallery credits перевірено, embedded images обох GLB декодовано Pillow (max1024px).
- Source IDs, resource paths і відсутність локальних абсолютних runtime paths.
- Regression для EDL85m/s, unknown launch performance/mass, battery43Ah vs unknown usable Wh та instrument IDs.
- SHA-256/bytes усіх release files, виключення TIFF/gzip/PDF та budget<20MB.
- Додаткова **локальна** перевірка чотирьох точок DEM: height quantization error<=0.01m, slope quantization<=0.005°. У чистому clone originals немає, тому тільки цей тест має skip; решта10 виконуються офлайн.

`node --test tests/runtime.test.mjs` — **15/15 passed**:

- Golden xorshift32, seed0 mapping, invalid seed rejection, repeatability і seed2026 fixture.
- **1000 seed0..999 без generation failures**: mass/radius/density/gravity/orbital period consistency, stellar exclusion, eccentricity/orbit/rotation limits, mutual Hill clearance.
- Бounded failure без прихованого зменшення planet count; Kepler ellipse closure/apsides; synchronous/retrograde day.
- Ephemeris delay та заборона extrapolation; little-endian binary decoding.
- Terrain sampling усіх211 points; поза bounds/nodata block; незалежний flat-route energy budget; caution/slope/empty battery failure.
- Data overflow/empty downlink і battery curtailment/unserved load.
- **Справжнє декодування геометрії обох GLB** через NodeIO: finite positions, triangle counts, embedded resources, відсутність Draco requirement.

Перший GitHub CI запуск на Node22 виявив1-ULP відмінності Math.pow/cbrt проти Node26 у збереженому прикладі. Fixture regression порівнює фізичні floats із relative tolerance1e-12; структура, ID, integer seed/RNG та повторний запуск у тому самому engine перевіряються точно. Це узгоджує тест із задокументованим числовим контрактом, без послаблення фізичних інваріантів.

## Браузер і візуальна перевірка

`examples/integration.html` відкрито в Codex In-app Browser через локальний static HTTP, порт8766 (8765 був зайнятий). Сторінка показала PASS: JSON fetch, binary terrain,211 PLACES waypoints,3 планети seed2026,5 WebP image decodes та2 GLB headers. На старті кешу one-way geometric delay≈660.9002s. Це не hardware measurement і не validated retarded light-time.

Візуально переглянуто CTX crop, passability proxy й contact sheet усіх25 оригінальних фотографій. Після перегляду залишено5 корисних кадрів: Mastcam-Z sol800,Navcam-right sol800,Hazcam-left sol1000,WATSON sol1800,PIXL sol2000; blurred/калібрувальні/дубльовані кадри не включено. Ортофото grayscale, без вигаданого кольору; карта похилів не претендує на wheel-scale hazards.

Browser smoke перевіряє fetch і media decode; **повне 3D-відображення, анімації, engine performance і controller не тестувались**, бо game stack у репозиторії відсутній. GLB geometry/material-image loading перевірене окремим reader. Тести не доводять довготривалої N-body stability чи безпечної реальної навігації.

## Перевірка джерел та обмежень

Переглянуто локальні PDS XML/SIS, NASA mission-design/CML/CubeSat матеріали, онлайн JPL constants/planet parameters/Horizons docs, NASA rover/instrument/relay pages, NASA KSC launcher reference і NASA/JPL launch press kit. Додано733-epoch Earth request, без великого догрузу наукових архівів. Додатковий launch press-kit PDF лишився в локальному preparation cache.

Не оголошено перевіреними відсутні C3 curves, arbitrary-mass EDL, usable battery Wh, точний rocket core CAD, повне Night Sky, soil traction чи team approval трьох профілів. Це конкретні прогалини, збережені в DATA_SELECTION та персональних інструкціях. Runtime не виконує API calls і не потребує raw archive; offline operation перевірено залежностями від локальних ресурсів.
