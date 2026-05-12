from .bl_info import bl_info

if "runtime" in locals():
    import importlib

    runtime = importlib.reload(runtime)
else:
    from .core import runtime


def register():
    runtime.register()


def unregister():
    runtime.unregister()
