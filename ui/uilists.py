import bpy
from bpy.types import UIList

class REFBOARD_UL_pins(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        board = data; pin = item
        name_filter = board.pin_filter.lower()
        tag_filter = board.tag_filter.lower()
        show = True
        if name_filter:
            p_name = pin.pin_name.lower() if pin.pin_name else ""
            p_note = pin.note.lower() if pin.note else ""
            if name_filter not in p_name and name_filter not in p_note: show = False
        if show and tag_filter:
            p_tags = pin.tags.lower()
            if tag_filter not in p_tags:
                pin_tags_set = {t.strip() for t in p_tags.split(',') if t.strip()}
                filter_tags_set = {t.strip() for t in tag_filter.split(',') if t.strip()}
                if not filter_tags_set.intersection(pin_tags_set): show = False
        if not show: return

        if pin.image:
            # Always try to show a preview if there is an image data-block
            if not pin.image.preview:
                pin.image.preview_ensure() # Request preview

            col = layout.column(align=True)
            # Add checkbox before the preview
            row_select = col.row(align=True)
            row_select.prop(pin, "is_selected", text="")
            # Add empty space to align with the preview if needed
            # row_select.label(text="") # Or use layout.split? For now, like this.

            if pin.image.preview: # If preview is available
                base_divisor = 100.0
                extra_scale_multiplier = 2.5 # Use a multiplier for size
                scale_factor = (board.thumbnail_size / base_divisor) * extra_scale_multiplier
                col.template_icon(pin.image.preview.icon_id, scale=scale_factor)
            else:
                # Placeholder if preview did NOT generate (but image exists)
                col.label(text="", icon='IMAGE_DATA')

            # Display pin name (custom or filename)
            col.alignment = 'CENTER'
            display_label = pin.pin_name if pin.pin_name else pin.image.name
            col.label(text=display_label)
        else:
            # If the pin has no associated image data-block at all
            col.label(text="Invalid Pin", icon='ERROR')

classes = (
    REFBOARD_UL_pins,
)