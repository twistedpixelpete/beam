"""Draws a Beam inspector against a recording layout, so tests can check what appears and in what order.

Every panel counts as open. Shared by the background tests and the feature test scene.
"""
from types import SimpleNamespace

import bpy


class RecordingLayout:
    def __init__(self, log):
        self.__dict__['log'] = log

    def __setattr__(self, name, value):
        pass

    def __getattr__(self, name):
        def call(*args, **kwargs):
            if name == 'prop':
                self.log.append(('prop', args[1]))
            elif name == 'operator':
                self.log.append(('operator', args[0]))
            elif name == 'label':
                self.log.append(('label', kwargs.get('text', '')))
            elif name == 'popover':
                self.log.append(('popover', args[0], kwargs.get('text', '')))
            elif name == 'panel':
                self.log.append(('panel', args[0]))
                return RecordingLayout(self.log), RecordingLayout(self.log)
            return RecordingLayout(self.log)
        return call


class InspectorContext:
    """The current context, with no viewport, so drawing works in background mode too."""
    screen = SimpleNamespace(areas=[])

    def __getattr__(self, name):
        return getattr(bpy.context, name)


def draw_inspector(ui, inspector):
    bpy.context.scene.ps_study.inspector = inspector
    log = []
    ui.draw(RecordingLayout(log), InspectorContext())
    return log


def draw_project_settings(ui):
    log = []
    ui.project_settings(RecordingLayout(log), InspectorContext())
    return log


def before_first_panel(log):
    panels = [i for i, entry in enumerate(log) if entry[0] == 'panel']
    return log[:panels[0]] if panels else log


def labels(entries):
    return [entry[1] for entry in entries if entry[0] == 'label']
