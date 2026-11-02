"""Selecting a Blend Group only stales a Group-scope analysis. Background, no GPU."""
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import projection_study as addon  # noqa: E402
from projection_study import analysis_runtime  # noqa: E402


def selecting_group_stales(settings, scope):
    settings.analysis_scope = scope
    result = dict(stale=False)
    analysis_runtime.CACHE[bpy.context.scene.as_pointer()] = result
    settings.blend_group_index = settings.blend_group_index + 1
    return result['stale']


def main():
    addon.register()
    settings = bpy.context.scene.ps_study
    assert not selecting_group_stales(settings, 'ALL')
    assert not selecting_group_stales(settings, 'PROJECTOR')
    assert selecting_group_stales(settings, 'GROUP')
    print('ANALYSIS STALE PASS: only a Group-scope analysis depends on the selected group')
    addon.unregister()


main()
