"""Mesh, weight, and shapekey helpers."""

import re

import bpy


def remove_mesh_shapekeys(obj):
    if obj.type != "MESH" or not obj.data.shape_keys:
        return 0

    count = len(obj.data.shape_keys.key_blocks)
    if bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.shape_key_remove(all=True)
    return count


def shapekey_stats(scene):
    total = 0
    unsafe = 0
    for obj in scene.objects:
        if obj.type != "MESH":
            continue
        shape_keys = getattr(obj.data, "shape_keys", None)
        if not shape_keys:
            continue
        for key in shape_keys.key_blocks:
            if key.name == "Basis":
                continue
            total += 1
            if key.name != sanitize_shapekey_name(key.name):
                unsafe += 1
    return total, unsafe


def sanitize_shapekey_name(name):
    safe = re.sub(r"\s+", "_", name.strip())
    safe = re.sub(r"[^A-Za-z0-9_]", "_", safe)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe or "ShapeKey"


def prepare_shapekeys(scene):
    renamed = 0
    total = 0
    for obj in scene.objects:
        if obj.type != "MESH":
            continue
        shape_keys = getattr(obj.data, "shape_keys", None)
        if not shape_keys:
            continue

        used = set()
        for key in shape_keys.key_blocks:
            if key.name == "Basis":
                used.add(key.name)
                continue
            total += 1
            base = sanitize_shapekey_name(key.name)
            name = base
            index = 1
            while name in used:
                index += 1
                name = f"{base}_{index}"
            used.add(name)
            if key.name != name:
                key.name = name
                renamed += 1
    return total, renamed


def mesh_objects(scene):
    from .scene import mesh_objects as scene_mesh_objects

    return scene_mesh_objects(scene)


def mesh_uses_armature(mesh, armature):
    from .scene import mesh_uses_armature as scene_mesh_uses_armature

    return scene_mesh_uses_armature(mesh, armature)


def model_export_objects(scene, armature):
    from .scene import model_export_objects as scene_model_export_objects

    return scene_model_export_objects(scene, armature)


def model_mesh_objects(scene, armature):
    from .scene import model_mesh_objects as scene_model_mesh_objects

    return scene_model_mesh_objects(scene, armature)


def validate_mapping_weights(scene):
    from .runtime import validate_mapping_weights as runtime_validate_mapping_weights

    return runtime_validate_mapping_weights(scene)


def weighted_bone_names(scene, armature):
    from .scene import weighted_bone_names as scene_weighted_bone_names

    return scene_weighted_bone_names(scene, armature)
