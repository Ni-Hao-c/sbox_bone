"""Model import helpers."""

import os

import bpy


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
    from .runtime import apply_imported_model_flow as runtime_apply_imported_model_flow

    return runtime_apply_imported_model_flow(scene, imported)


def run_cats_mmd_prepare(context, operator):
    from .runtime import run_cats_mmd_prepare as runtime_run_cats_mmd_prepare

    return runtime_run_cats_mmd_prepare(context, operator)
