# MISHA — масштаби, моделі й експорт

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
