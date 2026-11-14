"""Render an audit set through the live Blender UI, one camera per timer tick."""
import bpy
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
studio=bpy.data.collections['STUDIO — excluded from game']
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.025,.037,.055,1)
bg.inputs[1].default_value=.5
if not bpy.data.objects.get('Lower bounce'):
 d=bpy.data.lights.new('Lower bounce','AREA');d.energy=160;d.size=4
 o=bpy.data.objects.new('Lower bounce',d);studio.objects.link(o);o.location=(0,-2,-3);o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1400;scene.render.resolution_y=1200
scene.eevee.taa_render_samples=128
# Only LOD0 is shown. QA copy stays hidden and does not inflate visible geometry.
for c in scene.collection.children:
 if c.name.startswith('AQUATIC /'):c.hide_viewport=c.name!='AQUATIC / LOD0';c.hide_render=c.name!='AQUATIC / LOD0'
views=[('hero',(3,-4,2.9),(0,0,.72),3.35),
 ('rear',(3,4,2.4),(0,0,.71),3.35),
 ('underside',(2.7,3.6,-2.7),(0,0,.66),3.35),
 ('front',(0,-5,1.05),(0,0,.71),2.95),
 ('top',(0,0,5),(0,0,.68),2.95),
 ('mounts',(2.3,-1.5,.9),(.67,-.54,.66),1.35)]
cam=scene.camera

def pose(spec):
 name,loc,target,scale=spec;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 scene.render.filepath=str(OUT/'previews'/(name+'.png'))

def advance():
 state=bpy.app.driver_namespace['aquatic_render_state']
 i=state['index']
 if i>=len(views):
  pose(views[0]);scene['preview_views']='hero, rear, underside, front, top, mounts'
  bpy.data.orphans_purge(do_recursive=True)
  # The authoring file contains only its shared PBR material plus studio data.
  for area in bpy.context.screen.areas:
   if area.type=='VIEW_3D':
    area.spaces.active.region_3d.view_distance=4.2;area.spaces.active.region_3d.view_location=(0,0,.71)
    area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
    area.spaces.active.shading.type='MATERIAL';area.spaces.active.overlay.show_overlays=False
  bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Aquatic_Rover.blend'),compress=True)
  state['done']=True
  print('Aquatic previews complete; authoring file saved')
  return None
 pose(views[i]);bpy.ops.render.render(write_still=True)
 state['index']+=1
 return 0.5
bpy.app.driver_namespace['aquatic_render_state']={'index':0,'done':False}
bpy.app.timers.register(advance,first_interval=.5)
print('Preview rendering queued: six views')
