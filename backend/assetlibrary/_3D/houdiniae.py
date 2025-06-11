from pathlib import Path
import yaml
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod


class BlacksmithAtlasConfig:
    """Configuration for Blacksmith Atlas"""
    # Base paths - Updated to match your actual structure
    BASE_PATH = Path(r"C:\Users\alexh\Desktop\BlacksmithAtlas_Files\AssetLibrary\3D")
    CURRENT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = CURRENT_DIR.parent.parent

    # Database paths
    DATABASE_PATH = PROJECT_ROOT / "assetlibrary/database"
    YAML_FILE = DATABASE_PATH / "3DAssets.yaml"
    JSON_FILE = DATABASE_PATH / "3DAssets.json"

    # Database settings
    DATABASE = {
        'type': 'json',  # Using JSON as shown in your logs
        'yaml_file': YAML_FILE,
        'json_file': JSON_FILE,
        'arango': {
            'hosts': ['http://localhost:8529'],
            'database': 'blacksmith_atlas',
            'username': 'root',
            'password': ''
        }
    }

    # Export settings
    EXPORT_FORMATS = {
        'usd': {'enabled': True, 'extension': '.usd'},
        'fbx': {'enabled': False, 'extension': '.fbx'},  # Disabled since it's failing
        'obj': {'enabled': False, 'extension': '.obj'}
    }

    # Asset categories - Fixed to be strings
    ASSET_CATEGORIES = [
        "Characters",
        "Props",
        "Environments",
        "Vehicles",
        "Effects",
        "General",
        "Test"
    ]


def talktohoudini(name):
    print(f"{name}")


# Database handlers remain the same
class DatabaseHandler(ABC):
    @abstractmethod
    def save_asset(self, asset_data: Dict) -> bool:
        pass

    @abstractmethod
    def load_assets(self) -> List[Dict]:
        pass


class YAMLDatabaseHandler(DatabaseHandler):
    def __init__(self, yaml_path: Path):
        self.yaml_path = yaml_path

    def save_asset(self, asset_data: Dict) -> bool:
        try:
            data = self.load_assets()
            data.append(asset_data)

            self.yaml_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.yaml_path, 'w') as f:
                yaml.dump(data, f, sort_keys=False)
            print(f"✅ Metadata written to {self.yaml_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to save to YAML: {e}")
            return False

    def load_assets(self) -> List[Dict]:
        if self.yaml_path.exists() and self.yaml_path.stat().st_size > 0:
            try:
                with open(self.yaml_path, 'r') as f:
                    data = yaml.safe_load(f)
                    return data if isinstance(data, list) else []
            except Exception as e:
                print(f"⚠️ Failed to read YAML: {e}")
        return []


class JSONDatabaseHandler(DatabaseHandler):
    def __init__(self, json_path: Path):
        self.json_path = json_path

    def save_asset(self, asset_data: Dict) -> bool:
        try:
            data = self.load_assets()
            data.append(asset_data)

            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.json_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Metadata written to {self.json_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to save to JSON: {e}")
            return False

    def load_assets(self) -> List[Dict]:
        if self.json_path.exists() and self.json_path.stat().st_size > 0:
            try:
                with open(self.json_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to read JSON: {e}")
        return []


# Add this to your houdiniae.py file after the JSONDatabaseHandler class

class ArangoDBHandler(DatabaseHandler):
    def __init__(self, config: Dict):
        try:
            from arango import ArangoClient
            self.client = ArangoClient(hosts=config['hosts'])
            self.db = self.client.db(
                config['database'],
                username=config['username'],
                password=config['password']
            )
            self.collection = self.db.collection('assets')
            self.edges = self.db.collection('asset_relationships')
            print("✅ Connected to ArangoDB")
        except ImportError:
            raise ImportError("python-arango not installed. Run: pip install python-arango")
        except Exception as e:
            print(f"❌ ArangoDB connection failed: {e}")
            raise

    def save_asset(self, asset_data: Dict) -> bool:
        try:
            # Prepare document for ArangoDB
            arango_doc = {
                '_key': asset_data['id'],
                'name': asset_data['name'],
                'category': asset_data['category'],
                'asset_type': '3D',
                'folder': asset_data.get('folder', ''),
                'paths': asset_data.get('paths', {}),
                'metadata': asset_data.get('metadata', {}),
                'file_sizes': asset_data.get('file_sizes', {}),
                'dependencies': asset_data.get('dependencies', {}),
                'tags': asset_data.get('tags', []),
                'created_at': asset_data.get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat(),
                'copied_files': asset_data.get('copied_files', [])
            }

            # Insert or update
            result = self.collection.insert(arango_doc, overwrite=True)
            print(f"✅ Asset saved to ArangoDB with key: {result['_key']}")

            # Also save to JSON as backup
            self._save_to_json_backup(asset_data)

            return True
        except Exception as e:
            print(f"❌ Failed to save to ArangoDB: {e}")
            return False

    def load_assets(self) -> List[Dict]:
        try:
            # AQL query to get all assets
            query = """
                FOR asset IN assets
                    SORT asset.created_at DESC
                    RETURN asset
            """
            cursor = self.db.aql.execute(query)
            return list(cursor)
        except Exception as e:
            print(f"⚠️ Failed to load from ArangoDB: {e}")
            return []

    def _save_to_json_backup(self, asset_data: Dict):
        """Save to JSON as backup"""
        try:
            json_path = Path(__file__).parent.parent.parent / "assetlibrary/database/3DAssets.json"

            # Load existing data
            if json_path.exists():
                with open(json_path, 'r') as f:
                    data = json.load(f)
            else:
                data = []

            # Update or append
            found = False
            for i, existing in enumerate(data):
                if existing.get('id') == asset_data['id']:
                    data[i] = asset_data
                    found = True
                    break

            if not found:
                data.append(asset_data)

            # Save back
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"⚠️ JSON backup failed: {e}")


# Then update the _create_db_handler method in HoudiniAssetExporter:
def _create_db_handler(self) -> DatabaseHandler:
    """Create appropriate database handler based on config"""
    db_type = self.config.DATABASE['type']

    if db_type == 'yaml':
        return YAMLDatabaseHandler(self.config.YAML_FILE)
    elif db_type == 'json':
        return JSONDatabaseHandler(self.config.JSON_FILE)
    elif db_type == 'arango':
        return ArangoDBHandler(self.config.DATABASE['arango'])
    else:
        raise ValueError(f"Unknown database type: {db_type}")


class HoudiniAssetExporter:
    def __init__(self, name: str, category: str = "General"):
        self.config = BlacksmithAtlasConfig()
        self.name = name

        # Fix category - if it's a number, convert to category name
        if isinstance(category, (int, str)) and str(category).isdigit():
            category_index = int(category)
            if 0 <= category_index < len(self.config.ASSET_CATEGORIES):
                self.category = self.config.ASSET_CATEGORIES[category_index]
            else:
                self.category = "General"
        else:
            self.category = category if category else "General"

        self.asset_id = self.generate_id()
        self.folder_name = f"{self.asset_id}_{self.name}"
        self.asset_folder = self.config.BASE_PATH / self.folder_name

        # Create subfolder paths
        self.usd_folder = self.asset_folder / "USD"
        self.usd_path = self.usd_folder / f"{name}.usd"
        self.textures_folder = self.asset_folder / "Linked_Textures"
        self.fbx_folder = self.asset_folder / "FBX"
        self.thumbnail_folder = self.asset_folder / "Thumbnail"

        self.thumbnail_filename = f"{self.name}_thumbnail.png"
        self.thumbnail_path = self.thumbnail_folder / self.thumbnail_filename

        # Initialize database handler
        self.db_handler = self._create_db_handler()

        # Track copied files
        self.copied_files = []

    def _create_db_handler(self) -> DatabaseHandler:
        """Create appropriate database handler based on config"""
        db_type = self.config.DATABASE['type']

        if db_type == 'yaml':
            return YAMLDatabaseHandler(self.config.YAML_FILE)
        elif db_type == 'json':
            return JSONDatabaseHandler(self.config.JSON_FILE)
        else:
            raise ValueError(f"Unknown database type: {db_type}")

    def generate_id(self) -> str:
        return uuid.uuid4().hex[:8]

    def collect_houdini_metadata(self, node) -> Dict[str, Any]:
        """Collect metadata from Houdini - Fixed version"""
        try:
            import hou

            metadata = {
                'houdini_version': hou.applicationVersionString(),
                'hip_file': hou.hipFile.path(),
                'node_path': node.path(),
                'node_type': node.type().name(),
                'export_time': datetime.now().isoformat(),
                'created_by': os.environ.get('USER', 'unknown')
            }

            # Get HDA-specific metadata
            hda_metadata = {}
            for parm in node.parms():
                try:
                    name = parm.name()
                    if name in ['nameinput', 'category', 'notes']:  # Add other relevant parms
                        hda_metadata[name] = parm.eval()
                except:
                    pass

            metadata['hda_parameters'] = hda_metadata

            # Collect texture dependencies
            metadata['dependencies'] = self.collect_dependencies(node)

            print("✅ Extracted HDA metadata")
            return metadata

        except Exception as e:
            print(f"⚠️ Failed to collect Houdini metadata: {e}")
            return {}

    def collect_dependencies(self, node) -> Dict[str, List[str]]:
        """Collect all dependencies - Fixed version"""
        dependencies = {
            'textures': [],
            'materials': [],
            'geometry': []
        }

        try:
            # Find texture references
            for child in node.allSubChildren():
                node_type = child.type().name()

                # Check for texture nodes
                if any(tex_type in node_type.lower() for tex_type in ['texture', 'image']):
                    for parm in child.parms():
                        if any(keyword in parm.name().lower() for keyword in ['file', 'texture', 'map']):
                            try:
                                path = parm.evalAsString()
                                if path and os.path.exists(path):
                                    dependencies['textures'].append({
                                        'path': path,
                                        'node': child.path(),
                                        'parameter': parm.name()
                                    })
                            except:
                                pass

                # Check for material references
                if 'material' in node_type.lower() or 'shader' in node_type.lower():
                    dependencies['materials'].append({
                        'node': child.path(),
                        'type': node_type
                    })

        except Exception as e:
            print(f"⚠️ Error collecting dependencies: {e}")

        return dependencies

    def copy_dependencies(self, dependencies: Dict[str, List[Dict]]) -> int:
        """Copy dependency files - Fixed version"""
        import shutil
        copied_count = 0

        try:
            # Copy textures
            for texture_info in dependencies.get('textures', []):
                src_path = texture_info.get('path')
                if src_path and os.path.exists(src_path):
                    filename = os.path.basename(src_path)
                    dst_path = self.textures_folder / filename

                    try:
                        shutil.copy2(src_path, dst_path)
                        self.copied_files.append(filename)
                        copied_count += 1
                        print(f"  ✅ Copied: {filename}")
                    except Exception as e:
                        print(f"  ⚠️ Failed to copy {filename}: {e}")

        except Exception as e:
            print(f"⚠️ Dependency copying failed: {e}")

        return copied_count

    def create_folder_structure(self):
        """Create the folder structure for the asset"""
        try:
            print(f"📁 Target folder: {self.asset_folder}")

            # Create main folder
            self.asset_folder.mkdir(parents=True, exist_ok=False)
            print(f"✅ Created folder: {self.asset_folder}")

            # Create subfolders
            for folder in [self.usd_folder, self.textures_folder, self.fbx_folder, self.thumbnail_folder]:
                folder.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created folder: {folder}")

            return True

        except FileExistsError:
            print(f"⚠️ Folder already exists: {self.asset_folder}")
            return False
        except Exception as e:
            print(f"❌ Failed to create folders: {e}")
            return False

    def export_usd(self, node):
        """Export the USD file"""
        usd_node = node.node("Output_Component")
        if not usd_node:
            raise RuntimeError("❌ Could not find Output_Component node")

        parm = usd_node.parm("lopoutput")
        if not parm:
            raise RuntimeError("❌ 'lopoutput' parm not found")

        parm.set(str(self.usd_path))
        usd_node.parm("execute").pressButton()
        print(f"✅ Exported USD to {self.usd_path}")

    def export_fbx(self, node):
        """Export FBX if enabled and node exists"""
        if not self.config.EXPORT_FORMATS['fbx']['enabled']:
            return

        fbx_node = node.node("FBX_Export")  # Adjust node name as needed
        if fbx_node:
            try:
                output_parm = fbx_node.parm("sopoutput") or fbx_node.parm("file")
                if output_parm:
                    fbx_path = self.fbx_folder / f"{self.name}.fbx"
                    output_parm.set(str(fbx_path))

                    execute_parm = fbx_node.parm("execute")
                    if execute_parm:
                        execute_parm.pressButton()
                        print(f"✅ Exported FBX to {fbx_path}")
                else:
                    print("⚠️ FBX node has no output parameter")
            except Exception as e:
                print(f"⚠️ FBX export failed: {e}")
        else:
            print("⚠️ No FBX export node found")

    def render_thumbnail(self, node):
        """Render thumbnail for the asset or use custom thumbnail"""
        # Make sure thumbnail folder exists
        self.thumbnail_folder.mkdir(parents=True, exist_ok=True)

        # Check if custom thumbnail is enabled
        custom_toggle = node.parm("customthumbtoggle")
        custom_path_parm = node.parm("customthumbnail")

        # Debug prints
        print(f"🔍 Custom toggle value: {custom_toggle.eval() if custom_toggle else 'No toggle param'}")
        print(f"🔍 Custom path value: {custom_path_parm.eval() if custom_path_parm else 'No path param'}")

        if custom_toggle and custom_path_parm and custom_toggle.eval() == 1:
            # Use custom thumbnail
            custom_path = custom_path_parm.eval()

            if custom_path and os.path.exists(custom_path):
                print(f"📸 Using custom thumbnail: {custom_path}")

                # Copy the custom thumbnail to our thumbnail folder
                import shutil
                try:
                    shutil.copy2(custom_path, self.thumbnail_path)
                    print(f"✅ Copied custom thumbnail to: {self.thumbnail_path}")
                    # IMPORTANT: Return here to skip rendering
                    return
                except Exception as e:
                    print(f"⚠️ Failed to copy custom thumbnail: {e}")
                    print("   Falling back to render...")
            else:
                print(f"⚠️ Custom thumbnail path invalid or doesn't exist: {custom_path}")
                print("   Falling back to render...")
        else:
            print("📸 Custom thumbnail not enabled, will render normally")

        # If we get here, either custom is disabled or failed, so render normally
        # Get both nodes - settings and ROP
        rop = node.node("Thumbnail_BTY_ROP")
        karma_settings = node.node("Thumbnail_BTY")

        if not rop:
            print("⚠️ Thumbnail_BTY_ROP not found")
            return
        if not karma_settings:
            print("⚠️ Thumbnail_BTY not found")
            return

        try:
            # Simple direct set - just like the test that worked
            karma_settings.parm("picture").set(str(self.thumbnail_path))
            print(f"📸 Set thumbnail render path to: {self.thumbnail_path}")

            # Execute render
            execute_parm = rop.parm("execute")
            if execute_parm:
                print("🎬 Executing render...")
                execute_parm.pressButton()

                # Check if file was created
                import time
                time.sleep(1)

                if self.thumbnail_path.exists():
                    print(f"✅ Rendered thumbnail to {self.thumbnail_path}")
                else:
                    print(f"⚠️ Thumbnail not found at: {self.thumbnail_path}")

        except Exception as e:
            print(f"⚠️ Thumbnail render failed: {e}")
            import traceback
            traceback.print_exc()

    def prepare_document(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare document for database"""
        # Calculate file sizes
        file_sizes = {}
        if self.usd_path.exists():
            file_sizes['usd'] = os.path.getsize(self.usd_path)
        if self.thumbnail_path.exists():
            file_sizes['thumbnail'] = os.path.getsize(self.thumbnail_path)

        return {
            'id': self.asset_id,
            'name': self.name,
            'category': self.category,
            'folder': self.folder_name,
            'paths': {
                'usd': str(self.usd_path),
                'thumbnail': str(self.thumbnail_path),
                'textures': str(self.textures_folder),
                'fbx': str(self.fbx_folder / f"{self.name}.fbx") if self.config.EXPORT_FORMATS['fbx'][
                    'enabled'] else None
            },
            'metadata': metadata,
            'file_sizes': file_sizes,
            'dependencies': metadata.get('dependencies', {}),
            'created_at': datetime.now().isoformat(),
            'copied_files': self.copied_files
        }

    def save(self, node) -> bool:
        """Main save function"""
        print(f"💾 Saving asset '{self.name}' with ID {self.asset_id}...")

        try:
            # Create folder structure
            if not self.create_folder_structure():
                return False

            # Collect metadata first
            metadata = self.collect_houdini_metadata(node)

            # Export USD
            self.export_usd(node)

            # Copy dependencies
            if 'dependencies' in metadata:
                copied_count = self.copy_dependencies(metadata['dependencies'])
            else:
                copied_count = 0

            # Export FBX if enabled
            self.export_fbx(node)

            # Render thumbnail
            self.render_thumbnail(node)

            # Prepare and save document
            document = self.prepare_document(metadata)
            if self.db_handler.save_asset(document):
                print("✅ Asset save completed successfully!")
                print(f"📂 Asset saved to: {self.asset_folder}")
                print(f"🗄️ Database updated with asset ID: {self.asset_id}")
                print(f"📁 Files copied: {copied_count}")
                return True
            else:
                print("❌ Failed to save metadata")
                return False

        except Exception as e:
            print(f"❌ Save failed: {e}")
            import traceback
            traceback.print_exc()
            return False