"""Validate additive schema, all five image joins/hashes and controlling sources."""
import json,hashlib,copy
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
root=Path(__file__).resolve().parents[1];folder=root/'examples/surface-intelligence/Study-Package'
data=json.loads((folder/'beam-study.json').read_text());validator=Draft202012Validator(json.loads((root/'docs/beam-study-schema-v1.json').read_text()),format_checker=FormatChecker());validator.validate(data)
assert {v['analysis_overlay'] for v in data['views']}=={'DENSITY','STRETCH','ILLUMINANCE','DISTANCE','ACUITY'}
analysis=data['surface_analysis'][0];sources=set(analysis['projector_uuids'])
for v in data['views']:
 a=v['analysis_image'];f=folder/v['package_image'];assert hashlib.sha256(f.read_bytes()).hexdigest()==a['image_sha256'];assert json.loads(f.with_suffix('.analysis.json').read_text())==a
 assert a['analysis_uuid']==analysis['analysis_uuid'] and a['statistics']==analysis['statistics']
for sample in analysis['sample_metrics']:
 assert sample['distance_projector_uuid'] is None or sample['distance_projector_uuid'] in sources
 assert sample['acuity_projector_uuid'] is None or sample['acuity_projector_uuid'] in sources
 assert sample['illuminance_lux']>=0
for change in (lambda d:d['observers'][0].update(threshold_arcmin=0),lambda d:d['surface_analysis'][0]['statistics'].update(illuminance_uniformity_min_average=2)):
 bad=copy.deepcopy(data);change(bad);assert list(validator.iter_errors(bad))
print('PASS five-mode schema, hashes, sidecars, source IDs, observer thresholds and uniformity bounds')
