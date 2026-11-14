# Відтворюваний генератор систем

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
