/** Base URL is injected by the caller; supports subdirectory deployments. */
export async function loadJSON(base,path){const r=await fetch(new URL(path,base));if(!r.ok)throw new Error(`${path}: HTTP ${r.status}`);const d=await r.json();if(d.schema_version!=='1.0')throw new Error(`${path}: unsupported schema`);return d;}
export async function loadBuffer(base,path){const r=await fetch(new URL(path,base));if(!r.ok)throw new Error(`${path}: HTTP ${r.status}`);return r.arrayBuffer();}
