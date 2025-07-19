import bpy
from . import board_ops
from . import pin_ops
from . import web_ops

classes = (
    *board_ops.classes,
    *pin_ops.classes,
    *web_ops.classes,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)