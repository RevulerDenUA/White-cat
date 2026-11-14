"""Bootstrap concrete JSON contracts from approved initial package (review before regeneration)."""
from pathlib import Path
import json
from prepare_data import ROOT,write

def shape(values,key=''):
    if not values:return {}
    groups={}
    for x in values:
        t='null' if x is None else 'boolean' if isinstance(x,bool) else 'integer' if isinstance(x,int) else 'number' if isinstance(x,float) else 'string' if isinstance(x,str) else 'array' if isinstance(x,list) else 'object'
        groups.setdefault(t,[]).append(x)
    if 'integer' in groups and 'number' in groups:groups['number']+=groups.pop('integer')
    if len(groups)>1:return {'anyOf':[shape(v,key) for _,v in sorted(groups.items())]}
    t,items=next(iter(groups.items()));out={'type':t}
    if t=='object':
        keys=sorted(set().union(*(d.keys() for d in items)))
        out['properties']={k:shape([d[k] for d in items if k in d],k) for k in keys}
        out['required']=sorted(set.intersection(*(set(d) for d in items)))
        out['additionalProperties']=False
        if 'schema_version' in keys:out['properties']['schema_version']={'const':'1.0'}
    elif t=='array':
        out['items']=shape([v for a in items for v in a],key)
        if key in ['world_xyz_m','earth_position_m','mars_position_m','extents_native','body_dimensions_m','dimensions_length_width_height_m']:
            out.update(minItems=3,maxItems=3)
        elif key in ['origin_projected_m','origin_lon_lat_deg','cell_col_row']:
            out.update(minItems=2,maxItems=2)
    elif t in ['integer','number']:
        if key in ['mass_kg','radius_m','density_kg_m3','gravity_m_s2','semimajor_axis_m','orbital_period_s','rotation_period_s','width','height','spacing_m','capacity_ah_each','total_mass_kg','battery_capacity_wh']:
            out['exclusiveMinimum']=0
        if key=='eccentricity':out.update(minimum=0,exclusiveMaximum=1)
        if key=='seed':out.update(minimum=0,maximum=4294967295)
    elif t=='string' and key in ['id','unit','path']:out['minLength']=1
    return out

def main():
    files=[ROOT/'data/sources.json',*sorted((ROOT/'data/physics').glob('*.json')),*sorted((ROOT/'data/planets').glob('*.json')),*sorted((ROOT/'data/missions').glob('*.json')),*sorted((ROOT/'data/rover').glob('*.json')),*sorted((ROOT/'assets').rglob('*.json'))]
    definitions={};mapping={}
    for p in files:
        rel=p.relative_to(ROOT).as_posix();name=rel.replace('/','_').replace('.','_')
        definitions[name]=shape([json.loads(p.read_text())])
        mapping[rel]='#/$defs/'+name
    write('schemas/package.schema.json',{'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'https://white-cat.invalid/schemas/package.schema.json','title':'White Cat scientific package v1, concrete per-resource contracts','$defs':definitions})
    write('schemas/index.json',{'schema_version':'1.0','schema_file':'schemas/package.schema.json','resources':mapping})
    print(len(mapping),'resource schemas created')

if __name__=='__main__':main()
