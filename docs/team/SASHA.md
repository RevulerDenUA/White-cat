# SASHA — марсохід і навігація

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
