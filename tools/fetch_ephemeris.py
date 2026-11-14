"""Small optional preparation request. Runtime never calls Horizons."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

PARAMETERS = dict(format='json', COMMAND="'399'", CENTER="'500@10'", MAKE_EPHEM="'YES'",
                  EPHEM_TYPE="'VECTORS'", START_TIME="'2026-11-14'", STOP_TIME="'2028-11-15'",
                  STEP_SIZE="'1 d'", OUT_UNITS="'AU-D'", REF_PLANE="'ECLIPTIC'", REF_SYSTEM="'ICRF'",
                  VEC_CORR="'NONE'", VEC_TABLE="'2'", CSV_FORMAT="'YES'")

def fetch(output):
    url = 'https://ssd.jpl.nasa.gov/api/horizons.api?' + urlencode(PARAMETERS)
    with urlopen(url, timeout=90) as response:
        data = json.load(response)
    if 'error' in data or '$$SOE' not in data.get('result', ''):
        raise ValueError(f'Horizons did not return vectors: {data.get("error", "missing SOE")}')
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps({'query_url': url, **data}, indent=2) + '\n')
    print(output)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='.local/earth_horizons.json')
    fetch(parser.parse_args().output)
