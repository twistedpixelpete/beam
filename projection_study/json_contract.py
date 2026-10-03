"""Semantic checks beyond JSON Schema: UUID uniqueness and cross-record references."""
from uuid import UUID


def validate_relationships(data):
    """Reject corrupt relationships explicitly, never emit silently dangling UUIDs."""
    seen=set()
    for kind in ('projectors','blend_groups','study_views'):
        for record in data[kind]:
            identity=record['uuid']
            try: UUID(identity)
            except (ValueError,TypeError,AttributeError): raise ValueError(f'Invalid {kind} UUID: {identity!r}') from None
            if identity in seen: raise ValueError(f'Duplicate UUID: {identity}')
            seen.add(identity)
    projectors={p['uuid'] for p in data['projectors']}
    assigned=set()
    def resolve(identity,label):
        if identity not in projectors: raise ValueError(f'{label}: unresolved projector UUID {identity!r}')
    for group in data['blend_groups']:
        members=[m['projector_uuid'] for m in group['members']]
        for identity in members:
            resolve(identity,group['name'])
            if identity in assigned: raise ValueError(f'Projector appears in multiple group member slots: {identity}')
            assigned.add(identity)
        if group['anchor_projector_uuid'] not in members:
            raise ValueError(f"{group['name']}: anchor is not a group member")
        for pair in group['adjacent_pairs']:
            for key in ('a_uuid','b_uuid'):
                if pair[key] not in members: raise ValueError(f"{group['name']}: adjacent pair is not a group member")
    for row in data['disguise']['rows']: resolve(row[-1],'disguise row')
    for error in data['disguise'].get('validation',{}).get('errors',[]):
        if error['projector_uuid'] is not None: resolve(error['projector_uuid'],'disguise validation')
