# Architecture

This project is being migrated from a single-file Blender add-on into a small package while keeping the working PMX flow intact.

## Current Layout

```text
sbox_playermodel_wizard/
  __init__.py              thin Blender entrypoint
  bl_info.py               add-on metadata
  properties.py            property-group re-exports
  core/
    runtime.py             stable runtime and current source of behavior
    bones.py               bone helper re-exports
    meshes.py              mesh helper re-exports
    first_person.py        first-person arms re-exports
    importers.py           import and post-import flow re-exports
    paths.py               path helper re-exports
    vmdl.py                VMDL helper re-exports
  operators/
    workflow.py            operator re-exports
  ui/
    panel.py               panel re-export
    i18n.py                EN/CN text re-exports
  vendor/
    README.md              external/helper script notes
  tests/
    scripts/
      smoke_register.py    Blender background registration check
```

## Migration Rule

`core/runtime.py` is intentionally kept as the compatibility runtime for now. New modules re-export stable functions and classes from it so callers can begin using clearer import paths without changing behavior.

Move code out of `runtime.py` only one workflow at a time, and only after a Blender background smoke test passes.

## Stable PMX Contract

Do not rewrite the PMX path casually. The expected PMX flow is:

1. import with `mmd_tools` or CATS;
2. move imported objects into the `Input` collection;
3. assign the imported armature when possible;
4. refresh bone mapping;
5. optionally run CATS/MMD preparation;
6. continue through the shared mapping, shapekey, and export tools.

## FBX Contract

FBX should reuse the same post-import contract after Blender imports the file:

1. import with `bpy.ops.import_scene.fbx`;
2. move imported objects into the `Input` collection;
3. assign the imported armature when possible;
4. refresh bone mapping;
5. continue through the shared mapping, shapekey, and export tools.

The FBX path should not call MMD-only preparation.

## Verification

Minimum checks before packaging:

```powershell
python -m py_compile <all addon .py files>
blender --background --factory-startup --python tests/scripts/smoke_register.py
```
