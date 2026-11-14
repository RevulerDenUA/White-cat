"""Small original PBR atlas; source rover shader values are stored alongside the asset."""
from PIL import Image, ImageDraw
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'qweq/aquatic_rover'
palette=json.loads((OUT/'source_palette.json').read_text())
def srgb(v): return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
roles=['Ceramic white','Graphite','Gunmetal','Solar blue','Amber','Dark optics','Ceramic white','Ceramic white','Solar blue','Gunmetal','Graphite','Gunmetal','Ceramic white','Graphite','Solar blue','Ceramic white']
base=Image.new('RGB',(512,512));orm=Image.new('RGB',(512,512));d=ImageDraw.Draw(base)
for i,role in enumerate(roles):
 p=palette[role];c=tuple(srgb(v) for v in p['Base Color'][:3]); x=i%4*128;y=i//4*128
 d.rectangle((x,y,x+127,y+127),fill=c)
 rough=p['Roughness'];metal=p['Metallic']
 if i==6: c=(222,236,231);d.rectangle((x,y,x+127,y+127),fill=c);rough=.2;metal=.1
 ImageDraw.Draw(orm).rectangle((x,y,x+127,y+127),fill=(255,round(rough*255),round(metal*255)))
 if i in [7,8,11,12,15]:
  seam=(61,77,82) if i not in [8,11] else (23,36,47)
  d.rounded_rectangle((x+10,y+10,x+117,y+117),radius=10,outline=seam,width=2)
  for xx in [x+18,x+109]:
   for yy in [y+18,y+109]:
    d.ellipse((xx-3,yy-3,xx+3,yy+3),fill=(90,109,114));d.line((xx-2,yy,xx+2,yy),fill=(40,52,58))
  if i==7:
   d.rounded_rectangle((x+46,y+51,x+82,y+77),radius=4,fill=(46,63,68))
   d.rectangle((x+55,y+61,x+73,y+65),fill=(203,144,57))
  if i==12:
   d.line((x+12,y+85,x+115,y+85),fill=seam,width=2)
   d.rounded_rectangle((x+36,y+29,x+92,y+43),radius=5,fill=(39,59,70))
 if i==9:
  for yy in range(y+16,y+114,12):
   d.rounded_rectangle((x+18,yy,x+110,yy+5),radius=2,fill=(26,40,46))
 if i==5:
  d.ellipse((x+14,y+14,x+113,y+113),outline=(40,69,84),width=3)
  d.arc((x+27,y+22,x+97,y+104),200,270,fill=(74,111,132),width=3)
base.save(OUT/'aquatic_basecolor.png',optimize=True);orm.save(OUT/'aquatic_orm.png',optimize=True)
print('Two 512 x 512 RGB atlases generated')
