"""Bone mapping and validation helpers."""

import bpy

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
    from .scene import weighted_bone_names

    settings = scene.sbox_pm_wizard
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


def focus_bone_in_view(context, armature, bone_name):
    from .runtime import focus_bone_in_view as runtime_focus_bone_in_view

    return runtime_focus_bone_in_view(context, armature, bone_name)


def refresh_mapping(scene):
    settings = scene.sbox_pm_wizard
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
