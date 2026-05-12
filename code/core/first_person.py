"""First-person arms workflow helpers."""

import os

import bpy
from mathutils import Matrix, Vector

from .meshes import remove_mesh_shapekeys
from .scene import (
    FIRST_PERSON_COLLECTION,
    ensure_scene_collection,
    model_mesh_objects,
    object_in_collection,
)


def first_person_arm_weight_bone(name):
    lowered = name.lower()
    if "hair" in lowered or "head" in lowered or "skull" in lowered or "face" in lowered:
        return False
    if "clavicle" in lowered or "shoulder" in lowered:
        return False
    return (
        name.startswith("arm_upper_")
        or name.startswith("arm_lower_")
        or name.startswith("hand_")
        or name.startswith("finger_")
        or "arm_upper" in lowered
        or "arm_lower" in lowered
        or "hand" in lowered
        or "finger" in lowered
        or "wrist" in lowered
        or "elbow" in lowered
        or "twist" in lowered
        or "手" in name
        or "腕" in name
        or "指" in name
        or "肘" in name
        or "手首" in name
        or "ひじ" in name
    )


def first_person_template_bone(name):
    return (
        name in {
            "root",
            "camera",
            "weapon_root",
            "weapon_root_children",
            "clavicle_L",
            "clavicle_R",
            "hand_R_to_L_ikrule",
            "hand_L_to_R_ikrule",
            "hand_R_to_weapon_ikrule",
            "hand_L_to_weapon_ikrule",
            "weapon_IK_hand_L",
            "weapon_IK_hand_R",
        }
        or first_person_arm_weight_bone(name)
    )


def import_first_person_template_armature(context, filepath):
    filepath = bpy.path.abspath(filepath)
    if not filepath or not os.path.exists(filepath):
        raise FileNotFoundError("First person arms template FBX was not found.")

    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=filepath)
    imported = [obj for obj in bpy.data.objects if obj not in before]
    armatures = [obj for obj in imported if obj.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError("Template FBX did not import an armature.")

    def score(armature):
        names = {bone.name for bone in armature.data.bones}
        return sum(1 for name in ("root", "camera", "weapon_root", "hand_R", "hand_L") if name in names)

    armature = max(armatures, key=score)
    armature.name = "First Person Arms Working"
    armature.data.name = "First Person Arms Working Skeleton"

    collection = ensure_scene_collection(context.scene, FIRST_PERSON_COLLECTION)
    if not object_in_collection(armature, collection):
        collection.objects.link(armature)
    for old_collection in list(armature.users_collection):
        if old_collection != collection:
            old_collection.objects.unlink(armature)

    for obj in imported:
        if obj != armature and obj.type == "MESH":
            bpy.data.objects.remove(obj, do_unlink=True)

    return armature


def matching_first_person_bone_count(source_armature, target_armature):
    source_names = {bone.name for bone in source_armature.data.bones}
    return sum(
        1
        for bone in target_armature.data.bones
        if bone.name in source_names and first_person_arm_weight_bone(bone.name)
    )


def side_from_bone_name(name):
    lowered = name.lower()
    if lowered.endswith("_l") or "_l_" in lowered or "left" in lowered or "左" in name:
        return "L"
    if lowered.endswith("_r") or "_r_" in lowered or "right" in lowered or "右" in name:
        return "R"
    return ""


def dominant_arm_side(vertex, index_to_name):
    weights = {"L": 0.0, "R": 0.0}
    for assignment in vertex.groups:
        group_name = index_to_name.get(assignment.group)
        if not group_name or not first_person_arm_weight_bone(group_name):
            continue
        side = side_from_bone_name(group_name)
        if side:
            weights[side] += assignment.weight
    if weights["L"] <= 0.0 and weights["R"] <= 0.0:
        return ""
    return "L" if weights["L"] >= weights["R"] else "R"


def create_first_person_reference_armature(context, target_armature):
    reference = target_armature.copy()
    reference.data = target_armature.data.copy()
    reference.name = "First Person Arms Reference"
    reference.data.name = "First Person Arms Reference Skeleton"

    collection = ensure_scene_collection(context.scene, FIRST_PERSON_COLLECTION)
    collection.objects.link(reference)
    for old_collection in list(reference.users_collection):
        if old_collection != collection:
            old_collection.objects.unlink(reference)

    reference.hide_viewport = False
    reference.hide_render = True
    return reference


def move_first_person_armature_to_source(source_armature, target_armature):
    if bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    target_armature.select_set(True)
    bpy.context.view_layer.objects.active = target_armature
    bpy.ops.object.mode_set(mode="EDIT")
    target_bones = target_armature.data.edit_bones
    moved = 0
    for target_bone in target_bones:
        source_bone = source_armature.data.bones.get(target_bone.name)
        if not source_bone or not first_person_arm_weight_bone(target_bone.name):
            continue
        
        # 保持目标骨骼的原始方向（保证T-Pose正确），只移动头尾位置
        old_dir = target_bone.tail - target_bone.head
        old_length = old_dir.length
        if old_length < 0.001:
            old_dir = source_bone.tail_local - source_bone.head_local
            old_length = old_dir.length
            if old_length < 0.001:
                continue
                
        source_head_world = source_armature.matrix_world @ source_bone.head_local
        target_bone.head = target_armature.matrix_world.inverted() @ source_head_world
        target_bone.tail = target_bone.head + old_dir.normalized() * old_length
        moved += 1
        
    point_table = {
        "arm_upper_R": "arm_lower_R",
        "arm_lower_R": "hand_R",
        "arm_lower_R_twist0": "hand_R",
        "arm_lower_R_twist1": "hand_R",
        "arm_lower_R_twist2": "hand_R",
        "hand_R": "",
        "arm_upper_L": "arm_lower_L",
        "arm_lower_L": "hand_L",
        "arm_lower_L_twist0": "hand_L",
        "arm_lower_L_twist1": "hand_L",
        "arm_lower_L_twist2": "hand_L",
        "hand_L": "",
    }
    last_direction = None
    for bone_name, child_name in point_table.items():
        bone = target_bones.get(bone_name)
        if not bone:
            continue
        length = bone.length
        if child_name:
            child = target_bones.get(child_name)
            if not child:
                continue
            direction = child.head - bone.head
            if direction.length < 0.001:
                continue
            direction.normalize()
            bone.tail = bone.head + direction * length
            last_direction = direction
        elif last_direction:
            bone.tail = bone.head + last_direction * length
            
    bpy.ops.object.mode_set(mode="OBJECT")
    return moved


def make_arm_basis(armature, side):
    upper = armature.data.bones.get(f"arm_upper_{side}")
    lower = armature.data.bones.get(f"arm_lower_{side}")
    hand = armature.data.bones.get(f"hand_{side}")
    if not upper or not lower or not hand:
        return None, 1.0

    origin = armature.matrix_world @ upper.head_local
    elbow = armature.matrix_world @ lower.head_local
    wrist = armature.matrix_world @ hand.head_local
    x_axis = wrist - origin
    if x_axis.length < 0.0001:
        return None, 1.0
    length = x_axis.length
    x_axis.normalize()

    elbow_offset = elbow - origin
    y_axis = elbow_offset - x_axis * elbow_offset.dot(x_axis)
    if y_axis.length < 0.0001:
        y_axis = Vector((0.0, 0.0, 1.0))
        if abs(x_axis.dot(y_axis)) > 0.95:
            y_axis = Vector((0.0, 1.0, 0.0))
        y_axis = y_axis - x_axis * y_axis.dot(x_axis)
    y_axis.normalize()
    z_axis = x_axis.cross(y_axis)
    if z_axis.length < 0.0001:
        return None, 1.0
    z_axis.normalize()
    y_axis = z_axis.cross(x_axis)
    y_axis.normalize()

    basis = Matrix(
        (
            (x_axis.x, y_axis.x, z_axis.x, origin.x),
            (x_axis.y, y_axis.y, z_axis.y, origin.y),
            (x_axis.z, y_axis.z, z_axis.z, origin.z),
            (0.0, 0.0, 0.0, 1.0),
        )
    )
    return basis, length


def retarget_mesh_to_first_person_template(obj, source_armature, target_armature, side):
    source_basis, source_length = make_arm_basis(source_armature, side)
    target_basis, target_length = make_arm_basis(target_armature, side)
    if source_basis is None or target_basis is None or source_length < 0.0001:
        return 0

    scale = target_length / source_length
    source_inverse = source_basis.inverted_safe()
    new_world_coords = []
    for vertex in obj.data.vertices:
        local = source_inverse @ (obj.matrix_world @ vertex.co)
        local.x *= scale
        local.y *= scale
        local.z *= scale
        new_world_coords.append(target_basis @ local)

    obj.parent = None
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_world = Matrix.Identity(4)
    for vertex, world_coord in zip(obj.data.vertices, new_world_coords):
        vertex.co = world_coord
    obj.data.update()
    return len(new_world_coords)


def bake_first_person_meshes_to_reference(context, working_armature, reference_armature, meshes):
    if bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")

    for pbone in working_armature.pose.bones:
        if not reference_armature.pose.bones.get(pbone.name):
            continue
        constraint = pbone.constraints.new("COPY_ROTATION")
        constraint.name = "sbox_first_person_reference_rotation"
        constraint.target = reference_armature
        constraint.subtarget = pbone.name

    context.view_layer.update()

    for mesh in meshes:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        context.view_layer.objects.active = mesh
        mesh.select_set(True)
        remove_mesh_shapekeys(mesh)
        for modifier in mesh.modifiers:
            if modifier.type == "ARMATURE":
                modifier.object = working_armature
                break
        else:
            modifier = mesh.modifiers.new(name="Armature", type="ARMATURE")
            modifier.object = working_armature
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        modifier = mesh.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = reference_armature
        matrix_world = mesh.matrix_world.copy()
        mesh.parent = reference_armature
        mesh.matrix_parent_inverse = reference_armature.matrix_world.inverted()
        mesh.matrix_world = matrix_world

    for pbone in working_armature.pose.bones:
        for constraint in list(pbone.constraints):
            if constraint.name == "sbox_first_person_reference_rotation":
                pbone.constraints.remove(constraint)


def finalize_first_person_reference_armature(working_armature, reference_armature):
    bpy.data.objects.remove(working_armature, do_unlink=True)
    reference_armature.name = "First Person Arms Armature"
    reference_armature.data.name = "First Person Arms Skeleton"
    reference_armature.hide_set(False)
    reference_armature.hide_viewport = False
    reference_armature.hide_render = False
    return reference_armature


def duplicate_first_person_arm_meshes(context, source_armature, target_armature, threshold):
    import bmesh
    source_meshes = model_mesh_objects(context.scene, source_armature)
    if not source_meshes:
        raise RuntimeError("No meshes are bound to the assigned source armature.")
    collection = ensure_scene_collection(context.scene, FIRST_PERSON_COLLECTION)
    target_bone_names = {bone.name for bone in target_armature.data.bones}
    created = []
    removed_vertices = 0
    scanned_vertices = 0
    kept_vertices = 0
    moved_meshes = 0
    removed_shapekeys = 0
    retargeted_vertices = 0
    
    for mesh in source_meshes:
        index_to_name = {group.index: group.name for group in mesh.vertex_groups}
        side_keep = {"L": [], "R": []}
        
        for vertex in mesh.data.vertices:
            scanned_vertices += 1
            side = dominant_arm_side(vertex, index_to_name)
            keep = False
            if side:
                max_weight = 0.0
                for assignment in vertex.groups:
                    group_name = index_to_name.get(assignment.group)
                    if group_name and first_person_arm_weight_bone(group_name):
                        max_weight = max(max_weight, assignment.weight)
                
                # 使用最大权重而不是单个权重
                if max_weight >= threshold:
                    keep = True
            
            if keep:
                kept_vertices += 1
            side_keep["L"].append(keep and side == "L")
            side_keep["R"].append(keep and side == "R")
                
        for side, keep_vertices in side_keep.items():
            if not any(keep_vertices):
                continue
            copy_obj = mesh.copy()
            copy_obj.data = mesh.data.copy()
            copy_obj.animation_data_clear()
            copy_obj.name = f"{mesh.name}_first_person_arms_{side}"
            collection.objects.link(copy_obj)
            removed_shapekeys += remove_mesh_shapekeys(copy_obj)
            for old_collection in list(copy_obj.users_collection):
                if old_collection != collection:
                    old_collection.objects.unlink(copy_obj)
            bm = bmesh.new()
            bm.from_mesh(copy_obj.data)
            bm.verts.ensure_lookup_table()
            bm.verts.index_update()
            delete_verts = [vert for vert in bm.verts if vert.index >= len(keep_vertices) or not keep_vertices[vert.index]]
            removed_vertices += len(delete_verts)
            if delete_verts:
                bmesh.ops.delete(bm, geom=delete_verts, context="VERTS")
            remaining_vertices = len(bm.verts)
            bm.to_mesh(copy_obj.data)
            bm.free()
            copy_obj.data.update()
            if remaining_vertices == 0:
                bpy.data.objects.remove(copy_obj, do_unlink=True)
                continue
            moved_meshes += 1
            for group in list(copy_obj.vertex_groups):
                if group.name not in target_bone_names:
                    copy_obj.vertex_groups.remove(group)
            retargeted_vertices += retarget_mesh_to_first_person_template(copy_obj, source_armature, target_armature, side)
            for modifier in list(copy_obj.modifiers):
                if modifier.type == "ARMATURE":
                    modifier.object = target_armature
            if not any(modifier.type == "ARMATURE" for modifier in copy_obj.modifiers):
                modifier = copy_obj.modifiers.new(name="Armature", type="ARMATURE")
                modifier.object = target_armature
            matrix_world = copy_obj.matrix_world.copy()
            copy_obj.parent = target_armature
            copy_obj.matrix_parent_inverse = target_armature.matrix_world.inverted()
            copy_obj.matrix_world = matrix_world
            copy_obj.hide_set(False)
            copy_obj.hide_viewport = False
            copy_obj.hide_render = False
            created.append(copy_obj)
            
    if not created:
        raise RuntimeError(
            "No arm mesh was created. "
            f"Scanned {scanned_vertices} vertices and found {kept_vertices} arm-weighted vertices. "
            "Try lowering the weight threshold or check the source vertex group names."
        )
    if bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        target_armature.select_set(True)
        for obj in created:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = created[0]
    return created, removed_vertices, kept_vertices, moved_meshes, removed_shapekeys, retargeted_vertices


def export_first_person_arms_fbx(context, armature, meshes, filepath):
    filepath = bpy.path.abspath(filepath)
    if not filepath:
        raise RuntimeError("First person arms export path is empty.")

    output_dir = os.path.dirname(filepath)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    for mesh in meshes:
        mesh.select_set(True)
    context.view_layer.objects.active = armature

    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        path_mode="COPY",
        bake_anim=False,
    )
    return filepath


def delete_source_full_body_model(scene, armature):
    meshes = model_mesh_objects(scene, armature)
    removed = len(meshes)
    for mesh in meshes:
        bpy.data.objects.remove(mesh, do_unlink=True)
    if armature and armature.name in bpy.data.objects:
        bpy.data.objects.remove(armature, do_unlink=True)
        removed += 1
    return removed
