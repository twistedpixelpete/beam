// Beam JSON stays Z-up; only the presentation boundary converts to glTF Y-up.
export const toScene=([x,y,z])=>[x,z,-y];
export function validatePackage(manifest,data){
 if(manifest.schema!=='beam-review'||manifest.schema_version!=='0.1.0'||manifest.beam!=='beam.json'||manifest.scene!=='scene.glb')throw new Error('Unsupported Review Package');
 if(data.schema!=='beam-study'||data.schema_version!=='1.0.0'||!data.review)throw new Error('Unsupported Beam study');
 const seen=new Set();
 for(const key of ['projectors','screens','blend_groups','views']){
  if(!Array.isArray(data[key]))throw new Error(`Missing ${key}`);
  for(const item of data[key]){if(!item.uuid||seen.has(item.uuid))throw new Error('Missing or duplicate Beam UUID');seen.add(item.uuid);}
 }
 const projectors=new Set(data.projectors.map(p=>p.uuid));
 for(const group of data.blend_groups)for(const member of group.members)if(!projectors.has(member.projector_uuid))throw new Error('Unresolved blend member');
 for(const p of data.projectors)if(!data.review.projectors[p.uuid]||!p.position_m.every(Number.isFinite))throw new Error('Missing projector presentation');
 for(const v of data.views)if(v.camera&&!data.review.views[v.uuid])throw new Error('Missing saved camera projection');
}
export function glbDocument(buffer){
 const header=new DataView(buffer);if(header.getUint32(0,true)!==0x46546c67||header.getUint32(4,true)!==2||header.getUint32(8,true)!==buffer.byteLength)throw new Error('Invalid GLB');
 if(header.getUint32(16,true)!==0x4e4f534a)throw new Error('Missing GLB JSON');
 const json=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,20,header.getUint32(12,true))));
 if([...(json.buffers||[]),...(json.images||[])].some(x=>x.uri&&!x.uri.startsWith('data:')))throw new Error('Review GLB must embed its resources');
 return json;
}
export const metric=(n,suffix='',digits=2)=>Number.isFinite(n)?`${n.toLocaleString(undefined,{maximumFractionDigits:digits})}${suffix}`:'Unavailable';
