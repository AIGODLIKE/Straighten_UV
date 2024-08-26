import ast
import math, bmesh
#
import bpy
from bpy.props import EnumProperty, BoolProperty
from ..utils import get_islands, get_bbox, get_objects_seams
from bpy.app.translations import pgettext as _
from Straighten_UV.addons.Straighten_UV.config import __addon_name__


# from Straighten_UV.addons.Straighten_UV.preference.AddonPreferences import ExampleAddonPreferences
#
#
# This Example Operator will scale up the selected object
class Unwrap_island(bpy.types.Operator):
    bl_idname = "uv.unwrap_island_uv"
    bl_label = "Unwrap Island"
    bl_description = "Unwrap the island"
    bl_options = {'REGISTER', 'UNDO'}
    mouse_pos_x=0
    mouse_pos_y=0
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'
    def invoke(self, context, event):
        if bpy.context.scene.tool_settings.use_uv_select_sync:
            self.report({"ERROR"}, "此功能需要禁用uv同步")
            return {'CANCELLED'}
        self.mouse_pos_x=event.mouse_region_x
        self.mouse_pos_y=event.mouse_region_y
        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        # 计算归一化坐标
                        self.mouse_pos = region.view2d.region_to_view(event.mouse_region_x,event.mouse_region_y)

        return self.execute(context)
    def execute(self, context):
        scene = context.scene
        if bpy.context.scene.tool_settings.use_uv_select_sync:
            self.report({"ERROR"}, "此功能需要禁用uv同步")
            return {'CANCELLED'}

        bpy.ops.uv.select_linked_pick(extend=True, deselect=False, location=self.mouse_pos)
        bpy.ops.uv.unwrap_selected_uv()
        return {'FINISHED'}
class Unwrap_Selected(bpy.types.Operator):
    bl_idname = "uv.unwrap_selected_uv"
    bl_label = "Unwrap Selected"
    bl_description = "Unwrap the selected faces"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    method: EnumProperty(
        name="Method",
        items=[
            ("ANGLE_BASED", "Angle Based", ""),
            ("CONFORMAL", "Conformal", ""),
        ]
    )
    fill_holes: BoolProperty(
        name="Fill Holes",
        default=True,
    )
    correct_aspect: BoolProperty(
        name="Correct Aspect",
        default=False,
    )
    use_subsurf_data: BoolProperty(
        name="Use Subdivision Surface",
        default=False,
    )

    def clear_all_seams(self, bm):
        for e in bm.edges:
            e.seam = False

    def unwrap_selected_uv_verts(self, bm, uv):
        initial_pins = []
        initial_seams = []
        initial_selection = set()

        for f in bm.faces:
            for l in f.loops:
                if l[uv].pin_uv:
                    initial_pins.append(l[uv])

                if l.edge.seam:
                    initial_seams.append(l.edge)

                if l[uv].select:
                    initial_selection.add(l)
                else:
                    l[uv].pin_uv = True
                l[uv].select = True

        bpy.ops.uv.seams_from_islands(mark_seams=True)
        bpy.ops.uv.unwrap(method=self.method,
                          fill_holes=self.fill_holes,
                          correct_aspect=self.correct_aspect,
                          use_subsurf_data=self.use_subsurf_data,
                          margin=0)

        self.clear_all_seams(bm)

        for e in initial_seams:
            e.seam = True

        for f in bm.faces:
            for l in f.loops:
                l[uv].pin_uv = False

        for l in initial_pins:
            l.pin_uv = True

        for f in bm.faces:
            for l in f.loops:
                if l in initial_selection:
                    continue
                l[uv].select = False

    def execute(self, context):
        scene = context.scene
        if bpy.context.scene.tool_settings.use_uv_select_sync:
            self.report({"ERROR"}, "此功能需要禁用uv同步")
            return {'CANCELLED'}

        view_layer = context.view_layer
        act_ob = view_layer.objects.active
        selected_ob = tuple(context.objects_in_mode_unique_data)

        bpy.ops.object.mode_set(mode='OBJECT')

        for ob in selected_ob:
            ob.select_set(state=False)

        for ob in selected_ob:
            view_layer.objects.active = ob
            ob.select_set(state=True)

            bpy.ops.object.mode_set(mode='EDIT')

            me = ob.data
            bm = bmesh.from_edit_mesh(me)
            uv = bm.loops.layers.uv.verify()

            self.unwrap_selected_uv_verts(bm, uv)

            bpy.ops.object.mode_set(mode='OBJECT')
            ob.select_set(state=False)

        for ob in selected_ob:
            ob.select_set(state=True)

        bpy.ops.object.mode_set(mode='EDIT')
        view_layer.objects.active = act_ob
        return {'FINISHED'}


class Select_loop_index_list(bpy.types.Operator):
    '''ExampleAddon'''
    bl_idname = "object.select_loop_index_list"
    bl_label = "根据list选择uv顶点"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        # print(bpy.context.scene.loop_dict)
        bm = bmesh.from_edit_mesh(context.active_object.data)

        uv_layer = bm.loops.layers.uv.verify()
        dict_data = ast.literal_eval(bpy.context.scene.loop_list)
        # print('dict_data', dict_data)
        for loop_index in dict_data:
            v_index = context.active_object.data.loops[loop_index].vertex_index
            for loop in bm.verts[v_index].link_loops:
                if loop.index == loop_index:
                    loop[uv_layer].select = 1
        bmesh.update_edit_mesh(context.active_object.data, loop_triangles=False,
                               destructive=False)  # 更新mesh，应用所有bmesh的修改

        return {'FINISHED'}


class Select_loop_index_dict(bpy.types.Operator):
    '''ExampleAddon'''
    bl_idname = "object.select_loop_index_dict"
    bl_label = "根据dict选择uv顶点"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        # print(bpy.context.scene.loop_dict)
        bm = bmesh.from_edit_mesh(context.active_object.data)

        uv_layer = bm.loops.layers.uv.verify()
        dict_data = ast.literal_eval(bpy.context.scene.loop_dict)
        # print('dict_data', dict_data)
        for loop_index in dict_data:
            v_index = context.active_object.data.loops[loop_index].vertex_index
            for loop in bm.verts[v_index].link_loops:
                if loop.index == loop_index:
                    loop[uv_layer].select = 1
        bmesh.update_edit_mesh(context.active_object.data, loop_triangles=False,
                               destructive=False)  # 更新mesh，应用所有bmesh的修改

        return {'FINISHED'}

Axis=[
            ('MAX_U', 'Max X', ''),
            ('MIN_U', 'Min X', ''),
            ('MAX_V', 'Max Y', ''),
            ('MIN_V', 'Min Y', ''),
        ]

class Straighten_line_UV(bpy.types.Operator):
    '''Align and straighten according to the selected direction'''
    bl_idname = "uv.straighten_line_uv"
    bl_label = "根据选择的方向对齐拉直"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}
    Axis: EnumProperty(
        name='Axis',
        items=Axis,
    )
    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def align_islands(self, context):
        bboxes = []
        objects_seams = get_objects_seams(context)
        for ob in context.objects_in_mode_unique_data:
            seams = objects_seams[ob]
            me = ob.data
            bm = bmesh.from_edit_mesh(me)
            uv = bm.loops.layers.uv.verify()
            for island in get_islands(uv, bm, seams, has_selected_faces=True, islands_with_hidden_faces=False):
                bbox = get_bbox(uv, island)
                bboxes.append(bbox)

        if not bboxes:
            return {'CANCELED'}

        if self.Axis == 'MAX_U':
            max_u = max([bbox[1][0] for bbox in bboxes])
            for ob in context.objects_in_mode_unique_data:
                seams = objects_seams[ob]
                me = ob.data
                bm = bmesh.from_edit_mesh(me)
                uv = bm.loops.layers.uv.verify()
                for island in get_islands(uv, bm, seams, has_selected_faces=True, islands_with_hidden_faces=False):
                    bbox = get_bbox(uv, island)
                    bbox_max_u = bbox[1][0]
                    distance = max_u - bbox_max_u
                    for f in island:
                        for l in f.loops:
                            u, v = l[uv].uv
                            new_co = u + distance, v
                            l[uv].uv = new_co
                bmesh.update_edit_mesh(me)

        if self.Axis == 'MIN_U':
            min_u = min([bbox[0][0] for bbox in bboxes])
            for ob in context.objects_in_mode_unique_data:
                seams = objects_seams[ob]
                me = ob.data
                bm = bmesh.from_edit_mesh(me)
                uv = bm.loops.layers.uv.verify()
                for island in get_islands(uv, bm, seams, has_selected_faces=True, islands_with_hidden_faces=False):
                    bbox = get_bbox(uv, island)
                    bbox_min_u = bbox[0][0]
                    distance = bbox_min_u - min_u
                    for f in island:
                        for l in f.loops:
                            u, v = l[uv].uv
                            new_co = u - distance, v
                            l[uv].uv = new_co
                bmesh.update_edit_mesh(me)

        if self.Axis == 'MAX_V':
            max_v = max([bbox[1][1] for bbox in bboxes])
            for ob in context.objects_in_mode_unique_data:
                seams = objects_seams[ob]
                me = ob.data
                bm = bmesh.from_edit_mesh(me)
                uv = bm.loops.layers.uv.verify()
                for island in get_islands(uv, bm, seams, has_selected_faces=True, islands_with_hidden_faces=False):
                    bbox = get_bbox(uv, island)
                    bbox_max_v = bbox[1][1]
                    distance = max_v - bbox_max_v
                    for f in island:
                        for l in f.loops:
                            u, v = l[uv].uv
                            new_co = u, v + distance
                            l[uv].uv = new_co
                bmesh.update_edit_mesh(me)

        if self.Axis == 'MIN_V':
            min_v = min([bbox[0][1] for bbox in bboxes])
            for ob in context.objects_in_mode_unique_data:
                seams = objects_seams[ob]
                me = ob.data
                bm = bmesh.from_edit_mesh(me)
                uv = bm.loops.layers.uv.verify()
                for island in get_islands(uv, bm, seams, has_selected_faces=True, islands_with_hidden_faces=False):
                    bbox = get_bbox(uv, island)
                    bbox_min_v = bbox[0][1]
                    distance = bbox_min_v - min_v
                    for f in island:
                        for l in f.loops:
                            u, v = l[uv].uv
                            new_co = u, v - distance
                            l[uv].uv = new_co
                bmesh.update_edit_mesh(me)

    def align_vertices(self, context):
        coords = []

        for ob in context.objects_in_mode_unique_data:
            me = ob.data
            bm = bmesh.from_edit_mesh(me)
            uv = bm.loops.layers.uv.verify()

            for f in bm.faces:
                if f.select:
                    for l in f.loops:
                        if l[uv].select:
                            coords.append(l[uv].uv[:])

        if not coords:
            return {'CANCELED'}

        for ob in context.objects_in_mode_unique_data:
            me = ob.data
            bm = bmesh.from_edit_mesh(me)
            uv = bm.loops.layers.uv.verify()

            if self.Axis == 'MAX_U':
                u = max([uv[0] for uv in coords])
                for f in bm.faces:
                    if f.select:
                        for l in f.loops:
                            if l[uv].select:
                                for l in l.vert.link_loops:
                                    if l[uv].select:
                                        l[uv].uv[0] = u

            if self.Axis == 'MIN_U':
                u = min([uv[0] for uv in coords])
                for f in bm.faces:
                    if f.select:
                        for l in f.loops:
                            if l[uv].select:
                                for l in l.vert.link_loops:
                                    if l[uv].select:
                                        l[uv].uv[0] = u

            if self.Axis == 'MAX_V':
                v = max([uv[1] for uv in coords])
                for f in bm.faces:
                    if f.select:
                        for l in f.loops:
                            if l[uv].select:
                                for l in l.vert.link_loops:
                                    if l[uv].select:
                                        l[uv].uv[1] = v

            if self.Axis == 'MIN_V':
                v = min([uv[1] for uv in coords])
                for f in bm.faces:
                    if f.select:
                        for l in f.loops:
                            if l[uv].select:
                                for l in l.vert.link_loops:
                                    if l[uv].select:
                                        l[uv].uv[1] = v
            bmesh.update_edit_mesh(me)
    def execute(self, context: bpy.types.Context):
        bpy.ops.object.mode_set(mode='EDIT')
        if bpy.context.scene.tool_settings.use_uv_select_sync:
            self.report({"ERROR"}, "此功能需要禁用uv同步")
            return {'CANCELLED'}
        # obj = bpy.context.edit_object

        # v_index = context.active_object.data.loops[bpy.context.scene.loop_index].vertex_index
        # uv_layer = bm.loops.layers.uv.verify()
        self.align_vertices(context)
        a = UV_Data(self)
        # a.straiten_uv_line(self.Axis)
        # print(len(selected_uv_verts),selected_uv_verts,'\n',len(c),c)
        try:
            a.straiten_uv_line(self.Axis)
        except Exception as e:
            # print(e)
            if hasattr(self,'out_of_range') and self.out_of_range:
                return {'CANCELLED'}
        # a.sort_by_path2(self.Axis)
        return {'FINISHED'}


class Straighten_UV(bpy.types.Operator):
    '''选择四个端点,进行四边形拉直'''
    bl_idname = "uv.straighten_uv"
    bl_label = "Straighten UV."
    bl_description="Straighten UV"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}
    clean_up_dict = []

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context: bpy.types.Context):
        # 确保处于编辑模式和UV编辑上下文
        bpy.ops.object.mode_set(mode='EDIT')
        if bpy.context.scene.tool_settings.use_uv_select_sync:
            self.report({"ERROR"}, "此功能需要禁用uv同步")
            return {'CANCELLED'}
        # obj = bpy.context.edit_object
        a = UV_Data(self)
        if a.obj is None:
            self.report({'ERROR'}, "先选择顶点")
            return {'CANCELLED'}
        # print('xuanze', len(a.selected_objs))
        if len(a.selected_objs) > 1:
            self.report({'ERROR'}, "不要同时对两个物体的uv进行操作")
            return {'CANCELLED'}

        try:

            a.set_quad_bound()
        except:
            # print(2222, len(a.clean_up_dict(a.corner_uv)))
            if 4 > len(self.clean_up_dict):
                self.report({'ERROR'}, "不要选择歪着的形状")
                return {'CANCELLED'}
        bpy.ops.uv.select_linked()
        bpy.ops.uv.unwrap_selected_uv()
        del a
        return {'FINISHED'}


class Select_e_loop_index(bpy.types.Operator):
    '''ExampleAddon'''
    bl_idname = "object.select_e_loop_index"
    bl_label = "根据eloopindex选择uv"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        import bmesh, bpy
        bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
        u = bm.loops.layers.uv.verify()
        '''获取端点 v index v uv index
        sorted_indices[:2]
        '''
        dict = {}
        pairs = {}
        for v in bm.verts:
            # 点周围链接的边

            for v_link_edge in v.link_edges:
                # 每条边有两条环路 边界只有一条
                for v_uv_loop_e in v_link_edge.link_loops:
                    if v_uv_loop_e[u].select_edge:
                        # print(v.index,len(v.link_edges),len(v_link_edge.link_loops))
                        # print('v_link_edge',v_link_edge.verts[:])
                        ''' 每个环路只记录一次
                        如果uv边选中,记录下当前uv边的两个顶点信息
                        v: index, v_uv_loop_e ,v_uv_index ,uv: co
                        uv中选中的uv边含有两个顶点
                        '''
                        if v.index in dict:

                            dict[v.index][0].append([v_uv_loop_e.index])
                            # dict[v.index][1].append([loop_e.verts[0].index,loop_e.verts[1].index])
                        else:
                            dict[v.index] = [[[v_uv_loop_e.index]], [], []]
                            for vert in v_link_edge.verts:
                                if v.index != vert.index:
                                    if v.index not in pairs:
                                        pairs[v.index] = [vert.index]
                                    else:
                                        pairs[v.index].append(vert.index)
                                for v_uv_index in vert.link_loops:
                                    if v_uv_index[u].select:
                                        dict[v.index][1].append({v_uv_index.index: vert.index})
                                        if v_uv_index[u].uv not in dict[v.index][2]:
                                            dict[v.index][2].append(v_uv_index[u].uv)
                        # print('dict', dict)
                        # break

        sorted_indices = sorted(dict, key=lambda k: len(dict[k][0]))
        '''sorted_indices[:2]是两个端点 需要判断'''
        # print(len(sorted_indices))
        # print('dict', dict, '\n', sorted_indices)
        # print('pair', pairs, '\n', )
        '''
        新建一个列表,排序顶点
        对端点的link edge遍历,查找到选择的顶点,加入列表,继续循环,排除已经在列表的顶点
            
            '''
        list = [sorted_indices[0]]
        for i in range(len(sorted_indices)):
            for v_link_edge in bm.verts[list[i]].link_edges:
                if len(list) == i + 2:
                    break
                for loop in v_link_edge.link_loops:
                    # print(i, len(list))
                    if len(list) == i + 2:
                        break
                    if loop[u].select_edge:
                        for vert in v_link_edge.verts:
                            if vert.index != list[i]:
                                if i == 0:
                                    list.append(vert.index)
                                else:
                                    if vert.index != list[i - 1]:
                                        list.append(vert.index)

                                break

        # print(list)

        return {'FINISHED'}


class Select_loop_index(bpy.types.Operator):
    '''ExampleAddon'''
    bl_idname = "object.example_ops"
    bl_label = "根据vloopindex选择uv"

    # 确保在操作之前备份数据，用户撤销操作时可以恢复
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.active_object is not None

    def execute(self, context: bpy.types.Context):
        bm = bmesh.from_edit_mesh(context.active_object.data)
        v_index = context.active_object.data.loops[bpy.context.scene.loop_index].vertex_index
        uv_layer = bm.loops.layers.uv.verify()
        for loop in bm.verts[v_index].link_loops:
            if loop.index == bpy.context.scene.loop_index:
                loop[uv_layer].select = 1
        bmesh.update_edit_mesh(context.active_object.data, loop_triangles=False,
                               destructive=False)  # 更新mesh，应用所有bmesh的修改

        return {'FINISHED'}


import copy

import bpy
import bmesh
import math

from mathutils import Vector


def deselect_all():
    area = next(area for area in bpy.context.screen.areas if area.type == 'IMAGE_EDITOR')
    region = next(region for region in area.regions if region.type == 'WINDOW')
    with bpy.context.temp_override(area=area, region=region):
        # 在覆盖上下文中执行选择最短路径操作
        bpy.ops.uv.select_all(action='DESELECT')


def shortest_path_select():
    '''拾取两点之间的顶点'''
    area = next(area for area in bpy.context.screen.areas if area.type == 'IMAGE_EDITOR')
    region = next(region for region in area.regions if region.type == 'WINDOW')
    with bpy.context.temp_override(area=area, region=region):
        # 在覆盖上下文中执行选择最短路径操作
        bpy.ops.uv.shortest_path_select()


class UV_Data():
    def __init__(self, ops=None):
        self.ops = ops
        self.obj = self.get_obj()
        # print(self.obj)
        # print(len(self.selected_objs))

        # print('初始化self.boundary_dict的长度', len(self.boundary_dict))
        self.corner_uv = {}
        # 计算好boundingbox

        # print('self.lp_index_x  ', self.lp_index_x, '\nself.lp_index_y  ', self.lp_index_y)
        self.selected = {}

    def get_obj(self):
        self.selected_objs = []
        bpy.ops.object.mode_set(mode='OBJECT')
        for o in bpy.context.selected_objects:
            if len(self.selected_objs) > 1:
                break
            mesh = o.data
            if mesh.uv_layers.active:  # 检查是否有活动的UV layer
                uv_layer = mesh.uv_layers.active.data

                for poly in mesh.polygons:  # 遍历所有多边形
                    # print("Polygon index:", poly.index)
                    for loop_index in poly.loop_indices:  # 遍历多边形的所有loop
                        loop_uv = uv_layer[loop_index]
                        if loop_uv.select:
                            # print('o name', o.name)
                            if o in self.selected_objs:
                                break
                            self.selected_objs.append(o)
                            break
                    if len(self.selected_objs) > 1:
                        break

        bpy.ops.object.mode_set(mode='EDIT')
        if len(self.selected_objs)==0:
            return None
        return self.selected_objs[0]

    def clean_up_dict(self, dict):
        copy_dict = copy.deepcopy(dict)
        unique_uvs = []
        loops = list(copy_dict.keys())
        for loop in loops:
            # print(copy_dict[loop][1])
            if copy_dict[loop][1] not in unique_uvs:
                unique_uvs.append(copy_dict[loop][1])
            else:
                # 删除已有
                copy_dict.pop(loop)
        # print('清理dict0', len(copy_dict))
        return copy_dict

    def get_bound(self,dict):
        copy_dict = self.clean_up_dict(dict)
        # print('copy_dict', copy_dict)
        self.lp_index_y = sorted(copy_dict, key=lambda k: copy_dict[k][1][1])
        # for loop in self.lp_index_y:
        #     print('输出self.lp_index_y',copy_dict[loop][1])
        # print('lp_index_y', len(self.lp_index_y))
        self.min_y = copy_dict[self.lp_index_y[0]][1][1]
        self.max_y = copy_dict[self.lp_index_y[-1]][1][1]
        self.lp_index_x = sorted(copy_dict, key=lambda k: copy_dict[k][1][0])
        # for loop in self.lp_index_x:
        #     print('输出self.lp_index_x',copy_dict[loop][1])
        self.min_x = copy_dict[self.lp_index_x[0]][1][0]
        self.max_x = copy_dict[self.lp_index_x[-1]][1][0]
    def get_Boundary_points(self):
        pass

    def get_selected_uv(self, bm):
        '''返回选择的uv loop index和坐标
        dict:
        key:
            loops index
        val:
            [vertex index,Vector(x,y)]'''

        # UV层
        uv_layer = bm.loops.layers.uv.verify()
        bm.verts.ensure_lookup_table()
        # 使用字典防止重复，并且遍历bm.verts
        selected_uv_verts = {}
        for vert in bm.verts:
            if vert.select:
                for loop in vert.link_loops:
                    uv = loop[uv_layer]

                    if uv.select:
                        # print(111,loop.index)
                        uv.pin_uv = True
                        # print(loop.index)
                        selected_uv_verts[loop.index] = [vert.index, list(loop[uv_layer].uv)]
        # print(len(selected_uv_verts))

        # print('所有选中的loop:', selected_uv_verts)

        return selected_uv_verts
    def straiten_uv_line(self, direction=None):
        bm = bmesh.from_edit_mesh(self.obj.data)
        uv_layer = bm.loops.layers.uv.verify()
        bm.verts.ensure_lookup_table()
        selected_uv_verts = self.get_selected_uv(bm)

        clean_selected_uv_verts = self.clean_up_dict(selected_uv_verts)
        # self.get_bound(clean_selected_uv_verts)
        border,v_border=self.is_border(clean_selected_uv_verts)
        # print('是否边界点',border)
        if border:

            v_uv= {}
            '''记录了同一顶点,不同uv点的情况时
            uv点所有的loop index和 uv坐标'''
            start = 0
            start_co=0
            uv_offset=0
            '''如果端点是同一个点,根据ops的选择,判断一下位置,记录uv loop'''
            for loop in bm.verts[v_border].link_loops:
                if loop.index in selected_uv_verts:
                    # print(f'选择中的loop:{loop.index}并且在selected_uv_verts中')
                    # for e in loop.edge.link_loops:
                    #     print(loop.index,e.index,e[uv_layer].select_edge)
                    #     if e[uv_layer].select_edge:
                    # if loop[uv_layer].select_edge:
                    if loop.link_loop_next[uv_layer].select or loop.link_loop_prev[uv_layer].select:
                        v_uv[loop.index]=loop[uv_layer].uv
            # print(f'边界端点:{v_border}\n拥有选中边数v_uv大小:{len(v_uv)} \n所有:{selected_uv_verts.keys()}')
            # print('v_uv1',selected_uv_verts.keys())
            # loops=list(v_uv.keys())
            new_dict = {}
            seen_values = set()

            for key, value in v_uv.items():
                if tuple(value) not in seen_values:
                    new_dict[key] = tuple(value)
                    seen_values.add(tuple(value))
            loops = list(new_dict.keys())
            # print('v_uv', loops)
            # print('-------------------', loops)
            # print('new_dict', new_dict)
            # print('new_dict', new_dict)
            if direction in ['MAX_U','MIN_U']:
                if new_dict[loops[0]][1]>new_dict[loops[1]][1]:
                    start=loops[1]
                else:
                    start=loops[0]
                uv_offset=abs(selected_uv_verts[loops[0]][1][1] - selected_uv_verts[loops[1]][1][1])
            elif direction in ['MAX_V','MIN_V']:
                if new_dict[loops[0]][0]>new_dict[loops[1]][0]:
                    start=loops[1]
                else:
                    start=loops[0]
                # print(start,loops[1],loops[0])
                uv_offset = abs(selected_uv_verts[loops[0]][1][0] - selected_uv_verts[loops[1]][1][0])

            start_v=self.get_v_index_from_lp_index(start)
            # print('start', start,start_v)
            sorted_indices = [start_v]
            # print(f'sorted_indices {len(sorted_indices)}{sorted_indices}\n clean_selected_uv_verts大小{len(clean_selected_uv_verts)}')
            for i in range(len(clean_selected_uv_verts)):
                # print('i', i)
                for loop in bm.verts[sorted_indices[i]].link_loops:
                    # print('i:loop index:', loop.index)
                    if i==0:
                        # print(0,loop.index)
                        if loop.index==start:
                            # print('loop.index==start', loop.index==start)
                            # print('loop[uv_layer].select_edge', loop[uv_layer].select_edge)
                            # if loop[uv_layer].select_edge:
                            if loop.link_loop_next[uv_layer].select:
                                sorted_indices.append(loop.link_loop_next.vert.index)
                                # print(1,loop.link_loop_next.vert.index)
                            elif loop.link_loop_prev[uv_layer].select:
                                sorted_indices.append(loop.link_loop_prev.vert.index)
                                # print(2,loop.link_loop_prev.index,start_v,loop.link_loop_prev[uv_layer].uv)
                                # print(1, loop.link_loop_next.vert.index,loop.link_loop_next[uv_layer].uv)
                                # print('loop[uv_layer].select_edge2', loop[uv_layer].select_edge)
                                # for vert in loop.edge.verts:
                                #     if vert.index!=start_v:
                                #         sorted_indices.append(vert.index)
                        # print(f'检查长度{len(sorted_indices)} == {len(clean_selected_uv_verts)}')
                    else:
                        if len(sorted_indices) == i + 2:
                            break
                        if len(sorted_indices) == len(clean_selected_uv_verts):
                            break
                        # if loop[uv_layer].select_edge:
                        if loop.link_loop_next[uv_layer].select:
                            if loop.link_loop_next.vert.index not in sorted_indices[i-1:i+1]:
                                # print(f'sorted_indices {len(sorted_indices)}{sorted_indices}\n clean_selected_uv_verts大小{len(clean_selected_uv_verts)}')
                                sorted_indices.append(loop.link_loop_next.vert.index)
                        elif loop.link_loop_prev[uv_layer].select:
                            if loop.link_loop_prev.vert.index not in sorted_indices[i-1:i+1]:
                                # print(f'sorted_indices {len(sorted_indices)}{sorted_indices}\n clean_selected_uv_verts大小{len(clean_selected_uv_verts)}')
                                sorted_indices.append(loop.link_loop_prev.vert.index)
                        # if loop.link_loop_next[uv_layer].select or loop.link_loop_prev[uv_layer].select:
                        #     for vert in loop.edge.verts:
                        #         # print('v_lists[i-1:i]', sorted_indices[i-1:i+1])
                        #         if vert.index not in sorted_indices[i-1:i+1]:
                        #             print(
                        #                 f'sorted_indices {len(sorted_indices)}{sorted_indices}\n clean_selected_uv_verts大小{len(clean_selected_uv_verts)}')
                        #             sorted_indices.append(vert.index)
                        #             break
            # print('direction', sorted_indices,len(sorted_indices),len(clean_selected_uv_verts))
            #线段长度
            # print('offset',uv_offset)
        else:
            #还要判断下有一个端点是边界的情况 否则可能选择错误的uv端点
            bm,sorted_indices,uv_offset=self.sort_by_path(direction)

        # 处理端点的最大最小uv
        if border:
            self.border_same_p_set_minmax(bm, v_border)
        else:
            for v_index in [sorted_indices[0],sorted_indices[-1]]:
                self.border_same_p_set_minmax(bm, v_index)
        proportions=self.cal_3d_line_len(sorted_indices)
        # print('proportions',self.min_x,self.max_x,self.min_y,proportions,uv_offset)
        # if direction in ['MAX_U', 'MIN_U']:#设置y
        # print(f'排序好的顶点{sorted_indices}')
        for v_index in sorted_indices:
            if sorted_indices.index(v_index) == 0 or sorted_indices.index(v_index) == (len(sorted_indices) - 1):
                continue  # 跳过线段的两端点
            # print(f'分布设置y{len(bm.verts)}',)
            v_loop=0
            if bm.verts[v_index].select:
                for loop in bm.verts[v_index].link_loops:
                    if loop[uv_layer].select:
                        v_loop=loop[uv_layer]
                        # print('uv点选择',loop.index)
            same_points = self.get_same_uv_points(bm, v_index, v_loop)
            # print(len(same_points))
            for uv in same_points:
                if direction in ['MAX_U', 'MIN_U']:  # 设置y
                    uv.uv[1] = self.min_y + uv_offset * proportions[sorted_indices.index(v_index) - 1]
                # 按分布设置y
                elif direction in ['MAX_V', 'MIN_V']:
                    uv.uv[0] = self.min_x + abs(self.min_x-self.max_x) * proportions[sorted_indices.index(v_index) - 1]
        # elif direction in ['MAX_V', 'MIN_V']:
        #     print('分布设置x')
        #     pass
        # print('11',direction)
        # return sorted_indices
    def is_border(self,dict):
        list=[]
        for loop in dict.keys():
            v_index=self.get_v_index_from_lp_index(loop)
            if v_index not in list:
                list.append(v_index)
            else:
                return True, v_index
        return False,None
    def border_same_p_set_minmax(self,bm,v_index):
        pass
        uv_layer = bm.loops.layers.uv.verify()
        bm.verts.ensure_lookup_table()
        for loop in bm.verts[v_index].link_loops:
            if loop[uv_layer].select:
                if not hasattr(self, 'min_x'):
                    self.min_x = loop[uv_layer].uv.x
                if not hasattr(self, 'min_y'):
                    self.min_y = loop[uv_layer].uv.y
                if not hasattr(self, 'max_x'):
                    self.max_x = loop[uv_layer].uv.x
                if not hasattr(self, 'max_y'):
                    self.max_y = loop[uv_layer].uv.y

                # 更新
                if self.min_x>loop[uv_layer].uv.x:
                    self.min_x = loop[uv_layer].uv.x
                if self.min_y>loop[uv_layer].uv.y:
                    self.min_y = loop[uv_layer].uv.y
                if self.max_x<loop[uv_layer].uv.x:
                    self.max_x = loop[uv_layer].uv.x
                if self.max_y<loop[uv_layer].uv.y:
                    self.max_y = loop[uv_layer].uv.y
    def sort_by_path(self, direction=None):
        bm = bmesh.from_edit_mesh(self.obj.data)
        u = bm.loops.layers.uv.verify()
        '''获取端点 v index v uv index
        sorted_indices[:2]
        '''
        dict = {}
        pairs = {}
        for vert in bm.verts:
            # 点周围链接的边

            for v_link_edge in vert.link_edges:

                # 每条边有两条环路 边界只有一条
                for v_uv_loop_e in v_link_edge.link_loops:
                    if v_uv_loop_e[u].select_edge:
                        # print(vert.index,1)
                        # print(vert.index,len(vert.link_edges),len(v_link_edge.link_loops))
                        # print('v_link_edge',v_link_edge.verts[:])
                        ''' 每个环路只记录一次
                        如果uv边选中,记录下当前uv边的两个顶点信息
                        v: index, v_uv_loop_e ,v_uv_index ,uv: co
                        uv中选中的uv边含有两个顶点
                        '''
                        if vert.index in dict:

                            dict[vert.index][0].append([v_uv_loop_e.index])
                            # dict[vert.index][1].append([loop_e.verts[0].index,loop_e.verts[1].index])
                        else:
                            dict[vert.index] = [[[v_uv_loop_e.index]], [], []]
                            for verts_v in v_link_edge.verts:
                                if vert.index != verts_v.index:
                                    if vert.index not in pairs:
                                        pairs[vert.index] = [verts_v.index]
                                    else:
                                        pairs[vert.index].append(verts_v.index)
                                for v_uv_index in verts_v.link_loops:
                                    if v_uv_index[u].select:
                                        dict[vert.index][1].append({v_uv_index.index: verts_v.index})
                                        if v_uv_index[u].uv not in dict[vert.index][2]:
                                            dict[vert.index][2].append(v_uv_index[u].uv)
                        # print('dict', dict)
                        # break

        sorted_indices = sorted(dict, key=lambda k: len(dict[k][0]))
        bm.verts.ensure_lookup_table()
        '''sorted_indices[:2]是两个端点 需要判断'''
        # print('sorted_indices[:]',sorted_indices[:])
        # print('sorted_indices[:]',len(bm.verts))
        v_uv=[0,0]
        final=0
        for i in range(2):
            try:
                print('v index:',sorted_indices[i])
            except:
                self.ops.report({'INFO'}, "不要跨uv岛选择顶点")
                self.ops.out_of_range=True

            for loop in bm.verts[sorted_indices[i]].link_loops:
                # print(f'{i},顶点 {sorted_indices[i]},数量{len(bm.verts[sorted_indices[i]].link_loops)}, 选择uv{loop[u].select}')
                # print(sorted_indices[i],loop.index,loop[u].select)
                if loop[u].select:
                    # print(1111)
                    # print(loop[u].uv)
                    # print('direction',direction)
                    if direction in ['MAX_U', 'MIN_U']:
                        # print(loop[u].uv.y)
                        v_uv[i]=loop[u].uv.y
                    elif direction in ['MAX_V', 'MIN_V']:
                        v_uv[i] = loop[u].uv.x
                    # print('v_uvv_uv',v_uv)
                    break

            '''比较y的值'''
        # print('v_uv', v_uv)
        if v_uv[0]>v_uv[1]:
            final=1
        else:
            final=0
        uv_offset=abs(v_uv[1]-v_uv[0])
        # print('uv_offset',uv_offset)
        # final = 1
        # print(len(sorted_indices))
        # print('dict', dict, '\n', sorted_indices)
        # print('pair', pairs, '\n', )
        '''
        新建一个列表,排序顶点
        对端点的link edge遍历,查找到选择的顶点,加入列表,继续循环,排除已经在列表的顶点

            '''
        
        list = [sorted_indices[final]]
        for i in range(len(sorted_indices)):
            for v_link_edge in bm.verts[list[i]].link_edges:
                if len(list) == i + 2:
                    break
                for loop in v_link_edge.link_loops:
                    # print(i, len(list))
                    if len(list) == i + 2:
                        break
                    if loop[u].select_edge:
                        for vert in v_link_edge.verts:
                            if vert.index != list[i]:
                                if i == 0:
                                    list.append(vert.index)
                                else:
                                    if vert.index != list[i - 1]:
                                        list.append(vert.index)

                                break

        # print(list)
        # bm.free()
        return bm,list,uv_offset
    def aaa(self):
        list=self.sort_by_path()
        # list2=self.cal_3d_line_len(list)
        # print(1)
    def calculate_uv_angle(self, uv1, uv2):
        """计算两个UV坐标之间的角度，结果归一化到0-180度范围内。"""
        # 计算向量 AB
        dx = uv1[1][0] - uv2[1][0]
        dy = uv1[1][1] - uv2[1][1]

        # 计算点积
        dot_product = dy  # 因为与 (0, 1) 的点积为 dy

        # 计算向量 AB 的模长
        magnitude_AB = math.sqrt(dx ** 2 + dy ** 2)

        # 计算余弦值
        if magnitude_AB == 0:
            return 0  # 如果两点相同，则没有明确的角度

        cos_theta = abs(dot_product / magnitude_AB)

        # 计算角度（转换为度）
        angle_radians = math.acos(cos_theta)
        angle_degrees = math.degrees(angle_radians)

        return angle_degrees

    def classify_uv_lines(self, angles, threshold=10):
        """根据角度将UV线段分类为垂直或水平。

        线段角度接近90度被认为是垂直的，而接近0度或180度的线段被认为是水平的。
        """
        vertical_lines = []
        horizontal_lines = []
        for (index_pair, angle) in angles.items():
            if abs(angle - 90) <= threshold:
                vertical_lines.append(index_pair)
            elif abs(angle - 0) <= threshold or abs(angle - 180) <= threshold:
                horizontal_lines.append(index_pair)
        return vertical_lines, horizontal_lines

    def get_uv_direction(self, bm, selected_uv_coords):
        """识别UV坐标中的水平和垂直线段，并返回这些线段的loop索引。

        参数:
        obj -- 需要分析的Blender对象
        """
        vertical_lines = []
        horizontal_lines = []
        copy_dict = self.clean_up_dict(selected_uv_coords)
        # print(len(copy_dict))
        loops = list(copy_dict.keys())
        for i in range(3):
            line = [copy_dict[loops[0]], copy_dict[loops[i + 1]]]
            # if 0<self.calculate_uv_angle(*line)<180
            if int(self.calculate_uv_angle(*line)) not in [0, 90]:
                for s in range(3):
                    # print('loops', len(loops), len(copy_dict))
                    line2 = [copy_dict[loops[i + 1]], copy_dict[loops[s + 1]]]
                    if line2[0] == line2[1]:
                        continue
                    if int(self.calculate_uv_angle(*line2)) == 90:
                        vertical_lines.append([loops[i + 1], loops[s + 1]])
                    elif int(self.calculate_uv_angle(*line2)) == 0:
                        horizontal_lines.append([loops[i + 1], loops[s + 1]])
            if int(self.calculate_uv_angle(*line)) == 90:
                vertical_lines.append([loops[0], loops[i + 1]])
            elif int(self.calculate_uv_angle(*line)) == 0:
                horizontal_lines.append([loops[0], loops[i + 1]])

        # # 分类线段为垂直或水平
        # print('竖2 横2:', horizontal_lines + vertical_lines)

        return horizontal_lines + vertical_lines

    def cal_line_len(self, bm, direction):
        '''根据x或y方向，计算单条路径中每个线段的长度，并计算其相对于总长度的累计比例。'''

        # 获取当前选择的UV点
        line = self.get_selected_uv(bm)
        segment_lengths = []  # 用于存储各段的长度
        sorted_indices = []  # 存储根据指定方向排序后的索引
        self.selected = self.selected | line
        # 根据指定的方向对UV点进行排序
        if direction == 'y':  # 如果是竖直方向
            sorted_indices = sorted(line, key=lambda k: line[k][1][1])
        elif direction == 'x':  # 如果是水平方向
            sorted_indices = sorted(line, key=lambda k: line[k][1][0])

        # 计算相邻两点间的直线距离
        for i in range(len(sorted_indices) - 1):
            offset = self.obj.data.vertices[line[sorted_indices[i]][0]].co - self.obj.data.vertices[
                line[sorted_indices[i + 1]][0]].co
            # x_distance = abs(line[sorted_indices[i]][0] - line[sorted_indices[i + 1]][0])
            # y_distance = abs(line[sorted_indices[i]][0] - line[sorted_indices[i + 1]][0])
            # z_distance = abs(line[sorted_indices[i]][0] - line[sorted_indices[i + 1]][0])
            segment_lengths.append(math.sqrt(offset.x ** 2 + offset.y ** 2 + offset.z ** 2))

        # 计算所有段长度的总和
        total_length = sum(segment_lengths)

        # 计算各段长度的累计占比
        cumulative_proportions = []
        if total_length == 0:
            # 如果总长度为0，则避免除以零的错误
            cumulative_proportions = [0] * len(segment_lengths)
        else:
            cumulative_sum = 0
            for length in segment_lengths:
                cumulative_sum += length / total_length  # 计算当前段占总长度的比例，并累加
                cumulative_proportions.append(cumulative_sum)  # 添加到累计比例列表

        # 打印索引和累计占比的对应关系
        # print('Sorted indices and their cumulative proportions:', sorted_indices, cumulative_proportions)
        return sorted_indices, cumulative_proportions

    def cal_3d_line_len(self, sorted_indices):
        '''根据x或y方向，计算单条路径中每个线段的长度，并计算其相对于总长度的累计比例。'''

        # # 获取当前选择的UV点
        # line = self.get_selected_uv(bm)
        segment_lengths = []  # 用于存储各段的长度
        # sorted_indices = []  # 存储根据指定方向排序后的索引
        # self.selected = self.selected | line
        # # 根据指定的方向对UV点进行排序
        # if direction == 'y':  # 如果是竖直方向
        #     sorted_indices = sorted(line, key=lambda k: line[k][1][1])
        # elif direction == 'x':  # 如果是水平方向
        #     sorted_indices = sorted(line, key=lambda k: line[k][1][0])

        # 计算相邻两点间的直线距离
        for i in range(len(sorted_indices) - 1):
            offset = self.obj.data.vertices[sorted_indices[i]].co - self.obj.data.vertices[
                sorted_indices[i + 1]].co
            # x_distance = abs(line[sorted_indices[i]][0] - line[sorted_indices[i + 1]][0])
            # y_distance = abs(line[sorted_indices[i]][0] - line[sorted_indices[i + 1]][0])
            # z_distance = abs(line[sorted_indices[i]][0] - line[sorted_indices[i + 1]][0])
            segment_lengths.append(math.sqrt(offset.x ** 2 + offset.y ** 2 + offset.z ** 2))

        # 计算所有段长度的总和
        total_length = sum(segment_lengths)

        # 计算各段长度的累计占比
        cumulative_proportions = []
        if total_length == 0:
            # 如果总长度为0，则避免除以零的错误
            cumulative_proportions = [0] * len(segment_lengths)
        else:
            cumulative_sum = 0
            for length in segment_lengths:
                cumulative_sum += length / total_length  # 计算当前段占总长度的比例，并累加
                cumulative_proportions.append(cumulative_sum)  # 添加到累计比例列表

        # 打印索引和累计占比的对应关系
        # print('Sorted indices and their cumulative proportions:', sorted_indices, cumulative_proportions)
        return cumulative_proportions

    def get_loop_from_lp_index(self, bm, lp_index):
        v_index = self.obj.data.loops[lp_index].vertex_index
        uv_layer = bm.loops.layers.uv.verify()
        for loop in bm.verts[v_index].link_loops:
            if loop.index == lp_index:
                return loop[uv_layer]

    def get_v_index_from_lp_index(self,lp_index):
        v_index = self.obj.data.loops[lp_index].vertex_index
        return v_index
    def get_same_uv_points(self, bm, v_index, uv):
        '''一个包含所有匹配 UV 点的列表'''
        uv_layer = bm.loops.layers.uv.verify()
        matching_uvs = []
        for loop in bm.verts[v_index].link_loops:
            # if loop.index == lp_index:

            if loop[uv_layer].uv == uv.uv:
                # print('测试list loop[uv_layer].uv', loop[uv_layer].uv)
                matching_uvs.append(loop[uv_layer])
        return matching_uvs

    def recover_corner_uv(self, bm):
        # bm = bmesh.from_edit_mesh(self.obj.data)  # 从对象数据中创建bmesh对象，以便进行编辑
        uv_layer = bm.loops.layers.uv.verify()  # 确保UV层可用
        bm.verts.ensure_lookup_table()
        for loop_index in self.corner_uv:
            v_index = self.boundary_dict[loop_index][0]
            for loop in bm.verts[v_index].link_loops:
                if loop.index == loop_index:
                    loop[uv_layer].uv = self.corner_uv[loop_index][1]
        bmesh.update_edit_mesh(self.obj.data, loop_triangles=False, destructive=False)  # 更新mesh，应用所有bmesh的修改
        # bm.free()  # 释放bmesh，避免内存泄漏

    def initial_corner_uv(self, bm):
        # bm = bmesh.from_edit_mesh(self.obj.data)  # 从对象数据中创建bmesh对象，以便进行编辑
        uv_layer = bm.loops.layers.uv.verify()  # 确保UV层可用
        bm.verts.ensure_lookup_table()
        for loop_index in self.boundary_dict:
            v_index = self.boundary_dict[loop_index][0]
            for loop in bm.verts[v_index].link_loops:
                if loop.index == loop_index:
                    loop[uv_layer].uv = self.boundary_dict[loop_index][1]
        bmesh.update_edit_mesh(self.obj.data, loop_triangles=False, destructive=False)  # 更新mesh，应用所有bmesh的修改
        bm.free()  # 释放bmesh，避免内存泄漏

    def set_quad_bound(self):
        bm = bmesh.from_edit_mesh(self.obj.data)
        bm.verts.ensure_lookup_table()
        self.boundary_dict = self.get_selected_uv(bm)
        self.get_bound(self.boundary_dict)
        # bm = bmesh.from_edit_mesh(self.obj.data)  # 从对象数据中创建bmesh对象，以便进行编辑
        # bm.verts.ensure_lookup_table()
        self.set_corner_uv(bm)
        # lines = self.get_direction(self.boundary_dict)  # 获取线段端点的loop index
        lines = self.get_uv_direction(bm, self.corner_uv)  # 获取线段端点的loop index
        # 恢复初始四个顶点
        # self.initial_corner_uv(bm)
        # print(f'初始{len(self.boundary_dict)} {len(self.corner_uv)}')

        for line in lines:
            deselect_all()  # 取消选择所有元素

            # 获取顶点索引
            bm = bmesh.from_edit_mesh(self.obj.data)  # 从对象数据中创建bmesh对象，以便进行编辑
            uv_layer = bm.loops.layers.uv.verify()  # 确保UV层可用
            bm.verts.ensure_lookup_table()
            for v_index in [self.boundary_dict[line[0]][0], self.boundary_dict[line[1]][0]]:
                for loop in bm.verts[v_index].link_loops:
                    if loop.index in line:  # 如果循环的索引在当前线中
                        loop[uv_layer].select = True  # 选择当前循环的UV层

            bmesh.update_edit_mesh(self.obj.data, loop_triangles=False, destructive=False)  # 更新mesh，应用所有bmesh的修改
            bm.free()  # 释放bmesh，避免内存泄漏

            # 选择给定的两点之间的所有点
            shortest_path_select()  # 选择最短路径上的点

            # 根据最大边界进行拉直，对齐
            max = False
            bm = bmesh.from_edit_mesh(self.obj.data)  # 再次创建bmesh对象
            bm.verts.ensure_lookup_table()
            uv_layer = bm.loops.layers.uv.verify()  # 确保UV层可用
            if lines.index(line) < 2:  # 竖线
                lp_index, proportions = self.cal_line_len(bm, 'y')  # 计算线长，这里传入'y'可能意味着按照y方向计算
                new_len = self.max_y - self.min_y

                # y是竖边，要判断是左边还是右边；x判断上边还是下边
                for i in lp_index:
                    # 当前线段中，判断每个顶点的x，是左边还是右边
                    v_index = bpy.context.object.data.loops[i].vertex_index
                    if self.max_x == self.get_loop_from_lp_index(bm, i).uv[0]:
                        max = True
                        break

                for i in lp_index:
                    v_index = bpy.context.object.data.loops[i].vertex_index
                    if lp_index.index(i) == 0 or lp_index.index(i) == (len(lp_index) - 1):
                        continue  # 跳过线段的两端点
                    same_points = self.get_same_uv_points(bm, v_index, self.get_loop_from_lp_index(bm, i))
                    # for l in bm.verts[v_index].link_loops:
                    #     if l.index == i:
                    #         print('point x', l[uv_layer].uv)
                    for uv in same_points:
                        if max:  # 右边边
                            uv.uv[0] = self.max_x  # 将uv点的x坐标设置为最大x
                        else:  # 左边
                            uv.uv[0] = self.min_x  # 将uv点的x坐标设置为最小x
                        # 按分布设置y
                        uv.uv[1] = self.min_y + new_len * proportions[lp_index.index(i) - 1]

                max = False
                # bmesh.update_edit_mesh(self.obj.data, loop_triangles=False, destructive=False)  # 再次更新mesh
                # bm.free()
            else:
                lp_index, proportions = self.cal_line_len(bm, 'x')  # 对横线进行处理
                new_len = self.max_x - self.min_x
                bm = bmesh.from_edit_mesh(self.obj.data)
                uv_layer = bm.loops.layers.uv.verify()
                for i in lp_index:
                    v_index = bpy.context.object.data.loops[i].vertex_index
                    if self.max_y == self.get_loop_from_lp_index(bm, i).uv[1]:
                        max = True
                        break

                for i in lp_index:
                    v_index = bpy.context.object.data.loops[i].vertex_index
                    if lp_index.index(i) == 0 or lp_index.index(i) == (len(lp_index) - 1):
                        continue

                    for uv in self.get_same_uv_points(bm, v_index, self.get_loop_from_lp_index(bm, i)):
                        if max:
                            uv.uv[1] = self.max_y  # 设置y坐标为最大值
                        else:  # 左边
                            uv.uv[1] = self.min_y  # 设置y坐标为最小值
                        uv.uv[0] = self.min_x + new_len * proportions[lp_index.index(i) - 1]

                max = False
            bmesh.update_edit_mesh(self.obj.data, loop_triangles=False, destructive=False)  # 最后更新mesh

            # bm.free()  # 释放bmesh
            # pass
        # 设置边界框的四个顶点
        # self.recover_corner_uv(bm)
        bmesh.update_edit_mesh(self.obj.data, loop_triangles=False, destructive=False)
        bm.free()
        # print(len(self.boundary_dict),len(self.corner_uv))

    def set_corner_uv(self, bm):
        '''
        排序x y 
        第一第二设置为第一
        第三第四设置为第四'''

        # 确保UV层可用
        uv_layer = bm.loops.layers.uv.verify()
        for i in range(4):
            if i == 1:
                loop = self.get_loop_from_lp_index(bm, self.lp_index_x[i])
                v_index = self.obj.data.loops[self.lp_index_x[i]].vertex_index
                same_points = self.get_same_uv_points(bm, v_index, loop)
                for point in same_points:
                    point.uv[0] = self.min_x

                loop = self.get_loop_from_lp_index(bm, self.lp_index_y[i])
                v_index = self.obj.data.loops[self.lp_index_y[i]].vertex_index
                same_points = self.get_same_uv_points(bm, v_index, loop)
                for point in same_points:
                    point.uv[1] = self.min_y

            if i == 2:
                loop = self.get_loop_from_lp_index(bm, self.lp_index_x[i])
                v_index = self.obj.data.loops[self.lp_index_x[i]].vertex_index
                same_points = self.get_same_uv_points(bm, v_index, loop)
                for point in same_points:
                    point.uv[0] = self.max_x

                loop = self.get_loop_from_lp_index(bm, self.lp_index_y[i])
                v_index = self.obj.data.loops[self.lp_index_y[i]].vertex_index
                same_points = self.get_same_uv_points(bm, v_index, loop)
                for point in same_points:
                    point.uv[1] = self.max_y
        bmesh.update_edit_mesh(self.obj.data, loop_triangles=False, destructive=False)  # 更新mesh，应用所有bmesh的修改
        # 记录四个角 长方形的uv坐标 方便恢复
        bm.verts.ensure_lookup_table()
        # print('set_corner_uv', self.boundary_dict)
        for loop_index in self.boundary_dict:
            v_index = self.boundary_dict[loop_index][0]
            for loop in bm.verts[v_index].link_loops:
                if loop.index == loop_index:
                    self.corner_uv[loop_index] = [v_index, list(loop[uv_layer].uv)]
        # 返回给ops,方便打印错误
        if hasattr(self.ops, 'clean_up_dict'):
            self.ops.clean_up_dict = self.clean_up_dict(self.corner_uv)
        uv_layer = bm.loops.layers.uv.verify()
        for i in self.selected.keys():
            v_index = bpy.context.object.data.loops[i].vertex_index
            for loop in bm.verts[v_index].link_loops:
                if loop.index == i:
                    loop[uv_layer].select = True
        # print(len(self.selected))
        return bm
