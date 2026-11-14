# PASHA — фізика, планети та UI

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
