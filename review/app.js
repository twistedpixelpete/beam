import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {toScene,validatePackage,glbDocument,metric} from './core.js';
const $=id=>document.getElementById(id), el=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
const scene=new THREE.Scene();scene.background=new THREE.Color('#18232b');
const world=new THREE.Group();scene.add(world);
let camera=new THREE.PerspectiveCamera(45,1,.02,3000),controls,renderer,selection=null,savedView=null;
const records=new Map(), labels=[], pickable=[], qConversion=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1,0,0),-Math.PI/2);
const point=a=>new THREE.Vector3(...toScene(a));
const quaternion=q=>qConversion.clone().multiply(new THREE.Quaternion(q[1],q[2],q[3],q[0]));
const num=(n,s='',d=2)=>metric(n,s,d);
let data,manifest,bounds;
function rows(entries,parent=$('inspector')){const dl=el('dl');for(const [name,value] of entries){dl.append(el('dt',name),el('dd',value));}parent.append(dl);}
function status(text){$('status').textContent=text;}
function cameraControls(){if(controls)controls.dispose();controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.listenToKeyEvents(renderer.domElement);controls.dampingFactor=.12;controls.minDistance=.05;controls.maxDistance=2000;let navigating=false;controls.addEventListener('start',()=>{navigating=true;});controls.addEventListener('end',()=>{navigating=false;});controls.addEventListener('change',()=>{if(navigating&&savedView){savedView=null;$('views').value='';resize();status('Free navigation · metres');}});}
function fitBox(box){if(box.isEmpty())return;const centre=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3()).length();
 savedView=null;camera=new THREE.PerspectiveCamera(45,1,.01,Math.max(3000,size*20));camera.position.copy(centre).add(new THREE.Vector3(.8,.55,1).normalize().multiplyScalar(Math.max(1.5,size*1.2)));camera.lookAt(centre);cameraControls();controls.target.copy(centre);controls.update();$('views').value='';resize();}
function frameSelection(){if(selection){const record=records.get(selection);const box=new THREE.Box3();for(const object of record.objects)box.expandByObject(object);fitBox(box);status(`Framed ${record.item.name}`);}}
function setView(uuid){const view=data.views.find(v=>v.uuid===uuid);if(!view?.camera)return;
 const c=view.camera,meta=data.review.views[uuid];savedView=view;
 camera=c.type==='ORTHO'?new THREE.OrthographicCamera(-1,1,1,-1,meta.clip_start_m,meta.clip_end_m):new THREE.PerspectiveCamera(45,view.resolution.x/view.resolution.y,meta.clip_start_m,meta.clip_end_m);
 camera.position.copy(point(c.position_m));camera.quaternion.copy(quaternion(c.rotation_quaternion_wxyz));
 camera.up.set(0,1,0).applyQuaternion(camera.quaternion);
 const direction=new THREE.Vector3(0,0,-1).applyQuaternion(camera.quaternion);
 const focus=Math.max(1,camera.position.distanceTo(bounds.getCenter(new THREE.Vector3())));
 cameraControls();controls.target.copy(camera.position).addScaledVector(direction,focus);controls.update();
 const matrix=meta.projection_matrix_row_major;
 if(camera.isOrthographicCamera){camera.left=(-1-matrix[0][3])/matrix[0][0];camera.right=(1-matrix[0][3])/matrix[0][0];camera.bottom=(-1-matrix[1][3])/matrix[1][1];camera.top=(1-matrix[1][3])/matrix[1][1];}
 else{camera.fov=THREE.MathUtils.radToDeg(2*Math.atan(1/matrix[1][1]));camera.aspect=view.resolution.x/view.resolution.y;}
 camera.projectionMatrix.set(...matrix.flat());camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
 resize();status(`${view.name} · saved camera · ${view.analysis_overlay==='NONE'?'scene':view.analysis_overlay.toLowerCase()+' statistics available'}`);
}
function resize(){if(!renderer)return;const wrap=$('canvas-wrap'),w=wrap.clientWidth,h=wrap.clientHeight;let width=w,height=h;
 if(savedView){const aspect=savedView.resolution.x/savedView.resolution.y;if(w/h>aspect)width=h*aspect;else height=w/aspect;}
 else{camera.aspect=w/h;camera.updateProjectionMatrix();}
 renderer.setSize(Math.max(1,Math.floor(width)),Math.max(1,Math.floor(height)),true);
}
function select(uuid){selection=uuid;const r=records.get(uuid);if(!r)return;
 for(const [id,record] of records){record.row?.classList.toggle('selected',id===uuid);for(const helper of record.highlights)helper.visible=id===uuid&&helper.userData.reviewObject.visible;record.label?.classList.toggle('selected',id===uuid);}
 const panel=$('inspector');panel.replaceChildren(el('h1',r.item.name),el('div',r.type,'object-type'));$('frame').disabled=false;
 const p=r.item;
 if(r.type==='Projector'){
  const optics=data.optics.find(o=>o.projector_uuid===uuid),c=p.calculated||{};
  rows([['Model',optics?.projector_preset?[optics.projector_preset.manufacturer,optics.projector_preset.model].join(' '):'Generic / manual'],['Lens',optics?.lens_preset?.model||'Manual / unspecified'],['Resolution',`${p.resolution.x} × ${p.resolution.y}`],['Throw ratio',num(p.throw_ratio,' : 1',3)],['Throw distance',num(c.throw_distance_m,' m',3)],['Image size',`${num(c.image_width_m,' m',3)} × ${num(c.image_height_m,' m',3)}`],['Pixel density',num(c.pixel_density_px_per_m,' px/m',1)],['Lens shift (H / V)',`${num(p.lens_shift_percent.horizontal,' %')} / ${num(p.lens_shift_percent.vertical,' %')}`],['Nominal lumens',num(p.nominal_lumens,' lm',0)],['Effective total',num(p.total_lumens,' lm',0)],['Target',p.target?.status==='hit'?p.target.object_name:'No centre target']]);
  if(optics?.warnings?.length)panel.append(el('p',optics.warnings.join(' '),'small'));
 }else if(r.type==='Screen')rows([['Dimensions',`${num(p.width_m,' m')} × ${num(p.height_m,' m')}`],['Aspect',num(p.aspect,' : 1',3)],['Notes',p.notes||'—']]);
 else if(r.type==='Blend Group'){
  rows([['Layout',p.layout],['Members',p.members.map(m=>data.projectors.find(p=>p.uuid===m.projector_uuid)?.name||'Unresolved').join(', ')],['Requested horizontal overlap',`${num(p.desired_horizontal_overlap)} ${p.input_mode==='PERCENT'?'%':p.input_mode==='PIXELS'?'px':'m'}`]]);
  const list=el('ul');for(const pair of p.adjacent_pairs)list.append(el('li',`${pair.a} / ${pair.b}: ${num(pair.actual?.pixels,' px',1)} · ${num(pair.gap_m,' m gap',3)}`));panel.append(list);
 }else rows([['Source object',p.name],['Role','Venue / receiver geometry']]);
 panel.append(el('p',`UUID · ${uuid}`,'small'));status(`Selected ${p.name}`);
}
function line(points,colour,opacity=1){return new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(points),new THREE.LineBasicMaterial({color:colour,transparent:opacity<1,opacity}));}
function addRecord(type,item,objects,colour='#8299a7'){
 const highlights=[];for(const object of objects){const h=new THREE.BoxHelper(object.userData.highlightObject||object,0xa5e7ff);h.visible=false;h.userData.reviewObject=object;world.add(h);highlights.push(h);}
 const record={type,item,objects,highlights};records.set(item.uuid,record);
 const row=el('div',undefined,'tree-row'),dot=el('span',undefined,'dot');dot.style.background=colour;const button=el('button',item.name);button.addEventListener('click',()=>select(item.uuid));row.append(dot,button);record.row=row;
 if(type==='Projector'){const check=el('input');check.type='checkbox';check.checked=true;check.setAttribute('aria-label',`Show ${item.name}`);check.addEventListener('change',()=>{for(const o of objects)o.visible=check.checked;for(const [id,record] of records)for(const h of record.highlights)h.visible=selection===id&&h.userData.reviewObject.visible;status(`${item.name} ${check.checked?'shown':'hidden'}`);});row.append(check);}
 return row;
}
function projectors(){const tree=$('tree');tree.append(el('div','Projectors','tree-title'));
 for(const p of data.projectors){const meta=data.review.projectors[p.uuid],group=new THREE.Group();group.userData.beamUuid=p.uuid;world.add(group);const colour=p.study_colour_hex;
  const body=new THREE.Mesh(new THREE.BoxGeometry(.6,.3,.5),new THREE.MeshStandardMaterial({color:'#263844',roughness:.55,metalness:.25}));body.position.copy(point(p.position_m));body.quaternion.copy(quaternion(meta.rotation_quaternion_wxyz));body.userData.beamUuid=p.uuid;group.userData.highlightObject=body;group.add(body);pickable.push(body);
  const edge=new THREE.LineSegments(new THREE.EdgesGeometry(body.geometry),new THREE.LineBasicMaterial({color:colour}));edge.position.copy(body.position);edge.quaternion.copy(body.quaternion);group.add(edge);
  const corners=meta.frustum_endpoints_m.map(point),origin=point(p.position_m),segments=[];corners.forEach((v,i)=>segments.push(origin,v,v,corners[(i+1)%4]));group.add(line(segments,colour,.68));group.add(line([origin,point(meta.axis_endpoint_m)],colour,.35));
  if(p.target?.point_m){const marker=new THREE.Mesh(new THREE.SphereGeometry(.045,12,8),new THREE.MeshBasicMaterial({color:colour}));marker.position.copy(point(p.target.point_m));group.add(marker);}
  tree.append(addRecord('Projector',p,[group],colour));
  const label=el('button',p.name,'projector-label');label.style.setProperty('--colour',colour);label.addEventListener('click',()=>select(p.uuid));$('labels').append(label);labels.push({label,position:origin.clone().add(new THREE.Vector3(0,.35,0)),group});records.get(p.uuid).label=label;
 }
}
function analysis(){const section=$('analysis');section.replaceChildren(el('h2','Exported Surface Analysis'));const a=data.surface_analysis?.[0];
 if(!a){section.append(el('p','No current analysis was exported. Run Analyse Surface in Blender before publishing a new revision.'));return;}
 const s=a.statistics;section.append(el('p',`${a.receiver_name||'Receiver'} · Authoring snapshot`));
 rows([['Visible coverage',num(s.coverage_percent,' %',1)],['Density · min / avg / max',`${num(s.density_min_px_m)} / ${num(s.density_average_px_m)} / ${num(s.density_max_px_m)} px/m`],['Estimated Illuminance · min / avg / max',`${num(s.illuminance_min_lux)} / ${num(s.illuminance_average_lux)} / ${num(s.illuminance_max_lux)} lux`],['Distance · min / avg / max',`${num(s.distance_min_m)} / ${num(s.distance_average_m)} / ${num(s.distance_max_m)} m`],['Acuity · min / avg / max',`${num(s.acuity_min_arcmin)} / ${num(s.acuity_average_arcmin)} / ${num(s.acuity_max_arcmin)} arcmin`]],section);
 section.append(el('p','Saved views change the camera. The exported analysis is a fixed snapshot, not a live browser calculation.'));
}
async function fetchBuffer(name){const response=await fetch(`/package/${name}`);if(!response.ok)throw new Error(`Cannot load ${name} (${response.status})`);return response.arrayBuffer();}
async function verified(name){const bytes=await fetchBuffer(name);const actual=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(x=>x.toString(16).padStart(2,'0')).join('');if(actual!==manifest.files?.[name]?.sha256)throw new Error(`${name} does not match this revision's checksum`);return bytes;}
async function load(){
 renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.2;renderer.domElement.tabIndex=0;renderer.domElement.setAttribute('aria-label','3D scene');renderer.domElement.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){savedView=null;$('views').value='';resize();status('Free navigation · keyboard pan');}});$('canvas-wrap').append(renderer.domElement);
 scene.add(new THREE.HemisphereLight(0xe1efff,0x34424a,2));const sun=new THREE.DirectionalLight(0xffffff,2);sun.position.set(8,20,10);scene.add(sun);
 manifest=JSON.parse(new TextDecoder().decode(await fetchBuffer('manifest.json')));
 const [json,glb]=await Promise.all([verified('beam.json'),verified('scene.glb')]);data=JSON.parse(new TextDecoder().decode(json));validatePackage(manifest,data);glbDocument(glb);
 const loaded=await new GLTFLoader().parseAsync(glb,'/package/');world.add(loaded.scene);
 const byUuid=new Map();loaded.scene.traverse(o=>{if(o.userData.beam_uuid){const id=o.userData.beam_uuid;if(!byUuid.has(id))byUuid.set(id,[]);byUuid.get(id).push(o);}if(o.isMesh){o.material.side=THREE.DoubleSide;pickable.push(o);}});
 bounds=new THREE.Box3().setFromObject(loaded.scene);projectors();const tree=$('tree');tree.append(el('div','Screens','tree-title'));
 for(const screen of data.screens)tree.append(addRecord('Screen',screen,byUuid.get(screen.uuid)||[],'#94d7c0'));
 tree.append(el('div','Blend Groups','tree-title'));for(const group of data.blend_groups)tree.append(addRecord('Blend Group',group,group.members.flatMap(m=>records.get(m.projector_uuid)?.objects||[]),'#b2a0df'));
 tree.append(el('div','Venue geometry','tree-title'));for(const o of loaded.scene.children){if(o.userData.beam_kind==='screen')continue;const uid=o.userData.beam_uuid||o.uuid;o.userData.beamUuid=uid;tree.append(addRecord('Geometry',{uuid:uid,name:o.userData.beam_name||o.name},[o]));}
 $('project-title').textContent=data.project.project_name||'Beam study';$('revision').textContent=manifest.revision_label;
 for(const v of data.views){if(!v.camera)continue;const option=el('option',v.name);option.value=v.uuid;$('views').append(option);}
 $('views').addEventListener('change',e=>{if(e.target.value)setView(e.target.value);else{savedView=null;resize();status('Free navigation · metres');}});$('reset').addEventListener('click',()=>{const first=data.views.find(v=>v.camera);if(first){$('views').value=first.uuid;setView(first.uuid);}else fitBox(bounds);});$('frame').addEventListener('click',frameSelection);
 analysis();if(data.views[0]?.camera){$('views').value=data.views[0].uuid;setView(data.views[0].uuid);}else{fitBox(bounds);status('Ready · metres');}
 let down;const raycaster=new THREE.Raycaster();renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});renderer.domElement.addEventListener('pointerup',e=>{if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>4||e.button!==0)return;const r=renderer.domElement.getBoundingClientRect();raycaster.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);const hit=raycaster.intersectObjects(pickable,false).find(h=>{let o=h.object;while(o){if(!o.visible)return false;o=o.parent;}return true;});if(hit){let o=hit.object;while(o){const id=o.userData.beamUuid||o.userData.beam_uuid;if(records.has(id)){select(id);break;}o=o.parent;}}});
 new ResizeObserver(resize).observe($('canvas-wrap'));
 renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);const r=renderer.domElement.getBoundingClientRect(),parent=$('labels').getBoundingClientRect();for(const l of labels){const p=l.position.clone().project(camera);const visible=l.group.visible&&p.z>=-1&&p.z<=1&&Math.abs(p.x)<=1&&Math.abs(p.y)<=1;l.label.hidden=!visible;if(visible){l.label.style.left=`${r.left-parent.left+(p.x+1)*r.width/2}px`;l.label.style.top=`${r.top-parent.top+(1-p.y)*r.height/2}px`;}}});
}
load().catch(error=>{$('error').hidden=false;$('error').textContent=`Unable to open this review: ${error.message}`;status('Review unavailable');console.error(error);});
