"""
Blacksmith Atlas Context Menu Hook
Place this file in: $HOUDINI_USER_PREF_DIR/scripts/python/nodegraphcontextmenus.py

This adds "Collapse to BL Atlas Asset" to the right-click context menu when nodes are selected.
"""

import hou

def createEventHandler():
    """Create the context menu event handler"""
    return BLAtlasContextMenu()

class BLAtlasContextMenu:
    """Handles context menu events for Blacksmith Atlas"""
    
    def __init__(self):
        self.menu_items = []
    
    def createContextMenu(self, uievent):
        """Called when context menu is created"""
        try:
            # Get the current editor and selection
            editor = uievent.editor
            if not editor:
                return
            
            # Check if we have selected nodes
            selected_nodes = hou.selectedNodes()
            if not selected_nodes:
                return
            
            # Only show menu if we have multiple nodes or specific node types
            if len(selected_nodes) >= 1:
                # Check if nodes are in the same context
                parent = selected_nodes[0].parent()
                all_same_parent = all(node.parent() == parent for node in selected_nodes)
                
                if all_same_parent:
                    # Add separator
                    separator = hou.ContextMenuItem("BLAtlas_sep", hou.contextMenuItemType.Separator)
                    uievent.addMenuItem(separator)
                    
                    # Add Blacksmith Atlas menu item
                    atlas_item = hou.ContextMenuItem(
                        "collapse_to_bl_atlas",
                        hou.contextMenuItemType.Normal,
                        "Collapse to BL Atlas Asset",
                        self.collapse_to_atlas_asset
                    )
                    atlas_item.setIcon("NETWORKS_subnet")  # Use subnet icon
                    uievent.addMenuItem(atlas_item)
                    
                    # Add submenu with Atlas tools
                    submenu = hou.ContextMenuItem("bl_atlas_submenu", hou.contextMenuItemType.SubMenu, "Blacksmith Atlas")
                    submenu.setIcon("NETWORKS_subnet")
                    
                    # Collapse item
                    collapse_item = hou.ContextMenuItem(
                        "collapse_to_atlas_detailed",
                        hou.contextMenuItemType.Normal, 
                        "Collapse to Atlas Asset",
                        self.collapse_to_atlas_asset
                    )
                    
                    # Info item
                    info_item = hou.ContextMenuItem(
                        "atlas_info",
                        hou.contextMenuItemType.Normal,
                        "About Atlas Assets",
                        self.show_atlas_info
                    )
                    
                    submenu.addMenuItem(collapse_item)
                    submenu.addMenuItem(info_item)
                    uievent.addMenuItem(submenu)
                    
        except Exception as e:
            print(f"❌ Context menu error: {e}")
    
    def collapse_to_atlas_asset(self, menu_item):
        """Handle collapse to Atlas Asset action"""
        try:
            # Import the collapse function from our HDA module
            import sys
            from pathlib import Path
            
            backend_path = Path("/net/dev/alex.parks/scm/int/Blacksmith-Atlas/backend")
            if str(backend_path) not in sys.path:
                sys.path.insert(0, str(backend_path))
            
            # Import and execute the collapse function from shelf tool
            from assetlibrary.houdini.tools.shelf_create_atlas_asset import main
            main()
            
        except Exception as e:
            print(f"❌ Collapse error: {e}")
            hou.ui.displayMessage(f"Error: {e}", severity=hou.severityType.Error)
    
    def show_atlas_info(self, menu_item):
        """Show information about Atlas Assets"""
        info_text = """🏭 BLACKSMITH ATLAS ASSETS

Template-based asset system using Houdini's native serialization.

WORKFLOW:
1. Select nodes (matnet, geometry, etc.)
2. Right-click → "Collapse to BL Atlas Asset"
3. Configure asset parameters
4. Export as template

BENEFITS:
• Perfect reconstruction using saveChildrenToFile()
• No complex JSON serialization
• Works with any Houdini nodes
• Future-proof and reliable

Location: /net/library/atlaslib/3D/Assets/"""
        
        hou.ui.displayMessage(info_text, title="Blacksmith Atlas Info")

# Register the event handler
def onCreateNodeGraphContextMenu(uievent):
    """Called when node graph context menu is created"""
    handler = BLAtlasContextMenu()
    handler.createContextMenu(uievent)

# Auto-register if imported
try:
    import hou
    print("🏭 Blacksmith Atlas context menu handler loaded")
except ImportError:
    pass
