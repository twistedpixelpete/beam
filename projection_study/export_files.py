"""Permissions and atomic writing for exported files.

Python's temporary files are private to their owner. Exports are meant to be shared,
so they get normal permissions, and overwriting a file keeps the permissions it had.
"""
import os
import tempfile
from pathlib import Path


def _umask():
    mask = os.umask(0)
    os.umask(mask)
    return mask


def new_folder_mode():
    return 0o777 & ~_umask()


def file_mode(destination):
    try:
        return Path(destination).stat().st_mode & 0o777
    except FileNotFoundError:
        return 0o666 & ~_umask()


def write_atomic(destination, payload):
    """Replace destination in one step, so a failed export never leaves half a file."""
    destination = Path(destination)
    descriptor, name = tempfile.mkstemp(prefix='.beam-export-', dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(payload)
        os.chmod(temporary, file_mode(destination))
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
