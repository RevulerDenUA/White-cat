import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {xorshift32,gravity,density,orbitalPeriod,visViva,solarDay,orbitPosition,geometricDelay,dataStep,batteryStep} from '../lib/science.mjs';
import {generateSystem} from '../lib/generator.mjs';
import {createTerrain,decodeUint16LE,estimateRoute} from '../lib/terrain.mjs';
import {NodeIO} from '../tools/node_modules/@gltf-transform/core/dist/index.js';
import {ALL_EXTENSIONS} from '../tools/node_modules/@gltf-transform/extensions/dist/index.js';
const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const j=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p)));
const buffer=p=>{const b=fs.readFileSync(path.join(ROOT,p));return b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength);};
const params=j('data/planets/generation_parameters.json'),constants=j('data/physics/physical_constants.json'),anchors=j('data/planets/mass_radius_anchors.json');
const cv=k=>constants.constants[k].value;
const meta=j('assets/terrain/metadata.json');
const terrain=createTerrain(meta,decodeUint16LE(buffer('assets/terrain/heightmap.u16')),decodeUint16LE(buffer('assets/terrain/slope.u16')),new Uint8Array(buffer('assets/terrain/traversability.u8')));
const specs=j('data/rover/rover_specs.json'),profile=specs.profiles.find(x=>x.id==='science');
const close=(a,b,tol=1e-9)=>assert.ok(Math.abs(a-b)<=tol*Math.max(1,Math.abs(b)),`${a} != ${b}`);
// Math.pow/cbrt may differ by one ULP across V8 releases; compare physical values, keep structure exact.
function equivalent(a,b){
 if(typeof a==='number'&&typeof b==='number'){if(Number.isInteger(a)&&Number.isInteger(b)&&Math.abs(a)<=0xffffffff&&Math.abs(b)<=0xffffffff)assert.equal(a,b);else close(a,b,1e-12);return;}
 if(a&&b&&typeof a==='object'&&typeof b==='object'){assert.equal(Array.isArray(a),Array.isArray(b));assert.deepEqual(Object.keys(a),Object.keys(b));for(const k of Object.keys(a))equivalent(a[k],b[k]);return;}
 assert.equal(a,b);
}

test('xorshift32 golden sequence, zero mapping and invalid seeds',()=>{const r=xorshift32(1);assert.deepEqual([r.uint32(),r.uint32(),r.uint32()],[270369,67634689,2647435461]);assert.equal(xorshift32(0).uint32(),xorshift32(1831565813).uint32());for(const s of [-1,1.2,2**32,NaN])assert.throws(()=>xorshift32(s));});
test('seed2026 fixture and repeatability',()=>{const a=generateSystem(2026,params,constants,anchors);assert.deepEqual(a,generateSystem(2026,params,constants,anchors));equivalent(a,j('data/planets/generated_example.json'));assert.notDeepEqual(a,generateSystem(2027,params,constants,anchors));});
test('1000 seeds satisfy coupled physical and spacing constraints',()=>{
 for(let seed=0;seed<1000;seed++){
  const s=generateSystem(seed,params,constants,anchors);assert.ok(s.planets.length>=3&&s.planets.length<=8);
  for(let i=0;i<s.planets.length;i++){
   const p=s.planets[i];close(p.density_kg_m3,p.mass_kg/(4*Math.PI*p.radius_m**3/3));close(p.gravity_m_s2,cv('G')*p.mass_kg/p.radius_m**2);
   assert.ok(p.density_kg_m3>=100&&p.density_kg_m3<=15000);assert.ok(p.semimajor_axis_m*(1-p.eccentricity)>s.star.radius_m+p.radius_m);
   assert.ok(p.eccentricity>=0&&p.eccentricity<=params.eccentricity_max);assert.ok(p.semimajor_axis_m<=params.outer_orbit_au_max*cv('au'));
   assert.ok(p.rotation_period_s>=params.rotation_breakup_safety_factor*2*Math.PI*Math.sqrt(p.radius_m**3/(cv('G')*p.mass_kg)));
   close(p.orbital_period_s**2,4*Math.PI**2*p.semimajor_axis_m**3/(cv('G')*(s.star.mass_kg+p.mass_kg)));
   if(i){const q=s.planets[i-1],rh=(p.semimajor_axis_m+q.semimajor_axis_m)/2*((p.mass_kg+q.mass_kg)/(3*s.star.mass_kg))**(1/3);assert.ok((p.semimajor_axis_m*(1-p.eccentricity)-q.semimajor_axis_m*(1+q.eccentricity))/rh>=params.mutual_hill_clearance_min-1e-10);}
  }
 }
});
test('generation failure is explicit, no silent planet deletion',()=>{const p=structuredClone(params);p.outer_orbit_au_max=0;assert.throws(()=>generateSystem(1,p,constants,anchors),/Could not generate/);});
test('known SI reference calculations and synchronous day',()=>{close(gravity(cv('earth_mass'),cv('earth_mean_radius'),cv('G')),9.8202764,1e-8);close(density(cv('earth_mass'),cv('earth_mean_radius')),5513.421568,1e-8);close(orbitalPeriod(cv('au'),cv('mu_sun'))/86400,365.2569,1e-6);close(visViva(cv('mu_sun'),cv('au'),cv('au'))/1000,29.784692,1e-7);assert.equal(solarDay(100,100),null);close(solarDay(-100,1000),90.9090909,1e-8);assert.throws(()=>gravity(1,0,cv('G')));});
test('Kepler solver closes eccentric orbit, respects apsides and plane rotation',()=>{const p={semimajor_axis_m:cv('au'),eccentricity:.8,mean_anomaly_rad:0,inclination_rad:.4,ascending_node_rad:.2,argument_periapsis_rad:1};const mu=cv('mu_sun'),T=orbitalPeriod(p.semimajor_axis_m,mu),at0=orbitPosition(p,0,mu);close(Math.hypot(...at0),cv('au')*.2);close(Math.hypot(...orbitPosition(p,T/2,mu)),cv('au')*1.8);orbitPosition(p,T,mu).forEach((v,i)=>close(v,at0[i],1e-8));});
test('geometric delay uses both planets, rejects extrapolation',()=>{const d=j('data/missions/earth_mars_ephemeris.json'),s=d.samples[0],r=geometricDelay(d.samples,s.jd_tdb,cv('c'));const expected=Math.hypot(...s.mars_position_m.map((x,i)=>x-s.earth_position_m[i]));close(r.distance_m,expected);close(r.one_way_geometric_delay_s,s.one_way_geometric_delay_s);assert.throws(()=>geometricDelay(d.samples,d.first_jd_tdb-1,cv('c')));assert.throws(()=>geometricDelay(d.samples,d.last_jd_tdb+1,cv('c')));assert.ok(geometricDelay(d.samples,s.jd_tdb+.5,cv('c')).distance_m>0);});
test('binary reader explicitly supports little endian and rejects malformed lengths',()=>{assert.deepEqual([...decodeUint16LE(new Uint8Array([1,2,3,4]).buffer)],[513,1027]);assert.throws(()=>decodeUint16LE(new ArrayBuffer(3)));});
test('terrain coordinate roundtrip for all retained PLACES waypoints',()=>{const r=j('data/rover/routes.json');assert.equal(r.waypoints.length,211);for(const w of r.waypoints){const s=terrain.sample(w.world_xyz_m[0],w.world_xyz_m[2]);assert.equal(s.valid,true);assert.deepEqual([s.col,s.row],w.cell_col_row);close(s.height_m,w.terrain_height_m,1e-5);}});
test('terrain blocks missing, border and outside region',()=>{assert.equal(terrain.sample(1e9,1e9).valid,false);const m=structuredClone(meta);m.width=2;m.height=2;const t=createTerrain(m,new Uint16Array([0,1,1,1]),new Uint16Array([65535,0,0,0]),new Uint8Array(4));const [a,,c,,,f]=m.affine_corner;const x=c+a*.5-m.origin_projected_m[0],z=m.origin_projected_m[1]-(f-10);assert.equal(t.sample(x,z).reason,'nodata');});
test('flat-route energy matches independent analytic work and auxiliary load',()=>{const flat={metadata:{spacing_m:20},sample(){return {valid:true,status:1,slope_deg:0,y:0};}};const r=estimateRoute(flat,[[0,999,0],[100,-999,0]],profile,3.71);assert.equal(r.viable,true);close(r.distance_m,100);const t=100/profile.max_speed_m_s,energy=profile.total_mass_kg*3.71*profile.rolling_resistance*100/profile.drive_efficiency+profile.drive_aux_power_w*t;close(r.load_energy_Wh,energy/3600);close(r.final_energy_Wh,profile.battery_capacity_wh-(energy-profile.generation_w*t)/profile.battery_discharge_efficiency/3600);});
test('route fails closed on caution, impossible slope and exhausted energy',()=>{const sample={valid:true,status:2,slope_deg:1,y:0},fake={metadata:{spacing_m:20},sample(){return sample;}};assert.equal(estimateRoute(fake,[[0,0,0],[100,0,0]],profile,3.71).reason,'blocked-or-caution');sample.status=1;sample.slope_deg=30;assert.equal(estimateRoute(fake,[[0,0,0],[100,0,0]],profile,3.71).reason,'profile-slope-limit');sample.slope_deg=0;assert.equal(estimateRoute(fake,[[0,0,0],[100,0,0]],profile,3.71,0).reason,'energy-exhausted');});
test('data budget reports overflow and avoids transmitting nonexistent bytes',()=>{assert.deepEqual(dataStep(200e6,50e6,1e6,120,500e6),{stored_bit:130e6,transmitted_bit:120e6,overflow_bit:0});assert.deepEqual(dataStep(90,20,20,1,100),{stored_bit:80,transmitted_bit:20,overflow_bit:10});assert.equal(dataStep(0,0,10,100,100).transmitted_bit,0);assert.throws(()=>dataStep(-1,0,0,1,10));});
test('battery charges, curtails and reports unserved load explicitly',()=>{assert.deepEqual(batteryStep(100,10,0,10,150,1,1),{stored_J:150,unserved_J:0,curtailed_J:50});assert.deepEqual(batteryStep(100,0,20,10,150,1,1),{stored_J:0,unserved_J:100,curtailed_J:0});assert.throws(()=>batteryStep(200,0,0,1,100,1,1));});
test('NASA GLBs decode with finite nondegenerate vertices and embedded resources',async()=>{const io=new NodeIO().registerExtensions(ALL_EXTENSIONS),manifest=j('assets/models/manifest.json');for(const model of manifest.models){const doc=await io.read(path.join(ROOT,model.path));assert.ok(!doc.getRoot().listExtensionsRequired().some(e=>e.extensionName==='KHR_draco_mesh_compression'));let triangles=0;for(const mesh of doc.getRoot().listMeshes())for(const p of mesh.listPrimitives()){const a=p.getAttribute('POSITION');assert.ok(a.getCount()>0);assert.ok(Array.from(a.getArray()).every(Number.isFinite));triangles+=(p.getIndices()?.getCount()??a.getCount())/3;}assert.equal(triangles,model.triangles);assert.ok(doc.getRoot().listTextures().every(t=>t.getImage()?.length>0&&!t.getURI()));}});
