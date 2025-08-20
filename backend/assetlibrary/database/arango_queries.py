# backend/assetlibrary/database/arango_queries.py
from arango import ArangoClient
from typing import List, Dict, Optional


class AssetQueries:
    def __init__(self, db_config: dict):
        client = ArangoClient(hosts=db_config['hosts'])
        self.db = client.db(
            db_config['database'],
            username=db_config['username'],
            password=db_config['password']
        )
        self.assets = self.db.collection('Atlas_Library')

    def search_assets(self, search_term: str = "", category: str = None, tags: List[str] = None) -> List[Dict]:
        """Search assets with filters"""
        query = """
        FOR asset IN Atlas_Library
            FILTER (@search == "" OR CONTAINS(LOWER(asset.name), LOWER(@search)) OR 
                   CONTAINS(LOWER(asset.description || ""), LOWER(@search)))
            FILTER (@category == null OR @category == "" OR asset.category == @category)
            FILTER (@tags == null OR LENGTH(@tags) == 0 OR LENGTH(INTERSECTION(asset.tags, @tags)) > 0)
            SORT asset.created_at DESC
            RETURN asset
        """

        bind_vars = {
            'search': search_term,
            'category': category if category else None,
            'tags': tags if tags else None
        }

        cursor = self.db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)

    def get_asset_with_dependencies(self, asset_id: str) -> Dict:
        """Get asset with all its dependencies"""
        query = """
        LET asset = DOCUMENT('Atlas_Library', @asset_id)
        LET textures = (
            FOR texture IN asset.dependencies.textures
                RETURN texture
        )
        RETURN {
            asset: asset,
            texture_count: LENGTH(textures),
            total_size: asset.file_sizes.usd + asset.file_sizes.thumbnail
        }
        """

        cursor = self.db.aql.execute(query, bind_vars={'asset_id': asset_id})
        return cursor.next()

    def get_assets_by_artist(self, artist: str) -> List[Dict]:
        """Get all assets created by a specific user"""
        query = """
        FOR asset IN Atlas_Library
            FILTER asset.metadata.created_by == @artist
            SORT asset.created_at DESC
            RETURN {
                id: asset._key,
                name: asset.name,
                category: asset.category,
                created_at: asset.created_at,
                thumbnail: asset.paths.thumbnail
            }
        """

        cursor = self.db.aql.execute(query, bind_vars={'artist': artist})
        return list(cursor)

    def get_recent_assets(self, limit: int = 10) -> List[Dict]:
        """Get most recent assets"""
        query = """
        FOR asset IN Atlas_Library
            SORT asset.created_at DESC
            LIMIT @limit
            RETURN asset
        """

        cursor = self.db.aql.execute(query, bind_vars={'limit': limit})
        return list(cursor)

    def get_asset_statistics(self) -> Dict:
        """Get statistics about the asset library"""
        query = """
        LET total_assets = LENGTH(Atlas_Library)
        LET by_category = (
            FOR asset IN Atlas_Library
                COLLECT category = asset.category WITH COUNT INTO count
                RETURN {category: category, count: count}
        )
        LET by_type = (
            FOR asset IN Atlas_Library
                COLLECT type = asset.asset_type WITH COUNT INTO count
                RETURN {type: type, count: count}
        )
        LET total_size = SUM(
            FOR asset IN Atlas_Library
                RETURN asset.file_sizes.usd + asset.file_sizes.thumbnail
        )
        LET recent_week = (
            FOR asset IN Atlas_Library
                FILTER DATE_DIFF(asset.created_at, DATE_NOW(), 'days') <= 7
                RETURN 1
        )

        RETURN {
            total_assets: total_assets,
            by_category: by_category,
            by_type: by_type,
            total_size_bytes: total_size,
            total_size_gb: total_size / 1073741824,
            assets_this_week: LENGTH(recent_week)
        }
        """

        cursor = self.db.aql.execute(query)
        return cursor.next()

    def find_duplicate_names(self) -> List[Dict]:
        """Find assets with duplicate names"""
        query = """
        FOR asset IN Atlas_Library
            COLLECT name = asset.name WITH COUNT INTO count
            FILTER count > 1
            LET duplicates = (
                FOR a IN Atlas_Library
                    FILTER a.name == name
                    RETURN {
                        id: a._key,
                        category: a.category,
                        created_at: a.created_at
                    }
            )
            RETURN {
                name: name,
                count: count,
                assets: duplicates
            }
        """

        cursor = self.db.aql.execute(query)
        return list(cursor)

    def update_asset_tags(self, asset_id: str, tags: List[str]) -> bool:
        """Update tags for an asset"""
        try:
            self.assets.update({'_key': asset_id, 'tags': tags})
            return True
        except Exception as e:
            print(f"Failed to update tags: {e}")
            return False


# Example usage:
if __name__ == "__main__":
    config = {
        'hosts': ['http://localhost:8529'],
        'database': 'blacksmith_atlas',
        'username': 'root',
        'password': ''
    }

    queries = AssetQueries(config)

    # Get statistics
    stats = queries.get_asset_statistics()
    print("Asset Library Statistics:")
    print(f"Total assets: {stats['total_assets']}")
    print(f"Total size: {stats['total_size_gb']:.2f} GB")

    # Search for assets
    results = queries.search_assets(search_term="pig", category="Characters")
    print(f"\nFound {len(results)} assets matching 'pig' in Characters category")