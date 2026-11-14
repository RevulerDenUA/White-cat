"""Reduce local NASA/PDS products; no network and no changes to original datasets."""
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import math
import re
import shutil
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window, from_bounds
from rasterio.warp import reproject, Resampling
from PIL import Image
from pyproj import CRS, Transformer
from science import AU, C

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT/'tools/package_config.json').read_text())

def read(path):
    return json.loads((ROOT/path).read_text())

def write(path, data):
    p = ROOT/path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def quantiles(values):
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    return {'n': int(len(a)), 'p05': float(np.quantile(a,.05)), 'p50': float(np.quantile(a,.5)), 'p95': float(np.quantile(a,.95))} if len(a) else {'n':0}

def analyze_populations():
    nea = pd.DataFrame(read('data/solar_systems/nasa_exoplanet_archive_pscomppars.json')['planets'])
    exo = read('data/solar_systems/exovista_DEC21_universe1/systems.json')['systems']
    slots=sum(len(s['planets']) for s in exo)
    for system in exo:
        system['planets']=[p for p in system['planets'] if p['mass_earth'] and p['mass_earth']>0 and p['radius_earth']>0 and p['semimajor_axis_au']>0]
    soda = read('data/solar_systems/soda_orion_disks.json')['disks']
    radii = [(.3,1.6,'rocky_candidate'),(1.6,4,'sub_neptune'),(4,8,'ice_giant_candidate'),(8,14.00001,'gas_giant')]
    paired = []
    for system in exo:
        for p in system['planets']:
            m,r=p['mass_earth'],p['radius_earth']
            if m is None or r is None or not (m>0 and r>0): continue
            rho=m*5.9722e24/(4*math.pi*(r*6371008.4)**3/3)
            if .01 <= m <= 3000 and .3<=r<=14 and 100<=rho<=15000:
                paired.append({'mass_earth':m,'radius_earth':r,'density_kg_m3':rho,'source_star_id':system['star']['star_id'],'source_planet_index':p['planet_index']})
    anchors={}
    for lo,hi,key in radii:
        ps=sorted([p for p in paired if lo<=p['radius_earth']<hi],key=lambda x:x['radius_earth'])
        anchors[key]=[ps[i] for i in sorted(set(np.linspace(0,len(ps)-1,min(16,len(ps))).astype(int).tolist()))]
    rows=[]
    for col,unit in [('pl_bmasse','M_earth'),('pl_rade','R_earth'),('pl_orbsmax','au'),('pl_orbper','day'),('pl_orbeccen','1'),('st_mass','M_sun'),('st_teff','K')]:
        rows.append({'field':col,'unit':unit,'missing':int(nea[col].isna().sum()),**quantiles(nea[col].dropna())})
    counts={key:int(((nea.pl_rade>=lo)&(nea.pl_rade<hi)).sum()) for lo,hi,key in radii}
    mask=(nea.pl_bmasse>0)&(nea.pl_rade>0)
    densities=nea.loc[mask,'pl_bmasse']*5.9722e24/(4*math.pi*(nea.loc[mask,'pl_rade']*6371008.4)**3/3)
    q=nea[(nea.pl_orbper>0)&(nea.pl_orbsmax>0)&(nea.st_mass>0)]
    predicted=365.2569*np.sqrt(q.pl_orbsmax**3/q.st_mass)
    mismatches=int((np.abs(predicted/q.pl_orbper-1)>.2).sum())
    detection_counts=nea.discoverymethod.value_counts().to_dict()
    detected=[s['dust_mass_earth'] for s in soda if not s['dust_mass_upper_limit'] and s['dust_mass_earth'] is not None]
    report={'schema_version':'1.0','archive_rows':len(nea),'archive_unique_hosts':int(nea.hostname.nunique()),
            'archive_quantiles':rows,'archive_radius_bin_counts':counts,'discovery_methods':detection_counts,
            'archive_positive_mass_radius_pairs':int(mask.sum()),'archive_pair_density_summary_kg_m3':quantiles(densities),
            'archive_pairs_outside_game_density_envelope':int(((densities<100)|(densities>15000)).sum()),
            'kepler_consistency':{'tested':len(q),'relative_period_discrepancy_gt_20_percent':mismatches,'note':'Composite values and unknown mass provenance; diagnostic only, no inference of false planets.'},
            'exovista':{'systems':len(exo),'raw_slots':slots,'zero_padding_slots_removed':slots-sum(len(s['planets']) for s in exo),'planets':sum(len(s['planets']) for s in exo),'joint_pairs_in_game_envelope':len(paired),'planet_count_quantiles':quantiles([len(s['planets']) for s in exo])},
            'soda':{'rows':len(soda),'dust_upper_limits':sum(bool(s['dust_mass_upper_limit']) for s in soda),'dust_detections':len(detected),'detections_only_mass_earth':quantiles(detected),'note':'Detection-only quantiles are biased. No fit to the censored population; dust is not gas+dust.'},
            'caveats':['Observed archive selection is detection biased. Radius bins are game categories, not measured composition.', 'Archive export lacks mass provenance/uncertainty and can include estimated masses. Do not fit an independent mass-radius law.', 'ExoVista is synthetic; paired anchors preserve its mass-radius relation without claiming formation history.']}
    write('docs/audit/population_statistics.json',report)
    write('data/planets/mass_radius_anchors.json',{'schema_version':'1.0','status':'synthetic_ExoVista_derived','source_ids':['nasa_emac_exovista_dec21'],'anchors':anchors})
    # The source CSV has a units row; skip it without shifting any column names.
    targets=pd.read_csv(ROOT/'data/solar_systems/exovista_DEC21_universe1/target_database.csv',skiprows=[1],low_memory=False)
    stars=[]
    for _,r in targets.sort_values('VMAG').head(64).iterrows():
        if not all(np.isfinite(float(r[k])) for k in ['RA','DEC','VMAG']): continue
        stars.append({'id':f'exovista-target-{int(r.STARID)}','ra_deg':float(r.RA),'dec_deg':float(r.DEC),'v_mag':float(r.VMAG),'spectral_type':str(r.TYPE)})
    write('data/planets/stars.json',{'schema_version':'1.0','status':'target_catalog_subset_not_all_sky','source_ids':['nasa_emac_exovista_dec21'],'frame':'source target RA/DEC J2000; no proper-motion propagation','notes':['64 nearby ExoVista target directions, not a complete bright-star sky. Planet systems are synthetic. Night Sky background must be marked procedural.'],'stars':stars})
    demo=[]
    for s in exo[:3]:
        demo.append({'id':f'exovista-{s["star"]["star_id"]}','star':s['star'],'planets':[{k:v for k,v in p.items() if k!='albedo_file'} for p in s['planets']]})
    write('data/planets/example_systems.json',{'schema_version':'1.0','status':'synthetic','source_ids':['nasa_emac_exovista_dec21'],'units':{'mass_earth':'M_earth','radius_earth':'R_earth','semimajor_axis_au':'au','angles':'deg'},'systems':demo})

def terrain():
    cfg=CONFIG['terrain']; n=cfg['width_cells']; h=cfg['height_cells']; spacing=cfg['spacing_m']
    places=pd.read_csv(ROOT/'data/mars/places/best_tactical.csv')
    interp=pd.read_csv(ROOT/'data/mars/places/best_interp.csv')
    site=places[(places.frame=='SITE')&(places.site==1)].iloc[0]
    dem=ROOT/'data/mars/jezero/M20_JezeroCrater_CTXDEM_20m.tif'
    ortho=ROOT/'data/mars/jezero/M20_JezeroCrater_CTXortho_mosaic_5m.tif'
    dst=ROOT/'assets/terrain'; dst.mkdir(parents=True,exist_ok=True)
    with rasterio.open(dem) as src:
        geographic=CRS.from_proj4('+proj=longlat +R=3396190 +no_defs')
        project=Transformer.from_crs(geographic,src.crs,always_xy=True)
        x,y=project.transform(float(site.longitude),float(site.planetocentric_latitude))
        inv=~src.transform; cc=inv.a*x+inv.b*y+inv.c; rr=inv.d*x+inv.e*y+inv.f
        c0=int(math.floor(cc))-n//2; r0=int(math.floor(rr))-h//2
        halo=cfg['slope_source_halo_cells']
        window=Window(c0-halo,r0-halo,n+2*halo,h+2*halo)
        a=src.read(1,window=window,masked=True)
        valid=~np.ma.getmaskarray(a)
        aa=a.filled(np.nan).astype(float)
        dy,dx=np.gradient(aa,spacing,spacing)
        slope=np.degrees(np.arctan(np.hypot(dx,dy)))[halo:-halo,halo:-halo]
        z=aa[halo:-halo,halo:-halo]; valid=valid[halo:-halo,halo:-halo]&np.isfinite(slope)
        transform=src.window_transform(Window(c0,r0,n,h))
        bounds=rasterio.windows.bounds(Window(0,0,n,h),transform)
        crs=src.crs
        dem_meta={'shape':list(src.shape),'resolution_m':list(src.res),'nodata':src.nodata,'crs_wkt':crs.to_wkt(),'transform':list(src.transform)[:6]}
    if not valid.any(): raise ValueError('Terrain crop has no usable cells')
    offset=math.floor(float(np.nanmin(z[valid])))
    scale=cfg['height_quantization_m']
    encoded=np.zeros(z.shape,dtype='<u2')
    q=np.rint((z[valid]-offset)/scale)+1
    if q.max()>65535: raise ValueError('Heightmap exceeds configured uint16 range')
    encoded[valid]=q.astype('<u2')
    (dst/'heightmap.u16').write_bytes(encoded.tobytes())
    Image.fromarray(encoded).save(dst/'heightmap.png')
    slope_encoded=np.where(valid,np.minimum(np.rint(slope*100),9000),65535).astype('<u2')
    (dst/'slope.u16').write_bytes(slope_encoded.tobytes())
    # Morphology uses the 3x3 maximum slope to avoid declaring a safe cell next to a cliff.
    safe_slope=slope.copy(); safe_valid=valid.copy()
    for dr in [-1,0,1]:
        for dc in [-1,0,1]:
            safe_slope=np.maximum(safe_slope,np.roll(slope,(dr,dc),(0,1)))
            safe_valid &=np.roll(valid,(dr,dc),(0,1))
    safe_valid[[0,-1],:]=False; safe_valid[:,[0,-1]]=False
    trav=np.zeros(z.shape,dtype=np.uint8)
    trav[safe_valid&(safe_slope<=cfg['caution_max_slope_deg'])]=2
    trav[safe_valid&(safe_slope<=cfg['passable_max_slope_deg'])]=1
    (dst/'traversability.u8').write_bytes(trav.tobytes())
    colors=np.array([[70,20,25],[74,156,93],[220,170,45]],dtype=np.uint8)
    Image.fromarray(colors[trav]).save(dst/'traversability.png')
    visual=np.uint8(np.where(valid,np.clip(slope/45,0,1)*255,0))
    Image.fromarray(visual).save(dst/'slope.png')
    ts=cfg['texture_size_px']
    with rasterio.open(ortho) as src:
        if CRS(src.crs).to_dict()!=CRS(crs).to_dict(): raise ValueError('Unexpected ortho/DEM projection parameter mismatch')
        w=from_bounds(*bounds,transform=src.transform).round_offsets(op='floor')
        w=Window(int(w.col_off)-1,int(w.row_off)-1,int(math.ceil(w.width))+3,int(math.ceil(w.height))+3)
        subset=src.read(1,window=w)
        texture=np.zeros((ts,ts),np.uint8)
        tt=rasterio.transform.from_bounds(*bounds,ts,ts)
        reproject(subset,texture,src_transform=src.window_transform(w),src_crs=src.crs,dst_transform=tt,dst_crs=crs,resampling=Resampling.bilinear)
        ortho_meta={'shape':list(src.shape),'resolution_m':list(src.res),'crs_wkt':src.crs.to_wkt(),'transform':list(src.transform)[:6]}
    Image.fromarray(texture).save(dst/'ortho.webp',quality=85,method=6)
    im=Image.fromarray(texture);im.resize((ts//2,ts//2),Image.Resampling.LANCZOS).save(dst/'ortho_lod1.webp',quality=80,method=6)
    records=[]
    filtered=places[(places.frame=='ROVER')&(places.sol>=0)].sort_values(['sol','sclk']).drop_duplicates(['sol'],keep='last')
    # Project geodetic coordinates; Use the GeoTIFF CRS; check agreement with rounded PLACES easting/northing in audit.
    all_delta=[]
    for row in filtered.itertuples():
        if min(row.longitude,row.planetocentric_latitude,row.elevation)==-9999: continue
        px,py=project.transform(row.longitude,row.planetocentric_latitude)
        inv=~transform; col=inv.a*px+inv.b*py+inv.c; line=inv.d*px+inv.e*py+inv.f; ci=int(math.floor(col));ri=int(math.floor(line))
        if not(0<=ci<n and 0<=ri<h and valid[ri,ci]):continue
        hh=float(z[ri,ci]);all_delta.append(float(row.elevation)-hh)
        records.append({'id':f'places-tactical-sol-{int(row.sol)}','sol':int(row.sol),'site':int(row.site),'drive':int(row.drive),'pose':int(row.pose),'sclk_s':float(row.sclk),'longitude_east_deg':float(row.longitude),'latitude_planetocentric_deg':float(row.planetocentric_latitude),'elevation_areoid_m':float(row.elevation),'terrain_height_m':round(hh,3),'world_xyz_m':[round(px-x,3),round(hh-float(site.elevation),3),round(y-py,3)],'cell_col_row':[ci,ri],'cell_status':int(trav[ri,ci])})
    metadata={'schema_version':'1.0','id':cfg['id'],'source_ids':['usgs_jezero_ctx','nasa_pds_places'],'status':'derived_observation_with_game_slope_rules',
      'width':n,'height':h,'spacing_m':spacing,'crs_wkt':crs.to_wkt(),'crs_proj':crs.to_proj4(),'geographic_input':'planetocentric latitude degrees north; longitude degrees east; spherical radius 3396190 m',
      'affine_corner':[transform.a,transform.b,transform.c,transform.d,transform.e,transform.f],'bounds_m':list(bounds),
      'origin_projected_m':[x,y],'origin_elevation_areoid_m':float(site.elevation),'origin_lon_lat_deg':[float(site.longitude),float(site.planetocentric_latitude)],
      'world_axes':{'x':'east','y':'up','z':'south'},'height':h,'vertical_datum':'MOLA areoid; no conversion to ellipsoid height',
      'height_encoding':{'path':'assets/terrain/heightmap.u16','type':'uint16','endian':'little','order':'row-major north-to-south','nodata':0,'offset_m':offset,'scale_m':scale,'decode':'offset_m + (sample-1)*scale_m','max_quantization_error_m':scale/2},
      'slope_encoding':{'path':'assets/terrain/slope.u16','type':'uint16','endian':'little','scale_deg':.01,'nodata':65535,'method':'central differences on original DEM with one-cell halo; 20 m projected spacing'},
      'traversability':{'path':'assets/terrain/traversability.u8','values':{'0':'blocked/unknown/edge','1':'passable by slope proxy','2':'caution'},'neighborhood_max':'3x3','safe_max_slope_deg':cfg['passable_max_slope_deg'],'caution_max_slope_deg':cfg['caution_max_slope_deg'],'status':'game_assumption; not certified rover safety'},
      'texture':{'path':'assets/terrain/ortho.webp','width_px':ts,'height_px':ts,'pixel_size_m':n*spacing/ts,'orientation':'top=north; left=west','processing':'bilinear warp to DEM crop bounds; grayscale original, no invented color'},
      'limitations':['20 m DEM and 5 m ortho cannot resolve wheel-scale rocks or sand sinkage.', 'Projected spacing is approximately ground meters near the standard parallel.', 'PLACES and CTX elevations need not coincide; place rover on terrain height for collision, preserve measured elevation for display.'],
      'valid_cell_count':int(valid.sum()),'slope_deg':quantiles(slope[valid]),'height_m':quantiles(z[valid])}
    write('assets/terrain/metadata.json',metadata)
    write('data/rover/routes.json',{'schema_version':'1.0','id':'places-landing-region','source_ids':['nasa_pds_places','usgs_jezero_ctx'],'status':'observed_waypoints_not_certified_drivable_route','terrain_id':cfg['id'],'sampling':'last tactical rover pose per sol inside crop; chronological chord segments are not traverses','waypoints':records})
    rover_inter=interp[interp.frame=='ROVER']
    write('docs/audit/geospatial.json',{'schema_version':'1.0','dem':dem_meta,'ortho':ortho_meta,'crs_projection_parameters_equal':True,'crs_wkt_names_equal':False,'raster_origins_equal':False,'alignment_action':'warp ortho onto the exact DEM crop bounds; never align by source pixel indices','places_tactical_rows':len(places),'places_interp_rows':len(interp),'places_interp_rover_rows':len(rover_inter),'places_interp_unknown_elevation_rows':int((rover_inter.elevation==-9999).sum()),'retained_waypoints':len(records),'places_minus_dem_height_m':quantiles(all_delta),'landing_reprojected_minus_PLACES_easting_northing_m':[x-float(site.easting),y-float(site.northing)],'note':'At Site 1 reprojected longitude/planetocentric latitude match printed PLACES easting/northing within 1 mm; rounding is preserved. Never transfer PLACES image-pixel indices to this crop.'})

def weather():
    summaries=[];audit=[]
    ns={'p':'http://pds.nasa.gov/pds4/pds/v1'}
    selected={'ATS':['ATS_LOCAL_TEMP1'],'PS':['BAROCAP1_PRESSURE'],'RHS':['HUMICAP_A_HUMIDITY'],'WS':['BOOM1_HORIZONTAL_WIND_SPEED']}
    for p in sorted((ROOT/'data/weather/raw').rglob('*.CSV.gz')):
        xml=p.with_name(p.name.replace('.CSV.gz','.xml'));root=ET.parse(xml).getroot()
        label_fields=root.findall('.//p:Field_Delimited',ns)
        code=next((code for code in ['ATS','PS','RHS','WS','TIRS','RDS'] if f'CAL_{code}_' in p.name),None)
        if code is None:raise ValueError(f'Unknown MEDA product {p.name}')
        df=pd.read_csv(p,compression='gzip',low_memory=False)
        if len(df.columns)!=len(label_fields):raise ValueError(f'PDS label/header count mismatch {p.name}')
        fields={}; aliases=[]
        for header,field in zip(df.columns,label_fields):
            label=field.findtext('p:name',namespaces=ns)
            if header!=label:
                known_aliases={('RHS','THERMOCAP2_TEMP_UNCERTAINTY','THERMOCAP1_TEMP_UNCERTAINTY','13'),('WS','BOOM1_ALG_STATE_STABLE','BOOM1_ALG_IN_STABLE_STATE','16'),('WS','BOOM2_ALG_STATE_STABLE','BOOM2_ALG_IN_STABLE_STATE','17')}
                number=field.findtext('p:field_number',namespaces=ns)
                if (code,header,label,number) not in known_aliases:
                    raise ValueError(f'PDS label/header mismatch {p.name}: {header} != {label}')
                aliases.append({'field_number':int(number),'csv_name':header,'xml_name':label,'action':'Use positional XML metadata and CSV name. Known RHS duplicate-name typo or WS naming alias.'})
            fields[header]=field
        audit.append({'id':p.stem,'sol':int(p.parent.name[4:]),'code':code,'rows':len(df),'fields':len(fields),'label_aliases':aliases})
        for name in selected.get(code,[]):
            f=fields[name];a=pd.to_numeric(df[name],errors='coerce');mask=np.isfinite(a)
            for tag in ['missing_constant','invalid_constant','unknown_constant','not_applicable_constant','error_constant']:
                for e in f.findall('.//p:'+tag,ns):mask &= a!=float(e.text)
            # Physical-screen rules are declared game preparation filters, not PDS science-quality flags.
            unit=f.findtext('p:unit',default='1',namespaces=ns)
            if code=='ATS':mask &=a.between(100,350)
            elif code=='PS':mask &=a.between(100,1500)
            elif code=='RHS':mask &=a.between(0,100)
            elif code=='WS':
                mask &=a.between(0,100)
                mask &=(df.BOOM1_ALG_STATE_STABLE==1)&(df.ROVER_STILL==1)
            vals=a[mask]
            summaries.append({'id':f'meda-sol-{int(p.parent.name[4:])}-{name.lower()}','sol':int(p.parent.name[4:]),'field':name,'unit':unit,'rows_total':len(df),'rows_used':len(vals),'rows_rejected':len(df)-len(vals),**quantiles(vals),'min':float(vals.min()) if len(vals) else None,'max':float(vals.max()) if len(vals) else None})
    write('data/rover/weather_samples.json',{'schema_version':'1.0','source_ids':['nasa_pds_meda'],'status':'observed_subset_derived','filters':{'ATS':'100..350 K','PS':'100..1500 Pa','RHS':'0..100 percent','WS':'0..100 m/s; BOOM1_ALG_STATE_STABLE=1 and ROVER_STILL=1'},'limitations':['One sensor channel per selected product; uneven daytime coverage, not climatology or full-sol means.','Percentiles are empirical sample percentiles, not measurement uncertainty.','Physical plausibility screens supplement available instrument state; no claim of complete science QA.'],'samples':summaries})
    write('docs/audit/meda_products.json',{'schema_version':'1.0','products':audit,'raw_summary_not_used':'Original mars_weather.json includes unfiltered per-column summaries and instrument diagnostics. Recomputed selected physical channels from CSV+XML.'})

def ephemeris():
    def parse(d,body):
        text=d['result']
        required=['Center body name: Sun (10)','Output units    : AU-D','Reference frame : Ecliptic of J2000.0','GEOMETRIC']
        if not all(s in text for s in required):raise ValueError('Horizons center, units or frame mismatch')
        if f'({body})' not in text.split('Center body name:')[0]:raise ValueError('Wrong target')
        rows=[]
        for r in csv.reader(io.StringIO(text.split('$$SOE')[1].split('$$EOE')[0])):
            if len(r)<8:continue
            rows.append([float(r[0]),*map(float,r[2:8])])
        return rows
    mars=parse(read('data/ephemeris/mars_heliocentric_vectors_2026-11-14_to_2028-11-15.json'),'499')
    earth=parse(read('.local/earth_horizons.json'),'399')
    if len(mars)!=len(earth):raise ValueError('Epoch count mismatch')
    out=[]
    for m,e in zip(mars,earth):
        if m[0]!=e[0]:raise ValueError('Epoch mismatch')
        d=float(np.linalg.norm(np.array(m[1:4])-e[1:4])*AU)
        out.append({'jd_tdb':m[0],'earth_position_m':[v*AU for v in e[1:4]],'mars_position_m':[v*AU for v in m[1:4]],'distance_m':d,'one_way_geometric_delay_s':d/C})
    write('data/missions/earth_mars_ephemeris.json',{'schema_version':'1.0','source_ids':['jpl_horizons'],'frame':'heliocentric Ecliptic J2000; geometric states; TDB epochs','status':'derived_ephemeris','step_s':86400,'first_jd_tdb':out[0]['jd_tdb'],'last_jd_tdb':out[-1]['jd_tdb'],'earth_query_url':read('.local/earth_horizons.json')['query_url'],'limitations':['Simultaneous geometric distance/c; not retarded light-time, solar-conjunction radio availability or scheduling.','Linear interpolation is for UI only; do not extrapolate outside cache; TDB is not UTC.'],'samples':out})

def images():
    items=read('data/rover_images/images_manifest.json')['items'];chosen=[]
    wanted=[('MCZ_LEFT',800),('NAVCAM_RIGHT',800),('FRONT_HAZCAM_LEFT_A',1000),('SHERLOC_WATSON',1800),('PIXL_MCC',2000)]
    # Prefer different camera/sol combinations; fall back deterministically to distinct unselected entries.
    for camera,sol in wanted:
        match=next((x for x in items if x['camera_id']==camera and x['sol']==sol and x not in chosen),None)
        if match is None:match=next(x for x in items if x not in chosen and x['camera_id']!= 'SKYCAM')
        chosen.append(match)
    out=[];dst=ROOT/'assets/images';dst.mkdir(parents=True,exist_ok=True)
    previous=read('assets/images/manifest.json')['images'] if (dst/'manifest.json').exists() else []
    for x in chosen:
        with Image.open(ROOT/'data/rover_images'/x['filename']) as im:
            im=im.convert('RGB');im.thumbnail((CONFIG['images']['max_edge_px'],)*2)
            path=f'assets/images/{x["image_id"]}.webp';im.save(ROOT/path,quality=CONFIG['images']['webp_quality'],method=6)
            out.append({k:x[k] for k in ['image_id','camera_id','sol','caption','credit','source_page']}|{'id':x['image_id'],'path':path,'width':im.width,'height':im.height,'processing':'resize and lossy WebP only; real Mars photograph, not a generated planet texture'})
    for old in previous:
        if old['path'] not in {x['path'] for x in out}:
            obsolete=ROOT/old['path']
            if obsolete.parent!=dst:raise ValueError('Refusing to remove non-gallery file')
            obsolete.unlink(missing_ok=True)
    write('assets/images/manifest.json',{'schema_version':'1.0','source_ids':['nasa_mars_raw_images'],'images':out})

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('steps',nargs='*',default=['populations','terrain','weather','ephemeris','images'])
    steps={'populations':analyze_populations,'terrain':terrain,'weather':weather,'ephemeris':ephemeris,'images':images}
    for name in parser.parse_args().steps:
        steps[name]();print(name,'OK')
