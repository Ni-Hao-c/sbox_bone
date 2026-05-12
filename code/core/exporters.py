"""FBX export and conversion helpers."""

import os

import bpy

from .bones import (
    CORE_TARGET_BONES,
    FINGER_TARGET_BONES,
    JOINT_HELPER_BONES,
    OPTIONAL_EYE_TARGET_BONES,
    OPTIONAL_META_TARGET_BONES,
    REQUIRED_VMDL_BONES,
    TWIST_TARGET_BONES,
)
from .paths import manual_converter_script_path
from .scene import (
    OUTPUT_COLLECTION,
    ensure_input_collection,
    ensure_scene_collection,
    model_mesh_objects,
    move_to_input,
    object_in_collection,
)


def prepare_manual_converter_input(scene, armature):
    meshes = model_mesh_objects(scene, armature)
    if not armature or not meshes:
        return []

    source_objects = set([armature] + meshes)
    input_collection = ensure_input_collection(scene)
    ensure_scene_collection(scene, OUTPUT_COLLECTION)

    for obj in list(input_collection.objects):
        if obj in source_objects:
            continue
        if len(obj.users_collection) <= 1 and not object_in_collection(obj, scene.collection):
            scene.collection.objects.link(obj)
        input_collection.objects.unlink(obj)

    move_to_input(list(source_objects), scene)
    return [armature] + meshes


def run_manual_converter_script(export_path):
    script_path = manual_converter_script_path()
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Manual converter script not found: {script_path}")

    with open(script_path, "r", encoding="utf-8") as handle:
        script = handle.read()

    export_path = bpy.path.abspath(export_path)
    script = script.replace(
        'export_path = os.path.join(bpy.path.abspath("//"),  os.path.splitext(os.path.basename(bpy.data.filepath))[0] + ".fbx")',
        f'export_path = r"{export_path}"',
    )
    script = script.replace(
        'secondary_bone_axis="Z"\n)',
        'secondary_bone_axis="Z",\n\tpath_mode="COPY"\n)',
    )

    exec_globals = {
        "__name__": "__main__",
        "__file__": script_path,
    }
    exec(compile(script, script_path, "exec"), exec_globals)
    return export_path


def supported_export_bone_names(settings):
    names = set(CORE_TARGET_BONES)
    names.update(FINGER_TARGET_BONES)
    names.update(REQUIRED_VMDL_BONES)
    names.update(TWIST_TARGET_BONES)
    names.update(JOINT_HELPER_BONES)
    if settings.include_eye_bones:
        names.update(OPTIONAL_EYE_TARGET_BONES)
    if settings.include_finger_meta_bones:
        names.update(OPTIONAL_META_TARGET_BONES)
    return names


def find_supported_ancestor_name(armature, bone_name, supported_names):
    bone = armature.data.bones.get(bone_name)
    while bone and bone.parent:
        bone = bone.parent
        if bone.name in supported_names:
            return bone.name
    fallback = "pelvis" if armature.data.bones.get("pelvis") else None
    return fallback


def collapse_extra_bones_to_supported(context, armature, meshes, supported_names):
    if not armature or not meshes:
        return 0, 0

    unsupported_pairs = []
    for bone in armature.data.bones:
        if bone.name in supported_names:
            continue
        if not any(mesh.vertex_groups.get(bone.name) for mesh in meshes):
            continue
        target_name = find_supported_ancestor_name(armature, bone.name, supported_names)
        if target_name:
            unsupported_pairs.append((bone.name, target_name))

    transferred = 0
    for mesh in meshes:
        for source_name, target_name in unsupported_pairs:
            source_group = mesh.vertex_groups.get(source_name)
            if not source_group:
                continue
            target_group = mesh.vertex_groups.get(target_name)
            if not target_group:
                target_group = mesh.vertex_groups.new(name=target_name)

            source_index = source_group.index
            for vertex in mesh.data.vertices:
                weight = 0.0
                for group in vertex.groups:
                    if group.group == source_index:
                        weight = group.weight
                        break
                if weight > 0.0:
                    target_group.add([vertex.index], weight, "ADD")
                    transferred += 1
            mesh.vertex_groups.remove(source_group)

    if bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = armature.data.edit_bones

    depth_cache = {}

    def bone_depth(name):
        if name in depth_cache:
            return depth_cache[name]
        bone = armature.data.bones.get(name)
        depth = 0
        while bone and bone.parent:
            depth += 1
            bone = bone.parent
        depth_cache[name] = depth
        return depth

    removable_names = [name for name in edit_bones.keys() if name not in supported_names]
    removed = 0
    for name in sorted(removable_names, key=bone_depth, reverse=True):
        bone = edit_bones.get(name)
        if not bone:
            continue
        parent = bone.parent
        for child in list(bone.children):
            child.parent = parent
        edit_bones.remove(bone)
        removed += 1

    bpy.ops.object.mode_set(mode="OBJECT")
    return transferred, removed


def export_armature_fbx(context, armature, filepath):
    meshes = model_mesh_objects(context.scene, armature)
    if not armature or not meshes:
        raise RuntimeError("Need one armature and at least one bound mesh before export.")

    if bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    for obj in meshes:
        obj.select_set(True)
    context.view_layer.objects.active = armature

    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=True,
        add_leaf_bones=False,
        primary_bone_axis="X",
        secondary_bone_axis="Z",
        path_mode="COPY",
        bake_anim=False,
        object_types={"ARMATURE", "MESH"},
    )
    return filepath
