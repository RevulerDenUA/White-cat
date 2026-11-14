"""White Cat aquatic survey drone. Execute in Blender through Blender MCP.

Procedural editable parts, explicit mounts, construction-aware LODs. Metres;
+X starboard, -Y forward, +Z up. No changes to existing source files.
"""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'qweq/aquatic_rover'
TAU=math.tau

def enum(obj,prop,value):
    choices=[i.identifier for i in obj.bl_rna.properties[prop].enum_items]
    if value in choices:setattr(obj,prop,value)
    else:
        try:setattr(obj,prop,value)
        except (TypeError,ValueError):pass

# Re-running rebuilds only this artifact's in-memory data.
old=bpy.data.scenes.get('White Cat — Aquatic Rover')
if old:
 bpy.context.window.scene=bpy.data.scenes.new('Rebuild temporary context')
 for ob in list(old.objects):bpy.data.objects.remove(ob,do_unlink=True)
 bpy.data.scenes.remove(old)
for c in list(bpy.data.collections):
 if c.name.startswith(('AQUATIC /','STUDIO —')):bpy.data.collections.remove(c)
scene=bpy.data.scenes.new('White Cat — Aquatic Rover')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
studio=bpy.data.collections.new('STUDIO — excluded from game');scene.collection.children.link(studio)
mat=bpy.data.materials.new('Aquatic / rover palette / atlas PBR');mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links
p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
for fn,label in [('aquatic_basecolor.png','Base Color'),('aquatic_orm.png','ORM')]:
 im=bpy.data.images.load(str(OUT/fn),check_existing=True);im.pack()
 if label=='ORM':im.colorspace_settings.name='Non-Color'
 t=nodes.new('ShaderNodeTexImage');t.image=im;t.label=label
 if label=='Base Color':links.new(t.outputs['Color'],p.inputs['Base Color'])
 else:
  split=nodes.new('ShaderNodeSeparateColor');links.new(t.outputs['Color'],split.inputs[0]);links.new(split.outputs['Green'],p.inputs['Roughness']);links.new(split.outputs['Blue'],p.inputs['Metallic'])
mat.use_backface_culling=True
mat.diffuse_color=(.672443,.708376,.693872,1)
parts=[];rotors=[];mounts=[];lod_roots=[]

def mesh(name,vs,fs,tile=0):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
 ob=bpy.data.objects.new(name,me);coll.objects.link(ob);me.materials.append(mat)
 parts.append(ob);paint(ob,tile)
 return ob

def uvpoly(me,p,tile):
 if not me.uv_layers:me.uv_layers.new(name='UVMap')
 x=tile%4*128;y=tile//4*128
 # Plain colors sample padded small patches; illustrated tiles use face projection.
 if tile in [5,7,8,9,11,12,15]:
  axis=max(range(3),key=lambda k:abs(p.normal[k]));axes={0:(1,2),1:(0,2),2:(0,1)}[axis]
  cs=[me.vertices[me.loops[i].vertex_index].co for i in p.loop_indices]
  lo=[min(v[a] for v in cs) for a in axes];hi=[max(v[a] for v in cs) for a in axes]
  for li,v in zip(p.loop_indices,cs):
   u=(v[axes[0]]-lo[0])/max(hi[0]-lo[0],1e-8);w=(v[axes[1]]-lo[1])/max(hi[1]-lo[1],1e-8)
   me.uv_layers.active.data[li].uv=((x+4+120*u)/512,1-(y+124-120*w)/512)
 else:
  for li in p.loop_indices:me.uv_layers.active.data[li].uv=((x+64)/512,1-(y+64)/512)

def paint(ob,tile):
 for poly in ob.data.polygons:uvpoly(ob.data,poly,tile)

def box(name,loc,dims,tile=0,bevel=.025,top=None,side=None):
 x,y,z=[v/2 for v in dims]
 ob=mesh(name,[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)],[(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5),(1,5,7,3),(0,2,6,4)],tile)
 bpy.context.view_layer.objects.active=ob
 if bevel and (level==0 or level==1 and ('buoyancy module' in name or 'landing skid' in name)):
  mod=ob.modifiers.new('Applied silhouette chamfer','BEVEL');mod.width=min(bevel,min(dims)*.40);mod.segments=1;bpy.ops.object.modifier_apply(modifier=mod.name)
 for poly in ob.data.polygons:
  t=top if top is not None and poly.normal.z>.99 else side if side is not None and abs(poly.normal.x)>.99 else tile
  uvpoly(ob.data,poly,t)
 ob.location=loc
 return ob

def cylinder(name,a,b,r,tile=2,n=None,r2=None):
 n=n or segments; r2=r if r2 is None else r2
 d=Vector(b)-Vector(a);length=d.length
 vs=[(rr*math.cos(i*TAU/n),rr*math.sin(i*TAU/n),z) for rr,z in [(r,-length/2),(r2,length/2)] for i in range(n)]
 fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 ob=mesh(name,vs,fs,tile);ob.location=(Vector(a)+Vector(b))/2;ob.rotation_euler=d.to_track_quat('Z','Y').to_euler()
 for p in ob.data.polygons:p.use_smooth=len(p.vertices)==4
 return ob

def beam(name,a,b,width,depth=None,tile=2):
 d=Vector(b)-Vector(a);ob=box(name,(Vector(a)+Vector(b))/2,(width,depth or width,d.length),tile,0)
 ob.rotation_euler=d.to_track_quat('Z','Y').to_euler();return ob

def ring(name,center,axis,profile,tile=1,n=None):
 n=n or segments;vs=[(r*math.cos(i*TAU/n),r*math.sin(i*TAU/n),z) for r,z in profile for i in range(n)]
 fs=[]
 for k in range(len(profile)):
  kk=(k+1)%len(profile)
  for i in range(n):
   j=(i+1)%n;fs.append((k*n+i,k*n+j,kk*n+j,kk*n+i))
 ob=mesh(name,vs,fs,tile);ob.location=center;ob.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
 # Explicit radial profiles give smooth ducts with crisp lips.
 for f in ob.data.polygons:f.use_smooth=True
 return ob

def tube_collar(name,y,r,tile=1,width=.085):
 return ring(name,(0,y,.71),(0,1,0),[(r-.018,-width/2),(r,-width/2),(r,width/2),(r-.018,width/2)],tile)

def mount(name,a,b,w=.10):
 ob=beam(name,a,b,w,tile=2);mounts.append((name,list(a),list(b)));return ob

def thruster(name,center,axis,vertical=False):
 center=Vector(center);axis=Vector(axis).normalized();q=axis.to_track_quat('Z','Y')
 def pt(x,y,z):return center+q@Vector((x,y,z))
 radius=.218 if vertical else .205
 inner=radius-.035
 half=.135 if vertical else .16
 profile=[(inner,-half),(radius-.012,-half),(radius,-half+.026),(radius,half-.026),(radius-.012,half),(inner,half)] if level<2 else [(inner,-half),(radius,-half),(radius,half),(inner,half)]
 shroud=ring(name+' / protective duct',center,axis,profile,1)
 # The leading lip is a material region on the duct, avoiding a stacked ring.
 if level<2:
  for poly in shroud.data.polygons[:segments*2]:uvpoly(shroud.data,poly,3)
 cylinder(name+' / sealed motor',pt(0,0,.035),pt(0,0,half-.012),.054,2,n=max(8,segments//2))
 # Rear motor stators terminate exactly on the inside of the shroud.
 for i in range(3 if level<2 else 0):
  a=i*TAU/3
  beam(name+' / motor stator',pt(.043*math.cos(a),.043*math.sin(a),half-.04),pt((inner+.004)*math.cos(a),(inner+.004)*math.sin(a),half-.04),.025,tile=2)
 begin=len(parts)
 cylinder(name+' / rotor hub',pt(0,0,-.057),pt(0,0,.045),.055,2,n=max(8,segments//2),r2=.045)
 if level<2:
  for i in range(3):
   a=i*TAU/3
   # Swept thick blades, radial span stops short of the duct.
   shape=[(.035,-.022),(inner-.014,-.015),(inner-.018,.035),(.065,.050)]
   vs=[]
   for dz in [-.006,.006]:
    for x,y in shape:
     v=pt(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),-.022+dz);vs.append(v)
   mesh(name+' / impeller blade',vs,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],3)
 else:
  beam(name+' / low LOD impeller',pt(-inner+.02,0,-.02),pt(inner-.02,0,-.02),.045,tile=3)
  beam(name+' / low LOD impeller',pt(0,-inner+.02,-.02),pt(0,inner-.02,-.02),.045,tile=3)
 rotor_parts=parts[begin:]
 for ob in rotor_parts:parts.remove(ob)
 rotors.append((name,center,axis,rotor_parts))

for level in range(3):
 segments=[12,10,8][level]
 coll=bpy.data.collections.new('AQUATIC / LOD'+str(level));scene.collection.children.link(coll)
 root=bpy.data.objects.new('AquaticRover_LOD'+str(level),None);coll.objects.link(root);lod_roots.append(root)
 root['role']='Autonomous underwater survey vehicle';root['forward']='-Y';root['units']='metres';root['reference']='BlueROV2 six-thruster layout; original White Cat adaptation'
 parts=[];rotors=[];mounts=[]
 # Continuous faceted pressure canister with domed, flange-captured ends.
 cylinder('Pressure hull / ceramic barrel',(0,-.72,.71),(0,.72,.71),.315,0,n=16 if level==0 else segments)
 cylinder('Pressure hull / nose shoulder',(0,-.72,.71),(0,-.88,.71),.315,0,r2=.265)
 cylinder('Pressure hull / rear shoulder',(0,.72,.71),(0,.86,.71),.315,0,r2=.265)
 cylinder('Rear pressure bulkhead',(0,.85,.71),(0,.91,.71),.268,2)
 tube_collar('Front locking flange',-.75,.333,2,.08);tube_collar('Rear locking flange',.75,.333,2,.08)
 for y in [-.49,.49]:
  tube_collar('Load-bearing hull band',y,.331,1,.075)
  box('Hull saddle', (0,y,.385),(.40,.16,.11),2,.025)
  box('Chassis crossmember',(0,y,.30),(1.38,.13,.13),2,.018 if level==0 else 0)
 # Bottom-heavy protective chassis, two runner skids and four supports.
 side_meshes={}
 for s in [-1,1]:
  before=set(coll.objects)
  side='Port' if s<0 else 'Starboard'
  box(side+' / landing skid',(s*.63,0,.08),(.17,2.32,.16),1,.065)
  box(side+' / lower longitudinal rail',(s*.63,0,.30),(.12,1.70,.12),2,.016)
  box(side+' / upper outer rail',(s*.80,0,.955),(.09,1.92,.10),1,.018)
  for y in [-.68,.68]:
   mount(side+' / frame upright',(s*.63,y,.16),(s*.63,y,.95),.10)
   box(side+' / upright foot',(s*.63,y,.205),(.22,.21,.15),2,0)
   box(side+' / buoyancy saddle',(s*.57,y,.98),(.55,.23,.09),2,.02 if level==0 else 0)
   # Four pressure-tolerant buoyancy blocks leave the vertical duct unobstructed.
   box(side+' / buoyancy module',(s*.57,y,1.19),(.51,.86,.34),0,.105,top=8 if level==0 else 3,side=12 if level==0 else 0)
   # Low-profile outboard mounts meet the shroud from underneath.
   mount(side+' / thruster outrigger',(s*.63,y,.30),(s*.96,y,.30),.11)
   box(side+' / thruster mounting shoe',(s*.96,y,.35),(.20,.16,.10),2,0)
   direction=(s*math.sqrt(.5),(-1 if y<0 else 1)*math.sqrt(.5),0)
   thruster(side+(' / fore drive' if y<0 else ' / aft drive'),(s*.96,y,.60),direction)
  for y in [-.235,.235]:
   box(side+' / vertical duct bridge',(s*.57,y,1.10),(.17,.14,.10),2,.012 if level==0 else 0)
  thruster(side+' / vertical drive',(s*.57,0,1.13),(0,0,1),True)
  side_meshes[s]=[o for o in coll.objects if o not in before and o.type=='MESH']
 # Paired impellers are opposite-handed. Reflect actual geometry through the
 # centre plane, preserving each authored part's transform and rotor pivot.
 for left,right in zip(side_meshes[-1],side_meshes[1]):
  assert left.name.split(' / ',1)[1].split('.')[0]==right.name.split(' / ',1)[1].split('.')[0]
  bpy.context.view_layer.update()
  reflected=right.data.copy()
  reflected.transform(left.matrix_world.inverted() @ Matrix.Diagonal((-1,1,1,1)) @ right.matrix_world)
  left.data=reflected
 # Single optical system, sealed viewport and paired working lamps.
 ring('Camera / locking bezel',(0,-.901,.71),(0,-1,0),[(.202,-.033),(.245,-.033),(.245,.033),(.202,.033)],1)
 cylinder('Camera / optical window',(0,-.918,.71),(0,-.958,.71),.204,5,r2=.192)
 for s in [-1,1]:
  mount('Lamp / side bracket',(s*.25,-.77,.71),(s*.43,-.87,.71),.075)
  cylinder('Lamp / sealed housing',(s*.43,-.86,.71),(s*.43,-1.00,.71),.096,2)
  cylinder('Lamp / white lens',(s*.43,-.999,.71),(s*.43,-1.014,.71),.074,6)
  if level==0:ring('Lamp / retaining ring',(s*.43,-1.005,.71),(0,1,0),[(.074,-.014),(.091,-.014),(.091,.014),(.074,.014)],1,n=12)
 # Lid over pressure shell has a substantial sealing base, not a floating panel.
 box('Electronics / hatch seating',(0,.05,.986),(.37,.59,.13),1,.04)
 box('Electronics / removable hatch',(0,.05,1.058),(.39,.61,.07),0,.035,top=7 if level<2 else 0)
 cylinder('Acoustic modem / base',(0,.55,.982),(0,.55,1.063),.10,2)
 cylinder('Acoustic modem / transducer',(0,.55,1.06),(0,.55,1.12),.088,1,r2=.068)
 # Downward survey sonar is recessed above the skid plane and bolted to its saddle.
 box('Survey sonar / mount',(0,-.16,.394),(.24,.22,.15),2,.02)
 box('Survey sonar / housing',(0,-.16,.285),(.33,.32,.14),0,.035)
 cylinder('Survey sonar / acoustic face',(0,-.16,.211),(0,-.16,.198),.123,5,n=segments)
 # Rear water-quality cartridge: supported in a protective, flooded intake cage.
 box('Water sensor / bulkhead foot',(0,.924,.71),(.23,.09,.23),2,.025)
 box('Water sensor / intake cartridge',(0,1.015,.71),(.20,.19,.21),2,.025,side=9 if level==0 else 2,top=9 if level==0 else 2)
 if level<2:
  for s in [-1,1]:
   beam('Water sensor / guard',(s*.13,.90,.59),(s*.13,1.13,.59),.035,tile=2)
   beam('Water sensor / guard',(s*.13,.90,.83),(s*.13,1.13,.83),.035,tile=2)
  box('Water sensor / rear guard',(0,1.13,.71),(.30,.045,.29),1,.03)
 # Amber is restricted to two recovery-handle sleeves, both firmly attached.
 if level<2:
  for s in [-1,1]:
   for y in [.76,.95]:beam('Recovery grip / standoff',(s*.57,y,1.34),(s*.57,y,1.41),.04,tile=2)
   beam('Recovery grip / sleeve',(s*.57,.76,1.41),(s*.57,.95,1.41),.044,tile=4)
 # Tiny pressure fittings and sensing heads are below a useful pixel size in LOD2.
 if level==2:
  omit=('Front locking flange','Rear locking flange','Load-bearing hull band','Acoustic modem','Electronics /','Water sensor','Survey sonar')
  for ob in list(parts):
   if ob.name.startswith(omit):parts.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
 # Recalculate every closed part before keeping editable assembly.
 for ob in parts+[o for _,_,_,group in rotors for o in group]:
  bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(ob.data);bm.free()
  ob.parent=root;ob['purpose']=ob.name.split(' / ')[0]
 for name,center,axis,group in rotors:
  pivot=bpy.data.objects.new(name+' / rotation pivot',None);coll.objects.link(pivot);pivot.parent=root;pivot.location=center;pivot.rotation_euler=axis.to_track_quat('Z','Y').to_euler();bpy.context.view_layer.update()
  for ob in group:
   world=ob.matrix_world.copy();ob.parent=pivot;ob.matrix_world=world
  pivot['animation_axis']='local +Z';pivot['purpose']='Optional impeller rotation only; fixed duct and motor'
 root['mounts']=json.dumps(mounts)
 coll.hide_render=level>0;coll.hide_viewport=level>0
 # View layers can hide collections, while exports use explicit object lists later.
 print('LOD',level,'editable meshes',sum(o.type=='MESH' for o in coll.objects),'triangles',sum(len(p.vertices)-2 for o in coll.objects if o.type=='MESH' for p in o.data.polygons))

# Studio cameras and lights are not part of the exported asset.
world=bpy.data.worlds.new('Aquatic / soft studio');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.16,.20,.25,1);bg.inputs[1].default_value=.42;scene.world=world
try:scene.render.engine='BLENDER_EEVEE'
except TypeError:pass
scene.eevee.use_gtao=True;scene.eevee.gtao_distance=3;scene.eevee.gtao_factor=1.15;scene.eevee.taa_render_samples=96
scene.render.resolution_x=1400;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='Standard';enum(scene.view_settings,'look','Medium High Contrast');scene.view_settings.exposure=0;scene.view_settings.gamma=1

def area(name,loc,energy,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;d.color=color
 o=bpy.data.objects.new(name,d);studio.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler()
area('Key softbox',(0,-4,6),550,5,(.88,.94,1));area('Port fill',(-4,-1,2.8),350,4,(.68,.82,1));area('Rear rim',(2.5,4,4),700,3,(1,.87,.69))
camdata=bpy.data.cameras.new('Presentation camera');cam=bpy.data.objects.new('Presentation camera',camdata);studio.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=3.55
cam.location=(3,-4,2.8);cam.rotation_euler=(Vector((0,0,.72))-cam.location).to_track_quat('-Z','Y').to_euler()
# Preserve an artifact-only file, without bringing the original rover or station along.
for old in list(bpy.data.scenes):
 if old!=scene:bpy.data.scenes.remove(old)
for ob in list(bpy.data.objects):
 if not ob.users_scene:bpy.data.objects.remove(ob,do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Aquatic_Rover.blend'),compress=True)
print('Saved editable model',OUT/'Aquatic_Rover.blend')
