"""
Atlas Clipboard System - Web-inspired copy/paste for Atlas assets

This system adapts HPasteWeb logic for the Atlas library filesystem:
- Atlas Copy: Export asset to library + generate copy string
- Atlas Paste: Parse copy string + import from library with path remapping

Key differences from HPasteWeb:
- Uses Atlas library filesystem instead of web storage
- Copy string format: "AtlasAsset_{AssetName}_{UID}!{encryption_key}"
- Templates stored in asset directories, not web services
- Automatic texture/geometry file remapping during paste
"""

import hou
import os
import json
import hashlib
import base64
import bz2
import tempfile
import re
import random
import string
from typing import Optional, List, Dict, Tuple

# Crypto support (optional like HPaste)
crypto_available = True
try:
    from Crypto.Cipher import AES
    from Crypto import Random as CRandom
except Exception:
    crypto_available = False
    AES = CRandom = None

# Import our existing Atlas system
try:
    from .houdiniae import TemplateAssetExporter, TemplateAssetImporter
except ImportError:
    # Fallback for testing
    import sys
    sys.path.append(os.path.dirname(__file__))
    from houdiniae import TemplateAssetExporter, TemplateAssetImporter


class AtlasClipboardError(Exception):
    """Base exception for Atlas clipboard operations"""
    pass


class AtlasAssetNotFoundError(AtlasClipboardError):
    """Asset not found in library"""
    def __init__(self, asset_identifier):
        self.asset_identifier = asset_identifier
        super().__init__(f"Atlas asset not found: {asset_identifier}")


class AtlasEncryptionError(AtlasClipboardError):
    """Encryption/decryption related errors"""
    pass


class AtlasClipboardCopy:
    """
    Atlas Copy functionality - exports asset to library and generates copy string
    
    Workflow:
    1. Export selected nodes to Atlas library (like create_atlas_asset)
    2. Save template file to {AssetPath}/templates/
    3. Generate copy string: "AtlasAsset_{AssetName}_{UID}!{key}"
    4. Copy string to clipboard
    """
    
    def __init__(self):
        self.library_root = "/net/library/atlaslib/3D/Assets"
        
    def generate_encryption_key(self) -> str:
        """Generate random encryption key like HPasteWeb"""
        if not crypto_available:
            return None
        return ''.join([random.choice(string.ascii_letters + string.digits) 
                       for _ in range(16)])  # 16-char key like HPaste
    
    def encrypt_data(self, data: bytes, key: str) -> bytes:
        """Encrypt data using AES-CBC like HPasteWeb"""
        if not crypto_available or key is None:
            return data
            
        rng = CRandom.new()
        iv = rng.read(AES.block_size)
        cipher = AES.new(key.encode('utf-8')[:16], AES.MODE_CBC, iv)
        
        # Pad data to block size
        pad_len = AES.block_size - (len(data) % AES.block_size)
        padded_data = data + bytes([pad_len] * pad_len)
        
        encrypted = cipher.encrypt(padded_data)
        return iv + encrypted  # Prepend IV
    
    def atlas_copy(self, nodes: List[hou.Node], 
                   asset_name: str,
                   subcategory: str = "Props",
                   use_encryption: bool = False) -> str:
        """
        Main Atlas Copy function
        
        Args:
            nodes: Selected Houdini nodes to copy
            asset_name: Name for the asset
            subcategory: Asset subcategory (Props, Environments, etc.)
            use_encryption: Whether to encrypt the template data
            
        Returns:
            Copy string for clipboard: "AtlasAsset_{AssetName}_{UID}!{key}"
        """
        if not nodes:
            raise AtlasClipboardError("No nodes provided for Atlas Copy")
        
        # Generate UID like existing Atlas system
        content_hash = hashlib.md5(asset_name.encode()).hexdigest()[:12].upper()
        uid = content_hash
        
        # Create asset directory structure
        asset_folder_name = f"{uid}_{asset_name}"
        asset_path = os.path.join(self.library_root, subcategory, asset_folder_name)
        templates_path = os.path.join(asset_path, "templates")
        
        # Ensure directories exist
        os.makedirs(templates_path, exist_ok=True)
        
        # Use existing TemplateAssetExporter for file processing
        exporter = TemplateAssetExporter()
        
        try:
            # Export asset using existing system (handles textures, geometry, etc.)
            export_result = exporter.export_as_template(
                nodes=nodes,
                asset_name=asset_name,
                subcategory=subcategory,
                export_path=asset_path
            )
            
            # Generate template file for clipboard system
            template_filename = f"{asset_name}_clipboard.hip"
            template_path = os.path.join(templates_path, template_filename)
            
            # Save nodes to template file
            parent = nodes[0].parent()
            parent.saveChildrenToFile(nodes, (), template_path)
            
            # Read template file for clipboard
            with open(template_path, 'rb') as f:
                template_data = f.read()
            
            # Generate encryption key if requested
            encryption_key = None
            if use_encryption:
                encryption_key = self.generate_encryption_key()
                if encryption_key:
                    template_data = self.encrypt_data(template_data, encryption_key)
            
            # Create metadata for clipboard
            metadata = {
                'asset_name': asset_name,
                'uid': uid,
                'subcategory': subcategory,
                'asset_path': asset_path,
                'template_filename': template_filename,
                'encrypted': use_encryption and encryption_key is not None,
                'node_count': len(nodes),
                'context': self._get_node_context(nodes[0]),
                'exported_files': export_result.get('copied_files', []),
                'checksum': hashlib.sha256(template_data).hexdigest()
            }
            
            # Save metadata
            metadata_path = os.path.join(templates_path, f"{asset_name}_clipboard.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Generate copy string
            copy_string = f"AtlasAsset_{asset_name}_{uid}"
            if encryption_key:
                copy_string += f"!{encryption_key}"
            
            return copy_string
            
        except Exception as e:
            raise AtlasClipboardError(f"Failed to create Atlas copy: {str(e)}")
    
    def _get_node_context(self, node: hou.Node) -> str:
        """Get node context like HPaste"""
        houver = hou.applicationVersion()
        if houver[0] >= 16:
            return node.parent().type().childTypeCategory().name()
        else:
            return node.parent().childTypeCategory().name()


class AtlasClipboardPaste:
    """
    Atlas Paste functionality - parses copy string and imports from library
    
    Workflow:
    1. Parse copy string: "AtlasAsset_{AssetName}_{UID}!{key}"
    2. Locate asset in library: /net/library/atlaslib/3D/Assets/{Subcategory}/{UID}_{AssetName}/
    3. Load template file with decryption if needed
    4. Import using existing TemplateAssetImporter with path remapping
    """
    
    def __init__(self):
        self.library_root = "/net/library/atlaslib/3D/Assets"
    
    def decrypt_data(self, data: bytes, key: str) -> bytes:
        """Decrypt data using AES-CBC like HPasteWeb"""
        if not crypto_available or key is None:
            return data
            
        if len(data) < AES.block_size:
            raise AtlasEncryptionError("Invalid encrypted data")
            
        iv = data[:AES.block_size]
        encrypted = data[AES.block_size:]
        
        cipher = AES.new(key.encode('utf-8')[:16], AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(encrypted)
        
        # Remove padding
        pad_len = decrypted[-1]
        return decrypted[:-pad_len]
    
    def parse_copy_string(self, copy_string: str) -> Tuple[str, str, str, Optional[str]]:
        """
        Parse Atlas copy string
        
        Args:
            copy_string: "AtlasAsset_{AssetName}_{UID}!{key}" or "AtlasAsset_{AssetName}_{UID}"
            
        Returns:
            (asset_name, uid, asset_identifier, encryption_key)
        """
        copy_string = copy_string.strip()
        
        # Extract encryption key if present
        encryption_key = None
        if '!' in copy_string:
            copy_string, encryption_key = copy_string.split('!', 1)
        
        # Validate format
        if not copy_string.startswith('AtlasAsset_'):
            raise AtlasClipboardError(f"Invalid Atlas copy string format: {copy_string}")
        
        # Parse asset identifier
        identifier = copy_string[11:]  # Remove "AtlasAsset_" prefix
        
        # Split into asset_name and uid
        # Format: {AssetName}_{UID}
        parts = identifier.rsplit('_', 1)
        if len(parts) != 2:
            raise AtlasClipboardError(f"Invalid asset identifier format: {identifier}")
        
        asset_name, uid = parts
        
        return asset_name, uid, identifier, encryption_key
    
    def find_asset_in_library(self, asset_name: str, uid: str) -> Tuple[str, str]:
        """
        Find asset in library filesystem
        
        Args:
            asset_name: Asset name
            uid: Asset UID
            
        Returns:
            (asset_path, subcategory)
        """
        folder_name = f"{uid}_{asset_name}"
        
        # Search through subcategories
        if not os.path.exists(self.library_root):
            raise AtlasAssetNotFoundError(f"Library root not found: {self.library_root}")
        
        for subcategory in os.listdir(self.library_root):
            subcategory_path = os.path.join(self.library_root, subcategory)
            if not os.path.isdir(subcategory_path):
                continue
                
            asset_path = os.path.join(subcategory_path, folder_name)
            if os.path.exists(asset_path):
                return asset_path, subcategory
        
        raise AtlasAssetNotFoundError(f"Asset not found in library: {folder_name}")
    
    def atlas_paste(self, copy_string: str, 
                    target_parent: Optional[hou.Node] = None,
                    network_editor: Optional[hou.NetworkEditor] = None) -> List[hou.Node]:
        """
        Main Atlas Paste function
        
        Args:
            copy_string: Atlas copy string from clipboard
            target_parent: Target parent node (auto-detect if None)
            network_editor: Network editor for positioning (auto-detect if None)
            
        Returns:
            List of created nodes
        """
        try:
            # Parse copy string
            asset_name, uid, identifier, encryption_key = self.parse_copy_string(copy_string)
            
            # Find asset in library
            asset_path, subcategory = self.find_asset_in_library(asset_name, uid)
            
            # Load metadata
            templates_path = os.path.join(asset_path, "templates")
            metadata_path = os.path.join(templates_path, f"{asset_name}_clipboard.json")
            
            if not os.path.exists(metadata_path):
                raise AtlasAssetNotFoundError(f"Clipboard metadata not found: {metadata_path}")
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Validate context if we have target parent
            if target_parent is None:
                target_parent, network_editor = self._auto_detect_target(metadata['context'])
            
            # Load template file
            template_path = os.path.join(templates_path, metadata['template_filename'])
            if not os.path.exists(template_path):
                raise AtlasAssetNotFoundError(f"Template file not found: {template_path}")
            
            # Handle encryption
            if metadata.get('encrypted', False):
                if not encryption_key:
                    raise AtlasEncryptionError("Asset is encrypted but no key provided")
                
                # Read encrypted template
                with open(template_path, 'rb') as f:
                    encrypted_data = f.read()
                
                # Decrypt to temporary file
                decrypted_data = self.decrypt_data(encrypted_data, encryption_key)
                
                # Verify checksum
                if hashlib.sha256(decrypted_data).hexdigest() != metadata['checksum']:
                    raise AtlasEncryptionError("Decryption failed - wrong key or corrupted data")
                
                # Write to temporary file for import
                fd, temp_template_path = tempfile.mkstemp(suffix='.hip')
                try:
                    with open(temp_template_path, 'wb') as f:
                        f.write(decrypted_data)
                    
                    # Import nodes
                    return self._import_template_with_remapping(
                        temp_template_path, asset_path, target_parent, network_editor, metadata
                    )
                finally:
                    os.close(fd)
                    if os.path.exists(temp_template_path):
                        os.unlink(temp_template_path)
            else:
                # Import unencrypted template directly
                return self._import_template_with_remapping(
                    template_path, asset_path, target_parent, network_editor, metadata
                )
                
        except Exception as e:
            if isinstance(e, AtlasClipboardError):
                raise
            else:
                raise AtlasClipboardError(f"Atlas paste failed: {str(e)}")
    
    def _auto_detect_target(self, expected_context: str) -> Tuple[hou.Node, Optional[hou.NetworkEditor]]:
        """Auto-detect target parent and network editor like HPaste"""
        # Find suitable network editor
        network_editors = [x for x in hou.ui.paneTabs() 
                          if x.type() == hou.paneTabType.NetworkEditor]
        
        # Prefer network editor with matching context
        matching_ne = None
        for ne in network_editors:
            current_context = self._get_node_context(ne.pwd())
            if current_context == expected_context:
                matching_ne = ne
                break
        
        if matching_ne is None and network_editors:
            matching_ne = network_editors[0]  # Fallback to first available
        
        if matching_ne:
            return matching_ne.pwd(), matching_ne
        else:
            raise AtlasClipboardError(f"No suitable network editor found for context: {expected_context}")
    
    def _get_node_context(self, node: hou.Node) -> str:
        """Get node context like HPaste"""
        houver = hou.applicationVersion()
        if houver[0] >= 16:
            return node.type().childTypeCategory().name()
        else:
            return node.childTypeCategory().name()
    
    def _import_template_with_remapping(self, template_path: str, 
                                       asset_path: str,
                                       target_parent: hou.Node,
                                       network_editor: Optional[hou.NetworkEditor],
                                       metadata: Dict) -> List[hou.Node]:
        """Import template file with automatic path remapping"""
        
        # Record existing items for comparison
        houver = hou.applicationVersion()
        if houver[0] >= 16:
            old_items = target_parent.allItems()
        else:
            old_items = target_parent.children()
        
        # Load template file
        target_parent.loadChildrenFromFile(template_path)
        
        # Find newly created items
        if houver[0] >= 16:
            new_items = [x for x in target_parent.allItems() if x not in old_items]
        else:
            new_items = [x for x in target_parent.children() if x not in old_items]
        
        new_nodes = [x for x in new_items if isinstance(x, hou.Node)]
        
        if not new_nodes:
            raise AtlasClipboardError("No nodes were created during paste")
        
        # Apply path remapping using existing Atlas system
        importer = TemplateAssetImporter()
        
        # Remap texture paths
        importer.remap_texture_paths(new_nodes, asset_path)
        
        # Remap geometry file paths
        importer.remap_geometry_paths(new_nodes, asset_path)
        
        # Position nodes at cursor if network editor available
        if network_editor:
            self._position_nodes_at_cursor(new_nodes, network_editor)
        
        print(f"Atlas Paste: Successfully imported {len(new_nodes)} nodes from {metadata['asset_name']}")
        
        return new_nodes
    
    def _position_nodes_at_cursor(self, nodes: List[hou.Node], network_editor: hou.NetworkEditor):
        """Position nodes at network editor cursor like HPaste"""
        if not nodes:
            return
        
        # Calculate current center
        current_center = hou.Vector2(0, 0)
        for node in nodes:
            current_center += node.position()
        current_center /= len(nodes)
        
        # Get target position
        target_position = network_editor.cursorPosition()
        
        # Calculate offset
        offset = target_position - current_center
        
        # Apply offset to all nodes
        for node in nodes:
            node.setPosition(node.position() + offset)


# Convenience functions for shelf buttons
def atlas_copy_selected(asset_name: str = None, 
                       subcategory: str = "Props",
                       use_encryption: bool = False) -> str:
    """
    Copy selected nodes to Atlas clipboard
    
    Args:
        asset_name: Asset name (auto-generate if None)
        subcategory: Asset subcategory
        use_encryption: Whether to encrypt the data
        
    Returns:
        Copy string for clipboard
    """
    nodes = hou.selectedNodes()
    if not nodes:
        raise AtlasClipboardError("No nodes selected for Atlas Copy")
    
    if asset_name is None:
        # Auto-generate asset name
        asset_name = f"ClipboardAsset_{len(nodes)}nodes"
    
    copier = AtlasClipboardCopy()
    copy_string = copier.atlas_copy(nodes, asset_name, subcategory, use_encryption)
    
    # Copy to clipboard
    hou.ui.copyTextToClipboard(copy_string)
    
    return copy_string


def atlas_paste_from_clipboard() -> List[hou.Node]:
    """
    Paste Atlas asset from clipboard
    
    Returns:
        List of created nodes
    """
    clipboard_text = hou.ui.getTextFromClipboard().strip()
    
    if not clipboard_text.startswith('AtlasAsset_'):
        raise AtlasClipboardError("Clipboard does not contain Atlas copy string")
    
    paster = AtlasClipboardPaste()
    return paster.atlas_paste(clipboard_text)


if __name__ == "__main__":
    # Test functions
    print("Atlas Clipboard System - Testing")
    
    # Test copy string parsing
    test_strings = [
        "AtlasAsset_Helicopter_DEA80B867493",
        "AtlasAsset_Helicopter_DEA80B867493!x9K2mP1s",
        "AtlasAsset_Complex_Asset_Name_ABC123DEF456!encryptionkey123"
    ]
    
    paster = AtlasClipboardPaste()
    for test_string in test_strings:
        try:
            asset_name, uid, identifier, key = paster.parse_copy_string(test_string)
            print(f"Parsed: {test_string}")
            print(f"  Asset: {asset_name}, UID: {uid}, Key: {key}")
        except Exception as e:
            print(f"Failed to parse {test_string}: {e}")
