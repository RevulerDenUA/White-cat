import {xorshift32,gravity,density,orbitalPeriod,equilibriumTemperature} from './science.mjs';
/** Snapshot-driven, deterministic educational generator; no model of formation history. */
export function generateSystem(seed,parameters,constants,anchorCatalog){
 const p=parameters,c=Object.fromEntries(Object.entries(constants.constants).map(([k,v])=>[k,v.value]));
 const rng=xorshift32(seed,p.rng.zero_seed_maps_to);const uniform=(a,b)=>a+(b-a)*rng.uniform();
 const logUniform=(a,b)=>Math.exp(uniform(Math.log(a),Math.log(b)));
 const entries=Object.entries(p.class_weights);if(Math.abs(entries.reduce((s,[,v])=>s+v,0)-1)>1e-10)throw new Error('Class weights must sum to one');
 const pickClass=()=>{let u=rng.uniform();for(const [key,w] of entries){u-=w;if(u<0)return key;}return entries.at(-1)[0];};
 const targetCount=Math.floor(uniform(p.planet_count_range[0],p.planet_count_range[1]+1));
 for(let systemAttempt=0;systemAttempt<p.rejection.max_system_attempts;systemAttempt++){
  const ms=logUniform(...p.stellar_mass_sun_range),mass=ms*c.sun_mass,radius=ms**p.star_model.radius_exponent*c.sun_radius,L=ms**p.star_model.luminosity_exponent*c.sun_luminosity;
  const star={id:'generated-star',status:'model',mass_kg:mass,radius_m:radius,luminosity_W:L,effective_temperature_K:(L/(4*Math.PI*radius**2*c.sigma))**.25};
  const planets=[],inclination=Math.acos(uniform(-1,1)),node=uniform(0,2*Math.PI);
  for(let i=0;i<targetCount;i++){
   let accepted=false;
   for(let attempt=0;attempt<p.rejection.max_planet_attempts;attempt++){
    const type=pickClass(),anchors=anchorCatalog.anchors[type];if(!anchors?.length)throw new Error(`Missing paired anchors for ${type}`);
    const anchor=anchors[Math.floor(uniform(0,anchors.length))];
    const m=anchor.mass_earth*c.earth_mass,R=anchor.radius_earth*c.earth_mean_radius;
    const previous=planets.at(-1),aAu=previous?previous.semimajor_axis_m/c.au*uniform(...p.orbit_ratio_range):uniform(...p.inner_orbit_au_range),a=aAu*c.au,e=uniform(0,p.eccentricity_max);
    const rho=density(m,R);if(aAu>p.outer_orbit_au_max||rho<p.density_kg_m3_range[0]||rho>p.density_kg_m3_range[1])continue;
    if(a*(1-e)<=star.radius_m+R)continue;
    let hillClearance=null;
    if(previous){const hill=(a+previous.semimajor_axis_m)/2*((m+previous.mass_kg)/(3*mass))**(1/3);hillClearance=(a*(1-e)-previous.semimajor_axis_m*(1+previous.eccentricity))/hill;if(hillClearance<p.mutual_hill_clearance_min)continue;}
    const period=orbitalPeriod(a,c.G*(mass+m)),breakup=2*Math.PI*Math.sqrt(R**3/(c.G*m));
    const locked=aAu<p.tide_lock_distance_au;
    const spin=locked?period:Math.max(logUniform(...p.rotation_period_s_range),p.rotation_breakup_safety_factor*breakup);
    const albedo=uniform(...p.bond_albedo_range),flux=L/(4*Math.PI*a*a);
    let atmosphere=type==='rocky_candidate'?(rng.uniform()<p.rocky_atmosphere_probability?'thin_co2':'none'):'h2_he';
    const Teq=equilibriumTemperature(flux,albedo,p.emissivity,c.sigma);
    if(atmosphere==='thin_co2'&&Math.sqrt(2*c.G*m/R)<p.atmosphere_retention_escape_to_rms_min*Math.sqrt(3*c.R_gas*Teq/p.thin_co2_molar_mass_kg_mol))atmosphere='none';
    planets.push({id:`generated-planet-${i+1}`,status:'synthetic_game_model',type,mass_kg:m,radius_m:R,density_kg_m3:rho,gravity_m_s2:gravity(m,R,c.G),semimajor_axis_m:a,eccentricity:e,inclination_rad:inclination,ascending_node_rad:node,argument_periapsis_rad:uniform(0,2*Math.PI),mean_anomaly_rad:uniform(0,2*Math.PI),orbital_period_s:period,rotation_period_s:spin,spin_sense:'prograde_relative_to_orbit',tidally_locked_by_game_rule:locked,bond_albedo:albedo,equilibrium_temperature_K:equilibriumTemperature(flux,albedo,p.emissivity,c.sigma),atmosphere_preset:atmosphere,mutual_hill_clearance:hillClearance,anchor:{source_star_id:anchor.source_star_id,source_planet_index:anchor.source_planet_index}});
    accepted=true;break;
   }
   if(!accepted)break;
  }
  if(planets.length===targetCount)return {schema_version:'1.0',id:`generated-${seed}`,seed,stream_version:p.rng.stream_version,model:'statistically plausible educational architecture, not formation simulation or certified stable system',star,planets};
 }
 throw new Error(`Could not generate ${targetCount} admissible planets for seed ${seed} within configured limits`);
}
