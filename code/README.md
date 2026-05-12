# S&box Playermodel Wizard

Blender add-on for preparing MMD/FBX models for S&box Citizen-compatible export.

## Install

1. Zip or copy the `sbox_playermodel_wizard` folder.
2. In Blender: `Edit > Preferences > Add-ons > Install...`.
3. Enable `S&box Playermodel Wizard`.
4. Open the panel from `View3D > Sidebar > S&box`.

## Language

The panel supports `EN` and `CN`. Use the language selector at the top of the panel.

## Main Workflow

1. Initialize the work scene.
2. Pick `MMD` for PMX/PMD or `FBX` for direct FBX import.
3. Import the model.
4. Assign or detect bones.
5. Prepare shapekeys when needed.
6. Export the S&box FBX and VMDL.

## PMX / PMD

The PMX path is treated as the stable workflow. It still uses `mmd_tools` or CATS where available, then runs the same scene organization, armature assignment, bone mapping, shapekey cleanup, and export steps.

## FBX

FBX import is direct through Blender's FBX importer, then it enters the same post-import path as PMX:

- imported objects are moved to the `Input` collection;
- the imported armature is assigned automatically when possible;
- bone mapping is refreshed;
- export uses the same S&box preparation tools.

The only MMD-only step is the optional CATS/MMD preparation pass.

## First-Person Arms

The first-person arms workflow uses the official arms template as the reference skeleton, keeps arm vertices from the converted full-body model, retargets them to the template, and exports with FBX bone axes `Y/X` to match S&box first-person arms.

## Project Notes

See `docs/ARCHITECTURE.md` for the current module layout and migration rules.
See `docs/TROUBLESHOOTING.md` for common import/export problems.
