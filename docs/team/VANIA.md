# VANIA — procedural generator і Night Sky

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
