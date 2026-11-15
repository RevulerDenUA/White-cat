from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
p=Path(__file__).with_name('camera_test_target.png')
im=Image.new('RGB',(1600,900),(10,18,30));d=ImageDraw.Draw(im)
for x in range(0,1601,100):d.line((x,0,x,900),fill=(27,47,64),width=2)
for y in range(0,901,100):d.line((0,y,1600,y),fill=(27,47,64),width=2)
for r in (90,180,300):d.ellipse((800-r,450-r,800+r,450+r),outline=(58,93,120),width=3)
d.line((740,450,860,450),fill=(201,144,57),width=4);d.line((800,390,800,510),fill=(201,144,57),width=4)
fonts=list(Path('/usr/share/fonts').rglob('NotoSans-Regular.ttf'))
f=ImageFont.truetype(str(fonts[0]),32) if fonts else ImageFont.load_default(size=32);sm=ImageFont.truetype(str(fonts[0]),23) if fonts else ImageFont.load_default(size=23)
d.text((800,120),'TELESCOPE VIEW',font=f,fill=(214,219,217),anchor='mm');d.text((800,170),'OPTICAL AXIS  |  +Z glTF  |  -Y BLENDER',font=sm,fill=(120,135,139),anchor='mm')
d.text((800,750),'20 m test target - no telescope geometry in frame',font=sm,fill=(214,219,217),anchor='mm')
for xy,col,label in [((180,100),(201,144,57),'UP LEFT'),((1420,100),(35,100,180),'UP RIGHT'),((180,800),(60,140,110),'LOW LEFT'),((1420,800),(140,80,110),'LOW RIGHT')]:
 x,y=xy;d.rectangle((x-12,y-12,x+12,y+12),fill=col);d.text((x,y+35),label,font=sm,fill=(214,219,217),anchor='mm')
im.save(p)
