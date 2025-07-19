import bpy

def get_active_board(context: bpy.types.Context) -> bpy.types.PropertyGroup | None:
    """
    Gets the currently active reference board from the scene.
    Returns the board PropertyGroup or None if no board is active or found.
    """
    scene = context.scene
    if not hasattr(scene, "refboard_boards") or not hasattr(scene, "refboard_active_board_index"):
        return None
    idx = scene.refboard_active_board_index
    if 0 <= idx < len(scene.refboard_boards):
        return scene.refboard_boards[idx]
    return None

