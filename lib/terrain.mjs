import {batteryStep} from './science.mjs';
export function decodeUint16LE(buffer){if(buffer.byteLength%2)throw new RangeError('Odd uint16 byte length');const d=new DataView(buffer),out=new Uint16Array(buffer.byteLength/2);for(let i=0;i<out.length;i++)out[i]=d.getUint16(i*2,true);return out;}
export function createTerrain(metadata,heights,slopes,traversability){
 const m=metadata;if([heights.length,slopes.length,traversability.length].some(n=>n!==m.width*m.height))throw new RangeError('Terrain dimensions mismatch');
 const [a,b,c,d,e,f]=m.affine_corner;if(b!==0||d!==0||a<=0||e>=0)throw new Error('Expected north-up affine');
 return {metadata:m,sample(x,z){
  if(!Number.isFinite(x)||!Number.isFinite(z))throw new RangeError('Coordinates must be finite');
  const E=m.origin_projected_m[0]+x,N=m.origin_projected_m[1]-z,col=Math.floor((E-c)/a),row=Math.floor((N-f)/e);
  if(row<0||col<0||row>=m.height||col>=m.width)return {valid:false,reason:'outside-terrain'};
  const i=row*m.width+col;if(heights[i]===m.height_encoding.nodata||slopes[i]===m.slope_encoding.nodata)return {valid:false,reason:'nodata'};
  const height_m=m.height_encoding.offset_m+(heights[i]-1)*m.height_encoding.scale_m;
  return {valid:true,col,row,height_m,y:height_m-m.origin_elevation_areoid_m,slope_deg:slopes[i]*m.slope_encoding.scale_deg,status:traversability[i]};
 }};
}
export function estimateRoute(terrain,points,profile,g,initialEnergyWh=profile.battery_capacity_wh){
 if(!Array.isArray(points)||points.length<2||points.some(p=>!Array.isArray(p)||p.length!==3||!p.every(Number.isFinite)))throw new RangeError('Route needs >=2 finite XYZ waypoints');
 if(!(profile.max_speed_m_s>0&&profile.drive_efficiency>0&&profile.drive_efficiency<=1&&g>0))throw new RangeError('Invalid route model');
 let stored_J=initialEnergyWh*3600,distance_m=0,duration_s=0,load_energy_J=0;
 const check=(s)=>!s.valid?s.reason:s.status!==1?'blocked-or-caution':s.slope_deg>profile.operational_slope_limit_deg?'profile-slope-limit':null;
 for(let k=1;k<points.length;k++){
  const p0=points[k-1],p1=points[k],horizontal=Math.hypot(p1[0]-p0[0],p1[2]-p0[2]),steps=Math.max(1,Math.ceil(horizontal/(terrain.metadata.spacing_m/2)));
  let prev=terrain.sample(p0[0],p0[2]);let reason=check(prev);if(reason)return {viable:false,reason,segment:k-1};
  for(let j=1;j<=steps;j++){
   const next=terrain.sample(p0[0]+(p1[0]-p0[0])*j/steps,p0[2]+(p1[2]-p0[2])*j/steps);reason=check(next);if(reason)return {viable:false,reason,segment:k-1};
   const ds=Math.hypot(horizontal/steps,next.y-prev.y);if(ds===0){prev=next;continue;}
   const theta=Math.atan2(next.y-prev.y,horizontal/steps);
   if(Math.abs(theta)*180/Math.PI>profile.operational_slope_limit_deg)return {viable:false,reason:'segment-slope-limit',segment:k-1};
   const force=profile.total_mass_kg*g*(Math.sin(theta)+profile.rolling_resistance*Math.cos(theta));
   if(Math.abs(force)>profile.max_traction_coefficient*profile.total_mass_kg*g*Math.cos(theta))return {viable:false,reason:'traction-limit',segment:k-1};
   const dt=ds/profile.max_speed_m_s,energy=Math.max(0,force*ds)/profile.drive_efficiency+profile.drive_aux_power_w*dt;
   const battery=batteryStep(stored_J,profile.generation_w,energy/dt,dt,profile.battery_capacity_wh*3600,profile.battery_charge_efficiency,profile.battery_discharge_efficiency);
   if(battery.unserved_J>0)return {viable:false,reason:'energy-exhausted',segment:k-1};
   stored_J=battery.stored_J;distance_m+=ds;duration_s+=dt;load_energy_J+=energy;prev=next;
  }
 }
 return {viable:true,distance_m,duration_s,load_energy_Wh:load_energy_J/3600,final_energy_Wh:stored_J/3600,net_battery_used_Wh:initialEnergyWh-stored_J/3600,assumption:'nearest-cell height, constant commanded speed; no slip, pauses or instruments; input waypoint Y snapped to terrain'};
}
