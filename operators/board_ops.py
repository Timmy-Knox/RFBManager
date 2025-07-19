import bpy
from bpy.props import EnumProperty
from bpy.types import Operator
# Relative import is not needed, as get_active_board is not used here.

class REFBOARD_OT_AddBoard(Operator):
    bl_idname = "refboard.add_board"
    bl_label = "Add Reference Board"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        scene = context.scene
        new_board = scene.refboard_boards.add()
        base_name = "Board"
        count = 1
        existing_names = {b.name for b in scene.refboard_boards}
        new_name = f"{base_name} {len(scene.refboard_boards)}"
        while new_name in existing_names:
            count += 1
            new_name = f"{base_name} {len(scene.refboard_boards) + count}"
        new_board.name = new_name
        scene.refboard_active_board_index = len(scene.refboard_boards) - 1
        return {'FINISHED'}

class REFBOARD_OT_RemoveBoard(Operator):
    bl_idname = "refboard.remove_board"
    bl_label = "Remove Active Board"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        return len(context.scene.refboard_boards) > 0 and context.scene.refboard_active_board_index >= 0
    def execute(self, context):
        scene = context.scene
        boards = scene.refboard_boards
        index = scene.refboard_active_board_index
        if 0 <= index < len(boards):
            boards.remove(index)
            scene.refboard_active_board_index = min(max(0, index - 1), len(boards) - 1)
            if not boards: scene.refboard_active_board_index = -1
        return {'FINISHED'}

class REFBOARD_OT_MoveBoard(Operator):
    bl_idname = "refboard.move_board"
    bl_label = "Move Board"
    bl_options = {'REGISTER', 'UNDO'}
    direction: EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")], name="Direction", default='UP')
    @classmethod
    def poll(cls, context):
        return context.scene.refboard_active_board_index >= 0
    def execute(self, context):
        scene = context.scene
        boards = scene.refboard_boards
        old_index = scene.refboard_active_board_index
        board_count = len(boards)
        if self.direction == 'UP':
            if old_index <= 0: return {'CANCELLED'}
            new_index = old_index - 1
        elif self.direction == 'DOWN':
            if old_index >= board_count - 1: return {'CANCELLED'}
            new_index = old_index + 1
        else: return {'CANCELLED'}
        boards.move(old_index, new_index)
        scene.refboard_active_board_index = new_index
        if context.area: context.area.tag_redraw()
        return {'FINISHED'}

# List of classes for registration by this module.
classes = (
    REFBOARD_OT_AddBoard,
    REFBOARD_OT_RemoveBoard,
    REFBOARD_OT_MoveBoard,
)
