import bpy
import mathutils
import os
import math
from bpy.props import EnumProperty, FloatProperty, IntProperty # Added IntProperty
from bpy.types import Operator
from math import radians, sqrt # Added sqrt for grid

# Relative import of core
from ..core import get_active_board

class REFBOARD_OT_PlacePinInView(Operator):
    """Places selected pin(s) as Empties in the 3D View""" # Updated description
    bl_idname = "refboard.place_pin_in_view"
    bl_label = "Place Selected Pin(s)" # Updated label
    bl_description = (  # For tooltip
        "Place all pins marked as 'Selected' into the 3D scene as Image Empties. "
        "After placing, press F9 to adjust settings (Distance, Size, Layout, etc.)"
    )
    bl_options = {'REGISTER', 'UNDO'}

    # --- Main placement mode ---
    placement_mode: EnumProperty(
        items=[
            ('VIEW', "Align to View", ""), ('CAMERA', "Align to Camera", ""),
            ('FRONT', "Front (Y-)", ""), ('SIDE', "Right (X+)", ""), ('TOP', "Top (Z-)", ""),
        ], name="Placement Mode", default='VIEW'
    )

    # --- NEW PROPERTIES FOR LAYOUT ---
    layout_mode: EnumProperty(
        items=[
            ('STACK_X', "Stack X", "Arrange images horizontally"),
            ('STACK_Y', "Stack Y", "Arrange images vertically"),
            ('STACK_Z', "Stack Z (Depth)", "Arrange images one behind the other"),
            ('GRID', "Grid", "Arrange images in a grid"),
        ],
        name="Layout Mode", default='STACK_X',
        description="How to arrange multiple selected images"
    )
    spacing: FloatProperty(
        name="Spacing", default=0.2, min=0.0, subtype='DISTANCE', unit='LENGTH',
        description="Distance between placed images"
    )
    grid_columns: IntProperty( # Used only for GRID mode
         name="Grid Columns", default=4, min=1,
         description="Number of columns for grid layout"
    )
    # --- END OF NEW PROPERTIES ---

    distance: FloatProperty(name="Distance", default=5.0)
    size: FloatProperty(name="Size", default=2.0, min=0.01)

    @classmethod
    def poll(cls, context):
        # Active if there is an active board and at least one pin with an image
        board = get_active_board(context)
        if not board or not board.pins: return False
        # Check if there is AT LEAST ONE selected pin with a working image
        return any(pin.is_selected and pin.image for pin in board.pins)

    def execute(self, context):
        board = get_active_board(context)
        if not board: return {'CANCELLED'}

        # --- Collect selected pins with valid images ---
        selected_pins = []
        for pin in board.pins:
            if pin.is_selected and pin.image:
                selected_pins.append(pin)

        if not selected_pins:
            self.report({'WARNING'}, "No valid pins selected for placement.")
            return {'CANCELLED'}

        num_pins = len(selected_pins)
        self.report({'INFO'}, f"Placing {num_pins} selected pin(s)...")

        # --- Create collection (if it doesn't exist yet) ---
        target_coll_name = "RefBoard Empties"
        target_coll = bpy.data.collections.get(target_coll_name)
        if not target_coll:
            target_coll = bpy.data.collections.new(target_coll_name)
            context.scene.collection.children.link(target_coll)

        # --- Basic calculations for orientation and base position ---
        # (These calculations are done once, they will be the same for all Empties)
        base_location = mathutils.Vector((0,0,0))
        base_rotation_euler = mathutils.Euler((0,0,0), 'XYZ')
        base_matrix = mathutils.Matrix.Identity(4) # Matrix for transforming offsets

        try: # Wrap calculations in try in case of context errors
            if self.placement_mode == 'VIEW':
                region=context.region; rv3d=context.region_data
                if not region or not rv3d: raise RuntimeError("No 3D View context")
                view_inv_matrix = rv3d.view_matrix.inverted()
                base_location = view_inv_matrix.translation + view_inv_matrix.to_quaternion() @ mathutils.Vector((0.0, 0.0, -self.distance))
                base_rotation_euler = view_inv_matrix.to_euler('XYZ')
                base_matrix = view_inv_matrix
            elif self.placement_mode == 'CAMERA':
                cam = context.scene.camera
                if not cam or cam.type != 'CAMERA': raise RuntimeError("No active camera")
                cm = cam.matrix_world; direction = cm.to_quaternion() @ mathutils.Vector((0.0, 0.0, -1.0))
                loc = cm.translation; base_location = loc + direction * self.distance; base_rotation_euler = cm.to_euler('XYZ')
                base_matrix = cm
            elif self.placement_mode == 'FRONT':
                 base_location = mathutils.Vector((0.0, -self.distance, 0.0)); base_rotation_euler = mathutils.Euler((radians(90), 0, 0), 'XYZ')
                 base_matrix = mathutils.Matrix.Rotation(radians(90), 4, 'X') @ mathutils.Matrix.Translation(base_location) # Approximate matrix
            elif self.placement_mode == 'SIDE':
                 base_location = mathutils.Vector((self.distance, 0.0, 0.0)); base_rotation_euler = mathutils.Euler((radians(90), 0, radians(90)), 'XYZ')
                 base_matrix = mathutils.Matrix.Rotation(radians(90), 4, 'Z') @ mathutils.Matrix.Rotation(radians(90), 4, 'X') @ mathutils.Matrix.Translation(base_location)
            elif self.placement_mode == 'TOP':
                 base_location = mathutils.Vector((0.0, 0.0, -self.distance)); base_rotation_euler = mathutils.Euler((0, 0, 0), 'XYZ')
                 base_matrix = mathutils.Matrix.Translation(base_location)
            else: raise RuntimeError(f"Mode '{self.placement_mode}' NI.")
        except RuntimeError as e:
            self.report({'ERROR'}, f"Failed to calculate base transform: {e}"); return {'CANCELLED'}

        # --- Store context ---
        active_obj_before = context.view_layer.objects.active
        current_mode_before = context.object.mode if context.object else 'OBJECT'
        if current_mode_before != 'OBJECT': bpy.ops.object.mode_set(mode='OBJECT')

        # --- Loop for creating and placing Empties ---
        created_empties = []
        for i, pin in enumerate(selected_pins):
            img = pin.image
            empty_obj = None
            try:
                # Create Empty
                bpy.ops.object.empty_add(type='IMAGE', align='WORLD', location=base_location) # Create at base point
                empty_obj = context.view_layer.objects.active
                if not empty_obj or empty_obj.type != 'EMPTY': raise RuntimeError("Failed Empty create.")
                empty_obj.data = img # "Working" assignment
                if not empty_obj.data: raise RuntimeError("Empty .data None after assign.")

                # Setup
                empty_obj.empty_display_size = self.size
                empty_obj.name = f"Ref_{pin.pin_name or img.name}" # Add index for uniqueness
                empty_obj.show_name = False

                # --- Calculate offset for layout ---
                offset = mathutils.Vector((0.0, 0.0, 0.0))
                item_size_with_spacing = self.size + self.spacing

                if self.layout_mode == 'STACK_X':
                    offset.x = (i - (num_pins - 1) / 2.0) * item_size_with_spacing
                elif self.layout_mode == 'STACK_Y':
                    offset.y = (i - (num_pins - 1) / 2.0) * item_size_with_spacing
                elif self.layout_mode == 'STACK_Z':
                     # Place along the Z-axis of the view/camera (or global Z for ortho)
                     offset.z = i * item_size_with_spacing # Without centering, just one after another
                elif self.layout_mode == 'GRID':
                    cols = max(1, self.grid_columns)
                    row_num = i // cols
                    col_num = i % cols
                    num_rows = math.ceil(num_pins / cols)
                    # Center the grid
                    offset.x = (col_num - (cols - 1) / 2.0) * item_size_with_spacing
                    offset.y = ((num_rows - 1) / 2.0 - row_num) * item_size_with_spacing # Y goes down

                # Apply offset relative to the view/camera/axis orientation
                # Convert local offset to global
                global_offset = base_matrix.to_quaternion() @ offset

                # Apply transformations
                empty_obj.location = base_location + global_offset
                empty_obj.rotation_euler = base_rotation_euler

                # Move to collection
                current_collections = [coll for coll in empty_obj.users_collection]
                for coll in current_collections: coll.objects.unlink(empty_obj)
                if target_coll_name not in empty_obj.users_collection: target_coll.objects.link(empty_obj)

                created_empties.append(empty_obj) # Add to the list of created ones

            except Exception as e_loop:
                self.report({'ERROR'}, f"Failed for pin '{pin.name}': {e_loop}")
                if empty_obj and empty_obj.name in bpy.data.objects: # Remove partially created one
                    bpy.data.objects.remove(empty_obj, do_unlink=True)
                # Continue with the next pin? Or interrupt? For now, continue.

        # --- Restore context and selection ---
        # Attempt to restore the original active object and mode
        if active_obj_before and active_obj_before.name in context.view_layer.objects:
            context.view_layer.objects.active = active_obj_before
            if context.object and context.object.mode != current_mode_before: # Check that there is an active object
                try:
                    bpy.ops.object.mode_set(mode=current_mode_before)
                except RuntimeError as mode_err:
                    print(f"INFO: Could not restore mode '{current_mode_before}': {mode_err}")
        # If restoration failed or there was no original, ensure we are in Object Mode if possible
        elif context.object and context.object.mode != 'OBJECT': # If there is an active object, but not in Object Mode
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                 pass # If it didn't work, there might be no active object to change the mode for
        elif not context.object and created_empties: # If there is no active object, but something was created, make the created one active
             if created_empties[-1] and created_empties[-1].name in context.view_layer.objects:
                context.view_layer.objects.active = created_empties[-1]
                # Now that there is an active object, we can try to switch mode if necessary
                if context.object.mode != 'OBJECT':
                    try: bpy.ops.object.mode_set(mode='OBJECT')
                    except RuntimeError: pass


        # Deselect all objects
        # Check if the operation can be performed
        if context.mode == 'OBJECT' and context.view_layer.objects.active:
            bpy.ops.object.select_all(action='DESELECT')
        else:
            # Alternative, lower-level method if poll() for select_all fails
            # This will work even if there is no active object, but we are in Object Mode
            # (but we must be in object mode)
            if context.mode != 'OBJECT': # If still not in Object Mode, try one last time
                # Check if there is any object at all to allow mode switching
                if context.selectable_objects: # Check if there are any selectable objects in the scene at all
                    if not context.view_layer.objects.active and context.selectable_objects:
                        # If there is no active object, but there are selectable ones, temporarily make one of them active
                        # This is a hack to change the mode.
                        temp_active = context.selectable_objects[0]
                        original_active_after_creations = context.view_layer.objects.active
                        context.view_layer.objects.active = temp_active
                        try:
                            bpy.ops.object.mode_set(mode='OBJECT')
                        except RuntimeError:
                             pass # Failed
                        context.view_layer.objects.active = original_active_after_creations # Restore
                    elif context.view_layer.objects.active: # If there is an active one
                        try:
                            bpy.ops.object.mode_set(mode='OBJECT')
                        except RuntimeError:
                            pass # Failed
            # Now deselect manually if we are in object mode
            if context.mode == 'OBJECT':
                for obj in context.selectable_objects:
                    obj.select_set(False)
            else:
                self.report({'WARNING'}, "Could not ensure Object Mode to deselect all. Selection might be inconsistent.")


        # Select the newly created Empties
        newly_selected_active = None
        for obj in created_empties:
            if obj and obj.name in context.view_layer.objects:
                obj.select_set(True)
                newly_selected_active = obj # The last selected one will become active

        # Make the last created and selected object active
        if newly_selected_active:
            context.view_layer.objects.active = newly_selected_active
        elif created_empties and created_empties[-1] and created_empties[-1].name in context.view_layer.objects:
            # If for some reason newly_selected_active was not set, but objects exist
            context.view_layer.objects.active = created_empties[-1]


        self.report({'INFO'}, f"Placed {len(created_empties)} pin(s).")
        return {'FINISHED'}

    # --- ADDED: invoke method to show properties dialog ---
    def invoke(self, context, event):
        # Call the standard dialog box to edit operator properties
        return context.window_manager.invoke_props_dialog(self)

    # --- ADDED: draw method for the dialog box ---
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "placement_mode")
        layout.prop(self, "layout_mode")
        layout.prop(self, "spacing")
        if self.layout_mode == 'GRID': # Show columns only for grid
             layout.prop(self, "grid_columns")
        layout.prop(self, "distance")
        layout.prop(self, "size")

# List of classes for registration by this module
classes = (
    REFBOARD_OT_PlacePinInView,
)