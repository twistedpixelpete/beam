"""Run with Blender --background --factory-startup --python tools/build_theme.py.
Original Beam palette over Blender's factory semantic defaults; no third-party theme.
Only run in a disposable process: this resets that process's theme to factory.
"""
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import bpy
import _rna_xml

root=Path(__file__).resolve().parents[1]
bpy.ops.preferences.reset_default_theme()
with tempfile.TemporaryDirectory() as tmp:
    source=Path(tmp)/'factory.xml'
    _rna_xml.xml_file_write(bpy.context,str(source),bpy.types.USERPREF_MT_interface_theme_presets.preset_xml_map)
    tree=ET.parse(source)
blue='#285b91';text='#e3e7eb'
for element in tree.iter():
    if element.tag=='ThemeUserInterface':
        element.attrib.update(editor_border='#15191d',editor_outline='#54596070',editor_outline_active='#7794b580',widget_emboss='#00000012',widget_text_cursor='#8bb9e6',panel_roundness='0.15',panel_header='#292c30ff',panel_back='#25282cff',panel_sub_back='#00000018',panel_outline='#69758028',panel_title=text,panel_text=text,panel_active=blue+'ff',link='#8bb9e6ff',menu_shadow_fac='0.15',menu_shadow_width='4')
    elif element.tag=='ThemeWidgetColors':
        element.attrib.update(outline='#454b53ff',outline_sel='#80aad0ff',inner='#34383eff',inner_sel=blue+'ff',text=text,text_sel='#ffffff',show_shaded='FALSE',shadetop='0',shadedown='0',roundness='0.18')
    elif element.tag in {'ThemeSpaceGeneric','ThemeSpaceGradient'}:
        for key,value in dict(back='#202225',title=text,text=text,text_hi='#ffffff',header='#1c1e21ff',header_text=text,header_text_hi='#ffffff').items():
            if key in element.attrib:element.set(key,value)
    elif element.tag=='ThemeGradientColors':element.attrib.update(background_type='SINGLE_COLOR',high_gradient='#303234',gradient='#303234')
    elif element.tag=='ThemeOutliner':element.attrib.update(selected_highlight='#30465c',active=blue,edited_object='#387d7066',row_alternate='#ffffff04')
    elif element.tag=='ThemeWidgetStateColors':element.set('success','#326e60ff');element.set('info',blue+'ff')
# Neutral menu surfaces and a quieter inactive workspace tab. Semantic animation,
# warning/error, selection outlines, hidden-state fading and collection colors stay native.
ui=tree.find('./Theme/user_interface/ThemeUserInterface')
for name in ('wcol_menu_back','wcol_tooltip','wcol_box'):
    node=ui.find('./'+name+'/ThemeWidgetColors')
    if node is not None:node.set('inner','#242a30ff')
node=ui.find('./wcol_tab/ThemeWidgetColors');node.set('inner','#1c1e21ff')
node=ui.find('./wcol_scroll/ThemeWidgetColors');node.set('item','#8a949fff')
node=tree.find('./Theme/view_3d/ThemeView3D');node.set('grid','#484c5060');node.set('grid_major','#484c5090')
ET.indent(tree,space='  ')
out=root/'projection_study/themes/Beam.xml';out.parent.mkdir(parents=True,exist_ok=True);tree.write(out,encoding='unicode')
print(out)
