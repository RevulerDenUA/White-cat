"""Regression check: embedded glTF texture channels must match authored PNG pixels."""
import io,json,struct
from pathlib import Path
from PIL import Image,ImageChops
OUT=Path(__file__).resolve().parents[1]
report=json.loads((OUT/'validation.json').read_text())
for record in report['lods']:
 path=OUT/record['file'];blob=path.read_bytes();n=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+n])
 assert not doc['materials'][0].get('doubleSided',False)
 for entry in doc['images']:
  assert 'uri' not in entry
  v=doc['bufferViews'][entry['bufferView']];start=28+n+v.get('byteOffset',0)
  embedded=Image.open(io.BytesIO(blob[start:start+v['byteLength']])).convert('RGB')
  source=Image.open(OUT/(entry['name']+'.png')).convert('RGB')
  assert ImageChops.difference(embedded,source).getbbox() is None,(path,entry['name'])
 record['embedded_texture_pixels_match_source']=True
 record['backface_culling']=True
 print(path.name,record['round_trip']['triangles'],'triangles; texture channels verified')
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
