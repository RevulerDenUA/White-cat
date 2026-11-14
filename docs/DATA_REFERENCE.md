# Карта готових ресурсів

Усі шляхи від package root. Runtime читає `data/physics`, `data/planets`, `data/missions`, `data/rover`, `assets`. Audit/tools/docs не завантажувати в ігровий цикл. `data/package_manifest.json` містить SHA-256 і точні розміри всього релізу, крім самого manifest (щоб уникнути самопосилального hash).

| Файл | Кому | Призначення |
|---|---|---|
| `.gitattributes` | YURA / усі | Пакет, джерела або загальна документація |
| `.github/workflows/scientific-package.yml` | YURA | CI перевірки пакета |
| `.gitignore` | YURA / усі | Пакет, джерела або загальна документація |
| `README.md` | YURA / усі | Пакет, джерела або загальна документація |
| `assets/images/FLF_1000_0755716468_020ECM_N0474404FHAZ02418_01_295J.webp` | MISHA, YURA | 5 демонстраційних WebP і credits |
| `assets/images/NRF_0800_0737945673_612ECM_N0391170NCAM02799_01_195J.webp` | MISHA, YURA | 5 демонстраційних WebP і credits |
| `assets/images/PCW_2000_0844451597_000ECM_N09109707607424011703075J.webp` | MISHA, YURA | 5 демонстраційних WebP і credits |
| `assets/images/SI1_1800_0826736547_707ECM_N0870000SRLC00636_0000LMJ.webp` | MISHA, YURA | 5 демонстраційних WebP і credits |
| `assets/images/ZL0_0800_0737944022_785EBY_N0391170ZCAM08821_1100LMJ.webp` | MISHA, YURA | 5 демонстраційних WebP і credits |
| `assets/images/manifest.json` | MISHA, YURA | 5 демонстраційних WebP і credits |
| `assets/models/Mars_2020_Perseverance_Rover.glb` | MISHA | Embedded NASA visual GLB і геометричні metadata |
| `assets/models/Mars_Reconnaissance_Orbiter.glb` | MISHA | Embedded NASA visual GLB і геометричні metadata |
| `assets/models/authoring_specs.json` | MISHA | Embedded NASA visual GLB і геометричні metadata |
| `assets/models/manifest.json` | MISHA | Embedded NASA visual GLB і геометричні metadata |
| `assets/terrain/heightmap.png` | SASHA, MISHA | Суміщена CTX ділянка та slope/passability proxy |
| `assets/terrain/heightmap.u16` | SASHA, MISHA | Суміщена CTX ділянка та slope/passability proxy |
| `assets/terrain/metadata.json` | SASHA, MISHA | Суміщена CTX ділянка та slope/passability proxy |
| `assets/terrain/ortho.webp` | SASHA, MISHA | Суміщена CTX ділянка та slope/passability proxy |
| `assets/terrain/ortho_lod1.webp` | SASHA, MISHA | Суміщена CTX ділянка та slope/passability proxy |
| `assets/terrain/slope.png` | SASHA, MISHA | Суміщена CTX ділянка та slope/passability proxy |
| `assets/terrain/slope.u16` | SASHA, MISHA | Суміщена CTX ділянка та slope/passability proxy |
| `assets/terrain/traversability.png` | SASHA, MISHA | Суміщена CTX ділянка та slope/passability proxy |
| `assets/terrain/traversability.u8` | SASHA, MISHA | Суміщена CTX ділянка та slope/passability proxy |
| `data/missions/components.json` | PASHA, YURA | Mission engineering / траєкторії / зв’язок; null збережено |
| `data/missions/earth_mars_ephemeris.json` | PASHA, YURA | Mission engineering / траєкторії / зв’язок; null збережено |
| `data/missions/edl.json` | PASHA, YURA | Mission engineering / траєкторії / зв’язок; null збережено |
| `data/missions/game_scenario.json` | PASHA, YURA | Mission engineering / траєкторії / зв’язок; null збережено |
| `data/missions/launchers.json` | PASHA, YURA | Mission engineering / траєкторії / зв’язок; null збережено |
| `data/missions/orbits.json` | PASHA, YURA | Mission engineering / траєкторії / зв’язок; null збережено |
| `data/missions/relay_plans.json` | PASHA, YURA | Mission engineering / траєкторії / зв’язок; null збережено |
| `data/physics/formulas.json` | PASHA, VANIA | SI константи / формули й обчислені приклади |
| `data/physics/physical_constants.json` | PASHA, VANIA | SI константи / формули й обчислені приклади |
| `data/planets/atmospheres.json` | VANIA, PASHA | Planet generator catalog, paired anchors, examples і target stars |
| `data/planets/example_systems.json` | VANIA, PASHA | Planet generator catalog, paired anchors, examples і target stars |
| `data/planets/generated_example.json` | VANIA, PASHA | Planet generator catalog, paired anchors, examples і target stars |
| `data/planets/generation_parameters.json` | VANIA, PASHA | Planet generator catalog, paired anchors, examples і target stars |
| `data/planets/mass_radius_anchors.json` | VANIA, PASHA | Planet generator catalog, paired anchors, examples і target stars |
| `data/planets/planet_types.json` | VANIA, PASHA | Planet generator catalog, paired anchors, examples і target stars |
| `data/planets/stars.json` | VANIA, PASHA | Planet generator catalog, paired anchors, examples і target stars |
| `data/rover/routes.json` | SASHA, MISHA | Rover reference, умовні профілі, координати й MEDA subset |
| `data/rover/rover_specs.json` | SASHA, MISHA | Rover reference, умовні профілі, координати й MEDA subset |
| `data/rover/weather_samples.json` | SASHA, MISHA | Rover reference, умовні профілі, координати й MEDA subset |
| `data/sources.json` | YURA / усі | Пакет, джерела або загальна документація |
| `docs/DATA_REFERENCE.md` | YURA / усі | Пакет, джерела або загальна документація |
| `docs/DATA_SELECTION.md` | YURA / усі | Пакет, джерела або загальна документація |
| `docs/GENERATION.md` | YURA / усі | Пакет, джерела або загальна документація |
| `docs/PHYSICS.md` | YURA / усі | Пакет, джерела або загальна документація |
| `docs/VALIDATION.md` | YURA / усі | Пакет, джерела або загальна документація |
| `docs/audit/geospatial.json` | YURA | Початковий inventory, diagnostics і перетворення |
| `docs/audit/meda_products.json` | YURA | Початковий inventory, diagnostics і перетворення |
| `docs/audit/population_statistics.json` | YURA | Початковий inventory, diagnostics і перетворення |
| `docs/audit/raw_inventory.json` | YURA | Початковий inventory, diagnostics і перетворення |
| `docs/team/MISHA.md` | відповідний учасник | Персональний integration handoff |
| `docs/team/PASHA.md` | відповідний учасник | Персональний integration handoff |
| `docs/team/SASHA.md` | відповідний учасник | Персональний integration handoff |
| `docs/team/VANIA.md` | відповідний учасник | Персональний integration handoff |
| `docs/team/YURA.md` | відповідний учасник | Персональний integration handoff |
| `examples/integration.html` | усі | Локальна browser integration перевірка |
| `lib/generator.mjs` | SASHA, VANIA, PASHA | Готовий browser/Node runtime helper |
| `lib/load.mjs` | SASHA, VANIA, PASHA | Готовий browser/Node runtime helper |
| `lib/science.mjs` | SASHA, VANIA, PASHA | Готовий browser/Node runtime helper |
| `lib/terrain.mjs` | SASHA, VANIA, PASHA | Готовий browser/Node runtime helper |
| `schemas/index.json` | YURA, PASHA | JSON Schema2020-12; mapping контрактів |
| `schemas/package.schema.json` | YURA, PASHA | JSON Schema2020-12; mapping контрактів |
| `tests/runtime.test.mjs` | YURA, розробники | Автоматична регресійна перевірка runtime |
| `tools/authoring_specs.json` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/build_catalogs.py` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/build_docs.py` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/create_example.mjs` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/create_schemas.py` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/fetch_ephemeris.py` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/finalize_manifest.py` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/package-lock.json` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/package.json` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/package_config.json` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/prepare_data.py` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/prepare_models.mjs` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/requirements-lock.txt` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/requirements.txt` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/science.py` | YURA | Відтворювана підготовка, контракти й offline validation |
| `tools/validate_package.py` | YURA | Відтворювана підготовка, контракти й offline validation |
| `data/package_manifest.json` | YURA | Release file list, bytes і SHA-256 |

## Контракти та приклади

JSON — UTF-8, finite numbers, schema_version1.0, ID стабільні в межах snapshot. Константа `{value, unit, status, source, note}`; generated planet має kg/m/s/rad та `status=synthetic_game_model`. IDs не залежать від перекладу назви. Source_ids посилаються на `data/sources.json`; прямий URL/derivation у значень також допустимий. Числові suffix `_kg`, `_m`, `_s`, `_w`, `_wh`, `_pa`, `_deg`, `_rad`, `_mbit` задають одиниці; case у згенерованих `_W`, `_K` теж значущий. `null` ніколи не означає0. Немає SQLite чи runtime API dependency.

| Ресурс | Поля / типи | Виклик |
|---|---|---|
| physical_constants | constants: object; кожне value:number,unit/status/source:string | `constants.G.value` |
| formulas | formulas:array; variables:object; example.inputs:object; expected:number | `FORMULAS[id](**inputs)` у tools/science.py |
| planet_types / anchors | ID:string; radius bounds:number[2]; coupled mass/radius:number | `generateSystem(seed,p,c,anchors)` |
| profiles | total_mass_kg:number; battery_capacity_wh:number; instrument_ids:string[] | `specs.profiles.find(x=>x.id==='science')` |
| routes | waypoints:array; world_xyz_m:number[3];cell_col_row:integer[2] | `terrain.sample(x,z)`; observation ≠ certified route |
| weather_samples | sol:integer;field/unit:string;rows_used:integer;p05/p50/p95:number (nullable min/max when no samples) | select same field/sol, не змішувати sensor temperature з air climate |
| ephemeris | jd_tdb:number; Earth/Mars position_m:number[3];distance_m/delay_s:number | `geometricDelay(samples,jd,c)` |
| terrain | affine_corner:number[6]; encodings:object; CRS WKT:string | `createTerrain(meta,uint16,uint16,uint8)` |
| models/images manifests | id/path/source/credit + dimensions | GLTF/image loader із relative root |

Binary terrain: uint16 LE height/slope і uint8 traversability; row-major. Декодування висоти з offset/scale,0 nodata; slope0.01°,65535 nodata. WebP imagery embedded/standalone читається стандартним browser decoder. GLB2 self-contained, external Draco decoder не потрібен; перевірено mesh/image читання, не engine FPS.

Metadata/science data provenance і tuning limits описані в PHYSICS/GENERATION та team docs. GLB/source-level material properties не є engineering CAD tolerance. Явні обмеження/прогалини — DATA_SELECTION і YURA.
