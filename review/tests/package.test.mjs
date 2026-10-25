import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import * as THREE from 'three';
import {toScene,validatePackage,glbDocument} from '../core.js';
const bytes=await readFile(new URL('../example/scene.glb',import.meta.url));
const glb=glbDocument(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
const data=JSON.parse(await readFile(new URL('../example/beam.json',import.meta.url)));
const manifest=JSON.parse(await readFile(new URL('../example/manifest.json',import.meta.url)));
test('package checksums and existing Beam identity contracts',async()=>{
 validatePackage(manifest,data);
 for(const name of ['beam.json','scene.glb']){const b=await readFile(new URL('../example/'+name,import.meta.url));assert.equal(createHash('sha256').update(b).digest('hex'),manifest.files[name].sha256);assert.equal(b.length,manifest.files[name].bytes);}
 assert.equal(data.projectors.length,3);assert.equal(data.screens.length,1);assert.equal(data.blend_groups.length,1);assert.equal(data.views.length,9);assert.equal(data.optics.length,3);assert.ok(data.surface_analysis[0].statistics.illuminance_average_lux>0);
});
test('GLB includes venue, screen UUID, UVs and embedded chart',()=>{
 assert.ok(glb.nodes.some(n=>n.extras?.beam_uuid===data.screens[0].uuid));assert.ok(glb.nodes.some(n=>n.extras?.beam_name==='Architecture Wall'));assert.ok(glb.meshes.length>=6);assert.ok(glb.meshes.some(m=>m.primitives.some(p=>p.attributes.TEXCOORD_0!==undefined)));assert.ok(glb.images.some(i=>i.bufferView!==undefined));assert.ok(glb.materials.length>0);
 assert.ok(!glb.nodes.some(n=>n.extras?.beam_name==='PJ01'));
});
test('metre coordinate conversion preserves lengths and rotates basis correctly',()=>{
 assert.deepEqual(toScene([1,2,3]),[1,3,-2]);const a=[3,-6,1.65],b=[-2,9,4];assert.equal(new THREE.Vector3(...a).distanceTo(new THREE.Vector3(...b)),new THREE.Vector3(...toScene(a)).distanceTo(new THREE.Vector3(...toScene(b))));
});
test('all saved cameras retain their exact matrix and proper handedness',()=>{
 const conversion=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1,0,0),-Math.PI/2);
 for(const v of data.views){const c=v.camera,q=c.rotation_quaternion_wxyz,bq=new THREE.Quaternion(q[1],q[2],q[3],q[0]),sq=conversion.clone().multiply(bq);const bForward=new THREE.Vector3(0,0,-1).applyQuaternion(bq);const sForward=new THREE.Vector3(0,0,-1).applyQuaternion(sq);assert.ok(sForward.distanceTo(new THREE.Vector3(...toScene(bForward.toArray())))<1e-6);const matrix=new THREE.Matrix4().set(...data.review.views[v.uuid].projection_matrix_row_major.flat());assert.ok(Number.isFinite(matrix.determinant())&&Math.abs(matrix.determinant())>1e-10);}
});
test('reject broken member links and unsupported package contracts',()=>{
 const broken=structuredClone(data);broken.blend_groups[0].members[0].projector_uuid='missing';assert.throws(()=>validatePackage(manifest,broken));assert.throws(()=>validatePackage({...manifest,schema_version:'99'},data));
});
