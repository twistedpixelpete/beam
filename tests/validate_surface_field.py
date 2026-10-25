"""Portable checks for the six-view architectural field package."""
import json,hashlib
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
root=Path(__file__).resolve().parents[1];folder=root/'examples/surface-intelligence/field/Study-Package'
data=json.loads((folder/'beam-study.json').read_text())
Draft202012Validator(json.loads((root/'docs/beam-study-schema-v1.json').read_text()),format_checker=FormatChecker()).validate(data)
assert {v['analysis_overlay'] for v in data['views']}=={'NONE','DENSITY','STRETCH','ILLUMINANCE','DISTANCE','ACUITY'}
analysis=data['surface_analysis'][0];sources={p['uuid'] for p in data['projectors']}
assert set(analysis['projector_uuids'])==sources
assert analysis['observer']['uuid'] in {o['uuid'] for o in data['observers']}
assert analysis['receiver_uuid'] in {o['uuid'] for o in data['receivers']}
assert analysis['sample_point_units']=='metres' and analysis['scene_scale_length_m']==1
for v in data['views']:
 image=folder/v['package_image'];assert image.exists()
 if v['analysis_overlay']=='NONE':assert v.get('analysis_image') is None;continue
 a=v['analysis_image'];assert hashlib.sha256(image.read_bytes()).hexdigest()==a['image_sha256']
 assert json.loads(image.with_suffix('.analysis.json').read_text())==a
 assert a['analysis_uuid']==analysis['analysis_uuid'] and a['statistics']==analysis['statistics']
for sample in analysis['sample_metrics']:
 for key in ('distance_projector_uuid','acuity_projector_uuid'):assert sample[key] is None or sample[key] in sources
assert 'Estimated incident illuminance is not photometrically calibrated.' in data['assumptions']
print('PASS field schema, six views, five sidecars/hashes, SI units, source/Observer/receiver joins and wording')
