from collections import deque, defaultdict
import bpy,bmesh

def register_keymaps(keylist):
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    keymaps = []

    if kc:

        for item in keylist:
            keymap = item.get("keymap")
            space_type = item.get("space_type", "EMPTY")

            if keymap:
                km = kc.keymaps.new(name=keymap, space_type=space_type)

                if km:
                    idname = item.get("idname")
                    type = item.get("type")
                    value = item.get("value")

                    shift = item.get("shift", False)
                    ctrl = item.get("ctrl", False)
                    alt = item.get("alt", False)

                    kmi = km.keymap_items.new(idname, type, value, shift=shift, ctrl=ctrl, alt=alt)

                    if kmi:
                        properties = item.get("properties")

                        if properties:
                            # for attr in dir(kmi.properties):
                            #     print(111,attr)
                            for name, value in properties:
                                # print('name, value',name,value)
                                setattr(kmi.properties, name, value)

                        active = item.get("active", True)
                        kmi.active = active

                        keymaps.append((km, kmi))
    else:
        print("WARNING: Keyconfig not availabe, skipping color picker keymaps")

    return keymaps
def unregister_keymaps(keymaps):
    for km, kmi in keymaps:
        km.keymap_items.remove(kmi)
def get_bbox(uv, faces):
    """
    Return lower left point and top right point.
    """
    if isinstance(faces, list):
        initial_point = faces[0].loops[0][uv].uv
    else:
        for face in faces:
            break
        initial_point = face.loops[0][uv].uv

    u_min, v_min = initial_point
    u_max, v_max = initial_point

    for f in faces:
        for l in f.loops:
            u, v = l[uv].uv[0], l[uv].uv[1]
            if u < u_min:
                u_min = u
            if u_max < u:
                u_max = u
            if v < v_min:
                v_min = v
            if v_max < v:
                v_max = v
    return (u_min, v_min), (u_max, v_max)
def get_objects_seams(context):
    store_initial_seams = defaultdict(list)
    objects_seams = defaultdict(set)
    store_initial_selection = defaultdict(set)
    store_face_selection = defaultdict(set)
    store_verts_selection = defaultdict(set)
    store_edges_selection = defaultdict(set)

    scene = context.scene
    current_uv_select_mode = scene.tool_settings.uv_select_mode
    scene.tool_settings.uv_select_mode = 'VERTEX'

    for ob in context.objects_in_mode_unique_data:
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        uv = bm.loops.layers.uv.verify()
        for e in bm.edges:
            if e.seam:
                store_initial_seams[ob].append(e.index)
                e.seam = False
            if e.select:
                store_edges_selection[ob].add(e.index)
        for v in bm.verts:
            if v.select:
                store_verts_selection[ob].add(v.index)
        for f in bm.faces:
            if f.select:
                store_face_selection[ob].add(f.index)
            for l in f.loops:
                if l[uv].select:
                    store_initial_selection[ob].add(l.index)
                l[uv].select = True
            f.select = True

    bpy.ops.uv.seams_from_islands(mark_seams=True)

    for ob in context.objects_in_mode_unique_data:
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        for e in bm.edges:
            if e.seam:
                objects_seams[ob].add(e.index)
                e.seam = False

    for ob in context.objects_in_mode_unique_data:
        me = ob.data
        bm = bmesh.from_edit_mesh(me)
        uv = bm.loops.layers.uv.verify()
        bm.edges.ensure_lookup_table()
        for edge_idx in store_initial_seams[ob]:
            bm.edges[edge_idx].seam = True

        for f in bm.faces:
            for l in f.loops:
                if l.index in store_initial_selection[ob]:
                    continue
                l[uv].select = False

        for f in bm.faces:
            if f.index in store_face_selection[ob]:
                continue
            f.select = False
        for v in bm.verts:
            if v.index in store_verts_selection[ob]:
                v.select = True
        for e in bm.edges:
            if e.index in store_edges_selection[ob]:
                e.select = True

    scene.tool_settings.uv_select_mode = current_uv_select_mode

    return objects_seams


def get_islands(uv, bm, seams, has_selected_faces=False, islands_with_hidden_faces=True):
    if has_selected_faces:
        faces = {f for f in bm.faces for l in f.loops if l[uv].select}
    else:
        faces = set(bm.faces)
    while len(faces) != 0:
        init_face = faces.pop()
        island = {init_face}
        stack = [init_face]
        while len(stack) != 0:
            face = stack.pop()
            for e in face.edges:
                if e.index not in seams:
                    for f in e.link_faces:
                        if f != face and f not in island:
                            stack.append(f)
                            island.add(f)
        for f in island:
            faces.discard(f)

        if islands_with_hidden_faces is False:
            island_has_a_hidden_faces = False
            for face in island:
                if face.select is False:
                    island_has_a_hidden_faces = True
                    # print(">>>>>")
                    # print("has_a_hidden_faces")
                    break
            if island_has_a_hidden_faces:
                continue
        yield island
