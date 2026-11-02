"""Keeps background work alive and makes its failures visible. Independent of bpy.

Blender permanently drops a timer whose callback raises, so an unguarded failure
would freeze every live Beam update with nothing but a console message.
"""
import functools
import logging

_log = logging.getLogger('beam')
_active = {}


def report(source, exc):
    """Record a failure; log its traceback once, not on every retry."""
    message = f'{type(exc).__name__}: {exc}'
    if _active.get(source) != message:
        _log.error('%s failed', source, exc_info=exc)
    _active[source] = message


def clear(source=None):
    if source is None: _active.clear()
    else: _active.pop(source, None)


def summary():
    """One line per failing subsystem, for the Beam panel."""
    return tuple(f'{source}: {message}' for source, message in sorted(_active.items()))


def guarded(source, retry=1.0):
    """Decorate a timer callback so it survives exceptions and retries slowly."""
    def decorate(function):
        @functools.wraps(function)
        def run():
            try:
                result = function()
            except Exception as exc:
                report(source, exc)
                return retry
            clear(source)
            return result
        return run
    return decorate
