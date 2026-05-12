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

from .bones import (
    apply_mapped_bone_names,
    create_helper_bones,
    duplicate_mapped_sources,
    get_target_bones,
    missing_vmdl_bones,
    refresh_mapping,
    validate_mapping_weights,
)
from .first_person import (
    create_first_person_reference_armature,
    delete_source_full_body_model,
    duplicate_first_person_arm_meshes,
    export_first_person_arms_fbx,
    finalize_first_person_reference_armature,
    import_first_person_template_armature,
    matching_first_person_bone_count,
    move_first_person_armature_to_source,
)
from .exporters import (
    collapse_extra_bones_to_supported,
    export_armature_fbx,
    prepare_manual_converter_input,
    run_manual_converter_script,
    supported_export_bone_names,
)
from .importers import import_model_file
from .meshes import prepare_shapekeys, shapekey_stats
from .paths import DEFAULT_TEMPLATE
from .scene import (
    INPUT_COLLECTION,
    OUTPUT_COLLECTION,
    ensure_input_collection,
    ensure_scene_collection,
    find_armature,
    find_armature_with_bone,
    mesh_objects,
    model_export_objects,
    model_mesh_objects,
    move_to_input,
    object_in_collection,
    primary_template_armature,
    template_armatures,
    weighted_bone_names,
)
from .vmdl import write_first_person_arms_vmdl
from ..ui.i18n import ui_text


def get_settings(scene):
    return scene.sbox_pm_wizard


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
