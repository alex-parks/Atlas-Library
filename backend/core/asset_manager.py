#backend / core / asset_manager.py
from typing import List, Optional, Dict, Any
import json
from pathlib import Path

from .assets import AssetObject, AssetType, ValidationResult
from .base_atlas_object import BaseAtlasObject


class SearchQuery:
    def __init__(self,
                 text: str = "",
                 asset_type: Optional[AssetType] = None,
                 tags: List[str] = None,
                 artist: str = "",
                 date_range: tuple = None):
        self.text = text
        self.asset_type = asset_type
        self.tags = tags or []
        self.artist = artist
        self.date_range = date_range


class AssetRegistry:
    """In-memory asset registry with JSON persistence"""

    def __init__(self, storage_path: str = "backend/data/asset_registry.json"):
        self.storage_path = Path(storage_path)
        self.assets: Dict[str, AssetObject] = {}
        self.load_registry()

    def load_registry(self):
        """Load assets from JSON file"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for asset_data in data.get('assets', []):
                        asset = self._deserialize_asset(asset_data)
                        if asset:
                            self.assets[asset.id] = asset
            except Exception as e:
                print(f"Error loading registry: {e}")

    def save_registry(self):
        """Save assets to JSON file"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "assets": [asset.to_dict() for asset in self.assets.values()],
            "last_updated": datetime.now().isoformat()
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _deserialize_asset(self, data: Dict[str, Any]) -> Optional[AssetObject]:
        """Recreate asset from dictionary data"""
        try:
            asset_type = AssetType(data['asset_type'])
            asset = AssetObject(
                name=data['name'],
                asset_type=asset_type,
                file_path=data['file_path']
            )
            asset.id = data['id']
            asset.asset_metadata.tags = data.get('tags', [])
            asset.asset_metadata.description = data.get('description', '')
            asset.asset_metadata.artist = data.get('artist', '')
            asset.preview_data.thumbnail_path = data.get('thumbnail_path')
            return asset
        except Exception as e:
            print(f"Error deserializing asset: {e}")
            return None

    def register(self, asset: AssetObject) -> str:
        """Register new asset"""
        self.assets[asset.id] = asset
        self.save_registry()
        return asset.id

    def get(self, asset_id: str) -> Optional[AssetObject]:
        """Get asset by ID"""
        return self.assets.get(asset_id)

    def update(self, asset_id: str, updates: Dict[str, Any]) -> bool:
        """Update asset"""
        if asset_id in self.assets:
            asset = self.assets[asset_id]
            asset.update_metadata(updates)
            self.save_registry()
            return True
        return False

    def delete(self, asset_id: str) -> bool:
        """Delete asset"""
        if asset_id in self.assets:
            del self.assets[asset_id]
            self.save_registry()
            return True
        return False

    def search(self, query: SearchQuery) -> List[AssetObject]:
        """Search assets"""
        results = []
        for asset in self.assets.values():
            if self._matches_query(asset, query):
                results.append(asset)
        return results

    def _matches_query(self, asset: AssetObject, query: SearchQuery) -> bool:
        """Check if asset matches search query"""
        # Text search in name and description
        if query.text:
            text_lower = query.text.lower()
            if (text_lower not in asset.name.lower() and
                    text_lower not in asset.asset_metadata.description.lower()):
                return False

        # Asset type filter
        if query.asset_type and asset.asset_type != query.asset_type:
            return False

        # Tags filter
        if query.tags:
            if not any(tag in asset.asset_metadata.tags for tag in query.tags):
                return False

        # Artist filter
        if query.artist:
            if query.artist.lower() not in asset.asset_metadata.artist.lower():
                return False

        return True


class AssetManager(BaseAtlasObject):
    """Main Asset Manager following design document architecture"""

    def __init__(self):
        super().__init__("AssetManager")
        self.asset_registry = AssetRegistry()

    def register_asset(self, asset: AssetObject) -> str:
        """Register new asset"""
        validation = asset.validate()
        if not validation.is_valid:
            raise ValueError(f"Invalid asset: {', '.join(validation.errors)}")

        return self.asset_registry.register(asset)

    def retrieve_asset(self, asset_id: str) -> Optional[AssetObject]:
        """Retrieve asset by ID"""
        return self.asset_registry.get(asset_id)

    def update_asset(self, asset_id: str, updates: Dict[str, Any]) -> bool:
        """Update asset"""
        return self.asset_registry.update(asset_id, updates)

    def delete_asset(self, asset_id: str) -> bool:
        """Delete asset"""
        return self.asset_registry.delete(asset_id)

    def search_assets(self, query: SearchQuery) -> List[AssetObject]:
        """Search assets"""
        return self.asset_registry.search(query)

    def get_all_assets(self) -> List[AssetObject]:
        """Get all assets"""
        return list(self.asset_registry.assets.values())

    def validate(self) -> bool:
        """Validate asset manager"""
        return True