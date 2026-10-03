"""Development-only jsonschema dependency; no add-on dependency.
Usage: python tests/validate_json_exports.py [export.json ...]
"""
import sys,json,importlib.util,copy
from pathlib import Path
from jsonschema import Draft202012Validator,FormatChecker
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('json_contract',root/'projection_study/json_contract.py')
contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
schema=json.loads((root/'docs/beam-json-schema-v1.json').read_text())
Draft202012Validator.check_schema(schema)
validator=Draft202012Validator(schema,format_checker=FormatChecker())
paths=[Path(p) for p in sys.argv[1:]] or list((root/'examples/0.5.1').glob('*.json'))
for path in paths:
    data=json.loads(path.read_text(),parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
    validator.validate(data)
    contract.validate_relationships(data)
    print(f'PASS {path.name}: schema, finite JSON, UUIDs, group members, disguise references')
# Deliberately malformed target records must be rejected by the portable schema.
data=json.loads((root/'examples/0.5.1/Beam_mixed_validity.json').read_text())
bad=copy.deepcopy(data);p=next(p for p in bad['projectors'] if p['target']['status']=='no_hit');p['target']['point_m']=[1,2,3]
assert list(validator.iter_errors(bad)), 'Stale target accepted by schema'
bad=copy.deepcopy(data);bad['projectors'][0]['output_mode']='Calibration Grid'
assert list(validator.iter_errors(bad)), 'Human label accepted as enum'
bad=copy.deepcopy(data);bad['disguise']['validated']=True
assert list(validator.iter_errors(bad)), 'Unvalidated convention accepted as validated'
print('PASS negative schema checks: stale target, unstable enum, false transform-validation claim')
