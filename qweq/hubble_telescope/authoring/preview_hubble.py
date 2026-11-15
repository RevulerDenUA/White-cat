"""Render asset/LOD/roundtrip/camera QA and leave the comparison scene open in Blender."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/yura/Documents/ChatGPT/Space Mission Design Game');OUT=ROOT/'assets/models/hubble_telescope'
asset=bpy.data.scenes['White Cat | Hubble Telescope'];bpy.context.window.scene=asset
colls=[bpy.data.collections['HUBBLE / LOD'+str(i)] for i in range(3)]
cam=asset.camera

def settings(s,x=1600,y=1200):
 s.world=asset.world;s.render.engine=asset.render.engine;s.eevee.use_gtao=True;s.eevee.gtao_distance=.18;s.eevee.gtao_factor=1.15;s.eevee.taa_render_samples=96
 s.view_settings.view_transform=asset.view_settings.view_transform;s.view_settings.look=asset.view_settings.look;s.view_settings.exposure=asset.view_settings.exposure
 s.render.resolution_x=x;s.render.resolution_y=y;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False

def pose(c,pos,target,scale):
 c.location=pos;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=scale

def lightcopy(s,mult=1):
 for o in asset.objects:
  if o.type=='LIGHT':
   a=o.copy();a.data=o.data.copy();s.collection.objects.link(a);a.location*=mult;a.data.energy*=mult*mult;a.data.size*=mult

def newcam(s,name):
 d=bpy.data.cameras.new(name);c=bpy.data.objects.new(name,d);s.collection.objects.link(c);s.camera=c;return c
# Local append keeps the station source immutable and the comparison self-contained.
review=bpy.data.scenes.new('Style Review | station + Hubble');settings(review,1800,1200)
with bpy.data.libraries.load(str(ROOT/'космічна станція.blend'),link=False) as (a,b):b.collections=['SPACE STATION / LOD0']
station=b.collections[0];review.collection.children.link(station)
inst=bpy.data.objects.new('Hubble | free-flight placement',None);review.collection.objects.link(inst);inst.instance_type='COLLECTION';inst.instance_collection=colls[0];inst.location=(13,-6,0)
inst['note']='Artistic comparison at native asset scales; Hubble is free flying, no station mount.'
lightcopy(review,3)
rc=newcam(review,'Style comparison camera');pose(rc,(21,-35,19),(4,-1,0),26.5)
review['station_diameter_m']=12.76;review['hubble_span_m']=6.6;review['hubble_length_m']=5.075
# The actual camera and its mount in a separate QA scene; target is not part of any GLB.
qascene=bpy.data.scenes.new('Camera Clearance | test target');settings(qascene,1600,900);qascene.collection.children.link(colls[0]);viewcam=bpy.data.objects['Telescope_View_Check'];qascene.collection.objects.link(viewcam);qascene.camera=viewcam
boardmat=bpy.data.materials.new('QA target | emission | excluded');boardmat.use_nodes=True;n=boardmat.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');tx=n.new('ShaderNodeTexImage');im=bpy.data.images.load(str(OUT/'authoring/camera_test_target.png'));im.pack();tx.image=im;boardmat.node_tree.links.new(tx.outputs['Color'],em.inputs['Color']);boardmat.node_tree.links.new(em.outputs[0],out.inputs[0])
me=bpy.data.meshes.new('QA target plane');me.from_pydata([(-8,-22.78,-4.5),(8,-22.78,-4.5),(8,-22.78,4.5),(-8,-22.78,4.5)],[],[(0,1,2,3)]);me.materials.append(boardmat);uv=me.uv_layers.new()
for i,co in enumerate([(1,0),(0,0),(0,1),(1,1)]):uv.data[i].uv=co
board=bpy.data.objects.new('QA target | 20m ahead | excluded',me);qascene.collection.objects.link(board)
# A completely fresh imported GLB is rendered with the imported material.
rt=bpy.data.scenes.new('QA | freshly imported GLB');bpy.context.window.scene=rt;bpy.ops.import_scene.gltf(filepath=str(OUT/'Hubble_Telescope.glb'));settings(rt);lightcopy(rt);rtc=newcam(rt,'GLB roundtrip presentation');pose(rtc,(7,-10,6),(0,-.05,0),8)
# Main orthographic views share scale so shape and LOD changes are easy to compare.
specs=[('hero',asset,0,(7,-10,6),(0,-.05,0),8),('front',asset,0,(0,-12,.05),(0,-.10,0),7.5),('side',asset,0,(12,0,.04),(0,-.12,0),6.1),('rear',asset,0,(0,12,.1),(0,.1,0),7.5),('underside',asset,0,(6,-8,-5),(0,0,0),8),('aperture',asset,0,(.8,-3.7,.6),(0,-1.4,0),2.1),('LOD1',asset,1,(7,-10,6),(0,-.05,0),8),('LOD2',asset,2,(7,-10,6),(0,-.05,0),8),('GLB_roundtrip',rt,0,None,None,None),('station_comparison',review,0,None,None,None),('Telescope_View',qascene,0,None,None,None)]

def visible(lod):
 for i,c in enumerate(colls):c.hide_viewport=i!=lod;c.hide_render=i!=lod

def finish():
 visible(0);pose(cam,(7,-10,6),(0,-.05,0),8)
 for o in list(rt.objects):bpy.data.objects.remove(o,do_unlink=True)
 bpy.context.window.scene=review;bpy.data.scenes.remove(rt)
 for area in bpy.context.screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.region_3d.view_location=(4,-1,0);sp.region_3d.view_distance=31;sp.region_3d.view_rotation=rc.rotation_euler.to_quaternion();sp.region_3d.view_perspective='PERSP';sp.shading.type='MATERIAL';sp.overlay.show_overlays=False;sp.clip_end=1000
 bpy.ops.object.select_all(action='DESELECT');inst.select_set(True);bpy.context.view_layer.objects.active=inst
 bpy.ops.file.pack_all();bpy.data.orphans_purge(do_recursive=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hubble_Telescope.blend'),compress=True)
 state['done']=True;(OUT/'previews/render_status.json').write_text(json.dumps(state,indent=2));print('HUBBLE_PREVIEWS_DONE')

def advance():
 i=state['index']
 if i>=len(specs):finish();return None
 name,s,lod,pos,target,scale=specs[i];visible(lod);bpy.context.window.scene=s
 if pos is not None:pose(s.camera,pos,target,scale)
 s.render.filepath=str(OUT/'previews'/(name+'.png'));bpy.ops.render.render(write_still=True)
 state['completed'].append(name);state['index']+=1;(OUT/'previews/render_status.json').write_text(json.dumps(state,indent=2));return .5
state={'index':0,'completed':[],'done':False};bpy.app.driver_namespace['hubble_previews']=state
(OUT/'previews/render_status.json').write_text(json.dumps(state,indent=2))
bpy.app.timers.register(advance,first_interval=.5)
print('Queued',len(specs),'Hubble previews')
