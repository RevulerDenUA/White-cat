"""Whitelist the distributable Git-visible files and record release SHA-256 checksums."""
from pathlib import Path
import hashlib
import json
import subprocess
from prepare_data import ROOT,read,write

SELF='data/package_manifest.json'
OWNERS={
 'data/physics/':('PASHA, VANIA','SI константи / формули й обчислені приклади'),
 'data/planets/':('VANIA, PASHA','Planet generator catalog, paired anchors, examples і target stars'),
 'data/missions/':('PASHA, YURA','Mission engineering / траєкторії / зв’язок; null збережено'),
 'data/rover/':('SASHA, MISHA','Rover reference, умовні профілі, координати й MEDA subset'),
 'assets/terrain/':('SASHA, MISHA','Суміщена CTX ділянка та slope/passability proxy'),
 'assets/models/':('MISHA','Embedded NASA visual GLB і геометричні metadata'),
 'assets/images/':('MISHA, YURA','5 демонстраційних WebP і credits'),
 'docs/team/':('відповідний учасник','Персональний integration handoff'),
 'docs/audit/':('YURA','Початковий inventory, diagnostics і перетворення'),
 'schemas/':('YURA, PASHA','JSON Schema2020-12; mapping контрактів'),
 'lib/':('SASHA, VANIA, PASHA','Готовий browser/Node runtime helper'),
 'tools/':('YURA','Відтворювана підготовка, контракти й offline validation'),
 'tests/':('YURA, розробники','Автоматична регресійна перевірка runtime'),
 'examples/':('усі','Локальна browser integration перевірка'),
 '.github/':('YURA','CI перевірки пакета'),
}

def files():
    out=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT)
    return sorted({p.decode() for p in out.split(b'\0') if p and p.decode()!=SELF and (ROOT/p.decode()).is_file()})

def describe(path):
    for prefix,v in OWNERS.items():
        if path.startswith(prefix):return v
    return ('YURA / усі','Пакет, джерела або загальна документація')

def main():
    doc=ROOT/'docs/DATA_REFERENCE.md'
    if not doc.exists():doc.write_text('')
    paths=files()
    lines=['# Карта готових ресурсів','',
     'Усі шляхи від package root. Runtime читає `data/physics`, `data/planets`, `data/missions`, `data/rover`, `assets`. Audit/tools/docs не завантажувати в ігровий цикл. `data/package_manifest.json` містить SHA-256 і точні розміри всього релізу, крім самого manifest (щоб уникнути самопосилального hash).','',
     '| Файл | Кому | Призначення |','|---|---|---|']
    for p in paths:
        owner,description=describe(p);lines.append(f'| `{p}` | {owner} | {description} |')
    lines+=['| `data/package_manifest.json` | YURA | Release file list, bytes і SHA-256 |','',
     '## Контракти та приклади','',
     'JSON — UTF-8, finite numbers, schema_version1.0, ID стабільні в межах snapshot. Константа `{value, unit, status, source, note}`; generated planet має kg/m/s/rad та `status=synthetic_game_model`. IDs не залежать від перекладу назви. Source_ids посилаються на `data/sources.json`; прямий URL/derivation у значень також допустимий. Числові suffix `_kg`, `_m`, `_s`, `_w`, `_wh`, `_pa`, `_deg`, `_rad`, `_mbit` задають одиниці; case у згенерованих `_W`, `_K` теж значущий. `null` ніколи не означає0. Немає SQLite чи runtime API dependency.','',
     '| Ресурс | Поля / типи | Виклик |','|---|---|---|',
     '| physical_constants | constants: object; кожне value:number,unit/status/source:string | `constants.G.value` |',
     '| formulas | formulas:array; variables:object; example.inputs:object; expected:number | `FORMULAS[id](**inputs)` у tools/science.py |',
     '| planet_types / anchors | ID:string; radius bounds:number[2]; coupled mass/radius:number | `generateSystem(seed,p,c,anchors)` |',
     '| profiles | total_mass_kg:number; battery_capacity_wh:number; instrument_ids:string[] | `specs.profiles.find(x=>x.id===\'science\')` |',
     '| routes | waypoints:array; world_xyz_m:number[3];cell_col_row:integer[2] | `terrain.sample(x,z)`; observation ≠ certified route |',
     '| weather_samples | sol:integer;field/unit:string;rows_used:integer;p05/p50/p95:number (nullable min/max when no samples) | select same field/sol, не змішувати sensor temperature з air climate |',
     '| ephemeris | jd_tdb:number; Earth/Mars position_m:number[3];distance_m/delay_s:number | `geometricDelay(samples,jd,c)` |',
     '| terrain | affine_corner:number[6]; encodings:object; CRS WKT:string | `createTerrain(meta,uint16,uint16,uint8)` |',
     '| models/images manifests | id/path/source/credit + dimensions | GLTF/image loader із relative root |','',
     'Binary terrain: uint16 LE height/slope і uint8 traversability; row-major. Декодування висоти з offset/scale,0 nodata; slope0.01°,65535 nodata. WebP imagery embedded/standalone читається стандартним browser decoder. GLB2 self-contained, external Draco decoder не потрібен; перевірено mesh/image читання, не engine FPS.','',
     'Metadata/science data provenance і tuning limits описані в PHYSICS/GENERATION та team docs. GLB/source-level material properties не є engineering CAD tolerance. Явні обмеження/прогалини — DATA_SELECTION і YURA.']
    doc.write_text('\n'.join(lines)+'\n')
    paths=files();entries=[]
    for rel in paths:
        p=ROOT/rel
        if p.stat().st_size>12_000_000:raise ValueError(f'Oversized release file {rel}')
        if p.suffix.lower() in ['.tif','.gz','.pdf']:raise ValueError(f'Raw/archive file accidentally included {rel}')
        entries.append({'path':rel,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    total=sum(x['bytes'] for x in entries)
    write(SELF,{'schema_version':'1.0','id':'white-cat-scientific-package-v1','date_utc':'2026-11-14','manifest_excludes_itself':True,'raw_original_bytes':read('docs/audit/raw_inventory.json')['total_bytes'],'release_bytes_excluding_manifest':total,'release_to_raw_ratio':total/660259210,'files':entries})
    print(len(entries),'files + manifest;',total,'bytes excluding manifest')

if __name__=='__main__':main()
