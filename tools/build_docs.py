"""Generate concise Ukrainian handoff documentation and a runtime source registry."""
from pathlib import Path
import json
from prepare_data import ROOT, read, write

def doc(path,text):
    p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.strip()+'\n')

def sources():
    original=read('.local/original_sources.json') if (ROOT/'.local/original_sources.json').exists() else read('data/sources.json')
    records=[]
    for s in original['sources']:
        item=dict(s)
        if 'products' in item:item['local_archive_products']=item.pop('products')
        item['provenance_scope']='source/archive reference; local_archive_products are audit paths, not runtime dependencies'
        records.append(item)
    extras=[('nasa_mars_facts','NASA NSSDCA','https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html'),('jpl_parameters','NASA/JPL SSD','https://ssd.jpl.nasa.gov/astro_par.html'),('jpl_planet_parameters','NASA/JPL SSD','https://ssd.jpl.nasa.gov/planets/phys_par.html'),('horizons_api','NASA/JPL SSD','https://ssd-api.jpl.nasa.gov/doc/horizons.html'),('nasa_lsp_falcon','NASA KSC','https://public.ksc.nasa.gov/lspeducation/spacex/'),('nasa_archive_definitions','NASA Exoplanet Archive','https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html')]
    ids={s['id'] for s in records}
    for id,organization,url in extras:
        if id not in ids:records.append({'id':id,'organization':organization,'url':url})
    write('data/sources.json',{'schema_version':'1.0','generated_utc':'2026-11-14','source_policy':'Observed, synthetic, derived and game assumptions are distinguished in each product. Snapshot values are not live service guarantees.','sources':records})

def selection():
    stats=read('docs/audit/population_statistics.json');geo=read('docs/audit/geospatial.json')
    doc('docs/DATA_SELECTION.md',f'''# Відбір даних для MVP

Аудит 2026-11-14: **208 файлів, 660 259 210 байтів (660,26 MB, 629,67 MiB)**. Повний перелік розмірів і SHA-256: [raw_inventory.json](audit/raw_inventory.json). Оригінали залишаються локально; `.gitignore` виключає їх із поставки. Відповідності команди взято із завдання користувача; Trello безпосередньо не читався. Технологічного стека в репозиторії немає: поставка engine-neutral, JSON + GLB + WebP + ES modules.

| Набір | Група | Рішення й обґрунтування | Кінцевий ресурс |
|---|---|---|---|
| CTX DEM, 90,35 MB | A1 | Вікно 512×512, 20 m; лише 10,24 km навколо посадки | `assets/terrain/heightmap.u16`, `slope.u16`, `traversability.u8`, metadata |
| CTX ortho, 359,60 MB | A1 | Сумістити за координатами, зменшити до 2048² + 1024² LOD | `assets/terrain/ortho*.webp` |
| PLACES tactical + interp | A1/A2 | Перевірити обидві таблиці; з tactical залишити останню позу за sol у ділянці: {geo['retained_waypoints']} точок. Це не готовий безпечний маршрут | `data/rover/routes.json` |
| Horizons Mars 2026–2028 | A1/A2 | Додано малий запит Землі з тими ж центром, TDB, площиною, одиницями; виведено відстань і delay | `data/missions/earth_mars_ephemeris.json` |
| MEDA, 10 sols, CSV+XML | A2 | Усі локальні продукти прочитані; вибрані фізичні канали, фізичні фільтри й стани WS. Не кліматологія | `data/rover/weather_samples.json`, `audit/meda_products.json` |
| PSCompPars, {stats['archive_rows']} рядків | A2 | Квантили, пропуски, методи виявлення, контроль Кеплера; повні CSV/JSON не публікуються | `audit/population_statistics.json` |
| ExoVista, {stats['exovista']['systems']} систем | A2/A3 | {stats['exovista']['planets']} додатних планет; {stats['exovista']['zero_padding_slots_removed']} нульових слотів відкинуто. Парні anchors + 3 приклади замість усього набору | `data/planets/mass_radius_anchors.json`, `example_systems.json` |
| ExoVista target stars | A1/A3 | 64 напрямки найбільш яскравих цільових зір; не повне зоряне небо | `data/planets/stars.json` |
| SODA/ALMA, 873 диски | A2 | {stats['soda']['dust_upper_limits']} верхніх меж, {stats['soda']['dust_detections']} рядків без прапорця межі. Не фітити розподіл лише за detections, не прирівнювати пил до газу | лише агрегати `audit/population_statistics.json` |
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
- {stats['kepler_consistency']['relative_period_discrepancy_gt_20_percent']} із {stats['kepler_consistency']['tested']} archive rows мають >20% розбіжності періоду з простим Kepler check. Це composite-table діагностика, не твердження про хибність відкриттів.
''')

def physics():
    fs=read('data/physics/formulas.json')['formulas']
    intro='''# Фізика та ресурсні моделі

Обчислення у SI. `physical_constants.json` зберігає значення, одиниці, статус і URL; `formulas.json` — машинні аргументи й результати прикладів. Усі приклади нижче синтетичні обчислення, не вимірювання NASA. Реалізація для перевірки: `tools/science.py`; browser helper: `lib/science.mjs`. `null` означає «невідоме/не застосовується», не нуль.

## Математичне походження та застосування

Гравітація виводиться із F=GmM/R² та F=mg; густина й маса — з об’єму сфери. Для орбіт: збереження питомої енергії v²/2−μ/r=−μ/(2a) дає vis-viva; круговий баланс v²/r=μ/r² разом із кеплеровою геометрією дає період. Hohmann — півеліпс із a=(r1+r2)/2; C3 — квадрат різниці швидкостей апарата та планети на відльоті. Для двотільних задач μ=G(M+m); для Марса брати published body GM, а не system GM.

Обертання: ω=2π/P, v=ωR; breakup — рівність відцентрового й гравітаційного прискорень. Сонячна доба — обернена різниця знакових частот. Потік — світність на площу сфери; T_eq — баланс поглинання πR²S(1−A) і випромінювання 4πR²εσT⁴. T_eq не дорівнює температурі поверхні. Для атмосфери dp/dz=−ρg разом із p=ρR_gasT/M_mol дає H та експоненційний тиск; формули не прогнозують сам склад атмосфери.

Рух ровера — проєкція сили тяжіння плюс опір коченню та ma. Енергія — додатна механічна робота/ККД плюс допоміжна потужність×час. Кочення, ККД, idle/drive power в профілях — балансувальні параметри. Батарея інтегрує різницю генерації й усіх навантажень з різними ККД заряду/розряду; unserved energy явно блокує дію. Оптичні/радіо формули: геометричний delay=d/c, Friis — розходження потоку між антенами; без шуму й coding gain bitrate з нього не отримати. Drag — визначення коефіцієнта опору через dynamic pressure. Рівняння ракети походить з інтегрування збереження імпульсу для сталого Isp. Hill spacing — аналітична локальна оцінка, застосована як евристика.

Первинні довідники: [JPL константи](https://ssd.jpl.nasa.gov/astro_par.html), [JPL тіла](https://ssd.jpl.nasa.gov/planets/phys_par.html), [NIST SI](https://physics.nist.gov/cuu/Constants/), [Horizons](https://ssd.jpl.nasa.gov/horizons/manual.html). Решта формул має наведене тут математичне виведення; коефіцієнти ігрових моделей не оголошено емпіричним fit.

## Формули з усіма SI-аргументами
'''
    sections=[]
    for f in fs:
        args='; '.join(f'`{k}` — {v["meaning_uk"]}, {v["unit"]}' for k,v in f['variables'].items())
        inp=', '.join(f'{k}={v:.9g}' for k,v in f['example']['inputs'].items())
        sections.append(f'### `{f["id"]}` — {f["purpose_uk"]}\n\n`{f["expression"]}` → **{f["output_unit"]}**. {args}.\n\nПриклад: {inp} → **{f["example"]["expected"]:.9g} {f["output_unit"]}**. Межі: {f["domain_and_limits_uk"]}\n')
    ending='''
## Як зібрати місію

Моделюйте launch → cruise → EDL → surface → relay/ground → scientific return, а не лише rover mass. У budget слоти мають бути неперекривними. Наприклад, 1500 kg dry platform + 500 kg science + 700 kg propellant + 100 kg adapter = 2800 kg; це навчальний приклад. До маси цілого Perseverance не додавати ще раз MMRTG чи вже встановлені прилади.

`launchers.json` не містить C3-параметризованих performance curves. Тому UI показує **«сумісність не визначена»**, якщо користувач питає, чи підніме ракета довільну масу при заданому C3. Рекламна Mars capacity і LEO capacity не взаємозамінні. Ідеальний Hohmann ≈258.9 d, C3≈8.67 km²/s²; Mars 2020 — інше вікно, nominal press-kit C3=14.49. Ці точки не визначають лінійну криву.

EDL — автономна навчальна послідовність подій за NASA, а не повний solver: `edl.json`. Щоб підтверджувати безпеку посадки іншої маси, потрібні аеродинаміка, атмосфера по висоті, теплообмін, паливо й керування. Drag формула дозволяє демонстрацію тенденцій, не сертифікацію. Для поточного MVP `game_scenario.json` повертає indeterminate поза reference sequence.

Комунікації: у `earth_mars_ephemeris.json` є одночасні geometric positions Землі/Марса в heliocentric Ecliptic J2000, TDB. Delay — не готовий Horizons light-time: d/c без retarded position. 1 au →499.004784 s в один бік, ≈998.009568 s round-trip без processing time. Cache bounds обов’язкові; не екстраполювати. Сеанси гри 2×480 s при 350000 bit/s дають до168 Mbit за сеанс, але це ігрова угода, не прогноз прольоту MRO. Історичні Mb/day у NASA relay catalog — середні, не guaranteed SLA.

Ресурси інтегрувати за simulation seconds, без FPS-залежності. Інструмент P=25 W, t=600 s →4.1667 Wh. Data example: 200 Mbit у буфері +50 Mbit науки −120 Mbit downlink =130 Mbit за відсутності overflow. Реалізація `dataStep` уточнює порядок acquisition→capacity→downlink і повертає втрати явно. `batteryStep` відокремлює curtailed та unserved energy. 1 Wh=3600 J; 1 MB=8 Mbit, 1 Mb=1 Mbit; sol=88775.24415 s, Earth day=86400 s.

Системно-інженерний мінімум із NASA mission-design/CML/CubeSat посібників: для кожної наукової цілі вкажіть вимірювання → прилад → mass/power/data budget → операцію → тест отриманого результату. Розділяйте launch, space, ground, user segments; оцінка складності/вартості в грі є game assumption. CML показує зрілість концепції, а не автоматичний рівень наукової точності.
'''
    doc('docs/PHYSICS.md',intro+'\n'.join(sections)+ending)

def generation():
    doc('docs/GENERATION.md','''# Відтворюваний генератор систем

Вхід: `data/planets/generation_parameters.json`, `mass_radius_anchors.json`, `planet_types.json`, `atmospheres.json` і `data/physics/physical_constants.json`. Готовий алгоритм: `lib/generator.mjs`; seed прикладу —2026. Результат — статистично правдоподібна навчальна система; не реконструкція її формування й не N-body симуляція.

1. uint32 seed → xorshift32 (зсуви 13/17/5). Seed=0 замінюється на1831565813. Uniform=uint32/2³², верхня межа виключена. Усі випадкові вибори проходять через цей потік; `Math.random()` не використовувати. Зберігати seed, stream_version=1 та версії всіх JSON конфігів.
2. Кількість планет — рівномірно3–8. Для зорі log-uniform M=0.5–1.2 M_sun; L/L_sun=(M/M_sun)^4, R/R_sun=(M/M_sun)^0.8, T_eff вивести зі Stefan–Boltzmann. Це грубе main-sequence наближення, не IMF і не еволюційний трек. Подвійні зорі, гіганти, білі карлики поза моделлю.
3. Тип планети — ігрові ваги0.35/0.30/0.20/0.15. Радіусні класи0.3–1.6 /1.6–4 /4–8 /8–14 R_earth. Вони не визначають однозначно склад: rocky/ice — кандидатні назви. Ваги не дорівнюють intrinsic frequency відкриттів NASA.
4. Маса й радіус — **одна парна точка ExoVista** з відповідного класу. Не генерувати їх незалежно. До64 anchors обрано детерміновано за квантилами радіуса серед пар з 0.01–3000 M_earth, 100–15000 kg/m³. Це компактна дискретна підтримка моделі, не новий mass-radius fit. Густину й g завжди перераховувати з M,R.
5. Перша a=0.15–0.4 au; наступна a=previous_a×uniform(1.8,2.6); зовнішня межа40 au. e uniform0–0.08. Одна ізотропна площина для всієї системи: cos(i) uniform[-1,1], node uniform[0,2π). Розрізняйте inclination до сцени та взаємний нахил планет, тут останній0. Фази — uniform mean anomaly; аргумент перицентра випадковий.
6. Reject, якщо перицентр заходить у зорю, густина поза envelope, орбіта за40 au або gap між перицентром зовнішньої й апоцентром внутрішньої <10 mutual Hill radii. Максимум128 спроб на планету,16 на систему. Відмова — явна помилка, кількість тіл не зменшується приховано. Hill gate не гарантує довготривалу стабільність багатопланетної системи.
7. P_orbit за Кеплером; spin log-uniform10–96 h з P_spin>=2×P_break. Відстань<0.1 au вмикає умовну синхронізацію (у поточному inner range не досягається). Це перемикач дизайну, не tidal timescale. `solarDay` повертає null для synchronous day: показати «припливне захоплення».
8. Bond albedo uniform0.1–0.6; T_eq при a, epsilon=1, повний розподіл тепла, без greenhouse. Для e>0 потік змінюється по орбіті; mean-at-a температура не кліматична модель. rocky атмосфера none/thin_co2; невелика гаряча планета втрачає thin preset, якщо v_escape<5×sqrt(3R_gas*T_eq/M_mol). Це обережний retention screen, не інтеграція atmospheric escape. Інші класи — illustrative H2/He envelope. Склад не виміряний для згенерованої планети; O2/habitability автоматично не виводити.

## Приклад ES module

```js
import {generateSystem} from '../lib/generator.mjs';
import {loadJSON} from '../lib/load.mjs';
const base = new URL('../', import.meta.url);
const [parameters, constants, anchors] = await Promise.all([
  'data/planets/generation_parameters.json',
  'data/physics/physical_constants.json',
  'data/planets/mass_radius_anchors.json'
].map(path => loadJSON(base, path)));
const system = generateSystem(2026, parameters, constants, anchors);
console.log(system.planets[0].gravity_m_s2);
```

Рух: `orbitPosition(planet,time_s,G*(star.mass_kg+planet.mass_kg))` розв’язує E−e sin E=M, потім повертає scientific XYZ, z normal to reference plane. Для Y-up сцени `(x,z,-y)` зберігає праву систему; не робіть `x,y,z` простим перейменуванням осей. Реальний R й a лишаються SI; оглядові r_view=20 ln(1+a/(0.1 au)), R_view=0.5 sqrt(R/R_earth) — лише графіка. Приклад Earth a=1 au →47.958 view units, R=R_earth →0.5 view unit. У close-up rover scene1unit=1m; не використовувати стиснену гравітацію чи колізії.

## Статистика та чесне небо

`docs/audit/population_statistics.json` містить кількості, p05/p50/p95, missingness та Kepler diagnostics усіх6470 archive rows. Переважають транзити: це bias, не природний розподіл. `pl_bmasse` composite export не має прапорця provenance маси чи uncertainties; деякі маси/радіуси можуть бути оціненими. Тому не підганяємо вигаданий empirical relation. Ексцентриситет0 у таблиці може бути фіксованим припущенням спостережного fit.

ExoVista: 2258 synthetic systems, після видалення zero padding24744 планет. Це не спостереження історії народження. SODA:873 disks, dust masses з upper limits; не використовувати median detections як median population, не переводити dust mass у total disk mass без незалежного gas/dust model. Formation timeline можливий лише як позначена ілюстрація; P2 tracks не потрібні MVP.

`stars.json` —64 цільові зорі з RA/Dec/Vmag ExoVista target table. Це неповний набір близьких зір, без повного sky coverage і без propagation proper motion. Night Sky для MVP — процедурний фон з окремим seed, без назв реальних сузір’їв або претензії на правильну видиму картину з Марса. Для реального неба потрібен окремий перевірений all-sky catalog плюс орієнтація спостерігача/час; його тут немає.

Вигляд: кольори, хмари, смуги, кратери, кільця — procedural artwork за radius class; зв’язок кольору зі складом лише умовний. Справжнє ортофото CTX використовувати виключно для ділянки Марса. Фото Perseverance — gallery/science context, не albedo map екзопланети.
''')

def team():
    doc('docs/team/SASHA.md','''# SASHA — марсохід і навігація

Починай із `data/rover/rover_specs.json`, `routes.json`, `assets/terrain/metadata.json`. Математика готова в `lib/terrain.mjs` і `lib/science.mjs`. Дані офлайн; physics/code engine-independent. NASA reference1025kg, розміри3×2.7×2.2m,6 коліс діаметром0.525m, top hard-ground speed152m/h. 30° operational avoidance і45° static tilt не є дозволом маршруту на такий схил; у MVP safe15°, caution25°.

## Карта та координати

512×512 cells,20m/cell,10.24km квадрат. `heightmap.u16`: little-endian, row-major,0=nodata, h=offset+(u16−1)×scale з metadata. `slope.u16`: centidegrees,65535=nodata. `traversability.u8`:0 blocked/unknown/edge,1 slope-passable,2 caution. 3×3 maximum slope забезпечує обережний halo, але CTX не бачить колесного масштабу каміння/просідання. `ortho.webp` точно на тих самих bounds; верх=north,ліво=west. PNG heightmap для перегляду/імпорту, не читати16-bit через звичайний8-bit canvas.

Сцена права: +X east,+Y up,+Z south. Координати PLACES landing_x/y/z — north/east/down: для локального NED вектора `(N,E,D)` → `(E,−D,−N)`, лише для спільного origin/frame. Для карти використовуй надані `world_xyz_m`, отримані з planetocentric lat/lon через CRS GeoTIFF. Не підставляй planetodetic latitude. Surface Y=terrain height−origin elevation; measured areoid elevation збережена окремо, відмінність від CTX до кількох метрів очікувана.

```js
import {createTerrain,decodeUint16LE,estimateRoute} from '../lib/terrain.mjs';
import {loadJSON,loadBuffer} from '../lib/load.mjs';
const base=new URL('../',import.meta.url);
const meta=await loadJSON(base,'assets/terrain/metadata.json');
const [h,s,t]=await Promise.all(['heightmap.u16','slope.u16','traversability.u8']
  .map(n=>loadBuffer(base,'assets/terrain/'+n)));
const map=createTerrain(meta,decodeUint16LE(h),decodeUint16LE(s),new Uint8Array(t));
const specs=await loadJSON(base,'data/rover/rover_specs.json');
const profile=specs.profiles.find(p=>p.id==='science');
console.log(map.sample(0,0));
console.log(estimateRoute(map,[[0,0,0],[10,0,0]],profile,3.71));
```

Вхід маршруту: масив>=2 finite `[x,y,z]` у метрах, XZ оцінює маршрут, Y helper прив’язує до DEM. `estimateRoute` семплює не рідше10m, блокує вихід за bounds, nodata, caution, перевищення profile slope/тяги та вичерпання батареї. Це оцінювач, не pathfinder і не N-body/rigid-body rover controller. `routes.json` має211 last-tactical poses за sol, у межах ділянки. Прямі відрізки між ними не є фактично проїханими чи схваленими шляхами; планувальник має шукати маршрут по grid1 й перевіряти кожен крок.

## Рух і ресурси

F=ma+mg(sinθ+Crr cosθ), E=max(0,F*s)/eta+P_aux*t. θ зі знаком, підйом>0; t=s/v. На100m при5°, m1025kg,g3.71,Crr0.04,eta0.5,v0.03,P_aux120: F≈482.96N,load≈137.94Wh; за цей час MMRTG110W виробить≈101.85Wh. Батарея додатково враховує0.95 discharge efficiency; не віднімати генерацію двічі. `batteryStep` використовує J, профілі Wh; передавання даних — bit, каталоги можуть мати Mbit/MB. Наука25W за600s=4.1667Wh, її слід додати до всіх одночасних навантажень.

| Ігровий профіль | Повна маса kg | v m/s | Battery Wh | Buffer Mbit | slope ° |
|---|---:|---:|---:|---:|---:|
| scout |900|0.04|1600|2048|15|
| science |1025|0.03|2400|4096|15|
| cargo |1200|0.02|3200|8192|12|

Це **три умовні профілі, що потребують погодження SASHA/MISHA**, не NASA modifications. Всі маси цілого ровера вже включають його instrument_ids. Wheel geometry спільна; вигадане додаткове обладнання не видавати за NASA. Battery usable Wh реального апарата не підтверджено. MMRTG110W — початкова reference power, не поточна виміряна потужність2026.

Бракує wheel-scale hazard/soil mechanics і погодженого балансу профілів. Це не блокує grid navigation MVP; за межами slope proxy UI має показувати невідомий ризик. Узгодь wheel pivots/forward direction із MISHA за model manifest. Перевірки: `node --test tests/runtime.test.mjs`.
''')
    doc('docs/team/MISHA.md','''# MISHA — масштаби, моделі й експорт

Готові standalone GLB: `assets/models/Mars_2020_Perseverance_Rover.glb` і `Mars_Reconnaissance_Orbiter.glb`. У `manifest.json` — кількість трикутників, справжні decoded bounds, джерела, placement scale. Draco у вихідних NASA файлах приховував правильні координати від неповного reader; у поставці його декодовано, додатковий мережевий decoder не потрібен. WebP textures embedded, +Y up.

Perseverance: reference envelope length3m (без руки),width2.7m,height2.2m;6 коліс діаметром0.525m,рука~2.1m. У GLB поточна поза/геометрія має інший Y envelope: **не розтягувати модель окремо по осях до3×2.7×2.2**. Візьми `scale_for_rover_width_2_7_m` з manifest: uniform scale=2.7/native_width. Floor offset=−minY×scale, XZ origin при потребі центруй bounding box. Перед wheel animation звір pivot і authored front; manifest не вигадує forward orientation. Для MRO bounds — візуальна геометрія, метричний CAD-scale цим пакетом не сертифіковано.

Сцена right-handed: X east,Y up,Z south;1unit=1m у surface scene. glTF стандарт Y-up; експорт apply scale й normals, без абсолютних шляхів і зовнішніх текстур. Scientific orbital XYZ з осьовим Z-up перетворюється `(x,z,−y)`; planet overview використовує окремий логарифмічний масштаб відстаней. Не задавай collider оглядовим радіусом: real radius у JSON — m, visual radius — view units.

## Три модифікації

| ID | m kg (ігрове) | Базовий envelope m | Колеса m | Візуальна відмінність |
|---|---:|---|---|---|
| scout|900|3×2.7×2.2|0.525|менший умовний science pack|
| science|1025|3×2.7×2.2|0.525|набір instrument_ids із specs|
| cargo|1200|3×2.7×2.2|0.525|умовний вантажний модуль|

Ці профілі попередні, погодити з SASHA; геометрія додаткових модулів/їхні окремі маси не опубліковані NASA. Не додавати mass instrument вдруге до total_mass. Фізичні compound colliders: прості chassis boxes +6 wheel cylinders, окремі mast/arm, не один високий box на весь envelope. Center of mass/clearance не верифіковані — не виводити їх із середини render mesh як науковий факт.

Atlas V541: NASA launch press kit p.23 дає приблизну загальну висоту60m, номінальну категорію обтічника5m,4 SRBs,1 Centaur engine. В `authoring_specs.json` core diameter=null: dimensioned CAD не отримано. Для MVP схематична ракета з явно приблизною геометрією; не видавати5m fairing category за точний зовнішній діаметр. Character height1.75m — art assumption. Готових rocket/character meshes у наданому архіві немає.

## Ресурси та бюджет

- Ровер після підготовки~155k triangles, орбітер~14.8k; обидва реально прочитані GLB reader після експорту. Rover матеріалів багато: для багатьох копій потрібен atlas/material consolidation у вашому engine, перевірка FPS ще попереду.
- Бюджет MVP: rover<=200k triangles, orbiter<=30k,текстури<=2048px; рекомендовані LOD ratios1/0.5/0.2 — art targets, не вже створені mesh LODs. Текстура terrain має готовий1024px LOD.
- `assets/terrain/ortho.webp`: справжня grayscale CTX ділянка Марса,10.24km,UV північ угорі. DEM20m не displacement для деталей коліс; дрібні камені — лише окрема декоративна геометрія.
- `assets/images/manifest.json`:5 реальних фотографій із credits, для gallery. Для інших планет використовуй процедурні матеріали за GENERATION, позначені illustration.
- MGS й InSight залишені в локальному архіві як необов’язкові NASA refs, у runtime не дублюються.

Приклад placement (псевдо-API engine, самі дані готові): `node.uniformScale=manifest.placement.uniform_scale; node.position.y=manifest.placement.translation_y`. Реальне завантаження роби GLTF loader вашого engine без CDN. Джерела й кредити в manifest зберігати у presentation/credits. NASA модель не є схваленням гри NASA.
''')
    doc('docs/team/VANIA.md','''# VANIA — procedural generator і Night Sky

Візьми готовий `lib/generator.mjs` і конфіги `data/planets/`. Повний короткий алгоритм — `docs/GENERATION.md`. Програмувати astrophysical formation solver не потрібно.

```js
import {generateSystem} from '../lib/generator.mjs';
import {loadJSON} from '../lib/load.mjs';
const base=new URL('../',import.meta.url);
const [p,c,a]=await Promise.all([
 'data/planets/generation_parameters.json',
 'data/physics/physical_constants.json',
 'data/planets/mass_radius_anchors.json'
].map(f=>loadJSON(base,f)));
const system=generateSystem(2026,p,c,a);
console.log(system.id,system.planets.map(x=>x.radius_m));
```

RNG xorshift32, uint32 seed, stream_version1. Для seed1 перші uint32:270369,67634689,2647435461. Seed0 замінюється на1831565813. На одному config snapshot однаковий seed дає однакову структуру; floating point лише до tolerance між різними JS engines. Зберігати seed, version і SHA конфігів, не лише назву всесвіту.

Маса зорі0.5–1.2 M_sun;3–8 планет. Type weights0.35/0.30/0.20/0.15 — game balance, а не occurrence rate. Обирати **готову пару** mass/radius із anchors; rho,g обчислити. 64 pairs стискають ExoVista model; sample3 synthetic systems — для regression/examples. Не перемішувати масу однієї й радіус іншої планети. Радіусні класи не доводять склад.

Перша a0.15–0.4au,наступні×1.8–2.6,outer<=40au,e<=0.08. Reject crossing/star intersection та gap<10 mutual Hill radii, див. config. Це spacing heuristic, не N-body stable certificate. Є bounded retries й явна помилка; не замовчуй failed seed і не зменшуй кількість планет.

Для руху `orbitPosition` використовує mean anomaly й Kepler solver. Scientific XYZ z-up →scene `(x,z,−y)`. Орбітальний огляд `r=20*log1p(a/(0.1au))`;1au→47.958units. Видимий radius0.5*sqrt(R/R_earth), Earth→0.5units. Фізику завжди рахувати по real a,R у m; не стисненій сцені.

Атмосфери: illustrative presets `atmospheres.json`; H2/He для envelopes, thinCO2/none для rocky з простим retention screen. Gas fractions — mole fractions, сума1. O2 чи habitability не виводиться з маси/радіуса. T_eq — radiative balance без greenhouse; колір/хмари/rings — процедурна ілюстрація. Mars CTX/foto не перетворювати на «наукові текстури» інших світів.

Night Sky: `stars.json` містить64 nearby target directions з RA/Dec/Vmag, **не all-sky catalog**. Для красивого MVP фону використовуй інший RNG stream/seed та рівномірні solid-angle напрями: z uniform[-1,1],φ uniform[0,2π],x/y=sqrt(1−z²)*(cosφ,sinφ). Яскравості — art parameter, не виміряний sky. Познач «процедурне зоряне небо». Реальні сузір’я/видимість із Марса потребують окремого повного каталогу, observer/time transform; цього немає.

Перевірки готові: determinism, golden RNG,1000 seeds,фізичні інваріанти,Kepler orbit closure. Бракує formation evolution tracks/all-sky та downstream engine visuals; вони не потрібні статистичному MVP. Не нав’язуй генератору спостережні транзитні частоти як природну частку типів.
''')
    doc('docs/team/PASHA.md','''# PASHA — фізика, планети та UI

Твій entry point: `data/physics/physical_constants.json`, `formulas.json`, `data/planets/{planet_types,generation_parameters,atmospheres}.json`. Всі31 формула мають SI variables, computed example, domain/limits, mathematical derivation у `docs/PHYSICS.md`. Готові helpers у `lib/science.mjs`, orbit generator у `lib/generator.mjs`.

```js
import {gravity,density,orbitalPeriod,visViva,solarDay} from '../lib/science.mjs';
const G=6.67430e-11,M=5.9722e24,R=6371008.4;
console.log(gravity(M,R,G)); // ~9.82028 m/s²
console.log(density(M,R));   // ~5513.42 kg/m³
console.log(solarDay(88642.6632,686.98*86400)); // mean solar seconds
```

У production прочитай G,M,R з JSON; літерали вище — прозорий числовий приклад. M,R,rho не3 незалежні ручки: rho=3M/(4πR³), g=GM/R². Якщо UI редагує M,R, rho й g перераховувати; generator вибирає paired anchors. Позитивні M,R, радіусна підтримка0.3–14 R_earth,густина100–15000kg/m³ — game envelope, не універсальна область усіх планет. Не тверда поверхня для gas/sub-Neptune classes.

Орбіти: P=2πsqrt(a³/μ),v=sqrt(μ(2/r−1/a)),μ=G(M_star+M_planet). Earth circular example1au →~365.2569d,29.785km/s. Відрізняти миттєвий r від a. Обертання v_eq=2πR/P_spin; сидеричний і solar day різні, retrograde spin має від’ємний період у `solarDay`. Для locked day=null виводь «синхронне», не0секунд. Нижній P_spin>=2×P_break — safety rule генератора, не виміряний spin distribution.

Потік S=L/(4πr²),T_eq=[S(1−A)/(4σε)]^0.25. Earth-like A0.3,ε1 на1au →~254.6K; це не288K surface temperature. Припущення повного heat redistribution і відсутності greenhouse показуй у tooltip. Bond albedo≠geometric albedo. Склад атмосфер у presets — mole/volume fractions; sum1, M_mol уkg/mol,H=R_gas*T/(M_mol*g). Mars-like T210K,M_mol0.04334,g3.71 →H~10.86km. p=p0 exp(−z/H) лише isothermal illustration, не реальний профіль MEDA.

## UI контракт

| Величина | Storage | Display |
|---|---|---|
| Mass |kg|M_earth або kg,3 значущі цифри|
| Radius |m|km / R_earth; real radius окремо від render|
| Density |kg/m³|g/cm³ =kg/m³ /1000|
| Gravity |m/s²|m/s²; optionally Earth-g, знаменник явно conventional/reference|
| Orbit a/r |m|au/km; не view units|
| Speed |m/s|km/s для orbit,cm/s для rover|
| Rotation/period |s|h/day/sol із підписом sidereal/solar|
| Temperature |K|K або°C=K−273.15; T_eq позначити|
| Pressure |Pa|Pa/kPa/bar(1bar=100000Pa)|
| Energy/power |J/W|Wh=J/3600; W не Wh|
| Data/rate |bit/bit/s|Mbit/Mbit/s; MB окремо|
| Signal delay |s|one-way min:s; round-trip окремо|
| Ephemeris epoch |JD TDB|позначTDB, без удаваного UTC|

Поряд із значенням — published/derived/synthetic/game badge; `null` →«немає даних», жодного автоматичного0. Ліміт RIMFAX<3kg — нерівність, не точно3. Средній data-return/sol — не storage capacity. Для rocket capability при відсутності C3 curve показати indeterminate, для іншої маси EDL теж не «успішна посадка».

Візуальні r/R масштаби незалежні, огляд позначити «відстані й розміри стиснуто». Surface scene1unit=1m,gravity≈3.71m/s². Не передавати scaled orbit coordinates до engine gravity solver; орбітальний режим аналітичний. Simulation seconds відокремити від wall-clock/FPS, clamp фізичного кроку погодити з SASHA.

Три rover profiles — ігрові; параметри/порівняння в SASHA.md, mass budget уже full vehicle. Не додавати вдруге прилади. Unknown launch/EDL mass і usable battery Wh залишаються прогалинами джерел, не блокують референсний навчальний сценарій.
''')
    doc('docs/team/YURA.md','''# YURA — дані, API й інтеграція

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
''')

def main():
    sources();selection();physics();generation();team()
    doc('README.md','''# White Cat — науковий пакет Space Mission Design Game

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
''')
    print('documentation and sources OK')

if __name__=='__main__':main()
