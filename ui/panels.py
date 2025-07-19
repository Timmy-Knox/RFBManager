import bpy
from bpy.types import Panel
# Relative imports
from ..core import get_active_board
from ..operators.board_ops import REFBOARD_OT_AddBoard, REFBOARD_OT_RemoveBoard, REFBOARD_OT_MoveBoard
from ..operators.pin_ops import REFBOARD_OT_AddPinFromFile, REFBOARD_OT_RemovePin, REFBOARD_OT_MovePin, REFBOARD_OT_SelectAllPins
from ..operators.web_ops import REFBOARD_OT_WebSearch, REFBOARD_OT_AddPinFromURL
from ..operators.placement_ops import REFBOARD_OT_PlacePinInView

class REFBOARD_PT_BasePanel(Panel):
    bl_idname = "REFBOARD_PT_base_panel"; bl_label = "RefBoard Base"
    bl_space_type = 'VIEW_3D'; bl_region_type = 'UI'
    bl_category = 'RefBoard'; bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context): pass

# --- HELP PANEL ---
class REFBOARD_PT_Help(REFBOARD_PT_BasePanel):
    bl_idname = "REFBOARD_PT_help"
    bl_label = "RefBoard Manager - Help & Quick Start" # Changed title
    bl_order = -1 # Set a low order to keep the panel at the top
    bl_options = {'DEFAULT_CLOSED'} # Collapsed by default

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        # --- Introduction ---
        col_intro = box.column()
        col_intro.label(text="Welcome to RefBoard Manager!", icon='INFO')
        col_intro.label(text="This addon helps you organize and use reference images directly in Blender.")
        col_intro.label(text="Tip: Hover your mouse over buttons and fields for detailed tooltips!")
        col_intro.separator()

        # --- Core Concepts ---
        col_concepts = box.column(align=True)
        col_concepts.label(text="Core Concepts:", icon='FUND')
        col_concepts.label(text=" • Board: A collection or album for your reference images (pins).")
        col_concepts.label(
            text=" • Pin: Represents a single reference image. You can add notes, tags, and web links to it.")
        col_concepts.separator()

        # --- Basic Workflow ---
        col_workflow = box.column(align=True)
        col_workflow.label(text="Basic Workflow:", icon='SEQUENCE')
        col_workflow.label(
            text=" 1. Boards Panel: Click '+' to add a new board, or select an existing one from the list.")
        col_workflow.label(text=" 2. Pins Panel (for the active board):")
        col_workflow.label(text="    • Click '+' (top-right of Pins section) to add images from your computer.",
                           icon='FILEBROWSER')
        col_workflow.label(
            text="    • Or, expand 'Web Tools' (at the bottom) to add images from URLs or search online.", icon='WORLD')
        col_workflow.label(
            text=" 3. Selecting Pins: Click the small checkbox that appears above a pin's preview to select it.")
        col_workflow.label(text="    Use 'Select All' / 'Select None' buttons for quick selection.")
        col_workflow.label(text=" 4. Placing Pins: With pins selected, click 'Place Selected in 3D'.")
        col_workflow.label(
            text="    Tip: After placing, press F9 to open the 'Redo Last' panel and adjust placement settings.")
        col_workflow.label(
            text=" 5. Pin Details: Click directly on a pin's preview in the grid to make it active (highlighted).")
        col_workflow.label(
            text="    Its details (name, notes, tags) will then appear in the 'Active Pin Properties' panel for editing.")
        col_workflow.separator()

        # --- Panel Overview ---
        col_panels = box.column(align=True)
        col_panels.label(text="Panel Overview:", icon='PANEL_CLOSE')
        col_panels.label(text=" • Boards: Manage your boards (add, select active, reorder `▲▼`, remove `-`).")
        col_panels.label(text=" • Pins: Manage pins for the active board.")
        col_panels.label(text="    Includes: adding `+`, filters, selection tools, thumbnail size, 3D placement,")
        col_panels.label(
            text="    pin reordering `▲▼`, removing selected `-`, removing active (highlighted) `X`, and Web Tools.")
        col_panels.label(text=" • Active Pin Properties: Edit details for the currently highlighted pin in the grid.")
        # col_panels.label(text=" • Help & Quick Start: This panel you are reading!")
        col_panels.separator()

        # --- Sharing Tips ---
        col_sharing = box.column(align=True)
        col_sharing.label(text="Sharing Projects with RefBoard Images:", icon='SHADERFX')
        col_sharing.label(text="To ensure images are included when sharing your .blend file:")
        col_sharing.label(text=" 1. Easiest: File > External Data > Pack Resources. (Makes .blend file larger).")
        col_sharing.label(text=" 2. Recommended: Organize images in folders near your .blend file.")
        col_sharing.label(text="    Then use File > External Data > Make Paths Relative.")
        col_sharing.label(text="    Send a ZIP archive with the .blend file AND the image folders.")

        op = col_sharing.operator("wm.url_open", text="Learn More (Blender Manual on Packed Data)", icon='URL')
        op.url = "https://docs.blender.org/manual/en/latest/files/blend/packed_data.html"

class REFBOARD_PT_Boards(REFBOARD_PT_BasePanel):
    bl_idname = "REFBOARD_PT_boards"; bl_label = "Boards"
    bl_order = 0; bl_options = set()
    def draw(self, context):
        layout = self.layout; scene = context.scene; row = layout.row(align=True)
        row.template_list("UI_UL_list", "boards_list", scene, "refboard_boards",
                          scene, "refboard_active_board_index", rows=3)
        col_btns = row.column(align=True)
        col_btns.operator(REFBOARD_OT_AddBoard.bl_idname, text="", icon='ADD')
        col_sub = col_btns.column(align=True)
        op_up = col_sub.operator(REFBOARD_OT_MoveBoard.bl_idname, text="", icon='TRIA_UP'); op_up.direction = 'UP'
        op_down = col_sub.operator(REFBOARD_OT_MoveBoard.bl_idname, text="", icon='TRIA_DOWN'); op_down.direction = 'DOWN'
        col_sub.operator(REFBOARD_OT_RemoveBoard.bl_idname, text="", icon='REMOVE')
        col_sub.enabled = scene.refboard_active_board_index >= 0 and len(scene.refboard_boards) > 0

class REFBOARD_PT_Pins(REFBOARD_PT_BasePanel):
    bl_idname = "REFBOARD_PT_pins"; bl_label = "Pins"; bl_order = 1
    @classmethod
    def poll(cls, context): return get_active_board(context) is not None
    def draw(self, context):
        layout = self.layout; board = get_active_board(context)
        if not board: layout.label(text="Select a board"); return
        layout.label(text=f"Active Board: {board.name}")
        main_row = layout.row()

        # Left column for filters, selection, and pin grid
        left_col = main_row.column(align=True)
        left_col.scale_x = 2.5 # Make the left column wider

        box_filt = left_col.box()
        # Filter by name/note
        row_name_filter = box_filt.row(align=True)
        row_name_filter.prop(board, "pin_filter", text="Name/Note Filter", icon='TEXT') # Add explicit text

        # Filter by tags
        row_tag_filter = box_filt.row(align=True)
        row_tag_filter.prop(board, "tag_filter", text="Tag Filter", icon='OUTLINER_OB_GROUP_INSTANCE')

        row_select_btns = box_filt.row(align=True)
        op_select = row_select_btns.operator(REFBOARD_OT_SelectAllPins.bl_idname, text="Select All")
        op_select.select_mode = True
        op_deselect = row_select_btns.operator(REFBOARD_OT_SelectAllPins.bl_idname, text="Select None")
        op_deselect.select_mode = False
        row_select_btns.enabled = len(board.pins) > 0

        row_size = box_filt.row(align=True)
        row_size.prop(board, "thumbnail_size", text="Size")

        # --- Placement button ---
        row_place = layout.row()
        # Button is active if there are selected pins (operator's poll will check this)
        row_place.operator(
            REFBOARD_OT_PlacePinInView.bl_idname,
            text="Place Selected in 3D",
            icon='IMAGE_REFERENCE'
        )
        # Add some space above if needed
        layout.separator() # Adds a small margin

        if board.pins:
            layout.template_list("REFBOARD_UL_pins", "", board, "pins",
                                 board, "active_pin_index", rows=5, type='GRID', columns=4)
        else: layout.label(text="No pins on this board.")

        # Right column for pin list management buttons
        right_col = main_row.column(align=True)
        right_col.scale_x = 1 # Make the right column narrower for compact buttons

        # Add "Manage Pins" title or just an icon
        # right_col.label(text="Manage:") # Can be added if needed

        op_add_pin = right_col.operator(REFBOARD_OT_AddPinFromFile.bl_idname, text="", icon='ADD')
        # op_add_pin.description = "Add new pin(s) from image files" # If a tooltip needs to be added

        # Button group for moving the active pin
        move_col = right_col.column(align=True)
        op_move_up = move_col.operator(REFBOARD_OT_MovePin.bl_idname, text="", icon='TRIA_UP')
        op_move_up.direction = 'UP'
        op_move_down = move_col.operator(REFBOARD_OT_MovePin.bl_idname, text="", icon='TRIA_DOWN')
        op_move_down.direction = 'DOWN'
        move_col.enabled = board.active_pin_index >= 0 and len(board.pins) > 1 # Active if there is something to move

        # Button to remove SELECTED pins
        op_remove_selected = right_col.operator("refboard.remove_selected_pins", text="", icon='REMOVE')
        # op_remove_selected.description = "Remove all pins marked as 'Selected'" # Tooltip
        # --- NEW BUTTON: Remove ACTIVE pin ---
        op_remove_active = right_col.operator(REFBOARD_OT_RemovePin.bl_idname, text="", icon='CANCEL') # or 'TRASH'

        # --- WEB TOOLS SECTION (remains at the bottom of the left column or the entire panel) ---
        layout.separator() # Separate from main pin controls

        # --- BUTTON TO TOGGLE WEB TOOLS ---
        scene = context.scene # Ensure scene exists
        row_toggle_web = layout.row()
        # Use icon depending on state
        icon_web = 'TRIA_DOWN' if scene.refboard_show_web_tools else 'TRIA_RIGHT'
        row_toggle_web.prop(scene, "refboard_show_web_tools", text="Web Tools", icon=icon_web, toggle=True, emboss=True)
        # emboss=True makes the button look like standard panel collapse buttons

        # --- CONDITIONAL DRAWING OF WEB TOOLS SECTION ---
        if scene.refboard_show_web_tools:
            web_tools_main_box = layout.box()
            # web_tools_main_box.label(text="Web Tools", icon='WORLD') # Title is already in the .prop() button

            box_s = web_tools_main_box.box()
            box_s.label(text="Search Online:")
            box_s.prop(scene, "refboard_search_query", text="")
            row_s = box_s.row(align=True)
            op = row_s.operator(REFBOARD_OT_WebSearch.bl_idname, text="Pinterest");
            op.search_engine = "Pinterest"
            op = row_s.operator(REFBOARD_OT_WebSearch.bl_idname, text="Artstation");
            op.search_engine = "Artstation"
            op = row_s.operator(REFBOARD_OT_WebSearch.bl_idname, text="Google");
            op.search_engine = "Google Images"

            box_a = web_tools_main_box.box()
            box_a.label(text="Add Image from URL:")
            box_a.prop(scene, "refboard_image_url", text="")
            row_a = box_a.row()
            row_a.operator(REFBOARD_OT_AddPinFromURL.bl_idname, icon='URL', text="Add Image")

class REFBOARD_PT_PinProperties(REFBOARD_PT_BasePanel):
    bl_idname = "REFBOARD_PT_pin_properties"; bl_label = "Active Pin Properties"; bl_order = 2; bl_options = {'DEFAULT_CLOSED'}
    @classmethod
    def poll(cls, context):
        board = get_active_board(context)
        return board and 0 <= board.active_pin_index < len(board.pins)
    def draw(self, context):
        layout = self.layout; board = get_active_board(context); pin = board.pins[board.active_pin_index]
        box = layout.box(); box.prop(pin, "pin_name", text="Pin Name")
        col_info = box.column(align=True); col_info.label(text="Image Info:")
        if pin.image:
            r = col_info.row(align=True); r.label(text="Data:"); r.label(text=pin.image.name)
            if pin.image.filepath and not pin.image.packed_file:
                r = col_info.row(align=True); r.label(text="Path:")
                r.prop(pin.image, "filepath", text="", emboss=False) # Display path as text
            elif pin.image.packed_file: r = col_info.row(align=True); r.label(text="Path:"); r.label(text="(Packed)")
            if pin.image.has_data:
                r = col_info.row(align=True); r.label(text="Size:")
                r.label(text=f"{pin.image.size[0]}x{pin.image.size[1]} px")
        else: col_info.label(text="No Image Data!", icon='ERROR')
        box.prop(pin, "note", text="Note")
        box.prop(pin, "external_link", text="Link")
        if pin.external_link:
            valid = pin.external_link.startswith(("http://", "https://"))
            r = box.row(); r.enabled = valid
            op = r.operator("wm.url_open", text="Open Link", icon='URL'); op.url = pin.external_link
            if not valid: r.label(text="Invalid URL", icon='ERROR')
        box.prop(pin, "tags", text="Tags")


classes = (
    REFBOARD_PT_Help,
    REFBOARD_PT_Boards,
    REFBOARD_PT_Pins,
    REFBOARD_PT_PinProperties,
)