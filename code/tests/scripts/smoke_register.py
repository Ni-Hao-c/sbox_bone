import sys
from pathlib import Path

import bpy


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import sbox_playermodel_wizard


sbox_playermodel_wizard.register()
assert hasattr(bpy.types.Scene, "sbox_pm_wizard")
sbox_playermodel_wizard.unregister()
assert not hasattr(bpy.types.Scene, "sbox_pm_wizard")
print("sbox_playermodel_wizard register smoke ok")
