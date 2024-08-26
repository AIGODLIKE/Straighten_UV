import bpy

from Straighten_UV.addons.Straighten_UV.config import __addon_name__
from Straighten_UV.addons.Straighten_UV.operators.AddonOperators import Select_e_loop_index,Select_loop_index,Straighten_UV,Select_loop_index_dict,Select_loop_index_list,Straighten_line_UV
from Straighten_UV.common.i18n.i18n import i18n


class StraightenUVPanel(bpy.types.Panel):
    bl_label = "Straighten UV"
    bl_idname = "SCENE_PT_straighten_uv"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = 'UI'
    # name of the side panel
    bl_category = "Image"

    def draw(self, context: bpy.types.Context):
        # addon_prefs = context.preferences.addons[__addon_name__].preferences
        layout = self.layout

        row = layout.row(align=True)
        # First column
        col = row.column(align=True)
        col.label(text="")
        col.operator(Straighten_line_UV.bl_idname, text='←', ).Axis = 'MIN_U'
        # Second column
        col = row.column(align=True)
        # col.scale_x = 3.15
        col.operator(Straighten_line_UV.bl_idname, text='↑', ).Axis = 'MAX_V'
        col.operator('uv.unwrap_selected_uv',text='Relax')
        col.operator(Straighten_line_UV.bl_idname, text='↓', ).Axis = 'MIN_V'
        # Third column
        col = row.column(align=True)
        col.label(text="")
        col.operator(Straighten_line_UV.bl_idname, text='→').Axis = 'MAX_U'
        row = layout.row(align=True)
        row.operator('uv.straighten_uv',text='Straighten UV')


        # layout.label(text=i18n("Example Functions") + ": " + str(addon_prefs.number))
        # layout.prop(bpy.context.scene, "loop_index")

        # layout.separator()


        # layout.operator(Select_loop_index.bl_idname)
        # layout.operator(Select_e_loop_index.bl_idname)

        # layout.operator(Straiten_line_UV.bl_idname)
        # layout.prop(scene, "loop_dict")
        # layout.operator(Select_loop_index_dict.bl_idname)
        # layout.prop(scene, "loop_list")
        # layout.operator(Select_loop_index_list.bl_idname)


    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None
