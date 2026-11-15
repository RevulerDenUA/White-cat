"""Independently inspect container, node axes, index budgets and embedded texture channels."""
from pathlib import Path
from PIL import Image,ImageChops
import json,struct,io,math,hashlib
OUT=Path(__file__).resolve().parents[1]
records=[]
def quat_rotate(q,v):
 x,y,z,w=q;vx,vy,vz=v
 tx=2*(y*vz-z*vy);ty=2*(z*vx-x*vz);tz=2*(x*vy-y*vx)
 return [vx+w*tx+y*tz-z*ty,vy+w*ty+z*tx-x*tz,vz+w*tz+x*ty-y*tx]
for lod in range(3):
 file='Hubble_Telescope'+('' if lod==0 else '_LOD'+str(lod))+'.glb';data=(OUT/file).read_bytes();magic,version,total=struct.unpack_from('<4sII',data);assert magic==b'glTF' and version==2 and total==len(data)
 jl,jt=struct.unpack_from('<II',data,12);j=json.loads(data[20:20+jl]);bl,bt=struct.unpack_from('<II',data,20+jl);buf=data[28+jl:28+jl+bl];assert bt==0x004e4942
 assert len(j['meshes'])==3 and len(j['materials'])==1
 assert not j.get('extensionsRequired') and all('uri' not in x for x in j['images']+j['buffers'])
 tris=0;prim=0
 for mesh in j['meshes']:
  for p in mesh['primitives']:
   assert p.get('mode',4)==4;tris+=j['accessors'][p['indices']]['count']//3;prim+=1
 assert tris==[1564,702,304][lod] and prim==3
 mat=j['materials'][0];assert mat.get('alphaMode','OPAQUE')=='OPAQUE' and not mat.get('doubleSided',False)
 def tex(index):
  im=j['images'][j['textures'][index]['source']];v=j['bufferViews'][im['bufferView']];off=v.get('byteOffset',0)
  return Image.open(io.BytesIO(buf[off:off+v['byteLength']])).convert('RGB')
 bc=tex(mat['pbrMetallicRoughness']['baseColorTexture']['index']);mr=tex(mat['pbrMetallicRoughness']['metallicRoughnessTexture']['index'])
 bsrc=Image.open(OUT/'hubble_basecolor.png').convert('RGB');msrc=Image.open(OUT/'hubble_orm.png').convert('RGB')
 base_exact=ImageChops.difference(bc,bsrc).getbbox() is None;mr_exact=all(ImageChops.difference(mr.getchannel(c),msrc.getchannel(c)).getbbox() is None for c in ['G','B'])
 assert base_exact and mr_exact and bc.size==(1024,1024) and mr.size==(1024,1024)
 nd={n['name']:n for n in j['nodes']};root=nd['Hubble_Telescope'];view=nd['Telescope_View'];camera=nd['Telescope_View_Check']
 assert all(abs(a-b)<1e-6 for a,b in zip(view['translation'],[0,0,2.78]))
 assert all(abs(a-b)<1e-6 for a,b in zip(quat_rotate(camera.get('rotation',[0,0,0,1]),[0,0,-1]),[0,0,1]))
 assert all(abs(a-b)<1e-6 for a,b in zip(quat_rotate(camera.get('rotation',[0,0,0,1]),[0,1,0]),[0,1,0]))
 assert 'translation' not in root and 'rotation' not in root and 'scale' not in root
 assert all(n.get('scale',[1,1,1])==[1,1,1] for n in j['nodes'])
 for label,sgn in [('L',-1),('R',1)]:assert all(abs(a-b)<1e-6 for a,b in zip(nd['Solar_Panel_'+label]['translation'],[sgn*1.5,0,-.64]))
 records.append({'file':file,'triangles':tris,'primitives':prim,'materials':1,'images_embedded':len(j['images']),'basecolor_pixels_exact':base_exact,'roughness_metallic_channels_exact':mr_exact,'glTF_forward':[0,0,1],'glTF_up':[0,1,0],'view_translation':view['translation'],'camera_quaternion_xyzw':camera['rotation'],'root_identity':True,'external_resources':False,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(OUT/'glb_validation.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
