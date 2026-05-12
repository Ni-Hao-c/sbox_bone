# Troubleshooting

## PMX Imports

- Enable `mmd_tools` or CATS before importing PMX/PMD.
- Keep `MMD` selected in the add-on panel.
- If the model imports but mapping is empty, assign the armature manually and run bone detection again.

## FBX Imports

- Keep `FBX` selected in the add-on panel.
- The add-on imports FBX directly, then uses the same scene organization and bone mapping flow as PMX.
- If the wrong armature is selected, choose the source armature manually before detecting bones.

## First-Person Arms Are Twisted In Game

Use the add-on's first-person arms export instead of a default Blender FBX export. The add-on exports first-person arms with bone axes `Y/X`, matching the official S&box first-person arms template.

The generated VMDL should use:

```text
models/first_person/first_person_arms_base.vanmgrph
```

## Mesh Disappears After Arms Generation

Check these first:

- the full-body model was converted before generating arms;
- the arm mesh still has usable vertex groups;
- the keep-weight threshold is not too high;
- the official first-person arms template FBX path is selected manually.

## Game Looks Different From Blender

Blender can display a skeleton that looks correct while the game interprets FBX bone axes differently. For first-person arms, verify against the official template FBX instead of relying only on the viewport.
