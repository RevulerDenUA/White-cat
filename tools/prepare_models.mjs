/** Decode NASA Draco geometry before measuring; output standalone GLB with no decoder requirement. */
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {getBounds,simplify,prune,dedup} from '@gltf-transform/functions';
import draco3d from 'draco3dgltf';
import {MeshoptSimplifier} from 'meshoptimizer';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const config=JSON.parse(await fs.readFile(path.join(root,'tools/package_config.json'),'utf8')).models;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'draco3d.decoder':await draco3d.createDecoderModule()});
await MeshoptSimplifier.ready;
await fs.mkdir(path.join(root,'assets/models'),{recursive:true});
const sources=[['perseverance','Mars_2020_Perseverance_Rover.glb','nasa_perseverance_3d'],['mro','Mars_Reconnaissance_Orbiter.glb','nasa_mro_3d']];
const entries=[];
for(const [id,filename,sourceId] of sources){
 const source=path.join(root,'data/models',filename),document=await io.read(source),scene=document.getRoot().listScenes()[0];
 const before=getBounds(scene);const originalTriangles=document.getRoot().listMeshes().flatMap(m=>m.listPrimitives()).reduce((n,p)=>n+(p.getIndices()?.getCount()??p.getAttribute('POSITION').getCount())/3,0);
 document.getRoot().listExtensionsUsed().filter(x=>x.extensionName==='KHR_draco_mesh_compression').forEach(x=>x.dispose());
 if(id==='perseverance')await document.transform(dedup(),simplify({simplifier:MeshoptSimplifier,ratio:config.rover_simplify_ratio,error:config.rover_simplify_error,lockBorder:config.lock_border}),prune());
 const target=path.join(root,'assets/models',filename);await io.write(target,document);
 const check=await io.read(target);const bounds=getBounds(check.getRoot().listScenes()[0]);let triangles=0,vertices=0;
 for(const mesh of check.getRoot().listMeshes())for(const p of mesh.listPrimitives()){
  const a=p.getAttribute('POSITION');vertices+=a.getCount();triangles+=(p.getIndices()?.getCount()??a.getCount())/3;
  if(!Array.from(a.getArray()).every(Number.isFinite))throw new Error(`${id}: nonfinite vertices`);
 }
 const extents=bounds.min.map((v,i)=>bounds.max[i]-v);if(extents.some(v=>v<=0))throw new Error(`${id}: degenerate bounds`);
 const scale=id==='perseverance'?2.7/extents[0]:1;
 entries.push({id,path:'assets/models/'+filename,source_ids:[sourceId],status:'NASA_visual_model_derived',original_triangles:originalTriangles,triangles,vertices,bytes:(await fs.stat(target)).size,original_bounds_native:before,bounds_native:bounds,extents_native:extents,extensions_required:check.getRoot().listExtensionsRequired().map(x=>x.extensionName),scale_for_rover_width_2_7_m:id==='perseverance'?scale:null,placement:{uniform_scale:scale,translation_y:-bounds.min[1]*scale,orientation:'glTF +Y up; front direction is asset-authored, inspect before wheel animation'},notes:['Draco decoded before geometry analysis; exported without Draco requirement.','Textures and materials embedded. Browser must support WebP; material extensions may be rendered with core fallback.','Measured mesh pose is not identical to published envelope dimensions. Do not stretch axes independently.']});
 console.log(id,triangles,(await fs.stat(target)).size);
}
await fs.writeFile(path.join(root,'assets/models/manifest.json'),JSON.stringify({schema_version:'1.0',models:entries},null,2)+'\n');

await fs.copyFile(path.join(root,'tools/authoring_specs.json'),path.join(root,'assets/models/authoring_specs.json'));
