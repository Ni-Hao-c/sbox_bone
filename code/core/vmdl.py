"""VMDL helpers."""

import os
import re

import bpy

from .paths import source2_asset_path


def read_text_with_fallback(path):
    errors = []
    for encoding in ("utf-8-sig", "utf-8", "gbk", "mbcs"):
        try:
            with open(path, "r", encoding=encoding) as handle:
                return handle.read()
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    raise RuntimeError(
        "Could not decode VMDL template with utf-8-sig, utf-8, gbk, or mbcs. "
        + " | ".join(errors)
    )


def missing_vmdl_bones(armature):
    from .runtime import missing_vmdl_bones as runtime_missing_vmdl_bones

    return runtime_missing_vmdl_bones(armature)


def write_first_person_arms_vmdl(template_path, output_path, fbx_path):
    template_path = bpy.path.abspath(template_path)
    output_path = bpy.path.abspath(output_path)
    if not template_path:
        return None
    if not os.path.exists(template_path):
        raise FileNotFoundError("First person arms template VMDL was not found.")

    text = read_text_with_fallback(template_path)

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
