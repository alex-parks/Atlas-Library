from pathlib import Path
import yaml
import os
import uuid  # For unique ID generation

def talktohoudini(name):
    print(f"{name}")

class HoudiniAssetExporter:
    BASE_PATH = Path(r"C:\Users\alexh\Desktop\BlacksmithAtlas_Files\BlacksmithLibrary\3D\USD")
    CURRENT_DIR = Path(__file__).resolve().parent

    # Walk up to backend/
    PROJECT_ROOT = CURRENT_DIR.parent.parent  # => backend/
    YAML_FILE = PROJECT_ROOT / "assetlibrary/database/3DAssets.yaml"

    def __init__(self, name: str):
        self.name = name
        self.asset_id = self.generate_id()
        self.folder_name = f"{self.asset_id}_{self.name}"  # Prefixed folder
        self.asset_folder = self.BASE_PATH / self.folder_name
        self.usd_path = self.asset_folder / f"{name}.usd"
        self.textures_folder = self.asset_folder / "Linked_Textures"

        self.thumbnail_filename = f"{self.name}_{self.asset_id}_thumbnail.png"
        self.thumbnail_path = self.asset_folder / self.thumbnail_filename

    def generate_id(self) -> str:
        return uuid.uuid4().hex[:8]  # Shortened unique ID (8 characters)

    def write_metadata_to_yaml(self):
        yaml_path = self.YAML_FILE

        record = {
            "id": self.asset_id,
            "name": self.name,
            "folder": self.folder_name,
            "usd_path": str(self.usd_path),
            "thumbnail_path": str(self.asset_folder / "thumbnail.png"),
            "textures_path": str(self.textures_folder)
        }

        data = []

        # Try to load existing data
        if yaml_path.exists() and yaml_path.stat().st_size > 0:
            try:
                with open(yaml_path, "r") as f:
                    existing = yaml.safe_load(f)
                    if isinstance(existing, list):
                        data = existing
                    else:
                        print("⚠️ YAML file exists but is not a list. Starting fresh.")
            except Exception as e:
                print(f"⚠️ Failed to read YAML: {e}. Starting fresh.")

        # Append new record
        data.append(record)

        # Save back to YAML
        try:
            yaml_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure folder exists
            with open(yaml_path, "w") as f:
                yaml.dump(data, f, sort_keys=False)
            print(f"✅ Metadata written to {yaml_path}")
        except Exception as e:
            print(f"❌ Failed to write YAML: {e}")

    def create_folder_structure(self):
        try:
            self.asset_folder.mkdir(parents=True, exist_ok=False)
            self.textures_folder.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created folder: {self.asset_folder}")
            print(f"✅ Created textures folder: {self.textures_folder}")
            return True
        except FileExistsError:
            print(f"⚠️ Folder already exists: {self.asset_folder}")
            return False

    def export_usd(self, node):
        usd_node = node.node("Output_Component")
        if not usd_node:
            raise RuntimeError("❌ Could not find Output_Component node")

        parm = usd_node.parm("lopoutput")
        if not parm:
            raise RuntimeError("❌ 'lopoutput' parm not found")

        parm.set(str(self.usd_path))
        usd_node.parm("execute").pressButton()
        print(f"✅ Exported USD to {self.usd_path}")

    def render_thumbnail(self, node):
        rop = node.node("Thumbnail_BTY_ROP")
        cam = node.node("Thumbnail_BTY")

        if not rop or not cam:
            raise RuntimeError("❌ Missing ROP or Camera node in HDA")

        cam_parm = cam.parm("picture")
        if not cam_parm:
            raise RuntimeError("❌ 'picture' parameter not found on camera node")

        cam_parm.set(str(self.thumbnail_path))

        # Run the render
        execute_parm = rop.parm("execute") or rop.parm("render")  # Karma/OpenGL/Mantra difference
        if execute_parm:
            execute_parm.pressButton()
            print(f"✅ Rendered thumbnail to {self.asset_folder / 'thumbnail.png'}")
        else:
            raise RuntimeError("❌ ROP node does not have an 'execute' or 'render' parm")

    def save(self, node):
        print(f"💾 Saving asset '{self.name}' with ID {self.asset_id}...")
        if self.create_folder_structure():
            self.export_usd(node)
            self.render_thumbnail(node)
            self.write_metadata_to_yaml()

            print("✅ Save complete")
        else:
            print("❌ Save aborted (folder already exists)")

