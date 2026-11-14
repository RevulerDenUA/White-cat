import fs from 'node:fs';
import {generateSystem} from '../lib/generator.mjs';
const j=p=>JSON.parse(fs.readFileSync(p));
const system=generateSystem(2026,j('data/planets/generation_parameters.json'),j('data/physics/physical_constants.json'),j('data/planets/mass_radius_anchors.json'));
fs.writeFileSync('data/planets/generated_example.json',JSON.stringify(system,null,2)+'\n');
console.log(system.planets.length,'planets saved for seed 2026');
