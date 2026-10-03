"""Presentation-only conversions. Engineering and interchange remain SI."""
def dimension(metres, units='m'):
    return f'{metres*1000:,.1f} mm' if units=='mm' else f'{metres:,.3f} m'


def pixel_size(metres_per_pixel, units='mm'):
    mm=f'{metres_per_pixel*1000:.2f} mm/px'
    return mm if units=='mm' else f'{metres_per_pixel:.6f} m/px ({mm})'


def coordinates(position_m, units='m'):
    factor=1000 if units=='mm' else 1
    return ', '.join(f'{v*factor:.1f}' if units=='mm' else f'{v:.3f}' for v in position_m)+' '+units
