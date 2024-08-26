import bpy

from Straighten_UV.addons.Straighten_UV.config import __addon_name__
from Straighten_UV.addons.Straighten_UV.i18n.dictionary import dictionary
from Straighten_UV.common.class_loader import auto_load
from Straighten_UV.common.class_loader.auto_load import add_properties, remove_properties
from Straighten_UV.common.i18n.dictionary import common_dictionary
from Straighten_UV.common.i18n.i18n import load_dictionary
from Straighten_UV.addons.Straighten_UV.utils import register_keymaps,unregister_keymaps
from Straighten_UV.addons.Straighten_UV.keymaps import keys
from Straighten_UV.addons.Straighten_UV.preference.AddonPreferences import StraightenUVPreferences
# Add-on info
bl_info = {
    "name": "Straighten_UV",
    "author": "Cupcko",
    "blender": (4, 0, 0),
    "version": (1, 0, 1),
    "description": "Straighten_UV through the selected UV endpoints or segment",
    "warning": "",
    "doc_url": "[documentation url]",
    "tracker_url": "649730016@qq.com",
    "support": "COMMUNITY",
    "category": "3D View"
}

_addon_properties = {
    bpy.types.Scene: {
        "loop_index": bpy.props.IntProperty(name="loop index",description="An integer property",
        default=0) , # 默认值),

        'loop_dict':bpy.props.StringProperty(name="loop dict",),
        'loop_list':bpy.props.StringProperty(name="loop list",)
    },

}


# You may declare properties like following, framework will automatically add and remove them.
# Do not define your own property group class in the __init__.py file. Define it in a separate file and import it here.
# 注意不要在__init__.py文件中自定义PropertyGroup类。请在单独的文件中定义它们并在此处导入。
# _addon_properties = {
#     bpy.types.Scene: {
#         "property_name": bpy.props.StringProperty(name="property_name"),
#     },
# }

# Best practice: Please do not define Blender classes in the __init__.py file.
# Define them in separate files and import them here. This is because the __init__.py file would be copied during
# addon packaging, and defining Blender classes in the __init__.py file may cause unexpected problems.
# 建议不要在__init__.py文件中定义Blender相关的类。请在单独的文件中定义它们并在此处导入它们。
# __init__.py文件在代码打包时会被复制，在__init__.py文件中定义Blender相关的类可能会导致意外的问题。

def register():
    print("registering")
    bpy.utils.register_class(StraightenUVPreferences)
    # Register classes
    auto_load.init()
    auto_load.register()
    add_properties(_addon_properties)

    # Internationalization
    load_dictionary(dictionary)
    bpy.app.translations.register(__addon_name__, common_dictionary)
    global keymaps_
    keymaps_ = register_keymaps(keys['UV_STRAIGHTEN'])
    print("{} addon is installed.".format(bl_info["name"]))

#
def unregister():
    # Internationalization
    bpy.app.translations.unregister(__addon_name__)
    bpy.utils.unregister_class(StraightenUVPreferences)
    # unRegister classes
    auto_load.unregister()
    remove_properties(_addon_properties)
    global keymaps_
    if keymaps_:
        unregister_keymaps(keymaps_)
    print("{} addon is uninstalled.".format(bl_info["name"]))
