# Відбір даних для MVP

Аудит 2026-11-14: **208 файлів, 660 259 210 байтів (660,26 MB, 629,67 MiB)**. Повний перелік розмірів і SHA-256: [raw_inventory.json](audit/raw_inventory.json). Оригінали залишаються локально; `.gitignore` виключає їх із поставки. Відповідності команди взято із завдання користувача; Trello безпосередньо не читався. Технологічного стека в репозиторії немає: поставка engine-neutral, JSON + GLB + WebP + ES modules.

| Набір | Група | Рішення й обґрунтування | Кінцевий ресурс |
|---|---|---|---|
| CTX DEM, 90,35 MB | A1 | Вікно 512×512, 20 m; лише 10,24 km навколо посадки | `assets/terrain/heightmap.u16`, `slope.u16`, `traversability.u8`, metadata |
| CTX ortho, 359,60 MB | A1 | Сумістити за координатами, зменшити до 2048² + 1024² LOD | `assets/terrain/ortho*.webp` |
| PLACES tactical + interp | A1/A2 | Перевірити обидві таблиці; з tactical залишити останню позу за sol у ділянці: 211 точок. Це не готовий безпечний маршрут | `data/rover/routes.json` |
| Horizons Mars 2026–2028 | A1/A2 | Додано малий запит Землі з тими ж центром, TDB, площиною, одиницями; виведено відстань і delay | `data/missions/earth_mars_ephemeris.json` |
| MEDA, 10 sols, CSV+XML | A2 | Усі локальні продукти прочитані; вибрані фізичні канали, фізичні фільтри й стани WS. Не кліматологія | `data/rover/weather_samples.json`, `audit/meda_products.json` |
| PSCompPars, 6470 рядків | A2 | Квантили, пропуски, методи виявлення, контроль Кеплера; повні CSV/JSON не публікуються | `audit/population_statistics.json` |
| ExoVista, 2258 систем | A2/A3 | 24744 додатних планет; 42996 нульових слотів відкинуто. Парні anchors + 3 приклади замість усього набору | `data/planets/mass_radius_anchors.json`, `example_systems.json` |
| ExoVista target stars | A1/A3 | 64 напрямки найбільш яскравих цільових зір; не повне зоряне небо | `data/planets/stars.json` |
| SODA/ALMA, 873 диски | A2 | 370 верхніх меж, 503 рядків без прапорця межі. Не фітити розподіл лише за detections, не прирівнювати пил до газу | лише агрегати `audit/population_statistics.json` |
| Інженерні JSON | A1/A2 | Вибрано компоненти, запуск, орбіти, EDL, relay; виправлено перевірені помилки, непідтверджене лишено null | `data/missions/*.json` |
| 25 rover images | A3 | 5 фото різних спостережень, resize/WebP із кредитами; не планетні текстури | `assets/images/` |
| 25 NASA-library previews + JSON | A4 | Дублюють демонстраційну функцію rover photos, залишено в архіві | немає runtime копії |
| NASA Perseverance GLB | A3 | Decode Draco перед вимірами, обережне спрощення, self-contained export | `assets/models/Mars_2020_Perseverance_Rover.glb` |
| NASA MRO GLB | A3 | Візуальний ретранслятор; Draco декодовано для offline GLB | `assets/models/Mars_Reconnaissance_Orbiter.glb` |
| MGS та InSight GLB | A4 | Не потрібні поточному rover/relay сценарію; InSight >22 MB | лише локальний архів |
| MEDA/PLACES SIS PDF | A2 | Прочитані визначення, осі, missing constants, структура продуктів | короткі правила в PHYSICS/SASHA/YURA |
| NASA mission design, CubeSat101, CML PDF | A2 | Зведено launch/space/ground/user сегменти та цикл вимоги→ресурси→перевірка | розділ mission handoff у PHYSICS/YURA |
| formation_priors + hackathon transcript | A2/A4 | Контекст і межі джерел збережені; не історія формування конкретної системи | GENERATION + джерела |
| NGPPS/DACE tracks, full sky, rocket/character meshes | A4 / відсутні | Не завантажені; не підміняти наявність вигаданими ресурсами | конкретні прогалини в інструкціях |

## Виправлення й межі джерел

- EDL `powered_descent.velocity_m_s`: 306 → **85**: оригінал JPL наводить 306 km/h. Peak heating: **75 s**, за launch press kit, p.27.
- 3893 kg у локальному Mars 2020 каталозі не підтверджено його press kit; масу прибрано з operational fields, залишено `null`. Не використовувати для перевірки сумісності ракети. C3 14.49 km²/s² — номінальний профіль у pre-launch press kit p.24, а не виміряна телеметрія інжекції.
- 17410 kg LEO для Atlas V 541 не перепідтверджено конфігураційною кривою першоджерела: runtime поле `null`. Falcon Heavy: NASA KSC підтверджує рекламні 63800 kg LEO і 16800 kg Mars; C3 для цієї цифри відсутній.
- NASA launch press kit p.38 підтверджує пару батарей 26.5 kg і близько 43 Ah кожна. Без напруги та usable-capacity моделі це не 2408 Wh; runtime profiles мають явно ігрові Wh.
- У MEDA є 10 відомих duplicate-name RHS labels і 14 WS aliases; використано номер поля та CSV header, повний журнал в аудиті. Не підмінено одиниці.
- SODA JSON/table дають 503 рядки без upper-limit flag; локальна metadata цитує 502 detections у paper. Розбіжність збережена, не використана як fitted occurrence prior.
- CTX CRS мають різні WKT назви datum, але однакові числові параметри сфери й проєкції. Початки й pixel scale різні: ортофото ~5.0021×5.0023 m, не рівно 5 m. PLACES landing reprojection узгоджується з easting/northing у межах 1 mm.
- 140 із 5623 archive rows мають >20% розбіжності періоду з простим Kepler check. Це composite-table діагностика, не твердження про хибність відкриттів.
