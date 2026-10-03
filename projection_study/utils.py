"""Identity helpers independent of Blender."""
import re
import uuid

PALETTE = (
    (0.77, 0.39, 0.36), (0.44, 0.65, 0.49), (0.40, 0.58, 0.76),
    (0.43, 0.72, 0.72), (0.69, 0.46, 0.65), (0.78, 0.68, 0.36),
    (0.78, 0.49, 0.32), (0.59, 0.52, 0.77),
)

def new_uuid():
    return str(uuid.uuid4())

def next_identifier(names):
    numbers = [int(m.group(1)) for name in names if (m := re.fullmatch(r'PJ(\d+)', name))]
    return f'PJ{max(numbers, default=0) + 1:02d}'
