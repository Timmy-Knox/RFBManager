import bpy
import os
from bpy.props import StringProperty, CollectionProperty, EnumProperty
from bpy.types import Operator, OperatorFileListElement
# Relative import of core
from ..core import get_active_board

class REFBOARD_OT_AddPinFromFile(Operator):
    bl_idname = "refboard.add_pin_from_file"
    bl_label = "Add Pin From File"
    bl_options = {'REGISTER', 'UNDO'}
    filepath: StringProperty(subtype='FILE_PATH', options={'HIDDEN'})
    files: CollectionProperty(type=OperatorFileListElement, options={'HIDDEN'})
    directory: StringProperty(subtype='DIR_PATH', options={'HIDDEN'})
    @classmethod
    def poll(cls, context): return get_active_board(context) is not None
    def execute(self, context):
        board = get_active_board(context)
        if not board: self.report({'WARNING'}, "No board"); return {'CANCELLED'}
        num_added = 0
        if self.files:
            for file_elem in self.files:
                fpath = os.path.join(self.directory, file_elem.name)
                if os.path.exists(fpath) and os.path.isfile(fpath):
                    try:
                        img = bpy.data.images.load(fpath, check_existing=True); img.reload()
                        if any(pin.image == img for pin in board.pins):
                            self.report({'INFO'}, f"Skip duplicate: {img.name}"); continue
                        new_pin = board.pins.add(); new_pin.image = img
                        new_pin.name = img.name; new_pin.pin_name = img.name
                        if not img.preview: img.preview_ensure()
                        num_added += 1
                    except Exception as e: self.report({'ERROR'}, f"Load failed '{file_elem.name}': {e}")
            if num_added > 0: board.active_pin_index = len(board.pins) - 1
            return {'FINISHED'}
        self.report({'WARNING'}, "No files selected"); return {'CANCELLED'}
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self); return {'RUNNING_MODAL'}

class REFBOARD_OT_RemovePin(Operator):
    bl_idname = "refboard.remove_pin"
    bl_label = "Remove Active Pin"
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        board = get_active_board(context)
        return board and 0 <= board.active_pin_index < len(board.pins)
    def execute(self, context):
        board = get_active_board(context);
        if not board: return {'CANCELLED'}
        idx = board.active_pin_index
        if 0 <= idx < len(board.pins):
            board.pins.remove(idx)
            board.active_pin_index = min(max(0, idx - 1), len(board.pins) - 1)
            if not board.pins: board.active_pin_index = -1
        return {'FINISHED'}

class REFBOARD_OT_MovePin(Operator):
    bl_idname = "refboard.move_pin"
    bl_label = "Move Pin"
    bl_options = {'REGISTER', 'UNDO'}
    direction: EnumProperty(items=[('UP', "Up", ""), ('DOWN', "Down", "")], name="Direction", default='UP')
    @classmethod
    def poll(cls, context):
        board = get_active_board(context)
        return board and board.active_pin_index >= 0
    def execute(self, context):
        board = get_active_board(context);
        if not board: return {'CANCELLED'}
        old_idx = board.active_pin_index; count = len(board.pins)
        if self.direction == 'UP':
            if old_idx <= 0: return {'CANCELLED'}
            new_idx = old_idx - 1
        elif self.direction == 'DOWN':
            if old_idx >= count - 1: return {'CANCELLED'}
            new_idx = old_idx + 1
        else: return {'CANCELLED'}
        board.pins.move(old_idx, new_idx); board.active_pin_index = new_idx
        if context.area: context.area.tag_redraw()
        return {'FINISHED'}
class REFBOARD_OT_RemoveSelectedPins(Operator):
    """Removes all selected pins from the active board"""
    bl_idname = "refboard.remove_selected_pins"
    bl_label = "Remove Selected Pins"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Active if there is an active board and at least one pin
        board = get_active_board(context)
        return board and len(board.pins) > 0
        # It's difficult to check if *at least one* is selected using standard UIList means.
        # Therefore, for now, we just check if there is anything to delete.

    def execute(self, context):
        board = get_active_board(context)
        if not board: return {'CANCELLED'}

        # --- ACTUAL BATCH DELETION LOGIC ---
        indices_to_remove = []
        # Collect indices of all pins where is_selected == True
        for i, pin in enumerate(board.pins):
            if pin.is_selected:
                indices_to_remove.append(i)

        if not indices_to_remove:
             self.report({'INFO'}, "No pins marked for removal.")
             return {'CANCELLED'}

        removed_count = len(indices_to_remove) # Store the count for the report

        # Important: Delete from the end of the list so that indices do not shift
        indices_to_remove.sort(reverse=True)
        for index in indices_to_remove:
            # Logic for cleaning up linked data can be added here if necessary
            # pin_to_remove = board.pins[index]
            # if pin_to_remove.image and pin_to_remove.image.users <= 1:
            #     # Caution: Delete the image only if it is not used anywhere else?
            #     # bpy.data.images.remove(pin_to_remove.image, do_unlink=True)
            #     pass # For now, do not delete the Image data-block itself
            board.pins.remove(index) # Remove the pin itself (PropertyGroup) from the collection

        self.report({'INFO'}, f"Removed {removed_count} selected pin(s).")

        # After deletion, deselect the remaining pins (just in case)
        # and reset the active index
        for pin in board.pins:
            pin.is_selected = False
        board.active_pin_index = -1

        # Update UI
        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}
class REFBOARD_OT_SelectAllPins(Operator):
    """Selects all pins on the active board"""
    bl_idname = "refboard.select_all_pins"
    bl_label = "Select All Pins"
    bl_options = {'REGISTER', 'UNDO'} # Add UNDO

    select_mode: bpy.props.BoolProperty(name="Select", default=True)

    @classmethod
    def poll(cls, context):
        # Active if there is an active board and at least one pin
        board = get_active_board(context)
        return board and len(board.pins) > 0

    def execute(self, context):
        board = get_active_board(context)
        if not board: return {'CANCELLED'}

        selected_count = 0
        deselected_count = 0

        for pin in board.pins:
            if self.select_mode: # If "Select All" mode
                if not pin.is_selected: # Select only if not already selected
                    pin.is_selected = True
                    selected_count += 1
            else: # If "Deselect All" mode
                 if pin.is_selected: # Deselect only if it was selected
                    pin.is_selected = False
                    deselected_count += 1

        if self.select_mode:
            self.report({'INFO'}, f"Selected {selected_count} pin(s).")
        else:
            self.report({'INFO'}, f"Deselected {deselected_count} pin(s).")

        # Update UI to redraw checkboxes
        if context.area:
            context.area.tag_redraw()

        return {'FINISHED'}

# Note: Instead of creating a separate DeselectAll operator,
# we used the 'select_mode' BoolProperty in a single operator.
# This saves a bit of code. In the UI, we will call this operator
# with different values for select_mode.
# List of classes for registration by this module
classes = (
    REFBOARD_OT_AddPinFromFile,
    REFBOARD_OT_RemovePin,
    REFBOARD_OT_MovePin,
    REFBOARD_OT_RemoveSelectedPins,
    REFBOARD_OT_SelectAllPins,
)