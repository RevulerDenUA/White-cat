"""Export each LOD in isolation, reimport in clean scenes, validate exact geometry and camera."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path('/home/yura/Documents/ChatGPT/Space Mission Design Game');OUT=ROOT/'assets/models/hubble_telescope'
asset=bpy.data.scenes['White Cat | Hubble Telescope'];bpy.context.window.scene=asset
colls=[bpy.data.collections['HUBBLE / LOD'+str(i)] for i in range(3)]
roots=[next(o for o in c.objects if o.type=='EMPTY' and not o.parent) for c in colls]
viewcam=bpy.data.objects['Telescope_View_Check'];home=viewcam.parent
reports=[]
def stats(scene):
 meshes=[o for o in scene.objects if o.type=='MESH'];tris=0;bad=0;loose=0;verts=[];scales={};nodes={}
 for o in meshes:
  me=o.data;me.calc_loop_triangles();tris+=len(me.loop_triangles)
  bad+=sum(t.area<1e-11 for t in me.loop_triangles);used={v for t in me.loop_triangles for v in t.vertices};loose+=len(me.vertices)-len(used)
  verts.extend(o.matrix_world@v.co for v in me.vertices);scales[o.name]=list(o.scale)
 mn=[min(v[i] for v in verts) for i in range(3)];mx=[max(v[i] for v in verts) for i in range(3)]
 mats=set(m for o in meshes for m in o.data.materials)
 cam=next(o for o in scene.objects if o.type=='CAMERA');direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1));up=cam.matrix_world.to_quaternion()@Vector((0,1,0))
 view=next(o for o in scene.objects if o.name.startswith('Telescope_View') and o.type=='EMPTY')
 # Sample all camera rays against all telescope geometry, including backfaces.
 trees=[(o,BVHTree.FromObject(o,bpy.context.evaluated_depsgraph_get())) for o in meshes]
 clear=True;hits=0;origin=cam.matrix_world.translation;frame=cam.data.view_frame(scene=scene)
 for j in range(19):
  for i in range(33):
   x=(i+.5)/33;y=(j+.5)/19
   point=frame[2].lerp(frame[1],x).lerp(frame[3].lerp(frame[0],x),y);ray=cam.matrix_world.to_quaternion()@point.normalized()
   for o,tree in trees:
    inv=o.matrix_world.inverted();pos,normal,idx,dist=tree.ray_cast(inv@origin,inv.to_3x3()@ray,1000)
    if pos is not None:hits+=1
 clear=hits==0
 # Oblique rays must terminate on the inner sleeve/stop before the rear plane.
 # This catches the former unlined 7 cm interval that camera-clearance rays cannot see.
 body=next(o for o in meshes if o.name.startswith('Telescope_Body'))
 bore=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get());bore_misses=0;bore_rays=0;backfacing=0
 for i in range(72):
  a=i*math.tau/72
  for j in range(121):
   r=.50+j*.0025;start=Vector((0,-3.2,0));dest=Vector((r*math.cos(a),-1.32,r*math.sin(a)));delta=dest-start
   pos,normal,idx,dist=bore.ray_cast(start,delta.normalized(),delta.length+.0001);bore_rays+=1
   if pos is None:bore_misses+=1
   elif normal.dot(delta)>=0:backfacing+=1
 assert bore_misses==0 and backfacing==0,(bore_misses,backfacing)
 return {'bore_test_rays':bore_rays,'bore_uncovered_rays':bore_misses,'bore_backfacing_hits':backfacing,'triangles':tris,'mesh_count':len(meshes),'material_count':len(mats),'degenerate_triangles':bad,'loose_vertices':loose,'finite_positions':all(math.isfinite(q) for v in verts for q in v),'bounds_Blender_m':{'min':mn,'max':mx,'size':[mx[i]-mn[i] for i in range(3)]},'scales':scales,'view_position_Blender_m':list(view.matrix_world.translation),'camera_forward_Blender':list(direction),'camera_up_Blender':list(up),'camera_test_rays':33*19,'camera_geometry_hits':hits,'clear_camera':clear,'view_identity_rotation':all(abs(q)<1e-6 for q in view.rotation_euler),'materials':[m.name for m in mats]}
for lod in range(3):
 for c in colls:c.hide_viewport=False;c.hide_render=False
 bpy.ops.object.select_all(action='DESELECT')
 obs=list(colls[lod].objects);view=next(o for o in obs if o.type=='EMPTY' and o.parent)
 viewcam.parent=view;viewcam.location=(0,0,0);viewcam.rotation_euler=Vector((0,-1,0)).to_track_quat('-Z','Y').to_euler()
 # Consistent engine-facing node names across the three separate files.
 desired={roots[lod]:'Hubble_Telescope',view:'Telescope_View'}
 for o in obs:
  if o.type=='MESH':desired[o]=o.name.split('_LOD')[0]
 conflicts={o:o.name for o in list(bpy.data.objects) if o.name in set(desired.values()) and o not in desired}
 originals={o:o.name for o in desired}
 for o in conflicts:o.name='PARKED_'+o.name
 for o,name in desired.items():o.name=name
 for o in obs+[viewcam]:o.select_set(True)
 bpy.context.view_layer.objects.active=roots[lod];bpy.context.view_layer.update()
 before=stats(asset) if False else None
 file='Hubble_Telescope'+('' if lod==0 else '_LOD'+str(lod))+'.glb'
 bpy.ops.export_scene.gltf(filepath=str(OUT/file),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_cameras=True,export_extras=True,export_texcoords=True,export_normals=True,export_tangents=False,export_draco_mesh_compression_enable=False,export_image_format='AUTO')
 for o in desired:o.name='RESTORE_'+o.name
 for o,name in originals.items():o.name=name
 for o,name in conflicts.items():o.name=name
 # Import in a new scene with no existing material or meshes in that scene.
 check=bpy.data.scenes.new('QA imported LOD'+str(lod));bpy.context.window.scene=check
 bpy.ops.import_scene.gltf(filepath=str(OUT/file));bpy.context.view_layer.update();rep=stats(check);rep.update({'lod':lod,'file':file,'bytes':(OUT/file).stat().st_size})
 rr=next(o for o in check.objects if o.type=='EMPTY' and not o.parent);rep['root_identity']=all(abs(q)<1e-6 for q in rr.location) and all(abs(q)<1e-6 for q in rr.rotation_euler) and all(abs(q-1)<1e-6 for q in rr.scale)
 limits=[(1500,2500),(700,1200),(250,500)][lod]
 assert limits[0]<=rep['triangles']<=limits[1],rep
 assert rep['material_count']==1 and rep['mesh_count']==3 and rep['clear_camera'] and rep['root_identity'] and rep['degenerate_triangles']==0 and rep['loose_vertices']==0 and rep['finite_positions'],rep
 assert abs(rep['camera_forward_Blender'][1]+1)<1e-5 and abs(rep['camera_up_Blender'][2]-1)<1e-5,rep
 reports.append(rep)
 # Remove the QA scene only after its imported data is measured.
 for o in list(check.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.context.window.scene=asset;bpy.data.scenes.remove(check)
viewcam.parent=home;viewcam.location=(0,0,0);viewcam.rotation_euler=Vector((0,-1,0)).to_track_quat('-Z','Y').to_euler()
for i,c in enumerate(colls):c.hide_viewport=i>0;c.hide_render=i>0
sources=json.loads((OUT/'source_integrity.json').read_text());integrity={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in sources.items() if p!='космічна станція.blend'};assert all(integrity.values())
revision=json.loads((OUT/'station_revision.json').read_text());assert hashlib.sha256((ROOT/'космічна станція.blend').read_bytes()).hexdigest()==revision['station_after_sha256']
assert hashlib.sha256((ROOT/'assets/revisions/hubble_cleanup_2026-11-15/космічна станція.blend').read_bytes()).hexdigest()==sources['космічна станція.blend']
(OUT/'validation.json').write_text(json.dumps({'blender_version':bpy.app.version_string,'source_files_unchanged':integrity,'authorized_station_revision':revision,'roundtrip':reports},ensure_ascii=False,indent=2))
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hubble_Telescope.blend'),compress=True)
print(json.dumps(reports,indent=2))
