"""Portable study schema checks; development-only jsonschema dependency."""
import copy,json,sys
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
root=Path(__file__).resolve().parents[1]
schema=json.loads((root/'docs/beam-study-schema-v1.json').read_text())
Draft202012Validator.check_schema(schema)
validator=Draft202012Validator(schema,format_checker=FormatChecker())
path=Path(sys.argv[1]) if len(sys.argv)>1 else root/'examples/parity/study-package/beam-study.json'
data=json.loads(path.read_text());validator.validate(data)
for view in data['views']:
 if view['package_image']:assert (path.parent/view['package_image']).is_file()
for mutate in (lambda d:d['projectors'][0].update(uuid='not-a-uuid'),lambda d:d['views'][0].update(package_image='../outside.png'),lambda d:d['surface_analysis'][0]['statistics'].update(coverage_percent='100'),lambda d:d['transform_validation'].update(validated=True)):
 bad=copy.deepcopy(data);mutate(bad);assert list(validator.iter_errors(bad))
print('PASS study schema, image files, UUID format, path traversal, statistic type and validation-claim negatives')
