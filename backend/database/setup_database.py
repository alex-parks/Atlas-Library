# backend/setup_database.py
import sqlite3
import json
import yaml
import os
from pathlib import Path


def setup_database():
    """Create database and migrate YAML data in one simple script"""

    print("🔧 Setting up Blacksmith Atlas Database...")

    # Create database directory
    db_dir = Path("backend/database")
    db_dir.mkdir(exist_ok=True)

    # Database file
    db_path = db_dir / "assets.db"

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("📊 Creating database tables...")

    # Create assets table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS assets
                   (
                       id
                       TEXT
                       PRIMARY
                       KEY,
                       name
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       asset_type
                       TEXT
                       DEFAULT
                       'geometry',
                       file_path
                       TEXT,
                       file_size
                       INTEGER
                       DEFAULT
                       0,
                       file_format
                       TEXT
                       DEFAULT
                       '.usd',
                       thumbnail_path
                       TEXT,
                       textures_path
                       TEXT,
                       artist
                       TEXT
                       DEFAULT
                       'Blacksmith Team',
                       status
                       TEXT
                       DEFAULT
                       'approved',
                       tags
                       TEXT
                       DEFAULT
                       '[]',
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')

    conn.commit()
    print("✅ Database tables created!")

    # Load and migrate YAML data
    yaml_path = Path("backend/assetlibrary/database/3DAssets.yaml")

    if yaml_path.exists():
        print("📦 Loading YAML data...")

        with open(yaml_path, 'r') as f:
            assets = yaml.safe_load(f)

        print(f"Found {len(assets)} assets in YAML")

        # Clear existing data
        cursor.execute('DELETE FROM assets')

        # Insert each asset
        for asset in assets:
            try:
                # Get file size
                file_size = 0
                usd_path = asset.get('usd_path', '')
                if usd_path and Path(usd_path).exists():
                    file_size = Path(usd_path).stat().st_size

                # Insert asset
                cursor.execute('''
                               INSERT INTO assets (id, name, description, asset_type, file_path,
                                                   file_size, file_format, thumbnail_path, textures_path,
                                                   artist, status, tags)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                               ''', (
                                   asset['id'],
                                   asset['name'],
                                   f"3D Asset: {asset['name']}",
                                   'geometry',
                                   usd_path,
                                   file_size,
                                   '.usd',
                                   asset.get('thumbnail_path', ''),
                                   asset.get('textures_path', ''),
                                   'Blacksmith Team',
                                   'approved',
                                   json.dumps(['3d', 'geometry', 'usd'])
                               ))

                print(f"✅ Added: {asset['name']} ({asset['id']})")

            except Exception as e:
                print(f"❌ Error adding {asset.get('name', 'Unknown')}: {e}")

        conn.commit()
        print("🎉 YAML data migrated successfully!")

    else:
        print("❌ YAML file not found, creating sample data...")

        # Create sample data
        sample_assets = [
            {
                'id': 'sample_001',
                'name': 'Sample Cube',
                'description': 'A sample 3D cube asset',
                'asset_type': 'geometry',
                'file_path': '/sample/cube.usd',
                'file_size': 1024000,
                'file_format': '.usd',
                'thumbnail_path': '',
                'textures_path': '',
                'artist': 'Sample Artist',
                'status': 'approved',
                'tags': json.dumps(['sample', '3d', 'cube'])
            }
        ]

        for asset in sample_assets:
            cursor.execute('''
                           INSERT INTO assets (id, name, description, asset_type, file_path,
                                               file_size, file_format, thumbnail_path, textures_path,
                                               artist, status, tags)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                           ''', (
                               asset['id'], asset['name'], asset['description'],
                               asset['asset_type'], asset['file_path'], asset['file_size'],
                               asset['file_format'], asset['thumbnail_path'], asset['textures_path'],
                               asset['artist'], asset['status'], asset['tags']
                           ))

    conn.commit()

    # Show stats
    cursor.execute('SELECT COUNT(*) FROM assets')
    count = cursor.fetchone()[0]

    cursor.execute('SELECT id, name FROM assets')
    assets_list = cursor.fetchall()

    print(f"\n📊 Database Setup Complete!")
    print(f"Total assets: {count}")
    print("Assets in database:")
    for asset_id, name in assets_list:
        print(f"  - {name} ({asset_id})")

    conn.close()

    print(f"\n💾 Database saved to: {db_path.absolute()}")
    return str(db_path)


if __name__ == "__main__":
    setup_database()