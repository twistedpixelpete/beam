"""Pure SI projection model. Lens shifts are percentages of FULL image dimensions.

Throw distance is axial depth (perpendicular lens-to-image-plane distance).
A shifted image-centre ray has a longer slant length; never use it as axial depth.
"""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Metrics:
    distance: float
    width: float
    height: float
    pixels_per_metre: float
    pixel_size_m: float
    dpi: float
    total_lumens: float
    lux: float


def calculate(distance, throw_ratio, resolution_x, resolution_y, lumens=20000,
              brightness=100, stack=1):
    values = (distance, throw_ratio, resolution_x, resolution_y, lumens, brightness, stack)
    if not all(math.isfinite(v) for v in values):
        raise ValueError('All projection inputs must be finite')
    if min(distance, throw_ratio, resolution_x, resolution_y, stack) <= 0:
        raise ValueError('Distance, ratio, resolution and stack must be positive')
    if lumens < 0 or not 0 <= brightness <= 100:
        raise ValueError('Invalid output level')
    width = distance / throw_ratio
    height = width * resolution_y / resolution_x
    total = lumens * brightness / 100 * stack
    ppm = resolution_x / width
    return Metrics(distance, width, height, ppm, nominal_pixel_size(width, resolution_x), ppm * .0254, total, total/(width*height))


def image_point(u, v, depth, throw_ratio, resolution_x, resolution_y, shift_h=0, shift_v=0):
    width = depth / throw_ratio
    height = width * resolution_y / resolution_x
    return ((u-.5+shift_h/100)*width, (v-.5+shift_v/100)*height, -depth)


def camera_parameters(throw_ratio, resolution_x, resolution_y, shift_h=0, shift_v=0):
    return dict(lens=36*throw_ratio, sensor_width=36, sensor_fit='HORIZONTAL',
                shift_x=shift_h/100, shift_y=shift_v/100*resolution_y/resolution_x)


def nominal_pixel_size(image_width_m, resolution_x):
    """Nominal horizontal pixel pitch in metres; distortion is not modelled."""
    if not math.isfinite(image_width_m) or image_width_m<=0 or resolution_x<=0:
        raise ValueError('Image width and resolution must be positive')
    return image_width_m/resolution_x
