import bpy
from bpy.props import (
    StringProperty, IntProperty, FloatProperty, CollectionProperty,
    PointerProperty, BoolProperty, EnumProperty,
)

# --- Property Group for Pin ---
class RefBoardPin(bpy.types.PropertyGroup):
    image: PointerProperty(
        type=bpy.types.Image, description="The reference image data-block"
    )
    note: StringProperty(
        name="Note", default="", description="Optional text note"
    )
    pin_name: StringProperty(
        name="Pin Name", default="", description="Custom display name"
    )
    external_link: StringProperty(
        name="External Link", default="", description="URL associated with pin"
    )
    tags: StringProperty(
        name="Tags", default="", description="Comma-separated tags"
    )
    is_selected: BoolProperty(
        name="Selected",
        description="Mark this pin for batch operations",
        default=False
    )
# --- Property Group for Board ---
class RefBoardBoard(bpy.types.PropertyGroup):
    name: StringProperty(name="Board Name", default="New Board")
    pins: CollectionProperty(type=RefBoardPin)
    thumbnail_size: FloatProperty(
        name="Thumbnail Size", default=100.0, min=20, max=600, soft_max=256,
        subtype='PIXEL', description="Desired base size for thumbnails"
    )
    active_pin_index: IntProperty(default=-1)
    pin_filter: StringProperty(name="Name/Note Filter", default="")
    tag_filter: StringProperty(name="Tag Filter", default="")

# List of property classes
prop_classes = (
    RefBoardPin,
    RefBoardBoard,
)

# Scene Properties
scene_props = {
    'refboard_boards': CollectionProperty(type=RefBoardBoard),
    'refboard_active_board_index': IntProperty(name="Active Board Index", default=-1),
    'refboard_search_query': StringProperty(name="Search Query", default=""),
    'refboard_image_url': StringProperty(name="Image URL", default=""),
    'refboard_show_web_tools': BoolProperty( # <-- NEW PROPERTY
        name="Show Web Tools",
        description="Toggle visibility of the Web Tools section",
        default=False # Hidden by default
    ),
}

def register():
    for cls in prop_classes:
        bpy.utils.register_class(cls)
    for name, prop in scene_props.items():
        setattr(bpy.types.Scene, name, prop)

def unregister():
    for name in reversed(list(scene_props.keys())):
        if hasattr(bpy.types.Scene, name):
            delattr(bpy.types.Scene, name)
    for cls in reversed(prop_classes):
        bpy.utils.unregister_class(cls)