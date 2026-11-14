"""Compact GLB export and round-trip validation. Run after build_aquatic_rover.py."""
import bpy,bmesh,json,math,struct,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'qweq/aquatic_rover'
author=bpy.context.scene
stats=[]
for c in list(bpy.data.collections):
 if c.name.startswith('QA / reimported GLB'):
  for ob in list(c.objects):bpy.data.objects.remove(ob,do_unlink=True)
  bpy.data.collections.remove(c)

def metrics(objects):
 bpy.context.view_layer.update()
 obs=[o for o in objects if o.type=='MESH'];verts=[o.matrix_world@v.co for o in obs for v in o.data.vertices]
 tri=0;bad=0;nonmanifold=0
 for o in obs:
  o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
  for t in o.data.loop_triangles:
   a,b,c=[o.matrix_world@o.data.vertices[i].co for i in t.vertices]
   bad+=((b-a).cross(c-a).length<1e-10)
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6);nonmanifold+=sum(not e.is_manifold for e in bm.edges);bm.free()
 tree=KDTree(len(verts))
 for i,v in enumerate(verts):tree.insert(v,i)
 tree.balance()
 return {'triangles':tri,'mesh_objects':len(obs),'materials':len({s.material for o in obs for s in o.material_slots if s.material}),
  'bounds_m':[[round(min(v[k] for v in verts),7),round(max(v[k] for v in verts),7)] for k in range(3)],
  'dimensions_m':[round(max(v[k] for v in verts)-min(v[k] for v in verts),6) for k in range(3)],
  'non_finite_coordinates':sum(not all(math.isfinite(x) for x in v) for v in verts),'degenerate_triangles':int(bad),
  'non_manifold_edges_after_global_weld':nonmanifold,'mirror_max_error_m':max(tree.find(Vector((-v.x,v.y,v.z)))[2] for v in verts)}
for lod in range(3):
 coll=bpy.data.collections['AQUATIC / LOD'+str(lod)];coll.hide_viewport=False;bpy.context.view_layer.update()
 source=[o for o in coll.objects if o.type=='MESH'];expected=metrics(source)
 exportscene=bpy.data.scenes.new('Temporary GLB assembly');bpy.context.window.scene=exportscene
 for src in source:
  ob=bpy.data.objects.new(src.name,src.data.copy());exportscene.collection.objects.link(ob);ob.matrix_world=src.matrix_world.copy();ob.select_set(True)
 bpy.context.view_layer.objects.active=next(iter(exportscene.objects));bpy.ops.object.join()
 ob=bpy.context.object;ob.name='AquaticRover_LOD'+str(lod);ob.data.materials.clear()
 mat=next(s.material for s in source[0].material_slots if s.material);ob.data.materials.append(mat)
 for p in ob.data.polygons:p.material_index=0
 exportscene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 ob['asset']='White Cat Aquatic Rover';ob['lod']=lod;ob['units']='metres';ob['forward_blender']='-Y'
 assembled=metrics([ob])
 path=OUT/('Aquatic_Rover'+('' if lod==0 else '_LOD'+str(lod))+'.glb')
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_animations=False,export_cameras=False,export_lights=False,export_extras=True)
 for obj in list(exportscene.objects):bpy.data.objects.remove(obj,do_unlink=True)
 bpy.context.window.scene=author;bpy.data.scenes.remove(exportscene)
 # A separate clean scene proves the exported artifact is self-contained.
 check=bpy.data.scenes.new('Round trip LOD'+str(lod));bpy.context.window.scene=check
 bpy.ops.import_scene.gltf(filepath=str(path))
 actual=metrics(list(check.objects))
 assert actual['triangles']==expected['triangles'],(lod,actual,expected)
 assert actual['mesh_objects']==1 and actual['materials']==1
 assert actual['non_finite_coordinates']==0 and actual['degenerate_triangles']==0
 # A global weld fuses intentionally separate mounting shells; its contact-edge
 # count is diagnostic only. Compare actual triangle locations for fidelity.
 def centroids(objects):
  values=[]
  for obj in objects:
   if obj.type!='MESH':continue
   obj.data.calc_loop_triangles()
   for t in obj.data.loop_triangles:
    values.append(sum((obj.matrix_world@obj.data.vertices[i].co for i in t.vertices),Vector())/3)
  return values
 centres=centroids(source);kd=KDTree(len(centres))
 for i,c in enumerate(centres):kd.insert(c,i)
 kd.balance()
 centroid_error=max(kd.find(c)[2] for c in centroids(check.objects))
 assert centroid_error<1e-5
 actual['max_triangle_centroid_error_m']=centroid_error
 assert max(abs(a-b) for a,b in zip(actual['dimensions_m'],expected['dimensions_m']))<1e-5
 assert actual['mirror_max_error_m']<1e-5
 # Read embedded image headers rather than report a presumed source resolution.
 blob=path.read_bytes();jsonlen=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+jsonlen]);binstart=20+jsonlen+8
 images=[]
 for im in doc.get('images',[]):
  assert 'uri' not in im
  bv=doc['bufferViews'][im['bufferView']];offset=binstart+bv.get('byteOffset',0)
  assert blob[offset:offset+8]==b'\x89PNG\r\n\x1a\n'
  w,h=struct.unpack_from('>II',blob,offset+16);images.append({'name':im.get('name'),'mime':im['mimeType'],'width':w,'height':h,'bytes':bv['byteLength']})
 assert len(images)==2 and all(i['width']==512 and i['height']==512 for i in images)
 assert all('uri' not in b for b in doc['buffers'])
 record={'lod':lod,'file':path.name,'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest(),'source_parts':expected,'source_assembled':assembled,'round_trip':actual,'textures':images,'primitives':sum(len(m['primitives']) for m in doc['meshes'])}
 stats.append(record)
 # Retain an explicit GLB inspection copy for later visual comparison.
 if lod==0:
  for obj in check.objects:
   if obj.type=='MESH':
    rt=obj.copy();rt.data=obj.data.copy();rt.name='RoundTrip_AquaticRover';
    qa=bpy.data.collections.new('QA / reimported GLB — hidden');author.collection.children.link(qa);qa.objects.link(rt);qa.hide_render=True;qa.hide_viewport=True
 for obj in list(check.objects):bpy.data.objects.remove(obj,do_unlink=True)
 bpy.context.window.scene=author;bpy.data.scenes.remove(check)
 coll.hide_viewport=lod>0
(OUT/'validation.json').write_text(json.dumps({'validated_by':'Blender 3.6.23 GLB export and fresh-scene reimport','topology_note':'Editable individual parts are closed manifold shells. GLB contains independent overlapping mechanical components; global-weld contact statistics are diagnostic, not a fused printable solid.','lods':stats},ensure_ascii=False,indent=2)+'\n')
# Remove imported orphan textures/materials and source-model data from authoring file.
qa=bpy.data.collections.get('QA / reimported GLB — hidden')
if qa:
 for ob in qa.objects:
  ob.data.materials.clear();ob.data.materials.append(mat)
bpy.data.orphans_purge(do_recursive=True)
print([(s['file'],s['round_trip']['triangles'],s['bytes']) for s in stats])
