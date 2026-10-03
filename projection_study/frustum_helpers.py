"""Display-only ray endpoints; never used for projection extents or targeting."""
from .target_raycast import cast


def endpoints(origin, fallback_corners):
    """First visible evaluated surface on each corner ray, or its nominal corner.

    Fallback corners lie at the current nominal throw depth (the configured
    preview distance when the centre ray misses). Hits are not capped to that
    plane: a corner can hit a different receiver farther away than the centre.
    """
    result=[]
    for corner in fallback_corners:
        direction=corner-origin
        hit=cast(origin,direction.normalized()) if direction.length_squared>0 else None
        result.append(hit[0].copy() if hit else corner.copy())
    return result
