bl_info = {
    "name": "RefBoard Manager (Modular)",
    "author": "Timmy Knox",
    "version": (2, 1, 0), # Updated version
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > RefBoard",
    "description": "Modular reference manager.",
    "category": "3D View",
    "doc_url": "",
    "tracker_url": "",
}

import bpy
# Import modules directly
from . import core
from . import properties
# Import all operator modules
from .operators import board_ops
from .operators import pin_ops
# from .operators import relink_ops # Removed
from .operators import web_ops
from .operators import placement_ops
# Import UI
from . import ui

# Collect ALL classes manually
classes_to_register = (
    *board_ops.classes,       # Classes from board_ops.py
    *pin_ops.classes,         # Classes from pin_ops.py
    # *relink_ops.classes,    # Removed
    *web_ops.classes,         # Classes from web_ops.py
    *placement_ops.classes,   # Classes from placement_ops.py
    *ui.classes,           # Classes from ui/__init__.py (panels & uilists)
)


# Ensure relative imports work
if "." not in __name__:
    from . import core
    from . import properties
    from . import operators
    from . import ui
else:
    import core
    import properties
    import operators
    import ui

# Order is important
modules_ordered = (
    properties,
    operators,
    ui,
)

def register():
    print("Registering RefBoard Manager (Manual Class List)...")
    # Register scene properties
    properties.register()
    # Register all other classes
    for cls in classes_to_register:
        # Add try-except just in case
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"ERROR: Failed to register class {cls.__name__}: {e}")

    print("RefBoard Manager registration complete.")

def unregister():
    print("Unregistering RefBoard Manager (Manual Class List)...")
    # Unregister all classes
    for cls in reversed(classes_to_register):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as e:
            print(f"ERROR: Failed to unregister class {cls.__name__}: {e}")
    # Unregister scene properties
    properties.unregister()
    print("RefBoard Manager unregistration complete.")


# For debugging: reload on script execution in Blender
if __name__ == "__main__":
    # Attempt to unregister before registering
    # This might not work perfectly without a full Blender restart
    # due to Python module caching
    try:
        unregister()
    except Exception as e:
        print(f"Unregister failed (likely first run): {e}")
        pass
    register()