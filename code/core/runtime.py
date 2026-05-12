bl_info = {
    "name": "S&box Playermodel Wizard",
    "author": "CustomModel-2-Sbox",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > S&box",
    "description": "Guided MMD/FBX/Source 1 setup for Citizen-compatible S&box playermodel FBX export.",
    "category": "Import-Export",
}

import os
import re
import json

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Operator, Panel, PropertyGroup
from bpy_extras.io_utils import ExportHelper, ImportHelper
from mathutils import Matrix, Vector


ADDON_ROOT = os.path.dirname(os.path.dirname(__file__))
REPO_ROOT = os.path.dirname(ADDON_ROOT)
DEFAULT_TEMPLATE = os.path.join(REPO_ROOT, "custommodel2s&box.blend")
MANUAL_CONVERTER_SCRIPT = "convert_playermodel (Manual).py"
INPUT_COLLECTION = "Input"
OUTPUT_COLLECTION = "Output"
FIRST_PERSON_COLLECTION = "First Person Arms"


UI_TEXT = {
    "EN": {
        "language": "Language",
        "init_scene": "1. Initialize Work Scene",
        "template": "Template",
        "ready": "Ready",
        "required": "Required",
        "import_model": "2. Import Model",
        "cats_prepare": "CATS MMD prepare",
        "done": "Done",
        "pending": "Pending",
        "scene_setup": "3. Scene Setup",
        "input_collection": "Input collection",
        "ok": "OK",
        "missing": "Missing",
        "meshes": "Meshes",
        "armature": "Armature",
        "bone_remap": "4. Bone Remap",
        "include_eye_bones": "Include Eye Bones",
        "eye_note": "Eye bones animate later, but need extra ModelDoc setup.",
        "include_finger_meta_bones": "Include Finger Meta Bones",
        "finger_meta_note": "Use only when the model really has finger meta bones.",
        "ignore_extra_bones": "Ignore twist, helper, IK, and extra bones here.",
        "load_mapping": "Load Mapping",
        "save_mapping": "Save Mapping",
        "detect_bones": "Detect Bones",
        "matched": "Matched",
        "assign_armature": "Assign an armature, then detect bones.",
        "apply_rename": "Apply Bone Names",
        "validate_weights": "Validate Weights",
        "shapekeys": "5. Shapekeys",
        "shapekey_count": "Shapekeys",
        "unsafe_names": "Unsafe names",
        "shapekey_warning": "Recommended: keep shapekeys around 200 if possible.",
        "prepare_shapekeys": "Prepare Shapekeys",
        "auto_prepare_shapekeys": "Auto Prepare Shapekeys on Export",
        "export": "6. Export",
        "preferred_export": "Preferred: convert/export the Human Citizen Armature.",
        "run_conversion": "Run Citizen Conversion",
        "vmdl_bones": "VMDL bones",
        "needs_check": "Needs check",
        "missing_bones": "Missing",
        "auto_rename": "Auto Rename Mapped Bones Before Export",
        "block_missing": "Block Export if VMDL Bones Are Missing",
        "export_path": "Export Path",
        "export_fbx": "Export S&box FBX",
        "mmd_tip": "Tip: run CATS Fix Model before remap when available.",
        "source1_tip": "Tip: ValveBiped names should map automatically.",
        "fp_arms": "7. First Person Arms",
        "fp_note": "Create arms from the converted full-body Citizen model.",
        "fp_template_fbx": "Template Arms FBX",
        "fp_template_vmdl": "Template Arms VMDL",
        "fp_export_path": "Arms FBX Path",
        "fp_vmdl_path": "Arms VMDL Path",
        "fp_weight_threshold": "Keep Weight Threshold",
        "fp_create": "Create First Person Arms",
        "fp_status": "Status",
        "fp_ready": "Ready to create from the assigned armature.",
        "fp_need_armature": "Assign the converted full-body armature first.",
        },
    "CN": {
        "language": "语言",
        "init_scene": "1. 初始化工作场景",
        "template": "模板",
        "ready": "就绪",
        "required": "需要初始化",
        "import_model": "2. 导入模型",
        "cats_prepare": "CATS MMD 预处理",
        "done": "完成",
        "pending": "待处理",
        "scene_setup": "3. 场景整理",
        "input_collection": "Input 集合",
        "ok": "正常",
        "missing": "缺失",
        "meshes": "网格",
        "armature": "骨架",
        "bone_remap": "4. 骨骼重映射",
        "include_eye_bones": "包含眼部骨骼",
        "eye_note": "眼部骨骼可后续动画，但需要在 ModelDoc 额外设置。",
        "include_finger_meta_bones": "包含手指掌骨",
        "finger_meta_note": "仅在源模型确实有手指掌骨时启用。",
        "ignore_extra_bones": "这里忽略 twist、helper、IK 和额外骨骼。",
        "load_mapping": "加载映射",
        "save_mapping": "保存映射",
        "detect_bones": "检测骨骼",
        "matched": "已匹配",
        "assign_armature": "先指定骨架，然后检测骨骼。",
        "apply_rename": "应用骨骼命名",
        "validate_weights": "检查权重",
        "shapekeys": "5. 表情键",
        "shapekey_count": "表情键",
        "unsafe_names": "不安全名称",
        "shapekey_warning": "建议尽量将表情键控制在 200 个左右。",
        "prepare_shapekeys": "整理表情键",
        "auto_prepare_shapekeys": "导出时自动整理表情键",
        "export": "6. 导出",
        "preferred_export": "推荐：转换并导出 Human Citizen Armature。",
        "run_conversion": "运行 Citizen 转换",
        "vmdl_bones": "VMDL 骨骼",
        "needs_check": "需要检查",
        "missing_bones": "缺失",
        "auto_rename": "导出前自动重命名映射骨骼",
        "block_missing": "VMDL 骨骼缺失时阻止导出",
        "export_path": "导出路径",
        "export_fbx": "导出 S&box FBX",
        "mmd_tip": "提示：可用时先运行 CATS Fix Model，再做骨骼映射。",
        "source1_tip": "提示：ValveBiped 命名通常会自动匹配。",
        "fp_arms": "7. 第一人称手臂",
        "fp_note": "从已转换的全身 Citizen 模型生成第一人称手臂。",
        "fp_template_fbx": "手臂模板 FBX",
        "fp_template_vmdl": "手臂模板 VMDL",
        "fp_export_path": "手臂 FBX 路径",
        "fp_vmdl_path": "手臂 VMDL 路径",
        "fp_weight_threshold": "保留权重阈值",
        "fp_create": "生成第一人称手臂",
        "fp_status": "状态",
        "fp_ready": "可从当前指定骨架生成。",
        "fp_need_armature": "请先指定已转换的全身骨架。",
    },
}


def ui_text(settings, key):
    language = getattr(settings, "ui_language", "EN")
    return UI_TEXT.get(language, UI_TEXT["EN"]).get(key, UI_TEXT["EN"].get(key, key))


CORE_TARGET_BONES = [
    "pelvis",
    "spine_0",
    "spine_1",
    "spine_2",
    "neck_0",
    "head",
    "clavicle_L",
    "arm_upper_L",
    "arm_lower_L",
    "hand_L",
    "clavicle_R",
    "arm_upper_R",
    "arm_lower_R",
    "hand_R",
    "leg_upper_L",
    "leg_lower_L",
    "ankle_L",
    "ball_L",
    "leg_upper_R",
    "leg_lower_R",
    "ankle_R",
    "ball_R",
]

FINGER_TARGET_BONES = [
    "finger_thumb_0_L",
    "finger_thumb_1_L",
    "finger_thumb_2_L",
    "finger_index_0_L",
    "finger_index_1_L",
    "finger_index_2_L",
    "finger_middle_0_L",
    "finger_middle_1_L",
    "finger_middle_2_L",
    "finger_ring_0_L",
    "finger_ring_1_L",
    "finger_ring_2_L",
    "finger_pinky_0_L",
    "finger_pinky_1_L",
    "finger_pinky_2_L",
    "finger_thumb_0_R",
    "finger_thumb_1_R",
    "finger_thumb_2_R",
    "finger_index_0_R",
    "finger_index_1_R",
    "finger_index_2_R",
    "finger_middle_0_R",
    "finger_middle_1_R",
    "finger_middle_2_R",
    "finger_ring_0_R",
    "finger_ring_1_R",
    "finger_ring_2_R",
    "finger_pinky_0_R",
    "finger_pinky_1_R",
    "finger_pinky_2_R",
]

OPTIONAL_EYE_TARGET_BONES = [
    "eye_L",
    "eye_R",
]

OPTIONAL_META_TARGET_BONES = [
    "finger_index_meta_L",
    "finger_middle_meta_L",
    "finger_ring_meta_L",
    "finger_pinky_meta_L",
    "finger_index_meta_R",
    "finger_middle_meta_R",
    "finger_ring_meta_R",
    "finger_pinky_meta_R",
]

REQUIRED_VMDL_BONES = CORE_TARGET_BONES + [
    "root_IK",
    "aim_matrix_01",
    "aim_matrix_02a",
    "aim_matrix_02b",
    "foot_R_IK_target",
    "foot_L_IK_target",
    "hand_R_IK_attach",
    "hand_R_IK_target",
    "hand_L_IK_attach",
    "hand_L_IK_target",
    "hold_L",
    "hold_R",
]

TWIST_TARGET_BONES = [
    "arm_upper_L_twist0",
    "arm_upper_L_twist1",
    "arm_lower_L_twist0",
    "arm_lower_L_twist1",
    "arm_upper_R_twist0",
    "arm_upper_R_twist1",
    "arm_lower_R_twist0",
    "arm_lower_R_twist1",
    "leg_upper_L_twist0",
    "leg_upper_L_twist1",
    "leg_lower_L_twist0",
    "leg_lower_L_twist1",
    "leg_upper_R_twist0",
    "leg_upper_R_twist1",
    "leg_lower_R_twist0",
    "leg_lower_R_twist1",
]

JOINT_HELPER_BONES = [
    "arm_elbow_helper_L",
    "arm_elbow_helper_R",
    "leg_knee_helper_L",
    "leg_knee_helper_R",
]


SOURCE1_MAP = {
    "pelvis": ["ValveBiped.Bip01_Pelvis"],
    "spine_0": ["ValveBiped.Bip01_Spine"],
    "spine_1": ["ValveBiped.Bip01_Spine1", "ValveBiped.Bip01_Spine2"],
    "spine_2": ["ValveBiped.Bip01_Spine4"],
    "neck_0": ["ValveBiped.Bip01_Neck1"],
    "head": ["ValveBiped.Bip01_Head1"],
    "clavicle_L": ["ValveBiped.Bip01_L_Clavicle"],
    "arm_upper_L": ["ValveBiped.Bip01_L_UpperArm"],
    "arm_lower_L": ["ValveBiped.Bip01_L_Forearm"],
    "hand_L": ["ValveBiped.Bip01_L_Hand"],
    "clavicle_R": ["ValveBiped.Bip01_R_Clavicle"],
    "arm_upper_R": ["ValveBiped.Bip01_R_UpperArm"],
    "arm_lower_R": ["ValveBiped.Bip01_R_Forearm"],
    "hand_R": ["ValveBiped.Bip01_R_Hand"],
    "leg_upper_L": ["ValveBiped.Bip01_L_Thigh"],
    "leg_lower_L": ["ValveBiped.Bip01_L_Calf"],
    "ankle_L": ["ValveBiped.Bip01_L_Foot"],
    "ball_L": ["ValveBiped.Bip01_L_Toe0"],
    "leg_upper_R": ["ValveBiped.Bip01_R_Thigh"],
    "leg_lower_R": ["ValveBiped.Bip01_R_Calf"],
    "ankle_R": ["ValveBiped.Bip01_R_Foot"],
    "ball_R": ["ValveBiped.Bip01_R_Toe0"],
    "finger_thumb_0_L": ["ValveBiped.Bip01_L_Finger0"],
    "finger_thumb_1_L": ["ValveBiped.Bip01_L_Finger01"],
    "finger_thumb_2_L": ["ValveBiped.Bip01_L_Finger02"],
    "finger_index_0_L": ["ValveBiped.Bip01_L_Finger1"],
    "finger_index_1_L": ["ValveBiped.Bip01_L_Finger11"],
    "finger_index_2_L": ["ValveBiped.Bip01_L_Finger12"],
    "finger_middle_0_L": ["ValveBiped.Bip01_L_Finger2"],
    "finger_middle_1_L": ["ValveBiped.Bip01_L_Finger21"],
    "finger_middle_2_L": ["ValveBiped.Bip01_L_Finger22"],
    "finger_ring_0_L": ["ValveBiped.Bip01_L_Finger3"],
    "finger_ring_1_L": ["ValveBiped.Bip01_L_Finger31"],
    "finger_ring_2_L": ["ValveBiped.Bip01_L_Finger32"],
    "finger_pinky_0_L": ["ValveBiped.Bip01_L_Finger4"],
    "finger_pinky_1_L": ["ValveBiped.Bip01_L_Finger41"],
    "finger_pinky_2_L": ["ValveBiped.Bip01_L_Finger42"],
    "finger_thumb_0_R": ["ValveBiped.Bip01_R_Finger0"],
    "finger_thumb_1_R": ["ValveBiped.Bip01_R_Finger01"],
    "finger_thumb_2_R": ["ValveBiped.Bip01_R_Finger02"],
    "finger_index_0_R": ["ValveBiped.Bip01_R_Finger1"],
    "finger_index_1_R": ["ValveBiped.Bip01_R_Finger11"],
    "finger_index_2_R": ["ValveBiped.Bip01_R_Finger12"],
    "finger_middle_0_R": ["ValveBiped.Bip01_R_Finger2"],
    "finger_middle_1_R": ["ValveBiped.Bip01_R_Finger21"],
    "finger_middle_2_R": ["ValveBiped.Bip01_R_Finger22"],
    "finger_ring_0_R": ["ValveBiped.Bip01_R_Finger3"],
    "finger_ring_1_R": ["ValveBiped.Bip01_R_Finger31"],
    "finger_ring_2_R": ["ValveBiped.Bip01_R_Finger32"],
    "finger_pinky_0_R": ["ValveBiped.Bip01_R_Finger4"],
    "finger_pinky_1_R": ["ValveBiped.Bip01_R_Finger41"],
    "finger_pinky_2_R": ["ValveBiped.Bip01_R_Finger42"],
    "eye_L": ["ValveBiped.Bip01_L_Eye", "Eye_L"],
    "eye_R": ["ValveBiped.Bip01_R_Eye", "Eye_R"],
}


FBX_MAP = {
    "pelvis": ["Hips", "hips", "Pelvis", "pelvis"],
    "spine_0": ["Spine", "spine", "Spine1"],
    "spine_1": ["Spine1", "spine_01", "Chest"],
    "spine_2": ["Spine2", "UpperChest", "Chest"],
    "neck_0": ["Neck", "neck"],
    "head": ["Head", "head"],
    "clavicle_L": ["LeftShoulder", "Left Clavicle", "Shoulder_L"],
    "arm_upper_L": ["LeftArm", "Left UpperArm", "UpperArm_L"],
    "arm_lower_L": ["LeftForeArm", "Left LowerArm", "LowerArm_L"],
    "hand_L": ["LeftHand", "Hand_L"],
    "clavicle_R": ["RightShoulder", "Right Clavicle", "Shoulder_R"],
    "arm_upper_R": ["RightArm", "Right UpperArm", "UpperArm_R"],
    "arm_lower_R": ["RightForeArm", "Right LowerArm", "LowerArm_R"],
    "hand_R": ["RightHand", "Hand_R"],
    "leg_upper_L": ["LeftUpLeg", "Left UpperLeg", "Thigh_L"],
    "leg_lower_L": ["LeftLeg", "Left LowerLeg", "Calf_L"],
    "ankle_L": ["LeftFoot", "Foot_L"],
    "ball_L": ["LeftToeBase", "Toe_L"],
    "leg_upper_R": ["RightUpLeg", "Right UpperLeg", "Thigh_R"],
    "leg_lower_R": ["RightLeg", "Right LowerLeg", "Calf_R"],
    "ankle_R": ["RightFoot", "Foot_R"],
    "ball_R": ["RightToeBase", "Toe_R"],
    "eye_L": ["LeftEye", "Eye_L", "eye_L", "Left Eye"],
    "eye_R": ["RightEye", "Eye_R", "eye_R", "Right Eye"],
}


MMD_MAP = {
    "pelvis": ["下半身", "センター", "Hips"],
    "spine_0": ["上半身", "Spine"],
    "spine_1": ["上半身2", "UpperBody2", "Chest"],
    "neck_0": ["首", "Neck"],
    "head": ["頭", "Head"],
    "arm_upper_L": ["左腕", "LeftArm"],
    "arm_lower_L": ["左ひじ", "LeftForeArm"],
    "hand_L": ["左手首", "LeftHand"],
    "arm_upper_R": ["右腕", "RightArm"],
    "arm_lower_R": ["右ひじ", "RightForeArm"],
    "hand_R": ["右手首", "RightHand"],
    "leg_upper_L": ["左足", "LeftUpLeg"],
    "leg_lower_L": ["左ひざ", "LeftLeg"],
    "ankle_L": ["左足首", "LeftFoot"],
    "leg_upper_R": ["右足", "RightUpLeg"],
    "leg_lower_R": ["右ひざ", "RightLeg"],
    "ankle_R": ["右足首", "RightFoot"],
    "eye_L": ["左目", "左目先", "LeftEye", "Eye_L"],
    "eye_R": ["右目", "右目先", "RightEye", "Eye_R"],
}


def add_finger_candidates(mapping, prefix_left, prefix_right):
    fingers = {
        "thumb": ("Thumb", "Finger0"),
        "index": ("Index", "Finger1"),
        "middle": ("Middle", "Finger2"),
        "ring": ("Ring", "Finger3"),
        "pinky": ("Pinky", "Finger4"),
    }
    sides = {"L": prefix_left, "R": prefix_right}
    for side, prefix in sides.items():
        for target_finger, names in fingers.items():
            for segment in range(3):
                target = f"finger_{target_finger}_{segment}_{side}"
                mapping.setdefault(target, [])
                for name in names:
                    mapping[target].extend(
                        [
                            f"{prefix}{name}{segment + 1}",
                            f"{prefix}{name}{segment}",
                            f"{prefix}Hand{name}{segment + 1}",
                            f"{name}_{segment}_{side}",
                            f"{target_finger}_{segment}_{side}",
                        ]
                    )


add_finger_candidates(FBX_MAP, "Left", "Right")
add_finger_candidates(MMD_MAP, "左", "右")

FBX_MAP.update(
    {
        "finger_index_meta_L": ["LeftHandIndex_Meta", "Index_Meta_L", "finger_index_meta_L"],
        "finger_middle_meta_L": ["LeftHandMiddle_Meta", "Middle_Meta_L", "finger_middle_meta_L"],
        "finger_ring_meta_L": ["LeftHandRing_Meta", "Ring_Meta_L", "finger_ring_meta_L"],
        "finger_pinky_meta_L": ["LeftHandPinky_Meta", "Pinky_Meta_L", "finger_pinky_meta_L"],
        "finger_index_meta_R": ["RightHandIndex_Meta", "Index_Meta_R", "finger_index_meta_R"],
        "finger_middle_meta_R": ["RightHandMiddle_Meta", "Middle_Meta_R", "finger_middle_meta_R"],
        "finger_ring_meta_R": ["RightHandRing_Meta", "Ring_Meta_R", "finger_ring_meta_R"],
        "finger_pinky_meta_R": ["RightHandPinky_Meta", "Pinky_Meta_R", "finger_pinky_meta_R"],
    }
)


def mode_map(mode):
    if mode == "SOURCE1":
        return SOURCE1_MAP
    if mode == "MMD":
        merged = dict(FBX_MAP)
        merged.update(MMD_MAP)
        return merged
    return FBX_MAP


def get_target_bones(settings):
    targets = CORE_TARGET_BONES + FINGER_TARGET_BONES
    if settings.include_eye_bones:
        targets += OPTIONAL_EYE_TARGET_BONES
    if settings.include_finger_meta_bones:
        targets += OPTIONAL_META_TARGET_BONES
    return targets


def get_settings(scene):
    return scene.sbox_pm_wizard


def find_armature(context):
    settings = get_settings(context.scene)
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
    settings = get_settings(context.scene)
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


def descendant_has_weight(armature, bone_name, weighted_names):
    bone = armature.data.bones.get(bone_name) if armature else None
    if not bone:
        return False

    stack = list(bone.children)
    seen = set()
    while stack:
        child = stack.pop()
        if child.name in seen:
            continue
        seen.add(child.name)
        if child.name in weighted_names:
            return True
        stack.extend(child.children)
    return False


def validate_mapping_weights(scene):
    settings = get_settings(scene)
    armature = settings.armature
    for item in settings.bone_map:
        item.weight_checked = False
        item.direct_weight = False
        item.descendant_weight = False

    if not armature or armature.type != "ARMATURE":
        settings.deform_check_ok = False
        settings.deform_check_summary = "No armature assigned."
        return []

    weighted_names = weighted_bone_names(scene, armature)
    issues = []
    checked = 0
    direct_hits = 0

    for item in settings.bone_map:
        if not item.source:
            continue
        checked += 1
        item.weight_checked = True
        item.direct_weight = item.source in weighted_names
        item.descendant_weight = descendant_has_weight(armature, item.source, weighted_names)
        if item.direct_weight:
            direct_hits += 1
        else:
            relation = "weighted child" if item.descendant_weight else "no weights"
            issues.append(f"{item.target} <- {item.source} ({relation})")

    settings.deform_check_ok = checked > 0 and not issues
    if not checked:
        settings.deform_check_summary = "No mapped source bones to validate."
    elif not issues:
        settings.deform_check_summary = f"All {checked} mapped bones directly deform the mesh."
    else:
        settings.deform_check_summary = (
            f"{len(issues)} mapped bones have no direct weights. "
            f"Direct deform bones: {direct_hits}/{checked}."
        )
    return issues


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


def missing_vmdl_bones(armature):
    if not armature or armature.type != "ARMATURE":
        return list(REQUIRED_VMDL_BONES)
    return [bone for bone in REQUIRED_VMDL_BONES if not armature.data.bones.get(bone)]


def duplicate_mapped_sources(settings):
    seen = {}
    duplicates = []
    for item in settings.bone_map:
        if not item.source:
            continue
        if item.source in seen:
            duplicates.append(item.source)
        else:
            seen[item.source] = item.target
    return sorted(set(duplicates))


def apply_mapped_bone_names(armature, settings):
    renamed = 0
    missing_sources = []
    blocked = []
    if not armature or armature.type != "ARMATURE":
        return renamed, missing_sources, blocked

    for item in settings.bone_map:
        if not item.source or item.source == item.target:
            continue
        source_bone = armature.data.bones.get(item.source)
        target_bone = armature.data.bones.get(item.target)
        if not source_bone:
            missing_sources.append(item.source)
            continue
        if target_bone:
            blocked.append(item.target)
            continue
        source_bone.name = item.target
        renamed += 1

    return renamed, sorted(set(missing_sources)), sorted(set(blocked))


def manual_converter_script_path():
    candidates = [
        os.path.join(ADDON_ROOT, MANUAL_CONVERTER_SCRIPT),
        os.path.join(REPO_ROOT, "Scripts", MANUAL_CONVERTER_SCRIPT),
    ]
    for path in candidates:
        path = bpy.path.abspath(path)
        if os.path.exists(path):
            return path
    return bpy.path.abspath(candidates[0])


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


def source2_asset_path(filepath):
    normalized = bpy.path.abspath(filepath).replace("\\", "/")
    marker = "/Assets/"
    if marker in normalized:
        return normalized.split(marker, 1)[1]
    return os.path.basename(normalized)


def write_first_person_arms_vmdl(template_path, output_path, fbx_path):
    template_path = bpy.path.abspath(template_path)
    output_path = bpy.path.abspath(output_path)
    if not template_path:
        return None
    if not os.path.exists(template_path):
        raise FileNotFoundError("First person arms template VMDL was not found.")

    with open(template_path, "r", encoding="utf-8") as handle:
        text = handle.read()

    asset_path = source2_asset_path(fbx_path)
    text, count = re.subn(
        r'filename = "[^"]+\.fbx"',
        f'filename = "{asset_path}"',
        text,
        count=1,
    )
    if count != 1:
        raise RuntimeError("Could not replace the RenderMeshFile filename in the template VMDL.")
    text = re.sub(
        r'anim_graph_name = "[^"]*"',
        'anim_graph_name = "models/first_person/first_person_arms_base.vanmgrph"',
        text,
        count=1,
    )

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return output_path


def delete_source_full_body_model(scene, armature):
    meshes = model_mesh_objects(scene, armature)
    removed = len(meshes)
    for mesh in meshes:
        bpy.data.objects.remove(mesh, do_unlink=True)
    if armature and armature.name in bpy.data.objects:
        bpy.data.objects.remove(armature, do_unlink=True)
        removed += 1
    return removed


def edit_bone_midpoint(edit_bone):
    return (edit_bone.head + edit_bone.tail) * 0.5


def ensure_edit_bone(armature, name, parent_name=None, head=None, tail=None):
    bone = armature.data.edit_bones.get(name)
    if bone:
        return bone, False

    parent = armature.data.edit_bones.get(parent_name) if parent_name else None
    if head is None:
        head = parent.tail.copy() if parent else (0.0, 0.0, 0.0)
    if tail is None:
        tail = head.copy()
        tail.z += 2.0
    if (tail - head).length < 0.001:
        tail = head.copy()
        tail.z += 2.0

    bone = armature.data.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    if parent:
        bone.parent = parent
    return bone, True


def create_helper_bones(armature):
    if not armature or armature.type != "ARMATURE":
        return 0

    if bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")

    created = 0
    eb = armature.data.edit_bones

    pelvis = eb.get("pelvis")
    spine_1 = eb.get("spine_1")
    head_bone = eb.get("head")
    if not eb.get("spine_2") and spine_1 and head_bone:
        head = spine_1.tail.copy()
        tail = edit_bone_midpoint(head_bone)
        _, did_create = ensure_edit_bone(armature, "spine_2", "spine_1", head=head, tail=tail)
        created += int(did_create)

    root_head = pelvis.head.copy() if pelvis else (0.0, 0.0, 0.0)
    root_tail = root_head.copy()
    root_tail.z += 6.0
    _, did_create = ensure_edit_bone(armature, "root_IK", None, root_head, root_tail)
    created += int(did_create)

    aim_parent = "head" if eb.get("head") else "spine_2"
    aim_source = eb.get(aim_parent)
    if aim_source:
        aim_head = aim_source.head.copy()
        aim_tail = aim_source.tail.copy()
        for name in ("aim_matrix_01", "aim_matrix_02a", "aim_matrix_02b"):
            _, did_create = ensure_edit_bone(armature, name, aim_parent, aim_head, aim_tail)
            created += int(did_create)

    limb_helpers = [
        ("hand_L_IK_attach", "hand_L", "hand_L"),
        ("hand_R_IK_attach", "hand_R", "hand_R"),
        ("hand_L_IK_target", "root_IK", "hand_L"),
        ("hand_R_IK_target", "root_IK", "hand_R"),
        ("foot_L_IK_target", "root_IK", "ankle_L"),
        ("foot_R_IK_target", "root_IK", "ankle_R"),
        ("hold_L", "hand_L", "hand_L"),
        ("hold_R", "hand_R", "hand_R"),
    ]
    for name, parent_name, source_name in limb_helpers:
        source = eb.get(source_name)
        if not source:
            continue
        head = source.head.copy()
        tail = source.tail.copy()
        _, did_create = ensure_edit_bone(armature, name, parent_name, head, tail)
        created += int(did_create)

    twist_specs = [
        ("arm_upper_L", "arm_upper_L_twist0", "arm_upper_L_twist1"),
        ("arm_lower_L", "arm_lower_L_twist0", "arm_lower_L_twist1"),
        ("arm_upper_R", "arm_upper_R_twist0", "arm_upper_R_twist1"),
        ("arm_lower_R", "arm_lower_R_twist0", "arm_lower_R_twist1"),
        ("leg_upper_L", "leg_upper_L_twist0", "leg_upper_L_twist1"),
        ("leg_lower_L", "leg_lower_L_twist0", "leg_lower_L_twist1"),
        ("leg_upper_R", "leg_upper_R_twist0", "leg_upper_R_twist1"),
        ("leg_lower_R", "leg_lower_R_twist0", "leg_lower_R_twist1"),
    ]
    for parent_name, first_name, second_name in twist_specs:
        parent = eb.get(parent_name)
        if not parent:
            continue
        first_head = parent.head.lerp(parent.tail, 0.33)
        first_tail = first_head.copy()
        first_tail.z += 1.0
        second_head = parent.head.lerp(parent.tail, 0.66)
        second_tail = second_head.copy()
        second_tail.z += 1.0
        _, did_create = ensure_edit_bone(armature, first_name, parent_name, first_head, first_tail)
        created += int(did_create)
        _, did_create = ensure_edit_bone(armature, second_name, parent_name, second_head, second_tail)
        created += int(did_create)

    bpy.ops.object.mode_set(mode="OBJECT")
    return created


def shapekey_stats(scene):
    total = 0
    unsafe = 0
    for obj in mesh_objects(scene):
        shape_keys = getattr(obj.data, "shape_keys", None)
        if not shape_keys:
            continue
        for key_block in shape_keys.key_blocks:
            if key_block.name == "Basis":
                continue
            total += 1
            if sanitize_shapekey_name(key_block.name) != key_block.name:
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
    for obj in mesh_objects(scene):
        shape_keys = getattr(obj.data, "shape_keys", None)
        if not shape_keys:
            continue

        used = set()
        for key_block in shape_keys.key_blocks:
            if key_block.name == "Basis":
                used.add(key_block.name)
                continue

            total += 1
            base_name = sanitize_shapekey_name(key_block.name)
            new_name = base_name
            suffix = 1
            while new_name in used:
                suffix += 1
                new_name = f"{base_name}_{suffix}"
            used.add(new_name)

            if key_block.name != new_name:
                key_block.name = new_name
                renamed += 1
    return total, renamed


def normalize(name):
    return name.replace(" ", "").replace("_", "").replace(".", "").lower()


def find_candidate(bone_names, candidates):
    exact = set(bone_names)
    for candidate in candidates:
        if candidate in exact:
            return candidate
    normalized = {normalize(name): name for name in bone_names}
    for candidate in candidates:
        found = normalized.get(normalize(candidate))
        if found:
            return found
    return ""


def refresh_mapping(scene):
    settings = get_settings(scene)
    armature = settings.armature
    settings.bone_map.clear()
    if not armature or armature.type != "ARMATURE":
        return 0

    bone_names = [bone.name for bone in armature.data.bones]
    guesses = mode_map(settings.model_type)
    matched = 0
    for target in get_target_bones(settings):
        item = settings.bone_map.add()
        item.target = target
        item.source = find_candidate(bone_names, guesses.get(target, [target]))
        if item.source:
            matched += 1
    return matched


def import_mmd_model(filepath):
    errors = []
    for op_path in ("mmd_tools_local.import_model", "mmd_tools.import_model"):
        namespace, operator = op_path.split(".", 1)
        try:
            op_group = getattr(bpy.ops, namespace)
            op = getattr(op_group, operator)
            op(filepath=filepath)
            return op_path
        except Exception as exc:
            errors.append(f"{op_path}: {exc}")
    raise RuntimeError(
        "No registered MMD importer was found. Enable CATS/mmd_tools first. "
        + " | ".join(errors)
    )


def call_operator(op_path, **kwargs):
    namespace, operator = op_path.split(".", 1)
    op_group = getattr(bpy.ops, namespace)
    op = getattr(op_group, operator)
    return op(**kwargs)


def select_model_objects(armature, objects):
    if bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    selected = []
    if armature:
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        selected.append(armature)
    for obj in objects:
        if obj.type == "MESH":
            obj.select_set(True)
            selected.append(obj)
    return selected


def run_cats_mmd_prepare(context, operator):
    settings = get_settings(context.scene)
    armature = settings.armature or find_armature(context)
    if not armature:
        operator.report({"ERROR"}, "No armature assigned for CATS MMD preparation.")
        return False

    meshes = model_mesh_objects(context.scene, armature) or mesh_objects(context.scene)
    select_model_objects(armature, meshes)
    if hasattr(context.scene, "armature"):
        context.scene.armature = armature.name
    if hasattr(context.scene, "remove_rigidbodies_joints"):
        context.scene.remove_rigidbodies_joints = True

    try:
        bpy.ops.object.make_single_user(
            type="SELECTED_OBJECTS",
            object=True,
            obdata=True,
            material=True,
            animation=True,
        )
    except Exception as exc:
        operator.report({"WARNING"}, f"Make Single User skipped or failed: {exc}")

    try:
        result = call_operator("cats_armature.fix")
    except Exception as exc:
        operator.report({"ERROR"}, f"CATS Fix Model failed: {exc}")
        return False
    if "CANCELLED" in result:
        operator.report({"ERROR"}, "CATS Fix Model was cancelled. Check the CATS panel for details.")
        return False

    armature = find_armature(context) or armature
    settings.armature = armature
    move_to_input(model_export_objects(context.scene, armature), context.scene)
    matched = refresh_mapping(context.scene)
    settings.cats_mmd_ok = True
    settings.scene_ok = True
    settings.mapping_ok = matched >= 18
    operator.report({"INFO"}, "CATS MMD preparation completed.")
    return True


def import_model_file(filepath, model_type):
    ext = os.path.splitext(filepath)[1].lower()
    if model_type == "MMD" and ext in {".pmx", ".pmd"}:
        import_mmd_model(filepath)
        return ext
    if ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=filepath)
        return ext
    return None


def apply_imported_model_flow(scene, imported):
    settings = get_settings(scene)
    if imported:
        move_to_input(imported, scene)
        armatures = [obj for obj in imported if obj.type == "ARMATURE"]
        if armatures:
            settings.armature = armatures[0]
    settings.imported_ok = bool(imported)
    settings.scene_ok = bool(imported)
    settings.cats_mmd_ok = False
    settings.shapekeys_ok = False
    refresh_mapping(scene)
    return settings


def require_template_initialized(context, operator):
    settings = get_settings(context.scene)
    if settings.template_ok:
        return True
    operator.report({"ERROR"}, "Initialize the work scene from the template before importing or converting a model.")
    return False


def status_icon(ok):
    return "CHECKMARK" if ok else "ERROR"


def apply_bone_color(armature, color=(0.0, 0.85, 1.0)):
    armature.show_in_front = True
    armature.color = (color[0], color[1], color[2], 1.0)
    try:
        armature.data.display_type = "STICK"
    except Exception:
        pass

    for pose_bone in armature.pose.bones:
        bone_color = getattr(pose_bone, "color", None)
        if not bone_color:
            bone_color = getattr(pose_bone.bone, "color", None)
        if not bone_color:
            continue
        try:
            bone_color.palette = "CUSTOM"
            bone_color.custom.normal = color
            bone_color.custom.select = (1.0, 0.85, 0.1)
            bone_color.custom.active = (1.0, 0.35, 0.1)
        except Exception:
            try:
                bone_color.palette = "THEME09"
            except Exception:
                pass


def focus_bone_in_view(context, armature, bone_name):
    if not armature or not bone_name or not armature.data.bones.get(bone_name):
        return False

    if bpy.context.object:
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    context.view_layer.objects.active = armature
    armature.show_in_front = True

    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="DESELECT")
    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone:
        if hasattr(pose_bone, "select"):
            pose_bone.select = True
        else:
            pose_bone.bone.select = True
        armature.data.bones.active = pose_bone.bone
    else:
        return False

    for area in context.screen.areas:
        if area.type != "VIEW_3D":
            continue
        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        space = next((s for s in area.spaces if s.type == "VIEW_3D"), None)
        if region and space:
            with context.temp_override(area=area, region=region, space_data=space):
                bpy.ops.view3d.view_selected(use_all_regions=False)
            break
    return True


class SBOX_PMW_BoneMapItem(PropertyGroup):
    target: StringProperty(name="Citizen Bone")
    source: StringProperty(name="Source Bone")
    weight_checked: BoolProperty(name="Weight Checked", default=False)
    direct_weight: BoolProperty(name="Direct Weight", default=False)
    descendant_weight: BoolProperty(name="Descendant Weight", default=False)


class SBOX_PMW_Settings(PropertyGroup):
    ui_language: EnumProperty(
        name="Language",
        items=[
            ("EN", "EN", "English UI"),
            ("CN", "CN", "中文界面"),
        ],
        default="EN",
    )
    model_type: EnumProperty(
        name="Model Type",
        items=[
            ("MMD", "MMD", "PMX/PMD models prepared with mmd_tools or CATS"),
            ("FBX", "FBX", "Generic FBX humanoid models"),
            ("SOURCE1", "Source 1", "ValveBiped Source 1/GMod/SFM models"),
        ],
        default="FBX",
    )
    template_blend: StringProperty(
        name="Template Blend",
        subtype="FILE_PATH",
        default=DEFAULT_TEMPLATE,
    )
    export_path: StringProperty(
        name="Export Path",
        subtype="FILE_PATH",
        default="//sbox_playermodel.fbx",
    )
    fp_template_fbx: StringProperty(
        name="First Person Arms Template FBX",
        subtype="FILE_PATH",
        default="",
    )
    fp_template_vmdl: StringProperty(
        name="First Person Arms Template VMDL",
        subtype="FILE_PATH",
        default="",
    )
    fp_export_path: StringProperty(
        name="First Person Arms FBX Path",
        subtype="FILE_PATH",
        default="//custom_first_person_arms.fbx",
    )
    fp_vmdl_path: StringProperty(
        name="First Person Arms VMDL Path",
        subtype="FILE_PATH",
        default="//custom_first_person_arms.vmdl",
    )
    fp_weight_threshold: FloatProperty(
        name="First Person Arms Weight Threshold",
        description="Keep vertices with at least this much weight on arm, hand, finger, clavicle, or twist bones.",
        default=0.001,
        min=0.0,
        max=1.0,
        precision=4,
    )
    fp_status: StringProperty(name="First Person Arms Status", default="")
    armature: PointerProperty(name="Armature", type=bpy.types.Object)
    template_ok: BoolProperty(name="Template Initialized", default=False)
    auto_prepare_mmd: BoolProperty(name="Auto CATS Prepare MMD", default=True)
    cats_mmd_ok: BoolProperty(name="CATS MMD Prepared", default=False)
    include_eye_bones: BoolProperty(
        name="Include Eye Bones",
        description="Map eye_L and eye_R when the model has eye bones. This needs extra setup later in ModelDoc.",
        default=False,
    )
    include_finger_meta_bones: BoolProperty(
        name="Include Finger Meta Bones",
        description="Map optional finger metacarpal bones when the source model has them.",
        default=False,
    )
    auto_prepare_shapekeys: BoolProperty(name="Auto Prepare Shapekeys on Export", default=True)
    shapekeys_ok: BoolProperty(name="Shapekeys Prepared", default=False)
    shapekey_count: IntProperty(name="Shapekey Count", default=0)
    unsafe_shapekey_count: IntProperty(name="Unsafe Shapekey Names", default=0)
    strict_vmdl_validation: BoolProperty(name="Block Export if VMDL Bones Are Missing", default=False)
    auto_rename_bones_on_export: BoolProperty(name="Auto Rename Mapped Bones Before Export", default=True)
    vmdl_bones_ok: BoolProperty(name="VMDL Bones Ready", default=False)
    missing_vmdl_bones: StringProperty(name="Missing VMDL Bones", default="")
    imported_ok: BoolProperty(name="Imported", default=False)
    scene_ok: BoolProperty(name="Scene Organized", default=False)
    mapping_ok: BoolProperty(name="Mapping Ready", default=False)
    deform_check_ok: BoolProperty(name="Mapped Bones Deform", default=False)
    deform_check_summary: StringProperty(name="Deform Check Summary", default="")
    bone_map: CollectionProperty(type=SBOX_PMW_BoneMapItem)


class SBOX_PMW_OT_import_model(Operator, ImportHelper):
    bl_idname = "sbox_pmw.import_model"
    bl_label = "Import Model"
    bl_description = "Import a model for the selected route"

    filename_ext = ""
    filter_glob: StringProperty(
        default="*.fbx;*.pmx;*.pmd",
        options={"HIDDEN"},
    )

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        before = set(bpy.data.objects)

        try:
            imported_ext = import_model_file(self.filepath, settings.model_type)
        except Exception as exc:
            self.report({"ERROR"}, f"Import failed: {exc}")
            return {"CANCELLED"}
        if imported_ext is None:
            self.report({"ERROR"}, "This MVP imports FBX directly, or PMX/PMD when CATS/mmd_tools is enabled.")
            return {"CANCELLED"}

        imported = [obj for obj in bpy.data.objects if obj not in before]
        settings = apply_imported_model_flow(context.scene, imported)
        if settings.model_type == "MMD" and settings.auto_prepare_mmd:
            run_cats_mmd_prepare(context, self)
        self.report({"INFO"}, f"Imported {len(imported)} objects.")
        return {"FINISHED"}


class SBOX_PMW_OT_append_template(Operator):
    bl_idname = "sbox_pmw.append_template"
    bl_label = "Initialize Work Scene"
    bl_description = "Initialize this file with the CustomModel-2-Sbox template before importing a model"

    def execute(self, context):
        settings = get_settings(context.scene)
        template = bpy.path.abspath(settings.template_blend)
        if not os.path.exists(template):
            self.report({"ERROR"}, f"Template not found: {template}")
            return {"CANCELLED"}

        appended = 0
        with bpy.data.libraries.load(template, link=False) as (data_from, data_to):
            data_to.collections = [
                name for name in data_from.collections if name not in bpy.data.collections
            ]
        for collection in data_to.collections:
            if collection and not context.scene.collection.children.get(collection.name):
                context.scene.collection.children.link(collection)
                appended += 1

        ensure_input_collection(context.scene)
        for armature in template_armatures(context):
            apply_bone_color(armature)
        settings.template_ok = True
        settings.imported_ok = False
        settings.scene_ok = False
        settings.mapping_ok = False
        settings.cats_mmd_ok = False
        settings.shapekeys_ok = False
        self.report({"INFO"}, f"Initialized work scene. Loaded {appended} template collections.")
        return {"FINISHED"}


class SBOX_PMW_OT_organize_scene(Operator):
    bl_idname = "sbox_pmw.organize_scene"
    bl_label = "Organize Scene"
    bl_description = "Create the Input collection and move selected model objects into it"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        objects = list(context.selected_objects)
        if not objects:
            armature = find_armature(context)
            objects = model_export_objects(context.scene, armature)
        if not objects:
            self.report({"ERROR"}, "No selected model objects or scene meshes found.")
            return {"CANCELLED"}

        move_to_input(objects, context.scene)
        armature = find_armature(context)
        if armature:
            settings.armature = armature
        settings.scene_ok = True
        refresh_mapping(context.scene)
        self.report({"INFO"}, f"Moved {len(objects)} objects into Input.")
        return {"FINISHED"}


class SBOX_PMW_OT_color_template_bones(Operator):
    bl_idname = "sbox_pmw.color_template_bones"
    bl_label = "Color Template Bones"
    bl_description = "Color Citizen/template bones so they are easier to compare against the source model"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        targets = template_armatures(context)
        if not targets:
            self.report({"ERROR"}, "No Citizen/template armature found to color.")
            return {"CANCELLED"}

        for armature in targets:
            apply_bone_color(armature)
        self.report({"INFO"}, f"Colored {len(targets)} template armature(s).")
        return {"FINISHED"}


class SBOX_PMW_OT_prepare_mmd_cats(Operator):
    bl_idname = "sbox_pmw.prepare_mmd_cats"
    bl_label = "Run CATS MMD Prepare"
    bl_description = "Run Make Single User and CATS Fix Model on the imported MMD model"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}
        if get_settings(context.scene).model_type != "MMD":
            self.report({"ERROR"}, "CATS MMD preparation is only available in MMD mode.")
            return {"CANCELLED"}
        return {"FINISHED"} if run_cats_mmd_prepare(context, self) else {"CANCELLED"}


class SBOX_PMW_OT_detect_bones(Operator):
    bl_idname = "sbox_pmw.detect_bones"
    bl_label = "Detect Bones"
    bl_description = "Guess Citizen bone mapping from the selected armature"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        armature = find_armature(context)
        if not armature:
            self.report({"ERROR"}, "Select or assign one armature first.")
            return {"CANCELLED"}
        settings.armature = armature
        matched = refresh_mapping(context.scene)
        settings.mapping_ok = matched >= 18
        settings.deform_check_ok = False
        settings.deform_check_summary = ""
        self.report({"INFO"}, f"Matched {matched}/{len(get_target_bones(settings))} target bones.")
        return {"FINISHED"}


class SBOX_PMW_OT_save_mapping(Operator, ExportHelper):
    bl_idname = "sbox_pmw.save_mapping"
    bl_label = "Save Mapping"
    bl_description = "Save the current bone mapping to a JSON file"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def invoke(self, context, event):
        self.filepath = bpy.path.abspath("//sbox_bone_mapping.json")
        return super().invoke(context, event)

    def execute(self, context):
        settings = get_settings(context.scene)
        data = {
            "version": 1,
            "model_type": settings.model_type,
            "include_eye_bones": settings.include_eye_bones,
            "include_finger_meta_bones": settings.include_finger_meta_bones,
            "mapping": {item.target: item.source for item in settings.bone_map},
        }
        try:
            with open(self.filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except OSError as exc:
            self.report({"ERROR"}, f"Could not save mapping: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Saved {len(data['mapping'])} mappings.")
        return {"FINISHED"}


class SBOX_PMW_OT_load_mapping(Operator, ImportHelper):
    bl_idname = "sbox_pmw.load_mapping"
    bl_label = "Load Mapping"
    bl_description = "Load bone mapping from a JSON file"

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            self.report({"ERROR"}, f"Could not load mapping: {exc}")
            return {"CANCELLED"}

        mapping = data.get("mapping")
        if not isinstance(mapping, dict):
            self.report({"ERROR"}, "Mapping file is missing a 'mapping' object.")
            return {"CANCELLED"}

        settings.model_type = data.get("model_type", settings.model_type)
        settings.include_eye_bones = bool(data.get("include_eye_bones", settings.include_eye_bones))
        settings.include_finger_meta_bones = bool(data.get("include_finger_meta_bones", settings.include_finger_meta_bones))

        armature = settings.armature or find_armature(context)
        bone_names = set(armature.data.bones.keys()) if armature else set()
        skipped = 0
        settings.bone_map.clear()
        for target in get_target_bones(settings):
            source = str(mapping.get(target, ""))
            if source and bone_names and source not in bone_names:
                source = ""
                skipped += 1
            item = settings.bone_map.add()
            item.target = target
            item.source = source

        matched = sum(1 for item in settings.bone_map if item.source)
        settings.mapping_ok = matched >= 18
        settings.deform_check_ok = False
        settings.deform_check_summary = ""
        if skipped:
            self.report({"WARNING"}, f"Skipped {skipped} mappings whose source bones are not in the current armature.")
        self.report({"INFO"}, f"Loaded {matched}/{len(settings.bone_map)} mappings.")
        return {"FINISHED"}


class SBOX_PMW_OT_apply_rename(Operator):
    bl_idname = "sbox_pmw.apply_rename"
    bl_label = "Rename Bones to Citizen"
    bl_description = "Rename mapped source bones to Citizen target names"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        armature = settings.armature or find_armature(context)
        if not armature:
            self.report({"ERROR"}, "No armature assigned.")
            return {"CANCELLED"}

        duplicates = duplicate_mapped_sources(settings)
        if duplicates:
            self.report({"ERROR"}, f"Duplicate source bone mappings: {', '.join(duplicates[:5])}")
            return {"CANCELLED"}

        renamed, missing_sources, blocked = apply_mapped_bone_names(armature, settings)

        matched = refresh_mapping(context.scene)
        settings.mapping_ok = matched >= 18
        settings.deform_check_ok = False
        settings.deform_check_summary = ""
        if missing_sources:
            self.report({"WARNING"}, f"Some source bones were not found: {', '.join(missing_sources[:5])}")
        if blocked:
            self.report({"WARNING"}, f"Some target names already existed: {', '.join(blocked[:5])}")
        self.report({"INFO"}, f"Renamed {renamed} bones.")
        return {"FINISHED"}


class SBOX_PMW_OT_validate_deform_weights(Operator):
    bl_idname = "sbox_pmw.validate_deform_weights"
    bl_label = "Validate Deform Weights"
    bl_description = "Check whether each mapped source bone directly deforms the mesh, or only has weighted descendants"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        armature = settings.armature or find_armature(context)
        if not armature:
            self.report({"ERROR"}, "No source armature assigned.")
            return {"CANCELLED"}
        settings.armature = armature

        issues = validate_mapping_weights(context.scene)
        if issues:
            preview = ", ".join(issues[:4])
            if len(issues) > 4:
                preview += f", ... +{len(issues) - 4}"
            self.report({"WARNING"}, settings.deform_check_summary + " " + preview)
            return {"FINISHED"}

        self.report({"INFO"}, settings.deform_check_summary or "Mapped bones directly deform the mesh.")
        return {"FINISHED"}


class SBOX_PMW_OT_focus_bone(Operator):
    bl_idname = "sbox_pmw.focus_bone"
    bl_label = "Focus Bone"
    bl_description = "Select, highlight, and zoom to a source or target bone"

    focus_kind: EnumProperty(
        name="Kind",
        items=[
            ("SOURCE", "Source", "Focus the selected source model bone"),
            ("TARGET", "Target", "Focus the target Citizen/template bone"),
        ],
        default="SOURCE",
    )
    bone_name: StringProperty(name="Bone")

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        if self.focus_kind == "SOURCE":
            armature = settings.armature or find_armature(context)
            label = "source"
        else:
            source_armature = settings.armature or find_armature(context)
            armature = find_armature_with_bone(context, self.bone_name, exclude=source_armature)
            if not armature and source_armature and source_armature.data.bones.get(self.bone_name):
                armature = source_armature
            label = "target"

        if not self.bone_name:
            self.report({"ERROR"}, f"No {label} bone selected.")
            return {"CANCELLED"}
        if not armature or not armature.data.bones.get(self.bone_name):
            self.report({"ERROR"}, f"Could not find {label} bone: {self.bone_name}")
            return {"CANCELLED"}
        if not focus_bone_in_view(context, armature, self.bone_name):
            self.report({"ERROR"}, f"Could not focus bone: {self.bone_name}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Focused {label} bone: {self.bone_name}")
        return {"FINISHED"}


class SBOX_PMW_OT_prepare_shapekeys(Operator):
    bl_idname = "sbox_pmw.prepare_shapekeys"
    bl_label = "Prepare Shapekeys"
    bl_description = "Rename shapekeys to Source 2 safe names by replacing spaces and special characters"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        total, renamed = prepare_shapekeys(context.scene)
        settings.shapekey_count = total
        settings.unsafe_shapekey_count = 0
        settings.shapekeys_ok = True
        if total > 200:
            self.report({"WARNING"}, f"{total} shapekeys found. S&box may allow many, but keeping around 200 is recommended.")
        self.report({"INFO"}, f"Prepared {total} shapekeys. Renamed {renamed}.")
        return {"FINISHED"}


class SBOX_PMW_OT_run_citizen_conversion(Operator):
    bl_idname = "sbox_pmw.run_citizen_conversion"
    bl_label = "Run Citizen Conversion"
    bl_description = "Run the original Manual converter and export the template Human Citizen Armature"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        armature = settings.armature or find_armature(context)
        if not armature:
            self.report({"ERROR"}, "No source armature assigned.")
            return {"CANCELLED"}

        template = bpy.data.objects.get("Human Citizen Armature")
        if not template:
            self.report({"ERROR"}, "Human Citizen Armature was not found. Initialize the template scene first.")
            return {"CANCELLED"}

        meshes = model_mesh_objects(context.scene, armature)
        if not meshes:
            self.report({"ERROR"}, "No meshes are bound to the source armature.")
            return {"CANCELLED"}

        duplicates = duplicate_mapped_sources(settings)
        if duplicates:
            self.report({"ERROR"}, f"Conversion blocked. Duplicate source bone mappings: {', '.join(duplicates[:5])}")
            return {"CANCELLED"}

        if settings.auto_prepare_shapekeys:
            total, renamed = prepare_shapekeys(context.scene)
            settings.shapekey_count = total
            settings.unsafe_shapekey_count = 0
            settings.shapekeys_ok = True
            if renamed:
                self.report({"INFO"}, f"Prepared shapekeys before conversion. Renamed {renamed}.")

        if settings.auto_rename_bones_on_export:
            renamed, missing_sources, blocked = apply_mapped_bone_names(armature, settings)
            if renamed:
                self.report({"INFO"}, f"Applied mapped bone names before conversion. Renamed {renamed}.")
            if missing_sources:
                self.report({"WARNING"}, f"Some source bones were not found: {', '.join(missing_sources[:5])}")
            if blocked:
                self.report({"WARNING"}, f"Some target names already existed: {', '.join(blocked[:5])}")

        if not prepare_manual_converter_input(context.scene, armature):
            self.report({"ERROR"}, "Could not prepare the Input collection for conversion.")
            return {"CANCELLED"}

        export_path = bpy.path.abspath(settings.export_path)
        try:
            run_manual_converter_script(export_path)
        except Exception as exc:
            self.report({"ERROR"}, f"Citizen conversion failed: {exc}")
            return {"CANCELLED"}

        output_armature = bpy.data.objects.get("Human Citizen Armature")
        if output_armature:
            settings.armature = output_armature
            apply_bone_color(output_armature)
            missing = missing_vmdl_bones(output_armature)
            settings.vmdl_bones_ok = not missing
            settings.missing_vmdl_bones = ", ".join(missing)

        settings.export_path = export_path
        self.report({"INFO"}, f"Converted and exported Human Citizen Armature: {export_path}")
        return {"FINISHED"}


class SBOX_PMW_OT_export_source_skeleton(Operator):
    bl_idname = "sbox_pmw.export_source_skeleton"
    bl_label = "Try Source Skeleton Export"
    bl_description = "Export the original armature, collapsing unsupported extra deform bones into Citizen-compatible parents"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        armature = settings.armature or find_armature(context)
        meshes = model_mesh_objects(context.scene, armature)
        if not armature or not meshes:
            self.report({"ERROR"}, "Need one source armature and at least one mesh bound to it.")
            return {"CANCELLED"}

        duplicates = duplicate_mapped_sources(settings)
        if duplicates:
            self.report({"ERROR"}, f"Export blocked. Duplicate source bone mappings: {', '.join(duplicates[:5])}")
            return {"CANCELLED"}

        if settings.auto_prepare_shapekeys:
            total, renamed = prepare_shapekeys(context.scene)
            settings.shapekey_count = total
            settings.unsafe_shapekey_count = 0
            settings.shapekeys_ok = True
            if renamed:
                self.report({"INFO"}, f"Prepared shapekeys before export. Renamed {renamed}.")

        if settings.auto_rename_bones_on_export:
            renamed, missing_sources, blocked = apply_mapped_bone_names(armature, settings)
            if renamed:
                self.report({"INFO"}, f"Applied mapped bone names before export. Renamed {renamed}.")
            if missing_sources:
                self.report({"WARNING"}, f"Some source bones were not found: {', '.join(missing_sources[:5])}")
            if blocked:
                self.report({"WARNING"}, f"Some target names already existed: {', '.join(blocked[:5])}")

        created = create_helper_bones(armature)
        transferred, removed = collapse_extra_bones_to_supported(
            context,
            armature,
            meshes,
            supported_export_bone_names(settings),
        )
        missing = missing_vmdl_bones(armature)
        settings.vmdl_bones_ok = not missing
        settings.missing_vmdl_bones = ", ".join(missing)
        if missing and settings.strict_vmdl_validation:
            preview = ", ".join(missing[:8])
            if len(missing) > 8:
                preview += f", ... +{len(missing) - 8}"
            self.report({"ERROR"}, f"Export blocked. Missing VMDL bones: {preview}")
            return {"CANCELLED"}

        export_path = bpy.path.abspath(settings.export_path)
        try:
            export_armature_fbx(context, armature, export_path)
        except Exception as exc:
            self.report({"ERROR"}, f"Source skeleton export failed: {exc}")
            return {"CANCELLED"}

        settings.export_path = export_path
        settings.armature = armature
        self.report(
            {"INFO"},
            f"Exported source skeleton route: {export_path} "
            f"(helpers created: {created}, weights moved: {transferred}, bones removed: {removed})",
        )
        return {"FINISHED"}


class SBOX_PMW_OT_create_helper_bones(Operator):
    bl_idname = "sbox_pmw.create_helper_bones"
    bl_label = "Create Helper/IK Bones"
    bl_description = "Create placeholder Citizen helper, IK target, aim matrix, twist, and missing spine bones"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}
        settings = get_settings(context.scene)
        armature = settings.armature or find_armature(context)
        if not armature:
            self.report({"ERROR"}, "No source armature assigned.")
            return {"CANCELLED"}
        created = create_helper_bones(armature)
        missing = missing_vmdl_bones(armature)
        settings.vmdl_bones_ok = not missing
        settings.missing_vmdl_bones = ", ".join(missing)
        self.report({"INFO"}, f"Created {created} helper bones.")
        return {"FINISHED"}


class SBOX_PMW_OT_validate_vmdl_bones(Operator):
    bl_idname = "sbox_pmw.validate_vmdl_bones"
    bl_label = "Validate VMDL Bones"
    bl_description = "Check whether the source armature has the core Citizen and helper bones referenced by playermodel.vmdl"

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        armature = settings.armature or find_armature(context)
        duplicates = duplicate_mapped_sources(settings)
        if duplicates:
            self.report({"ERROR"}, f"Duplicate source bone mappings: {', '.join(duplicates[:5])}")
            return {"CANCELLED"}
        if settings.auto_rename_bones_on_export:
            renamed, missing_sources, blocked = apply_mapped_bone_names(armature, settings)
            if renamed:
                self.report({"INFO"}, f"Applied mapped bone names before validation. Renamed {renamed}.")
            if missing_sources:
                self.report({"WARNING"}, f"Some source bones were not found: {', '.join(missing_sources[:5])}")
            if blocked:
                self.report({"WARNING"}, f"Some target names already existed: {', '.join(blocked[:5])}")
        missing = missing_vmdl_bones(armature)
        settings.vmdl_bones_ok = not missing
        settings.missing_vmdl_bones = ", ".join(missing)
        if missing:
            preview = ", ".join(missing[:8])
            if len(missing) > 8:
                preview += f", ... +{len(missing) - 8}"
            self.report({"WARNING"}, f"Missing VMDL bones: {preview}")
            return {"FINISHED"}

        self.report({"INFO"}, "VMDL bone validation passed.")
        return {"FINISHED"}


class SBOX_PMW_OT_export_fbx(Operator, ExportHelper):
    bl_idname = "sbox_pmw.export_fbx"
    bl_label = "Export S&box FBX"
    bl_description = "Export selected/organized model as a Citizen-compatible FBX candidate"

    filename_ext = ".fbx"
    filter_glob: StringProperty(default="*.fbx", options={"HIDDEN"})

    def invoke(self, context, event):
        settings = get_settings(context.scene)
        self.filepath = bpy.path.abspath(settings.export_path)
        return super().invoke(context, event)

    def execute(self, context):
        if not require_template_initialized(context, self):
            return {"CANCELLED"}

        settings = get_settings(context.scene)
        armature = settings.armature or find_armature(context)
        meshes = model_mesh_objects(context.scene, armature)
        if not armature or not meshes:
            self.report({"ERROR"}, "Need one source armature and at least one mesh bound to it before export.")
            return {"CANCELLED"}
        duplicates = duplicate_mapped_sources(settings)
        if duplicates:
            self.report({"ERROR"}, f"Export blocked. Duplicate source bone mappings: {', '.join(duplicates[:5])}")
            return {"CANCELLED"}
        if settings.auto_rename_bones_on_export:
            renamed, missing_sources, blocked = apply_mapped_bone_names(armature, settings)
            if renamed:
                self.report({"INFO"}, f"Applied mapped bone names before export. Renamed {renamed}.")
            if missing_sources:
                self.report({"WARNING"}, f"Some source bones were not found: {', '.join(missing_sources[:5])}")
            if blocked:
                self.report({"WARNING"}, f"Some target names already existed: {', '.join(blocked[:5])}")
        missing = missing_vmdl_bones(armature)
        settings.vmdl_bones_ok = not missing
        settings.missing_vmdl_bones = ", ".join(missing)
        if missing and settings.strict_vmdl_validation:
            preview = ", ".join(missing[:8])
            if len(missing) > 8:
                preview += f", ... +{len(missing) - 8}"
            self.report({"ERROR"}, f"Export blocked. Missing VMDL bones: {preview}")
            return {"CANCELLED"}
        if settings.auto_prepare_shapekeys:
            total, renamed = prepare_shapekeys(context.scene)
            settings.shapekey_count = total
            settings.unsafe_shapekey_count = 0
            settings.shapekeys_ok = True
            if renamed:
                self.report({"INFO"}, f"Prepared shapekeys before export. Renamed {renamed}.")

        settings.export_path = self.filepath
        export_armature_fbx(context, armature, self.filepath)
        self.report({"INFO"}, f"Exported FBX: {self.filepath}")
        return {"FINISHED"}

class SBOX_PMW_OT_create_first_person_arms(Operator):
    bl_idname = "sbox_pmw.create_first_person_arms"
    bl_label = "Create First Person Arms"
    bl_description = "Extract arm-weighted vertices from the converted Citizen model and export a first-person arms FBX"

    def execute(self, context):
        settings = get_settings(context.scene)
        source_armature = settings.armature or find_armature(context)
        
        if not source_armature:
            self.report({"ERROR"}, "Assign the converted full-body armature first.")
            return {"CANCELLED"}
            
        if not settings.fp_template_fbx:
            self.report({"ERROR"}, "Choose a first person arms template FBX first.")
            return {"CANCELLED"}
            
        try:
            # 1. 导入第一人称手臂模板骨架
            working_armature = import_first_person_template_armature(context, settings.fp_template_fbx)
            
            # 2. 创建参考骨架（用于后续的顶点重定向计算）
            reference_armature = create_first_person_reference_armature(context, working_armature)
            
            # 3. 将工作骨架的手臂骨骼移动到源模型骨架的对应位置
            matched_bones = matching_first_person_bone_count(source_armature, working_armature)
            moved_bones = move_first_person_armature_to_source(source_armature, working_armature)
            
            # 4. 提取手臂网格并进行顶点重定向（此处调用了修复后的核心函数）
            arm_meshes, removed_vertices, kept_vertices, moved_meshes, removed_shapekeys, retargeted_vertices = duplicate_first_person_arm_meshes(
                context, source_armature, reference_armature, settings.fp_weight_threshold,
            )
            
            # 5. 清理工作骨架，保留参考骨架作为最终骨架
            target_armature = finalize_first_person_reference_armature(working_armature, reference_armature)
            
            # 6. 导出第一人称手臂 FBX
            export_path = export_first_person_arms_fbx(
                context, target_armature, arm_meshes, settings.fp_export_path,
            )
            
            # 7. 生成 VMDL 文件（如果设置了模板）
            vmdl_path = None
            if settings.fp_template_vmdl and settings.fp_vmdl_path:
                vmdl_path = write_first_person_arms_vmdl(
                    settings.fp_template_vmdl, settings.fp_vmdl_path, export_path,
                )
                
            # 8. 删除场景中的全身源模型
            removed_source = delete_source_full_body_model(context.scene, source_armature)
            
        except Exception as exc:
            settings.fp_status = str(exc)
            self.report({"ERROR"}, f"First person arms export failed: {exc}")
            return {"CANCELLED"}

        # 更新设置和状态信息
        settings.fp_export_path = export_path
        if vmdl_path:
            settings.fp_vmdl_path = vmdl_path
            
        settings.fp_status = (
            f"Created {len(arm_meshes)} mesh(es), matched {matched_bones} bones, moved {moved_bones} bones, "
            f"kept {kept_vertices} arm vertices, retargeted {retargeted_vertices} vertices from {moved_meshes} mesh object(s), "
            f"removed {removed_vertices} non-arm vertices and {removed_shapekeys} shapekeys "
            f"and {removed_source} source object(s)."
        )
        
        settings.armature = target_armature
        self.report({"INFO"}, settings.fp_status)
        return {"FINISHED"}


class SBOX_PMW_PT_panel(Panel):
    bl_label = "S&box Playermodel"
    bl_idname = "SBOX_PMW_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "S&box"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = get_settings(scene)
        armature = settings.armature
        meshes = mesh_objects(scene)
        input_col = bpy.data.collections.get(INPUT_COLLECTION)
        shape_total, shape_unsafe = shapekey_stats(scene)
        t = lambda key: ui_text(settings, key)

        layout.prop(settings, "ui_language", text=t("language"))
        layout.prop(settings, "model_type", expand=True)

        box = layout.box()
        box.label(text=t("init_scene"), icon="APPEND_BLEND")
        box.prop(settings, "template_blend")
        box.operator("sbox_pmw.append_template", icon="APPEND_BLEND")
        box.label(text=f"{t('template')}: {t('ready') if settings.template_ok else t('required')}", icon=status_icon(settings.template_ok))
        row = box.row()
        row.enabled = settings.template_ok
        row.operator("sbox_pmw.color_template_bones", icon="COLOR")

        box = layout.box()
        box.enabled = settings.template_ok
        box.label(text=t("import_model"), icon="IMPORT")
        if settings.model_type == "MMD":
            box.prop(settings, "auto_prepare_mmd")
        box.operator("sbox_pmw.import_model", icon="FILE_FOLDER")
        if settings.model_type == "MMD":
            box.operator("sbox_pmw.prepare_mmd_cats", icon="MOD_ARMATURE")
            box.label(text=f"{t('cats_prepare')}: {t('done') if settings.cats_mmd_ok else t('pending')}", icon=status_icon(settings.cats_mmd_ok))

        box = layout.box()
        box.enabled = settings.template_ok
        box.label(text=t("scene_setup"), icon="OUTLINER_COLLECTION")
        row = box.row()
        row.label(text=f"{t('input_collection')}: {t('ok') if input_col else t('missing')}", icon=status_icon(bool(input_col)))
        row = box.row()
        row.label(text=f"{t('meshes')}: {len(meshes)}", icon=status_icon(bool(meshes)))
        box.prop(settings, "armature", text=t("armature"))
        box.operator("sbox_pmw.organize_scene", icon="GROUP")

        box = layout.box()
        box.enabled = settings.template_ok
        box.label(text=t("bone_remap"), icon="ARMATURE_DATA")
        box.prop(settings, "include_eye_bones", text=t("include_eye_bones"))
        if settings.include_eye_bones:
            box.label(text=t("eye_note"), icon="INFO")
        box.prop(settings, "include_finger_meta_bones", text=t("include_finger_meta_bones"))
        if settings.include_finger_meta_bones:
            box.label(text=t("finger_meta_note"), icon="INFO")
        box.label(text=t("ignore_extra_bones"), icon="INFO")
        row = box.row(align=True)
        row.operator("sbox_pmw.load_mapping", text=t("load_mapping"), icon="IMPORT")
        row.operator("sbox_pmw.save_mapping", text=t("save_mapping"), icon="EXPORT")
        box.operator("sbox_pmw.detect_bones", text=t("detect_bones"), icon="VIEWZOOM")
        if armature and settings.bone_map:
            matched = sum(1 for item in settings.bone_map if item.source)
            box.label(text=f"{t('matched')}: {matched}/{len(settings.bone_map)}", icon=status_icon(matched >= 18))
            for item in settings.bone_map:
                row = box.row(align=True)
                row.prop_search(item, "source", armature.data, "bones", text=item.target)
                op = row.operator("sbox_pmw.focus_bone", text="", icon="ARMATURE_DATA")
                op.focus_kind = "TARGET"
                op.bone_name = item.target
                op = row.operator("sbox_pmw.focus_bone", text="", icon="VIEWZOOM")
                op.focus_kind = "SOURCE"
                op.bone_name = item.source
                if not item.source:
                    row.label(text="", icon="ERROR")
                elif not item.weight_checked:
                    row.label(text="", icon="QUESTION")
                elif item.direct_weight:
                    row.label(text="", icon="CHECKMARK")
                elif item.descendant_weight:
                    row.label(text="", icon="INFO")
                else:
                    row.label(text="", icon="ERROR")
            box.operator("sbox_pmw.apply_rename", text=t("apply_rename"), icon="FILE_TICK")
            box.operator("sbox_pmw.validate_deform_weights", text=t("validate_weights"), icon="MOD_VERTEX_WEIGHT")
            if settings.deform_check_summary:
                box.label(
                    text=settings.deform_check_summary[:100],
                    icon=status_icon(settings.deform_check_ok),
                )
        else:
            box.label(text=t("assign_armature"), icon="INFO")

        box = layout.box()
        box.enabled = settings.template_ok
        box.label(text=t("shapekeys"), icon="SHAPEKEY_DATA")
        box.label(text=f"{t('shapekey_count')}: {shape_total}", icon=status_icon(shape_total <= 220))
        box.label(text=f"{t('unsafe_names')}: {shape_unsafe}", icon=status_icon(shape_unsafe == 0))
        if shape_total > 200:
            box.label(text=t("shapekey_warning"), icon="ERROR")
        box.operator("sbox_pmw.prepare_shapekeys", text=t("prepare_shapekeys"), icon="FILE_TICK")
        box.prop(settings, "auto_prepare_shapekeys", text=t("auto_prepare_shapekeys"))

        box = layout.box()
        box.enabled = settings.template_ok
        box.label(text=t("export"), icon="EXPORT")
        box.label(text=t("preferred_export"), icon="INFO")
        box.operator("sbox_pmw.run_citizen_conversion", text=t("run_conversion"), icon="OUTLINER_OB_ARMATURE")
        box.label(text=f"{t('vmdl_bones')}: {t('ready') if settings.vmdl_bones_ok else t('needs_check')}", icon=status_icon(settings.vmdl_bones_ok))
        if settings.missing_vmdl_bones:
            box.label(text=f"{t('missing_bones')}: {settings.missing_vmdl_bones[:80]}", icon="ERROR")
        box.prop(settings, "auto_rename_bones_on_export", text=t("auto_rename"))
        box.prop(settings, "strict_vmdl_validation", text=t("block_missing"))
        box.prop(settings, "export_path", text=t("export_path"))
        box.operator("sbox_pmw.export_fbx", text=t("export_fbx"), icon="EXPORT")

        box = layout.box()
        box.enabled = settings.template_ok
        box.label(text=t("fp_arms"), icon="VIEW_CAMERA")
        box.label(text=t("fp_note"), icon="INFO")
        box.prop(settings, "fp_template_fbx", text=t("fp_template_fbx"))
        box.prop(settings, "fp_template_vmdl", text=t("fp_template_vmdl"))
        box.prop(settings, "fp_export_path", text=t("fp_export_path"))
        box.prop(settings, "fp_vmdl_path", text=t("fp_vmdl_path"))
        box.prop(settings, "fp_weight_threshold", text=t("fp_weight_threshold"))
        box.operator("sbox_pmw.create_first_person_arms", text=t("fp_create"), icon="VIEW_CAMERA")
        if settings.fp_status:
            box.label(text=f"{t('fp_status')}: {settings.fp_status[:100]}", icon="INFO")
        elif armature:
            box.label(text=t("fp_ready"), icon="CHECKMARK")
        else:
            box.label(text=t("fp_need_armature"), icon="ERROR")

        if settings.model_type == "MMD":
            layout.label(text=t("mmd_tip"), icon="INFO")
        if settings.model_type == "SOURCE1":
            layout.label(text=t("source1_tip"), icon="INFO")


classes = (
    SBOX_PMW_BoneMapItem,
    SBOX_PMW_Settings,
    SBOX_PMW_OT_import_model,
    SBOX_PMW_OT_append_template,
    SBOX_PMW_OT_organize_scene,
    SBOX_PMW_OT_color_template_bones,
    SBOX_PMW_OT_prepare_mmd_cats,
    SBOX_PMW_OT_detect_bones,
    SBOX_PMW_OT_save_mapping,
    SBOX_PMW_OT_load_mapping,
    SBOX_PMW_OT_apply_rename,
    SBOX_PMW_OT_validate_deform_weights,
    SBOX_PMW_OT_focus_bone,
    SBOX_PMW_OT_prepare_shapekeys,
    SBOX_PMW_OT_run_citizen_conversion,
    SBOX_PMW_OT_export_source_skeleton,
    SBOX_PMW_OT_create_helper_bones,
    SBOX_PMW_OT_validate_vmdl_bones,
    SBOX_PMW_OT_export_fbx,
    SBOX_PMW_OT_create_first_person_arms,
    SBOX_PMW_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.sbox_pm_wizard = PointerProperty(type=SBOX_PMW_Settings)


def unregister():
    del bpy.types.Scene.sbox_pm_wizard
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
