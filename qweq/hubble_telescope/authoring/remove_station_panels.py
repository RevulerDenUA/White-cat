"""Remove the two central auxiliary panels and their isolated hinges, preserving other geometry."""
import bpy,bmesh,json,hashlib
from pathlib import Path
ROOT=Path('/home/yura/Documents/ChatGPT/Space Mission Design Game');OUT=ROOT/'assets/models/space_station';HUB=ROOT/'assets/models/hubble_telescope'
scene=bpy.context.scene;core=bpy.data.objects['Station_Core'];me=core.data;bm=bmesh.new();bm.from_mesh(me);seen=set();remove=[];removed=[]
for v in bm.verts:
 if v in seen:continue
 todo=[v];group=set()
 while todo:
  w=todo.pop()
  if w in group:continue
  group.add(w);todo.extend(e.other_vert(w) for e in w.link_edges if e.other_vert(w) not in group)
 seen|=group;vs=[core.matrix_world@w.co for w in group];mn=[min(w[k] for w in vs) for k in range(3)];mx=[max(w[k] for w in vs) for k in range(3)];c=[(mn[k]+mx[k])/2 for k in range(3)]
 panel=abs(abs(c[0])-1.55)<1e-4 and abs(c[1]-.08)<1e-4 and abs(c[2]+.34)<1e-4
 hinge=abs(abs(c[0])-1.435)<1e-4 and abs(c[1]-.07)<1e-4 and abs(c[2]+.34)<1e-4
 if panel or hinge:remove.extend(group);removed.append({'part':'central auxiliary panel' if panel else 'panel hinge','center_Blender_m':c,'vertices':len(group)})
assert len(removed)==4,removed
before=sum(len(f.verts)-2 for f in bm.faces);bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(me);bm.free();me.update();me.calc_loop_triangles();after=len(me.loop_triangles)
core['triangle_count']=after;scene['revision_2026_11_15']='Removed the two central auxiliary panels and their hinges at user request during Hubble styling.'
original_scene=scene;exports=[]
for lod in range(3):
 root=bpy.data.objects['SpaceStation_LOD'+str(lod)];mesh=[o for o in root.children if o.type=='MESH']
 for o in [root]+mesh:
  for c in o.users_collection:c.hide_viewport=False
 bpy.ops.object.select_all(action='DESELECT')
 for o in [root]+mesh:o.select_set(True)
 file='Space_Station'+('' if lod==0 else '_LOD'+str(lod))+'.glb';p=ROOT/'assets/models'/file
 bpy.ops.export_scene.gltf(filepath=str(p),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=False,export_cameras=False,export_lights=False,export_extras=True,export_yup=True,export_normals=True,export_texcoords=True)
 expected=sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in mesh)
 check=bpy.data.scenes.new('Station revision roundtrip');bpy.context.window.scene=check;bpy.ops.import_scene.gltf(filepath=str(p));bpy.context.view_layer.update()
 meshes=[o for o in check.objects if o.type=='MESH'];tris=sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in meshes);assert tris==expected and len(meshes)==2
 exports.append({'lod':lod,'file':'assets/models/'+file,'triangles':tris,'mesh_objects':2,'materials':len({m for o in meshes for m in o.data.materials}),'bytes':p.stat().st_size,'roundtrip_pass':True})
 for o in list(check.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.context.window.scene=scene;bpy.data.scenes.remove(check)
for lod in [1,2]:
 for o in [bpy.data.objects['SpaceStation_LOD'+str(lod)]]+list(bpy.data.objects['SpaceStation_LOD'+str(lod)].children):
  for c in o.users_collection:c.hide_viewport=True;c.hide_render=True
bpy.ops.object.select_all(action='DESELECT');core.select_set(True);bpy.context.view_layer.objects.active=core
bpy.data.orphans_purge(do_recursive=True);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'космічна станція.blend'),compress=True)
report={'request':'Remove auxiliary solar-looking panels on central station craft (image 1).','backup':'assets/revisions/hubble_cleanup_2026-11-15','removed':removed,'triangles_removed':before-after,'exports':exports,'station_after_sha256':hashlib.sha256((ROOT/'космічна станція.blend').read_bytes()).hexdigest()}
(HUB/'station_revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(OUT/'panel_removal_revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
info=json.loads((OUT/'asset_info.json').read_text());info['lods']=exports;info['revision_2026_11_15']=report['request'];(OUT/'asset_info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2))
print(json.dumps(report,indent=2))
