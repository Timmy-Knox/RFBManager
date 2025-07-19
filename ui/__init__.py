import bpy
from . import panels
from . import uilists

classes = (
    *panels.classes,
    *uilists.classes,
)

def register():
    for cls in classes: 
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): 
        bpy.utils.unregister_class(cls)