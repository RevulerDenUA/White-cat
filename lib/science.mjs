/** SI calculations shared by browser clients and validation. No network or engine dependency. */
const TAU=2*Math.PI;
export function finitePositive(value,name){if(!Number.isFinite(value)||value<=0)throw new RangeError(`${name} must be finite and positive`);return value;}
export function gravity(mass,radius,G){finitePositive(mass,'mass');finitePositive(radius,'radius');return G*mass/radius**2;}
export function density(mass,radius){finitePositive(mass,'mass');finitePositive(radius,'radius');return mass/(4*Math.PI*radius**3/3);}
export function orbitalPeriod(a,mu){return TAU*Math.sqrt(finitePositive(a,'a')**3/finitePositive(mu,'mu'));}
export function visViva(mu,r,a){const s=finitePositive(mu,'mu')*(2/finitePositive(r,'r')-1/finitePositive(a,'a'));if(s<0)throw new RangeError('Impossible orbital radius');return Math.sqrt(s);}
export function solarDay(rotation,orbital){if(!Number.isFinite(rotation)||rotation===0)throw new RangeError('rotation must be nonzero and finite');finitePositive(orbital,'orbital');const f=Math.abs(1/rotation-1/orbital);return f<1e-15?null:1/f;}
export function xorshift32(seed,zeroReplacement=1831565813){if(!Number.isInteger(seed)||seed<0||seed>0xffffffff)throw new RangeError('seed must be uint32');let state=(seed||zeroReplacement)>>>0;return {uint32(){state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;},uniform(){return this.uint32()/4294967296;}};}
export function equilibriumTemperature(S,A,epsilon,sigma){finitePositive(S,'S');if(!Number.isFinite(A)||A<0||A>=1)throw new RangeError('Bond albedo must be in [0,1)');return (S*(1-A)/(4*finitePositive(sigma,'sigma')*finitePositive(epsilon,'epsilon')))**.25;}
export function orbitPosition(planet,time_s,mu){
 if(!Number.isFinite(time_s))throw new RangeError('time_s must be finite');
 const e=planet.eccentricity;if(!(e>=0&&e<1))throw new RangeError('elliptic eccentricity required');
 const a=finitePositive(planet.semimajor_axis_m,'a');
 const M=((planet.mean_anomaly_rad+Math.sqrt(mu/a**3)*time_s)%TAU+TAU)%TAU;
 let E=M;for(let k=0;k<16;k++){const correction=(E-e*Math.sin(E)-M)/(1-e*Math.cos(E));E-=correction;if(Math.abs(correction)<1e-13)break;}
 if(Math.abs(E-e*Math.sin(E)-M)>1e-10)throw new Error('Kepler solver did not converge');
 const x=a*(Math.cos(E)-e),y=a*Math.sqrt(1-e*e)*Math.sin(E);
 const O=planet.ascending_node_rad,w=planet.argument_periapsis_rad,i=planet.inclination_rad;
 const u=Math.cos(w)*x-Math.sin(w)*y,v=Math.sin(w)*x+Math.cos(w)*y;
 return [Math.cos(O)*u-Math.sin(O)*Math.cos(i)*v,Math.sin(O)*u+Math.cos(O)*Math.cos(i)*v,Math.sin(i)*v];
}
export function geometricDelay(samples,jd,c){
 if(!Number.isFinite(jd)||samples.length<2||jd<samples[0].jd_tdb||jd>samples.at(-1).jd_tdb)throw new RangeError('Epoch outside TDB cache');
 let lo=0,hi=samples.length-1;while(hi-lo>1){const m=(lo+hi)>>1;if(samples[m].jd_tdb<=jd)lo=m;else hi=m;}
 const a=samples[lo],b=samples[hi],u=(jd-a.jd_tdb)/(b.jd_tdb-a.jd_tdb);
 const delta=a.mars_position_m.map((x,i)=>(x+(b.mars_position_m[i]-x)*u)-(a.earth_position_m[i]+(b.earth_position_m[i]-a.earth_position_m[i])*u));
 return {distance_m:Math.hypot(...delta),one_way_geometric_delay_s:Math.hypot(...delta)/finitePositive(c,'c')};
}
export function dataStep(stored,created,rate,duration,capacity){
 for(const [k,v] of Object.entries({stored,created,rate,duration,capacity}))if(!Number.isFinite(v)||v<0)throw new RangeError(`${k} must be nonnegative finite`);
 if(stored>capacity)throw new RangeError('stored exceeds capacity');
 // Convention: acquisition then downlink; excess acquisition is explicitly dropped.
 const overflow_bit=Math.max(0,stored+created-capacity),available=Math.min(capacity,stored+created),transmitted_bit=Math.min(available,rate*duration);
 return {stored_bit:available-transmitted_bit,transmitted_bit,overflow_bit};
}
export function batteryStep(stored_J,generation_W,load_W,dt_s,capacity_J,etaCharge,etaDischarge){
 for(const [k,v] of Object.entries({stored_J,generation_W,load_W,dt_s,capacity_J}))if(!Number.isFinite(v)||v<0)throw new RangeError(`${k} must be nonnegative finite`);
 if(stored_J>capacity_J||![etaCharge,etaDischarge].every(x=>x>0&&x<=1))throw new RangeError('Invalid battery state or efficiency');
 const surplus=(generation_W-load_W)*dt_s;
 if(surplus>=0){const add=surplus*etaCharge;return {stored_J:Math.min(capacity_J,stored_J+add),unserved_J:0,curtailed_J:Math.max(0,stored_J+add-capacity_J)};}
 const demand=-surplus/etaDischarge;
 return {stored_J:Math.max(0,stored_J-demand),unserved_J:Math.max(0,demand-stored_J)*etaDischarge,curtailed_J:0};
}
