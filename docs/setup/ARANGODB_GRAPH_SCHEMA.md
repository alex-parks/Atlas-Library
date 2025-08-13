# ArangoDB Graph Schema for Blacksmith Atlas

## Overview
ArangoDB's multi-model approach allows us to store documents while creating powerful graph relationships. Here's how to structure metadata to leverage ArangoDB's parsing and relationship tools.

## Collections (Document Storage)

### Core Collections

#### `assets` (Documents)
Primary asset documents with rich metadata
```json
{
  "_key": "C0D6B8F1",
  "_id": "assets/C0D6B8F1",
  "name": "MyAtlasAsset",
  "category": "Props",
  "subcategory": "Vehicles",
  "description": "Atlas asset: MyAtlasAsset",
  "created_at": "2025-08-11T15:11:04.486961",
  "created_by": "alex.parks",
  "houdini_version": "20.5.445",
  "export_method": "template_based",
  "node_summary": {
    "total_nodes": 2,
    "node_types": { "matnet": 1, "geo": 1 }
  },
  "search_keywords": ["helicopter", "vehicle", "props"],
  "library_path": "/net/library/atlaslib/3D/Assets/Props/C0D6B8F1_MyAtlasAsset",
  "status": "published",
  "version": "1.0",
  "complexity_score": 7,
  "tags": ["helicopter", "vehicle", "military"]
}
```

#### `textures` (Documents)
Individual texture documents for granular relationships
```json
{
  "_key": "helicopter_BaseColor_1001",
  "_id": "textures/helicopter_BaseColor_1001",
  "filename": "helicopter_BaseColor.1001.png",
  "file_path": "Textures/Body/helicopter_BaseColor.1001.png",
  "texture_type": "BaseColor",
  "resolution": "2048x2048",
  "format": "PNG",
  "size_bytes": 4194304,
  "udim_tile": "1001",
  "is_udim_sequence": true,
  "color_space": "sRGB",
  "created_at": "2025-08-11T15:11:04.486961",
  "checksum": "sha256:abc123...",
  "usage_count": 3
}
```

#### `materials` (Documents)
Material network documents
```json
{
  "_key": "helicopter_body_material",
  "_id": "materials/helicopter_body_material",
  "material_name": "Body",
  "material_type": "principled_shader",
  "node_path": "/obj/MyAtlasAsset/Helicopter_MatNet/Body",
  "parameters": {
    "basecolor": [0.8, 0.8, 0.8],
    "roughness": 0.4,
    "metallic": 0.0
  },
  "shader_type": "redshift",
  "complexity": "medium",
  "created_at": "2025-08-11T15:11:04.486961"
}
```

#### `geometry` (Documents)
Geometry file documents
```json
{
  "_key": "helicopter_body_geo",
  "_id": "geometry/helicopter_body_geo",
  "filename": "Helicopter_modeling_helicopter_v007.abc",
  "file_path": "Geometry/Alembic/Helicopter_modeling_helicopter_v007.abc",
  "file_type": "Alembic",
  "polygon_count": 45670,
  "vertex_count": 23445,
  "has_uvs": true,
  "has_normals": true,
  "bounding_box": {
    "min": [-2.5, 0.0, -8.1],
    "max": [2.5, 3.2, 8.1]
  },
  "size_bytes": 2457600,
  "version": "v007",
  "created_at": "2025-08-11T15:11:04.486961"
}
```

#### `projects` (Documents)
Project context documents
```json
{
  "_key": "under_armour_7v7",
  "_id": "projects/under_armour_7v7",
  "project_name": "Under Armour 7v7",
  "client": "Under Armour",
  "start_date": "2025-01-03",
  "status": "active",
  "lead_artist": "alex.parks",
  "budget": 50000,
  "deadline": "2025-03-15"
}
```

#### `users` (Documents)
User/artist documents
```json
{
  "_key": "alex_parks",
  "_id": "users/alex_parks",
  "username": "alex.parks",
  "full_name": "Alex Parks",
  "email": "alex.parks@studio.com",
  "role": "senior_artist",
  "department": "3D",
  "specialties": ["modeling", "lookdev", "houdini"],
  "active": true
}
```

## Edge Collections (Relationships)

### `asset_uses_texture` (Asset → Texture relationships)
```json
{
  "_from": "assets/C0D6B8F1",
  "_to": "textures/helicopter_BaseColor_1001",
  "usage_type": "basecolor",
  "node_path": "/obj/MyAtlasAsset/Helicopter_MatNet/Body/BC",
  "parameter": "tex0",
  "uv_channel": 0,
  "tiling": [1.0, 1.0],
  "offset": [0.0, 0.0],
  "importance": "primary"
}
```

### `asset_has_material` (Asset → Material relationships)
```json
{
  "_from": "assets/C0D6B8F1",
  "_to": "materials/helicopter_body_material",
  "material_assignment": "Body",
  "primitive_group": "body_geo",
  "override_parameters": {
    "roughness": 0.6
  }
}
```

### `material_uses_texture` (Material → Texture relationships)
```json
{
  "_from": "materials/helicopter_body_material",
  "_to": "textures/helicopter_BaseColor_1001",
  "channel": "basecolor",
  "blend_mode": "multiply",
  "influence": 1.0
}
```

### `asset_uses_geometry` (Asset → Geometry relationships)
```json
{
  "_from": "assets/C0D6B8F1",
  "_to": "geometry/helicopter_body_geo",
  "transform": {
    "translate": [0, 0, 0],
    "rotate": [0, 0, 0],
    "scale": [1, 1, 1]
  },
  "visibility": true,
  "lod_level": 0
}
```

### `asset_depends_on` (Asset → Asset dependencies)
```json
{
  "_from": "assets/helicopter_scene",
  "_to": "assets/C0D6B8F1",
  "dependency_type": "reference",
  "required": true,
  "load_priority": 1
}
```

### `project_contains_asset` (Project → Asset relationships)
```json
{
  "_from": "projects/under_armour_7v7",
  "_to": "assets/C0D6B8F1",
  "usage_context": "hero_vehicle",
  "shot_list": ["sh010", "sh020", "sh035"],
  "approval_status": "approved",
  "notes": "Primary hero helicopter for chase sequence"
}
```

### `user_created_asset` (User → Asset relationships)
```json
{
  "_from": "users/alex_parks",
  "_to": "assets/C0D6B8F1",
  "role": "creator",
  "created_at": "2025-08-11T15:11:04.486961",
  "hours_spent": 24.5,
  "contribution_type": "full_creation"
}
```

## Graph Queries (AQL Examples)

### Find all textures used by an asset
```aql
FOR asset IN assets
  FILTER asset._key == "C0D6B8F1"
  FOR texture IN OUTBOUND asset asset_uses_texture
    RETURN {
      asset: asset.name,
      texture: texture.filename,
      usage: texture.texture_type,
      file_size: texture.size_bytes
    }
```

### Find asset dependency tree
```aql
FOR asset IN assets
  FILTER asset._key == "helicopter_scene"
  FOR dependency IN 1..5 OUTBOUND asset asset_depends_on
    RETURN {
      level: LENGTH(p.edges),
      asset: dependency.name,
      dependency_type: LAST(p.edges).dependency_type
    }
```

### Find all assets by a user with their complexity
```aql
FOR user IN users
  FILTER user.username == "alex.parks"
  FOR asset IN OUTBOUND user user_created_asset
    RETURN {
      creator: user.full_name,
      asset: asset.name,
      complexity: asset.complexity_score,
      created: asset.created_at
    }
```

### Find unused textures (orphaned assets)
```aql
FOR texture IN textures
  LET usage_count = LENGTH(
    FOR asset IN INBOUND texture asset_uses_texture
      RETURN 1
  )
  FILTER usage_count == 0
  RETURN {
    texture: texture.filename,
    path: texture.file_path,
    size: texture.size_bytes
  }
```

### Project asset usage analytics
```aql
FOR project IN projects
  FILTER project._key == "under_armour_7v7"
  FOR asset IN OUTBOUND project project_contains_asset
    LET texture_count = LENGTH(
      FOR texture IN OUTBOUND asset asset_uses_texture
        RETURN 1
    )
    LET material_count = LENGTH(
      FOR material IN OUTBOUND asset asset_has_material
        RETURN 1
    )
    RETURN {
      project: project.project_name,
      asset: asset.name,
      textures: texture_count,
      materials: material_count,
      complexity: asset.complexity_score
    }
```

### Material network analysis
```aql
FOR material IN materials
  LET textures = (
    FOR texture IN OUTBOUND material material_uses_texture
      RETURN {
        name: texture.filename,
        type: texture.texture_type,
        channel: texture.channel
      }
  )
  LET usage_count = LENGTH(
    FOR asset IN INBOUND material asset_has_material
      RETURN 1
  )
  RETURN {
    material: material.material_name,
    shader: material.shader_type,
    textures: textures,
    used_by_assets: usage_count
  }
```

## Advanced Features

### Graph Traversals
- **Shortest Path**: Find dependency chains between assets
- **Pattern Matching**: Find assets with similar material/texture patterns
- **Community Detection**: Group related assets by usage patterns

### Fulltext Search
```aql
FOR asset IN FULLTEXT(assets, "search_keywords", "helicopter,vehicle")
  RETURN asset
```

### Geospatial Queries (for bounding boxes)
```aql
FOR geo IN geometry
  FILTER GEO_INTERSECTS(geo.bounding_box, @query_bounds)
  RETURN geo
```

### Graph Analytics
- Calculate asset complexity scores based on dependency depth
- Identify critical assets (high in-degree in dependency graph)
- Find potential optimization opportunities (heavily used textures)

## Implementation Benefits

1. **Relationship Queries**: Instantly find all dependencies, usage patterns
2. **Impact Analysis**: Before deleting an asset, see what depends on it
3. **Asset Optimization**: Find duplicate textures, unused materials
4. **Project Analytics**: Track asset usage across projects
5. **Version Management**: Track asset evolution through relationships
6. **Performance Insights**: Identify bottlenecks in asset pipelines
7. **Collaboration**: See who created what and when
8. **Quality Control**: Find assets missing required relationships

This graph structure transforms your asset library from a simple file browser into an intelligent asset relationship system that can answer complex questions about your pipeline.