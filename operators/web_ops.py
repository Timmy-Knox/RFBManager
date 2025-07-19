import bpy
import os
import tempfile
import shutil
import webbrowser
import urllib.request
import urllib.parse
import hashlib
from bpy.props import StringProperty
from bpy.types import Operator
# Relative import of core
from ..core import get_active_board

class REFBOARD_OT_WebSearch(Operator):
    bl_idname = "refboard.web_search"
    bl_label = "Search Web"
    bl_description = "Search the selected web engine for the current query"
    bl_options = {'REGISTER'}
    search_engine: StringProperty(name="Engine")
    base_urls = {
        "Pinterest": "https://www.pinterest.com/search/pins/?q=",
        "Artstation": "https://www.artstation.com/search?sort_by=relevance&query=",
        "Google Images": "https://www.google.com/search?tbm=isch&q=",
    }
    @classmethod
    def poll(cls, context): return getattr(context.scene, "refboard_search_query", "") != ""
    def execute(self, context):
        query = context.scene.refboard_search_query
        if self.search_engine in self.base_urls:
            try:
                url = self.base_urls[self.search_engine] + urllib.parse.quote_plus(query)
                webbrowser.open(url)
                self.report({'INFO'}, f"Opening {self.search_engine} for '{query}'")
                return {'FINISHED'}
            except Exception as e: self.report({'ERROR'}, f"Browser error: {e}"); return {'CANCELLED'}
        self.report({'WARNING'}, f"Unknown engine: {self.search_engine}"); return {'CANCELLED'}

class REFBOARD_OT_AddPinFromURL(Operator):
    bl_idname = "refboard.add_pin_from_url"
    bl_label = "Add Pin from URL"
    bl_description = ( # Using parentheses for a multi-line string
        "Adds a pin using an image URL. "
        "IMPORTANT: Right-click the image on a webpage and choose 'Copy Image Link' or 'Copy Image Address' (not the browser's address bar URL). "
        "The URL should typically end with .jpg, .png, .gif, .webp, etc."
    )
    bl_options = {'REGISTER', 'UNDO'}
    @classmethod
    def poll(cls, context):
        board = get_active_board(context)
        url = getattr(context.scene, "refboard_image_url", "")
        return board is not None and url.startswith(("http://", "https://"))
    def execute(self, context):
        scene = context.scene; board = get_active_board(context)
        url = scene.refboard_image_url;
        if not board: self.report({'WARNING'}, "No board"); return {'CANCELLED'}
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="refboard_dl_")
            parsed = urllib.parse.urlparse(url); path = parsed.path
            orig_fname = os.path.basename(path) if path else "dl_img"
            _root, ext = os.path.splitext(orig_fname)
            if not ext: ext = ".tmp"
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            safe_name = "".join(c for c in _root if c.isalnum() or c in ('_', '-'))[:32]
            fname = f"refboard_{url_hash}_{safe_name}{ext}"
            fpath = os.path.join(temp_dir, fname); new_fpath = fpath
            self.report({'INFO'}, f"Downloading: {url} -> {fname}")
            headers = {'User-Agent': 'Mozilla/5.0'}; req = urllib.request.Request(url, headers=headers)
            ctype = ''
            with urllib.request.urlopen(req) as resp, open(fpath, 'wb') as out:
                ctype = resp.info().get('Content-Type', '').lower()
                if ext == ".tmp": # Guess extension
                    new_ext = ext
                    if ctype.startswith('image/jpeg') or ctype.startswith('image/jpg'): new_ext = ".jpg"
                    elif ctype.startswith('image/png'): new_ext = ".png"
                    elif ctype.startswith('image/gif'): new_ext = ".gif"
                    elif ctype.startswith('image/webp'): new_ext = ".webp"
                    if new_ext != ext:
                        new_fname = f"refboard_{url_hash}_{safe_name}{new_ext}"
                        new_fpath = os.path.join(temp_dir, new_fname); ext = new_ext
                shutil.copyfileobj(resp, out)
            if ext != ".tmp" and fpath != new_fpath: # Rename if ext guessed
                try: os.rename(fpath, new_fpath); self.report({'INFO'}, f"Renamed to: {new_fname}"); fpath = new_fpath
                except OSError as rn_err: self.report({'WARNING'}, f"Rename failed: {rn_err}.")
            if ctype and not ctype.startswith('image/'): raise ValueError(f"Not image (Type: {ctype})")
            self.report({'INFO'}, f"Loading: {os.path.basename(fpath)}")
            img = None
            try:
                img = bpy.data.images.load(fpath, check_existing=True); img.reload(); img.preview_ensure()
                try:
                    if not img.packed_file: img.pack(); self.report({'INFO'}, f"Packed '{img.name}'.")
                except RuntimeError as p_err: self.report({'WARNING'}, f"Pack fail: {p_err}.")
            except RuntimeError as l_err: raise ValueError(f"Load fail: {l_err}")
            if img is None: raise ValueError("Load result is None.")
            new_pin = board.pins.add(); new_pin.image = img; new_pin.name = img.name
            new_pin.pin_name = img.name; new_pin.external_link = url
            board.active_pin_index = len(board.pins) - 1; scene.refboard_image_url = ""
            self.report({'INFO'}, f"Added pin '{img.name}'.")
            if context.area: context.area.tag_redraw()
            return {'FINISHED'}
        except ValueError as ve: self.report({'ERROR'}, f"Add failed: {ve}"); return {'CANCELLED'}
        except urllib.error.URLError as ue: self.report({'ERROR'}, f"URL/Net error: {ue.reason}"); return {'CANCELLED'}
        except Exception as e: self.report({'ERROR'}, f"Unexpected error: {e}"); return {'CANCELLED'}
        finally:
            if temp_dir and os.path.exists(temp_dir):
                try: shutil.rmtree(temp_dir)
                except Exception as cl_err: self.report({'WARNING'}, f"Cleanup failed: {cl_err}")

# List of classes for registration by this module
classes = (
    REFBOARD_OT_WebSearch,
    REFBOARD_OT_AddPinFromURL,
)