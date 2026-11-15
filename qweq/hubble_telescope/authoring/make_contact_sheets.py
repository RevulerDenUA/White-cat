from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parents[1];P=OUT/'previews'
fonts=list(Path('/usr/share/fonts').rglob('NotoSans-Regular.ttf'))
f=ImageFont.truetype(str(fonts[0]),22) if fonts else ImageFont.load_default(size=22)
def sheet(files,labels,name,cols,tile=(600,460)):
 rows=(len(files)+cols-1)//cols;im=Image.new('RGB',(cols*tile[0],rows*tile[1]),(18,26,36));d=ImageDraw.Draw(im)
 for i,(file,label) in enumerate(zip(files,labels)):
  x=i%cols*tile[0];y=i//cols*tile[1];src=Image.open(P/(file+'.png')).convert('RGB');src.thumbnail((tile[0],tile[1]-42));im.paste(src,(x+(tile[0]-src.width)//2,y+(tile[1]-42-src.height)//2));d.text((x+18,y+tile[1]-33),label,font=f,fill=(214,219,217))
 im.save(P/name,quality=94)
sheet(['hero','front','side','rear','station_comparison','Telescope_View'],['WHITE CAT / HUBBLE','FRONT / OPEN APERTURE','SIDE','REAR / SERVICE BAY','STATION STYLE COMPARISON','TELESCOPE VIEW / CLEAR'], 'overview.jpg',2)
sheet(['hero','LOD1','LOD2'],['LOD0 / 1 564 TRIANGLES','LOD1 / 702 TRIANGLES','LOD2 / 304 TRIANGLES'],'LOD_comparison.jpg',3,(600,490))
print('Contact sheets saved')
