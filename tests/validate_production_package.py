"""Portable PATCH fixture verification: schema, image hashes and source joins."""
import json,hashlib,sys,copy
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
root=Path(__file__).resolve().parents[1]
folder=Path(sys.argv[1]) if len(sys.argv)>1 else root/'examples/production/PATCH-study-package'
data=json.loads((folder/'beam-study.json').read_text())
schema=json.loads((root/'docs/beam-study-schema-v1.json').read_text());validator=Draft202012Validator(schema,format_checker=FormatChecker());validator.validate(data)
analyses={a['analysis_uuid']:a for a in data['surface_analysis']}
for view in data['views']:
 path=folder/view['package_image'];assert path.is_file()
 image=view.get('analysis_image')
 if image:
  sidecar=json.loads(path.with_suffix('.analysis.json').read_text());assert sidecar==image
  assert image['image_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
  source=analyses[image['analysis_uuid']];assert image['statistics']==source['statistics'];assert image['projector_uuids']==source['projector_uuids'];assert image['receiver_uuid']==source['receiver_uuid'];assert image['mode']==view['analysis_overlay']
assert {v['analysis_overlay'] for v in data['views']}=={'NONE','DENSITY','STRETCH'}
for edit in (lambda d:d['views'][1]['analysis_image'].update(image_sha256='wrong'),lambda d:d['export_formats']['designer'].update(designer_application_tested=True),lambda d:d['views'][1].update(analysis_overlay='bogus')):
 bad=copy.deepcopy(data);edit(bad);assert list(validator.iter_errors(bad))
print('PASS PATCH fixture: schemas, image hashes, sidecars, source joins, modes and false-validation negatives')
