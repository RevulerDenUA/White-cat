"""Deterministic atlas authored from shader values sampled in mars rover.blend."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,math
OUT=Path(__file__).resolve().parents[1]
p=json.loads((OUT/'source_palette.json').read_text())
def srgb(v): return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
C={k:tuple(srgb(v) for v in p[k]['Base Color'][:3]) for k in ['Ceramic white','Graphite','Gunmetal','Amber','Solar blue','Dark optics']}
roles=['Ceramic white','Graphite','Gunmetal','Amber','Solar blue','Dark optics','Ceramic white','Graphite','Ceramic white','Ceramic white','Graphite','Ceramic white','Gunmetal','Ceramic white','Graphite','Ceramic white']
base=Image.new('RGB',(1024,1024));orm=Image.new('RGB',(1024,1024));d=ImageDraw.Draw(base);o=ImageDraw.Draw(orm)
for i,k in enumerate(roles):
 x=i%4*256;y=i//4*256;d.rectangle((x,y,x+255,y+255),fill=C[k]);o.rectangle((x,y,x+255,y+255),fill=(255,round(p[k]['Roughness']*255),round(p[k]['Metallic']*255)))
 def line(coords,role='Graphite',width=2):d.line([(x+a,y+b) for a,b in coords],fill=C[role],width=width)
 def rect(coords,role,outline=None,width=1):d.rectangle(tuple([x+coords[0],y+coords[1],x+coords[2],y+coords[3]]),fill=C[role] if role else None,outline=C[outline] if outline else None,width=width)
 if i==4:
  # Four columns, twelve rows. All bus bars and cell boundaries are texture.
  rect((6,6,249,249),'Graphite')
  for row in range(12):
   for col in range(4):
    a=11+col*59;b=11+row*19.5
    d.rectangle((x+int(a),y+int(b),x+int(a+55),y+int(b+16)),fill=C['Solar blue'])
    d.line((x+a+10,y+b+1,x+a+10,y+b+15),fill=(62,85,110),width=1)
    d.line((x+a+43,y+b+1,x+a+43,y+b+15),fill=(62,85,110),width=1)
  for a in (7,128,248):line([(a,8),(a,247)],'Gunmetal',2)
 if i in (6,9,11,13,15):
  d.rounded_rectangle((x+11,y+11,x+244,y+244),radius=13,outline=C['Gunmetal'],width=2)
  for a in (23,232):
   for b in (23,232):
    d.ellipse((x+a-3,y+b-3,x+a+3,y+b+3),fill=C['Gunmetal']);line([(a-2,b),(a+2,b)],'Graphite',1)
 if i==6:
  rect((92,173,163,205),'Graphite');rect((105,183,150,193),'Amber');line([(12,191),(80,191)],'Gunmetal',2)
 if i==7:
  rect((12,12,243,243),'Gunmetal')
  for yy in range(22,236,15):
   rect((21,yy,234,yy+8),'Graphite');line([(22,yy+9),(234,yy+9)],'Gunmetal',1)
 if i==8:
  # Full cylindrical unwrap: eight broad panels rather than many tiny brackets.
  for xx in range(0,257,32):line([(min(xx,255),0),(min(xx,255),255)],'Gunmetal',1)
  for yy in (24,231):line([(0,yy),(255,yy)],'Gunmetal',1)
  for xx in range(14,256,32):rect((xx,31,xx+4,38),'Graphite');rect((xx,217,xx+4,224),'Graphite')
 if i==9:
  rect((20,35,235,46),'Amber');rect((47,140,209,211),'Graphite')
  for yy in range(147,207,10):rect((54,yy,202,yy+3),'Gunmetal')
 if i==10:
  # Panel backside: broad graphite honeycomb-like structural ribs.
  for xx in (25,128,230):line([(xx,8),(xx,247)],'Gunmetal',3)
  for yy in (30,128,225):line([(8,yy),(247,yy)],'Gunmetal',2)
 if i==11:
  for xx in (88,145):
   d.polygon([(x+xx,y+154),(x+xx+29,y+128),(x+xx,y+102),(x+xx+14,y+102),(x+xx+43,y+128),(x+xx+14,y+154)],fill=C['Amber'])
 if i==12:
  for rr in (38,76,106):d.ellipse((x+128-rr,y+128-rr,x+128+rr,y+128+rr),outline=C['Graphite'],width=3)
  for a in range(0,360,90):
   xx=128+math.cos(math.radians(a))*88;yy=128+math.sin(math.radians(a))*88
   d.ellipse((x+xx-4,y+yy-4,x+xx+4,y+yy+4),fill=C['Amber'])
base.save(OUT/'hubble_basecolor.png',optimize=True);orm.save(OUT/'hubble_orm.png',optimize=True)
(OUT/'atlas_palette.json').write_text(json.dumps({'source':'mars rover.blend; exact shader linear values in source_palette.json','srgb_8bit':C,'tiles':roles,'size':1024},ensure_ascii=False,indent=2))
print(C)
