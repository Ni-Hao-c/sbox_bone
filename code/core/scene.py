"""Scene, collection, armature, and mesh helpers."""

import bpy

from .bones import CORE_TARGET_BONES


INPUT_COLLECTION = "Input"
OUTPUT_COLLECTION = "Output"
FIRST_PERSON_COLLECTION = "First Person Arms"


def find_armature(context):
    settings = context.scene.sbox_pm_wizard
    if settings.armature:
        return settings.armature
    selected = [obj for obj in context.selected_objects if obj.type == "ARMATURE"]
    if selected:
        settings.armature = selected[0]
        return selected[0]
    armatures = [obj for obj in context.scene.objects if obj.type == "ARMATURE"]
    if len(armatures) == 1:
        settings.armature = armatures[0]
        return armatures[0]
    return None


def find_armature_with_bone(context, bone_name, exclude=None):
    if not bone_name:
        return None
    for obj in context.scene.objects:
        if obj.type != "ARMATURE" or obj == exclude:
            continue
        if obj.data.bones.get(bone_name):
            return obj
    return None


def primary_template_armature(context):
    candidates = template_armatures(context)
    if not candidates:
        return None
    exact = next((obj for obj in candidates if obj.name == "Human Citizen Armature"), None)
    return exact or candidates[0]


def is_template_armature(armature, source_armature=None):
    if not armature or armature.type != "ARMATURE" or armature == source_armature:
        return False
    name = armature.name.lower()
    if "citizen" in name or "human" in name:
        return True
    core_hits = sum(1 for bone in CORE_TARGET_BONES if armature.data.bones.get(bone))
    return core_hits >= 10


def template_armatures(context):
    settings = context.scene.sbox_pm_wizard
    source_armature = settings.armature
    return [
        obj
        for obj in context.scene.objects
        if is_template_armature(obj, source_armature=source_armature)
    ]


def ensure_input_collection(scene):
    collection = bpy.data.collections.get(INPUT_COLLECTION)
    if collection is None:
        collection = bpy.data.collections.new(INPUT_COLLECTION)
        scene.collection.children.link(collection)
    return collection


def ensure_scene_collection(scene, name):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if not scene.collection.children.get(name):
        scene.collection.children.link(collection)
    return collection


def object_in_collection(obj, collection):
    return any(col == collection for col in obj.users_collection)


def move_to_input(objects, scene):
    collection = ensure_input_collection(scene)
    for obj in objects:
        if not object_in_collection(obj, collection):
            collection.objects.link(obj)
        for old_collection in list(obj.users_collection):
            if old_collection != collection:
                old_collection.objects.unlink(obj)
    return collection


def mesh_objects(scene):
    return [obj for obj in scene.objects if obj.type == "MESH"]


def mesh_uses_armature(mesh, armature):
    if mesh.parent == armature:
        return True
    for modifier in mesh.modifiers:
        if modifier.type == "ARMATURE" and modifier.object == armature:
            return True
    return False


def model_mesh_objects(scene, armature):
    if not armature:
        return []
    return [obj for obj in mesh_objects(scene) if mesh_uses_armature(obj, armature)]


def model_export_objects(scene, armature):
    meshes = model_mesh_objects(scene, armature)
    return ([armature] + meshes) if armature else meshes


def weighted_bone_names(scene, armature):
    weighted = set()
    for mesh in model_mesh_objects(scene, armature):
        index_to_name = {group.index: group.name for group in mesh.vertex_groups}
        for vertex in mesh.data.vertices:
            for assignment in vertex.groups:
                if assignment.weight <= 0.0:
                    continue
                name = index_to_name.get(assignment.group)
                if name:
                    weighted.add(name)
    return weighted
