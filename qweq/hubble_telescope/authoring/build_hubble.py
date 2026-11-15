"""White Cat Hubble: deliberately rebuilt profile geometry and three independent LODs.
Run through the connected Blender. Source files are read/append only, never saved.
"""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path('/home/yura/Documents/ChatGPT/Space Mission Design Game');OUT=ROOT/'assets/models/hubble_telescope'
scene=bpy.data.scenes.new('White Cat | Hubble Telescope');bpy.context.window.scene=scene
for s in list(bpy.data.scenes):
 if s!=scene:bpy.data.scenes.remove(s)
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)
scene.name='White Cat | Hubble Telescope'
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
mat=bpy.data.materials.new('White Cat | Hubble | atlas PBR');mat.use_nodes=True;mat.use_backface_culling=True
bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
for file,role in [('hubble_basecolor.png','color'),('hubble_orm.png','orm')]:
 im=bpy.data.images.load(str(OUT/file));im.pack();tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;tx.interpolation='Linear'
 if role=='color':mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
 else:
  im.colorspace_settings.name='Non-Color';sp=mat.node_tree.nodes.new('ShaderNodeSeparateColor');mat.node_tree.links.new(tx.outputs['Color'],sp.inputs[0]);mat.node_tree.links.new(sp.outputs['Green'],bs.inputs['Roughness']);mat.node_tree.links.new(sp.outputs['Blue'],bs.inputs['Metallic'])
mat.diffuse_color=(.672443151,.708375752,.693871737,1)

def uv(tile,u=.5,v=.5,pad=7):
 return ((tile%4*256+pad+(256-2*pad)*u)/1024,1-(tile//4*256+pad+(256-2*pad)*(1-v))/1024)

def make(name,vs,fs,tiles=0,uvs=None,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.materials.append(mat)
 # Consistent outward normals on the closed subassemblies. Open panels are wound explicitly.
 layer=me.uv_layers.new(name='AtlasUV')
 for i,p in enumerate(me.polygons):
  tile=tiles[i] if isinstance(tiles,list) else tiles
  p.use_smooth=smooth
  for j,li in enumerate(p.loop_indices):layer.data[li].uv=uv(tile,*(uvs[i][j] if uvs else (.5,.5)))
 ob=bpy.data.objects.new(name,me);coll.objects.link(ob);ob.parent=root;parts.append(ob);return ob

def recalc(ob):
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(ob.data);bm.free();ob.data.update()

def profile(name,rings,n,tiles,closed=False,caps=(False,False),decor=None,end_tile=None):
 # Ring=(y,radius,slope). slope shears the sunshade lip longitudinally with Z.
 vs=[(r*math.cos(i*math.tau/n),y+slope*math.sin(i*math.tau/n),r*math.sin(i*math.tau/n)) for y,r,slope in rings for i in range(n)]
 fs=[];ts=[];us=[]
 for k in range(len(rings) if closed else len(rings)-1):
  kk=(k+1)%len(rings)
  for i in range(n):
   j=(i+1)%n;fs.append((k*n+i,kk*n+i,kk*n+j,k*n+j));ts.append(tiles[k] if isinstance(tiles,list) else tiles)
   us.append([(i/n,0),(i/n,1),(j/n,1),(j/n,0)] if decor and k in decor else [(.5,.5)]*4)
 for k,cap in enumerate(caps):
  if cap:
   off=0 if k==0 else (len(rings)-1)*n;f=tuple(off+i for i in (range(n) if k==0 else reversed(range(n))))
   fs.append(f);ts.append(end_tile if end_tile is not None else (tiles[-1] if isinstance(tiles,list) else tiles));us.append([(.5+vs[v][0]/(2*max(r[1] for r in rings)),.5+vs[v][2]/(2*max(r[1] for r in rings))) for v in f] if decor else [(.5,.5)]*n)
 ob=make(name,vs,fs,ts,us,smooth=False);recalc(ob)
 # Circumferential smoothing only for the large circular hull, with sharp profile transitions.
 if n>=12:
  for p in ob.data.polygons:p.use_smooth=len(p.vertices)==4
  ob.data.use_auto_smooth=True;ob.data.auto_smooth_angle=math.radians(35)
 return ob

def box(name,loc,size,tile=0,bevel=0,decor=False,omit=None):
 x,y,z=[v/2 for v in size];vs=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
 fs=[(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5),(1,5,7,3),(0,2,6,4)]
 ob=make(name,vs,fs,tile);ob.location=loc
 if bevel:
  bpy.context.view_layer.objects.active=ob;md=ob.modifiers.new('Single edge chamfer','BEVEL');md.width=bevel;md.segments=1;bpy.ops.object.modifier_apply(modifier=md.name)
 if omit is not None:
  bm=bmesh.new();bm.from_mesh(ob.data);axis,sign=omit;bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.normal[axis]*sign>.99],context='FACES');bm.to_mesh(ob.data);bm.free();ob.data.update()
 if decor:
  for p in ob.data.polygons:
   axis=max(range(3),key=lambda a:abs(p.normal[a]));axes={0:(1,2),1:(0,2),2:(0,1)}[axis]
   coords=[ob.data.vertices[ob.data.loops[li].vertex_index].co for li in p.loop_indices]
   for li,v in zip(p.loop_indices,coords):
    vv=[]
    for a in axes:
     lo=min(c[a] for c in coords);hi=max(c[a] for c in coords);vv.append((v[a]-lo)/max(hi-lo,1e-7))
    ob.data.uv_layers.active.data[li].uv=uv(tile,*vv)
 return ob

def rod(name,a,b,r,tile=2,n=8,cap_a=False,cap_b=False):
 d=Vector(b)-Vector(a);q=d.to_track_quat('Y','Z')
 ob=profile(name,[(-d.length/2,r,0),(d.length/2,r,0)],n,tile,caps=(cap_a,cap_b));ob.location=(Vector(a)+Vector(b))/2;ob.rotation_euler=q.to_euler();return ob

def face_panel(name,center,u,v,width,height,tile,bevel=.035,thickness=.035):
 # Eight corner chamfer panel, only visible front and edge walls; no buried backside.
 u=Vector(u);v=Vector(v);normal=u.cross(v).normalized();c=Vector(center);a=width/2;b=height/2;q=min(bevel,a*.2,b*.2)
 outline=[(-a+q,-b),(a-q,-b),(a,-b+q),(a,b-q),(a-q,b),(-a+q,b),(-a,b-q),(-a,-b+q)] if q else [(-a,-b),(a,-b),(a,b),(-a,b)]
 N=len(outline);vs=[tuple(c+u*x+v*y+normal*t) for t in [0,thickness] for x,y in outline]
 fs=[tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 us=[[(x/width+.5,y/height+.5) for x,y in outline]]+[[ (.5,.5)]*4 for _ in range(N)]
 return make(name,vs,fs,[tile]+[0]*N,us)

def joined(obs,name,pivot):
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();ob=bpy.context.object;ob.name=name
 scene.cursor.location=pivot;bpy.ops.object.origin_set(type='ORIGIN_CURSOR');bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 ob.parent=root;ob.data.materials.clear();ob.data.materials.append(mat)
 for p in ob.data.polygons:p.material_index=0
 # Remove loose vertices left when deleting buried caps, then triangulate.
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(ob.data);bm.free()
 # Triangulation is applied, so the authoring budget equals the exported budget.
 md=ob.modifiers.new('Final game triangulation','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=md.name)
 return ob

def count(obs):return sum(len(o.data.loop_triangles) for o in obs if o.type=='MESH')
def tri(ob):ob.data.calc_loop_triangles();return len(ob.data.loop_triangles)
records=[];collections=[]
for lod in range(3):
 coll=bpy.data.collections.new('HUBBLE / LOD'+str(lod));scene.collection.children.link(coll);collections.append(coll)
 root=bpy.data.objects.new('Hubble_Telescope' if lod==0 else 'Hubble_Telescope_LOD'+str(lod),None);coll.objects.link(root);root.empty_display_size=.35
 root['asset']='White Cat / authorial Hubble adaptation';root['reference_credit']='NASA 3D Resources; DigitalSpace Corporation';root['units']='metres';root['forward_Blender']='-Y';root['forward_glTF']='+Z';root['artist_scale']='5.075 m long, 6.60 m span relative to 12.76 m station';root['lod']=lod
 parts=[];n=[24,18,12][lod]
 if lod==0:
  rings=[(-1.4,.74,0),(-1.31,.77,0),(-1.17,.77,0),(-1.10,.74,0),(1.05,.74,0),(1.12,.80,0),(1.31,.80,0)]
  profile('Optical barrel / ceramic bands',rings,n,[2,1,2,8,2,1],decor={3})
 elif lod==1:profile('Optical barrel', [(-1.4,.74,0),(-1.28,.77,0),(-1.11,.74,0),(1.09,.74,0),(1.3,.80,0)],n,[2,1,8,2],decor={2})
 else:profile('Optical barrel',[(-1.4,.74,0),(1.09,.74,0),(1.39,.80,0)],n,[8,1],decor={0})
 # One continuous open-front cavity: sleeve, recessed shoulder and stop share vertices.
 # The only open boundary is the buried outer rear rim, inside the ceramic barrel.
 if lod==0:
  hood=[(-1.39,.74,0),(-1.49,.80,0),(-2.36,.80,-.23),(-2.44,.75,-.23),(-2.42,.67,-.23),(-2.30,.63,-.23),(-1.39,.63,0),(-1.32,.59,0)]
  hood_tiles=[2,0,0,0,1,1,2]
 elif lod==1:
  hood=[(-1.40,.78,0),(-2.44,.78,-.23),(-2.42,.65,-.23),(-1.40,.63,0),(-1.32,.59,0)]
  hood_tiles=[0,0,1,2]
 else:
  hood=[(-1.40,.74,0),(-2.44,.80,-.23),(-2.42,.64,-.23),(-1.40,.62,0),(-1.32,.58,0)]
  hood_tiles=[0,0,1,2]
 cavity=profile('Sunshade / continuous sealed optical cavity',hood,n,hood_tiles,caps=(False,True),end_tile=5)
 cap=cavity.data.polygons[-1]
 if cap.normal.y>0:
  cavity.data.flip_normals();cavity.data.update()
 assert cavity.data.polygons[-1].normal.y<-.99
 cavity['construction']='Inner sleeve, shoulder and stop are one connected mesh; no open seam in the bore.'
 # Wider octagonal aft service bay; transverse facet seams and vents use the atlas.
 if lod==0:rear=[(1.30,.80,0),(1.40,.94,0),(1.51,.97,0),(2.10,.97,0),(2.22,.88,0),(2.28,.78,0)]
 elif lod==1:rear=[(1.30,.80,0),(1.48,.97,0),(2.10,.97,0),(2.28,.78,0)]
 else:rear=[(1.30,.80,0),(1.48,.97,0),(2.28,.88,0),(2.405,.60,0)]
 rear_tiles=[2,0,1,0,2] if lod==0 else ([2,9,2] if lod==1 else [2,9,2])
 if lod<2:
  rear += [(2.28,.70,0),(2.34,.70,0),(2.405,.60,0)];rear_tiles += [2,2,2]
 service=profile('Octagonal service bus',rear,8,rear_tiles,caps=(False,True),decor=set(range(len(rear)-1)),end_tile=12)
 # Large readable rear access panels. No individual screw or louvre geometry.
 if lod==0:
  for i in range(8):
   a=(i+.5)*math.tau/8;normal=Vector((math.cos(a),0,math.sin(a)));u=Vector((-math.sin(a),0,math.cos(a)));v=Vector((0,-1,0));center=normal*(.97*math.cos(math.pi/8)+.004)+Vector((0,1.81,0))
   face_panel('Service cassette '+str(i+1),center,u,v,.64,.50,9 if i%2==0 else 6,.035,.035)
 # Barrel external equipment reduced to two broad sensor housings.
 if lod==0:
  for s in [-1,1]:
   box('Navigation sensor housing',(s*.56,-.65,.46),(.24,.47,.24),2,bevel=.035,omit=(0,-s))
   ob=face_panel('Navigation sensor aperture',(s*.56,-.892,.46),(1,0,0),(0,0,1),.16,.13,5,.025,.012)
  # Shallow low-poly communication discs, on the service bay shoulders.
  for s in [-1,1]:
   rod('Antenna neck',(s*.68,.83,.45),(s*.95,.83,.65),.038,2,n=6)
   ant=profile('Communication puck',[(-.025,.14,0),(.025,.19,0),(.055,.16,0)],8,0,caps=(True,True));ant.location=(s*.99,.83,.68);ant.rotation_euler=Vector((s*.7,0,.7)).to_track_quat('Y','Z').to_euler()
 if lod<2:
  # Two restrained amber longitudinal orientation keys on the ceramic barrel.
  for s in [-1,1]:
   ob=face_panel('Observation direction key',(s*.54,-.20,.53),(-.707,0,s*.707),(0,-1,0),.16,.50,11,.015,.006)
 # Solar drive yokes are part of the fixed body. Far end penetrates the wing hinge.
 for s in [-1,1]:
  rod('Solar cross shaft',(s*.76,.64,0),(s*1.54,.64,0),.085 if lod<2 else .10,2,n=[8,6,4][lod])
  # Housing axis is X; center location sets the independent panel hinge.
  h=profile('Ceramic solar drive',[(-.16,.15,0),(-.12,.20,0),(.12,.20,0),(.16,.15,0)] if lod<2 else [(-.15,.18,0),(.15,.18,0)],[8,6,4][lod],0,caps=(True,True));h.location=(s*1.30,.64,0);h.rotation_euler.z=-math.pi/2
  if lod==0:
   h=profile('Amber motor band',[(-.025,.204,0),(.025,.204,0)],8,3);h.location=(s*1.30,.64,0);h.rotation_euler.z=-math.pi/2
 # Merge static geometry once; wing transforms remain independent for articulation.
 bodyparts=parts[:];body=joined(bodyparts,'Telescope_Body'+('' if lod==0 else '_LOD'+str(lod)),(0,0,0));parts=[]
 wings=[]
 for s,label in [(-1,'L'),(1,'R')]:
  x=s*2.10;start=len(parts)
  # Both wings cover X=1.50..3.30, Y=-.96..2.24. Their top surface faces +Z.
  wing=box('Solar frame '+label,(s*2.4,.64,0),(1.8,3.2,.095),2,bevel=.04 if lod<2 else 0)
  # Remove full front/back of solid frame; a perimeter surrounds inset cell/rear quads.
  bm=bmesh.new();bm.from_mesh(wing.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if abs(f.normal.z)>.999],context='FACES');bm.to_mesh(wing.data);bm.free();wing.data.update()
  a=1.8/2;b=3.2/2;inner_a=a-.062;inner_b=b-.062;cx=s*2.4;cy=.64
  # Single shared border, front cells and back skin. No coplanar layers.
  v=[(cx+sx*rr[0],cy+sy*rr[1],z) for rr,z in [((a-(.04 if lod<2 else 0),b-(.04 if lod<2 else 0)),.0475),((inner_a,inner_b),.0475)] for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  f=[(i,(i+1)%4,4+(i+1)%4,4+i) for i in range(4)]+[(4,5,6,7)]
  uvs=[[ (.5,.5)]*4 for _ in range(4)]+[[(0,0),(1,0),(1,1),(0,1)]]
  make('Solar cells '+label,v,f,[0,0,0,0,4],uvs)
  make('Solar backside '+label,[(cx-inner_a,cy-inner_b,-.0475),(cx-inner_a,cy+inner_b,-.0475),(cx+inner_a,cy+inner_b,-.0475),(cx+inner_a,cy-inner_b,-.0475)],[(0,1,2,3)],10,[[(0,0),(0,1),(1,1),(1,0)]])
  # Back border joins to frame so it remains opaque from every direction.
  v=[(cx+sx*rr[0],cy+sy*rr[1],-.0475) for rr in [(a-(.04 if lod<2 else 0),b-(.04 if lod<2 else 0)),(inner_a,inner_b)] for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
  make('Solar rear border '+label,v,[(i,4+i,4+(i+1)%4,(i+1)%4) for i in range(4)],2)
  if lod<2:
   box('Wing center spar '+label,(cx,.64,-.073),(1.78,.085,.08),2,omit=(2,1))
  wingob=joined(parts[start:],'Solar_Panel_'+label+('' if lod==0 else '_LOD'+str(lod)),(s*1.50,.64,0));wingob['hinge_axis_Blender']='+X';wingob['hinge_axis_glTF']='+X';wingob['deployment_pose']='open; rotate local X for solar tracking';wings.append(wingob)
  parts=parts[:start]
 view=bpy.data.objects.new('Telescope_View' if lod==0 else 'Telescope_View_LOD'+str(lod),None);coll.objects.link(view);view.parent=root;view.location=(0,-2.78,0);view.rotation_euler=(0,0,0);view.empty_display_size=.20;view.empty_display_type='ARROWS';view['look_axis']='Blender -Y / glTF +Z; Blender +Z / glTF +Y is up; neutral mount rotation';view['optical_clearance_m']=.11;view['glTF_position_m']='0, 0, 2.78';view['optical_axis_Blender']='world -Y';view['optical_axis_glTF']='world +Z'
 tris=[tri(o) for o in [body]+wings];records.append({'lod':lod,'triangles':sum(tris),'by_mesh':dict(zip([o.name for o in [body]+wings],tris)),'meshes':3,'material_count':1,'view_node':view.name})
 coll.hide_viewport=lod>0;coll.hide_render=lod>0
# Inspection camera is kept in the .blend, with exact identity under the mount.
qa=bpy.data.collections.new('STUDIO | not exported');scene.collection.children.link(qa)
vc=bpy.data.cameras.new('Telescope view | 50 mm');viewcam=bpy.data.objects.new('Telescope_View_Check',vc);qa.objects.link(viewcam);viewcam.parent=bpy.data.objects['Telescope_View'];viewcam.location=(0,0,0);viewcam.rotation_euler=Vector((0,-1,0)).to_track_quat('-Z','Y').to_euler();vc.lens=50;vc.clip_start=.01;vc.clip_end=10000
world=bpy.data.worlds.new('Hubble studio');world.use_nodes=True;scene.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.025,.035,.052,1);bg.inputs[1].default_value=.6
try:scene.render.engine='BLENDER_EEVEE'
except TypeError:pass
scene.eevee.use_gtao=True;scene.eevee.gtao_distance=.18;scene.eevee.gtao_factor=1.15;scene.eevee.taa_render_samples=96
for name,loc,power,size,color in [('Key',(1,-5,7),1800,7,(.90,.95,1)),('Rim',(-4,4,5),2100,6,(.7,.83,1)),('Fill',(-5,-2,3),1100,6,(1,.90,.78)),('Lower',(2,-1,-4),650,5,(.7,.83,1))]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power*.65;d.shape='DISK';d.size=size;d.color=color;d.specular_factor=.2
 ob=bpy.data.objects.new(name,d);qa.objects.link(ob);ob.location=loc;ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
c=bpy.data.cameras.new('Presentation');cam=bpy.data.objects.new('Presentation',c);qa.objects.link(cam);scene.camera=cam;c.type='ORTHO';c.ortho_scale=8.5;cam.location=(7,-10,6);cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene['design']='Rebuilt Hubble silhouette with open swept baffle, ceramic barrel, octagonal service cassettes, independent blue solar wings. Artistic dimensions relative to station.'
scene['reference']='https://science.nasa.gov/3d-resources/hubble-space-telescope-a/ | DigitalSpace Corporation'
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  area.spaces.active.region_3d.view_location=(0,0,0);area.spaces.active.region_3d.view_distance=10;area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion();area.spaces.active.shading.type='MATERIAL';area.spaces.active.overlay.show_overlays=False
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
(OUT/'build_stats.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Hubble_Telescope.blend'),compress=True)
