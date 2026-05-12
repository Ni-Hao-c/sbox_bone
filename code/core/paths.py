"""Path helpers."""

import os

import bpy


ADDON_ROOT = os.path.dirname(os.path.dirname(__file__))
REPO_ROOT = os.path.dirname(ADDON_ROOT)
DEFAULT_TEMPLATE = os.path.join(REPO_ROOT, "custommodel2s&box.blend")
MANUAL_CONVERTER_SCRIPT = "convert_playermodel (Manual).py"


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


def source2_asset_path(filepath):
    normalized = bpy.path.abspath(filepath).replace("\\", "/")
    marker = "/Assets/"
    if marker in normalized:
        return normalized.split(marker, 1)[1]
    return os.path.basename(normalized)
