"""Fail-closed offline package validation; optional raw-data cross-checks when originals exist."""
from pathlib import Path
import hashlib
import io
import json
import math
import re
import struct
import sys
import unittest

import jsonschema
import numpy as np
from PIL import Image
from pyproj import CRS,Transformer
from prepare_data import ROOT,read
from science import FORMULAS,AU,MU_SUN

class PackageChecks(unittest.TestCase):
    def test_json_contracts(self):
        index=read('schemas/index.json');schema=read(index['schema_file']);jsonschema.Draft202012Validator.check_schema(schema)
        for path,ref in index['resources'].items():
            with self.subTest(path=path):
                v=jsonschema.Draft202012Validator({'$ref':ref,'$defs':schema['$defs']})
                v.validate(read(path))
                # Scientific JSON rejects non-standard NaN/Infinity tokens.
                json.loads((ROOT/path).read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))

    def test_formula_examples_and_independent_references(self):
        data=read('data/physics/formulas.json');self.assertEqual(len(data['formulas']),31)
        for f in data['formulas']:
            with self.subTest(formula=f['id']):
                self.assertEqual(set(f['variables']),set(f['example']['inputs']))
                self.assertTrue(all(v['unit'] for v in f['variables'].values()))
                actual=FORMULAS[f['id']](**f['example']['inputs']);expected=f['example']['expected']
                self.assertTrue(math.isclose(actual,expected,rel_tol=f['example']['relative_tolerance']))
        self.assertAlmostEqual(FORMULAS['hohmann_time'](AU,1.523679*AU,MU_SUN)/86400,258.866,delta=.01)
        self.assertAlmostEqual(FORMULAS['departure_c3'](AU,1.523679*AU,MU_SUN)/1e6,8.671,delta=.01)
        self.assertAlmostEqual(FORMULAS['signal_delay'](AU),499.0047838,places=6)
        self.assertAlmostEqual(FORMULAS['gravity'](5.9722e24,6371008.4),9.8202764,places=7)

    def test_planet_pairs_and_atmosphere_fractions(self):
        a=read('data/planets/mass_radius_anchors.json')['anchors'];types=read('data/planets/planet_types.json')['types']
        for t in types:
            pairs=a[t['id']];self.assertEqual(len(pairs),16)
            for p in pairs:
                self.assertGreaterEqual(p['radius_earth'],t['radius_earth_range'][0]);self.assertLessEqual(p['radius_earth'],t['radius_earth_range'][1])
                rho=p['mass_earth']*5.9722e24/(4*math.pi*(p['radius_earth']*6371008.4)**3/3)
                self.assertTrue(100<=rho<=15000);self.assertAlmostEqual(rho,p['density_kg_m3'])
        for p in read('data/planets/atmospheres.json')['presets']:
            fractions=p['mole_fractions']
            if fractions:self.assertAlmostEqual(sum(fractions.values()),1,places=10)
            self.assertTrue(all(0<=v<=1 for v in fractions.values()))

    def test_terrain_binary_and_png_encoding(self):
        m=read('assets/terrain/metadata.json');n=m['width']*m['height']
        a=np.fromfile(ROOT/'assets/terrain/heightmap.u16',dtype='<u2').reshape(m['height'],m['width'])
        b=np.array(Image.open(ROOT/'assets/terrain/heightmap.png'))
        self.assertTrue(np.array_equal(a,b))
        self.assertEqual((ROOT/'assets/terrain/slope.u16').stat().st_size,n*2)
        t=np.fromfile(ROOT/'assets/terrain/traversability.u8',dtype=np.uint8).reshape(a.shape)
        self.assertEqual(t.size,n);self.assertTrue(set(np.unique(t))<={0,1,2})
        self.assertTrue(np.all(t[[0,-1],:]==0));self.assertTrue(np.all(t[:,[0,-1]]==0))
        self.assertEqual(m['vertical_datum'],'MOLA areoid; no conversion to ellipsoid height')

    def test_coordinates(self):
        m=read('assets/terrain/metadata.json');src=CRS.from_proj4('+proj=longlat +R=3396190 +no_defs')
        forward=Transformer.from_crs(src,CRS.from_wkt(m['crs_wkt']),always_xy=True)
        reverse=Transformer.from_crs(CRS.from_wkt(m['crs_wkt']),src,always_xy=True)
        x0,y0=m['origin_projected_m'];lon,lat=m['origin_lon_lat_deg'];x,y=forward.transform(lon,lat)
        self.assertAlmostEqual(x,x0,places=7);self.assertAlmostEqual(y,y0,places=7)
        for w in read('data/rover/routes.json')['waypoints']:
            x,y=forward.transform(w['longitude_east_deg'],w['latitude_planetocentric_deg']);lo,la=reverse.transform(x,y)
            self.assertAlmostEqual(lo,w['longitude_east_deg'],places=9);self.assertAlmostEqual(la,w['latitude_planetocentric_deg'],places=9)
            self.assertAlmostEqual(x-x0,w['world_xyz_m'][0],delta=.001);self.assertAlmostEqual(y0-y,w['world_xyz_m'][2],delta=.001)
        # NED -> scene is a proper right-handed rotation, not a reflection.
        rotation=np.array([[0,1,0],[0,0,-1],[-1,0,0]])
        self.assertAlmostEqual(np.linalg.det(rotation),1)
        self.assertTrue(np.array_equal(rotation@np.array([3,4,5]),[4,-5,-3]))

    def test_ephemeris(self):
        d=read('data/missions/earth_mars_ephemeris.json');s=d['samples'];self.assertEqual(len(s),733)
        for i,r in enumerate(s):
            if i:self.assertEqual(r['jd_tdb']-s[i-1]['jd_tdb'],1)
            distance=math.dist(r['earth_position_m'],r['mars_position_m'])
            self.assertAlmostEqual(distance/r['distance_m'],1,places=12)
            self.assertAlmostEqual(distance/299792458,r['one_way_geometric_delay_s'],places=9)
            self.assertTrue(.3*AU<distance<3*AU)

    def test_images_open_and_models_have_embedded_images(self):
        for p in (ROOT/'assets').rglob('*'):
            if p.suffix in ['.png','.webp']:
                with self.subTest(path=p.name):
                    with Image.open(p) as im:im.load();self.assertGreater(im.width,0)
        manifest=read('assets/images/manifest.json');self.assertEqual(len(manifest['images']),5)
        for x in manifest['images']:self.assertTrue(x['credit']);self.assertTrue(x['source_page'].startswith('https://'));self.assertTrue((ROOT/x['path']).is_file())
        for m in read('assets/models/manifest.json')['models']:
            b=(ROOT/m['path']).read_bytes();magic,version,size=struct.unpack_from('<III',b)
            self.assertEqual((magic,version,size),(0x46546c67,2,len(b)));length,kind=struct.unpack_from('<II',b,12)
            d=json.loads(b[20:20+length]);self.assertEqual(kind,0x4e4f534a)
            self.assertTrue(all('uri' not in x for x in d.get('buffers',[])));self.assertTrue(all('bufferView' in x for x in d.get('images',[])))
            start=20+length+8
            for im in d.get('images',[]):
                view=d['bufferViews'][im['bufferView']];offset=start+view.get('byteOffset',0)
                with Image.open(io.BytesIO(b[offset:offset+view['byteLength']])) as texture:texture.load();self.assertGreater(texture.width,0);self.assertLessEqual(max(texture.size),1024)

    def test_sources_and_links(self):
        ids={s['id'] for s in read('data/sources.json')['sources']}
        files=[ROOT/p for p in read('schemas/index.json')['resources']]
        def visit(x):
            if isinstance(x,dict):
                if 'source_ids' in x:self.assertTrue(set(x['source_ids'])<=ids,x['source_ids'])
                if 'path' in x:self.assertFalse(Path(x['path']).is_absolute());self.assertTrue((ROOT/x['path']).is_file(),x['path'])
                for v in x.values():visit(v)
            elif isinstance(x,list):
                for v in x:visit(v)
            elif isinstance(x,str):self.assertNotIn('/home/',x);self.assertNotIn('C:\\Users\\',x)
        for p in files:visit(json.loads(p.read_text()))
        self.assertEqual(len(ids),len(read('data/sources.json')['sources']))

    def test_engineering_corrections_and_no_double_counting(self):
        d=read('data/missions/edl.json');self.assertEqual(next(p for p in d['phases'] if p['phase']=='powered_descent')['velocity_m_s'],85)
        launches=read('data/missions/launchers.json')['launchers'];self.assertIsNone(launches[0]['flight_reference']['spacecraft_payload_mass_kg']);self.assertIsNone(launches[0]['c3_performance_curve'])
        self.assertIsNone(launches[1]['c3_at_payload_to_mars_kg'])
        spec=read('data/rover/rover_specs.json');self.assertIsNone(spec['reference']['battery_capacity_wh'])
        self.assertEqual(spec['reference']['battery_capacity_ah_each'],43)
        component_ids={c['id'] for c in read('data/missions/components.json')['components']}
        self.assertEqual(len(component_ids),len(read('data/missions/components.json')['components']))
        for p in spec['profiles']:self.assertTrue(set(p['instrument_ids'])<=component_ids);self.assertIn('game_assumption',p['status'])

    def test_release_manifest(self):
        manifest_path=ROOT/'data/package_manifest.json'
        self.assertTrue(manifest_path.is_file(),'Run tools/finalize_manifest.py before release validation')
        m=read('data/package_manifest.json')
        self.assertLess(m['release_bytes_excluding_manifest'],20_000_000)
        for x in m['files']:
            p=ROOT/x['path'];self.assertEqual(p.stat().st_size,x['bytes']);self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),x['sha256'])
        paths={x['path'] for x in m['files']}
        for p in read('schemas/index.json')['resources']:self.assertIn(p,paths)
        self.assertTrue(all(not p.endswith(('.tif','.gz','.pdf')) for p in paths))

    @unittest.skipUnless((ROOT/'data/mars/jezero/M20_JezeroCrater_CTXDEM_20m.tif').exists(),'Original DEM not part of distributed package')
    def test_archive_height_and_slope_crosscheck(self):
        import rasterio
        m=read('assets/terrain/metadata.json');z=np.fromfile(ROOT/'assets/terrain/heightmap.u16',dtype='<u2').reshape(m['height'],m['width']);s=np.fromfile(ROOT/'assets/terrain/slope.u16',dtype='<u2').reshape(z.shape)
        with rasterio.open(ROOT/'data/mars/jezero/M20_JezeroCrater_CTXDEM_20m.tif') as r:
            x0,y0=m['affine_corner'][2],m['affine_corner'][5];inv=~r.transform;col,row=round(inv.a*x0+inv.b*y0+inv.c),round(inv.d*x0+inv.e*y0+inv.f)
            for cr,rr in [(100,100),(256,256),(400,200),(200,400)]:
                a=r.read(1,window=rasterio.windows.Window(col+cr-1,row+rr-1,3,3)).astype(float)
                expected=a[1,1];decoded=m['height_encoding']['offset_m']+(int(z[rr,cr])-1)*m['height_encoding']['scale_m'];self.assertLessEqual(abs(expected-decoded),.01001)
                dx=(a[1,2]-a[1,0])/40;dy=(a[2,1]-a[0,1])/40;theta=math.degrees(math.atan(math.hypot(dx,dy)));self.assertLessEqual(abs(int(s[rr,cr])*.01-theta),.00501)

if __name__=='__main__':
    unittest.main(verbosity=2)
