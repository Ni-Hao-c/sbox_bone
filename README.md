# S&box Playermodel Wizard

Blender add-on for preparing MMD/FBX models for S&box Citizen-compatible export.

Blender 插件，用于将 MMD/FBX 模型转换为与 S&box Citizen 兼容的导出格式。

## Install — 安装

1. Zip or copy the `sbox_playermodel_wizard` folder.
   将 `sbox_playermodel_wizard` 文件夹打包为 zip 或直接复制。
2. In Blender: `Edit > Preferences > Add-ons > Install...`.
   在 Blender 中：`编辑 > 偏好设置 > 插件 > 安装...`。
3. Enable `S&box Playermodel Wizard`.
   启用 `S&box Playermodel Wizard`。
4. Open the panel from `View3D > Sidebar > S&box`.
   从 `3D视图 > 侧边栏 > S&box` 打开面板。

## Language — 语言

The panel supports `EN` and `CN`. Use the language selector at the top of the panel.

面板支持 `EN`（英文）和 `CN`（中文）。使用面板顶部的语言选择器切换。

## Main Workflow — 主要工作流程

1. Initialize the work scene. / 初始化工作场景。
2. Pick `MMD` for PMX/PMD or `FBX` for direct FBX import.
   选择 `MMD`（用于 PMX/PMD）或 `FBX`（直接导入 FBX）。
3. Import the model. / 导入模型。
4. Assign or detect bones. / 指定或检测骨骼。
5. Prepare shapekeys when needed. / 在需要时准备形态键。
6. Export the S&box FBX and VMDL. / 导出 S&box FBX 和 VMDL 文件。

## PMX / PMD

The PMX path is treated as the stable workflow. It still uses `mmd_tools` or CATS where available, then runs the same scene organization, armature assignment, bone mapping, shapekey cleanup, and export steps.

PMX 路径被视为稳定工作流程。它仍会使用 `mmd_tools` 或 CATS（如果可用），然后执行相同的场景整理、骨架指定、骨骼映射、形态键清理和导出步骤。

## FBX

FBX import is direct through Blender's FBX importer, then it enters the same post-import path as PMX:

FBX 通过 Blender 自带的 FBX 导入器直接导入，然后进入与 PMX 相同的导入后处理流程：

- imported objects are moved to the `Input` collection;
  导入的对象会被移动到 `Input`（输入）集合中；
- the imported armature is assigned automatically when possible;
  导入的骨架会在可能的情况下自动指定；
- bone mapping is refreshed;
  骨骼映射会被刷新；
- export uses the same S&box preparation tools.
  导出使用相同的 S&box 预处理工具。

The only MMD-only step is the optional CATS/MMD preparation pass.

唯一 MMD 专属的步骤是可选的 CATS/MMD 预处理阶段。

## First-Person Arms — 第一人称手臂

The first-person arms workflow uses the official arms template as the reference skeleton, keeps arm vertices from the converted full-body model, retargets them to the template, and exports with FBX bone axes `Y/X` to match S&box first-person arms.

第一人称手臂工作流程使用官方手臂模板作为参考骨架，从转换后的全身模型中保留手臂顶点，将其重定向到模板，并使用 FBX 骨骼轴向 `Y/X` 导出，以匹配 S&box 第一人称手臂。

## Project Notes — 项目说明

See `docs/ARCHITECTURE.md` for the current module layout and migration rules.
查看 `docs/ARCHITECTURE.md` 了解当前模块布局和迁移规则。

See `docs/TROUBLESHOOTING.md` for common import/export problems.
查看 `docs/TROUBLESHOOTING.md` 了解常见的导入/导出问题。
