# ArangoDB Graph Query Examples for Blacksmith Atlas

## Asset Relationship Queries

### Find all textures used by an asset
```aql
FOR asset IN assets
  FILTER asset._key == "C0D6B8F1"
  FOR texture IN OUTBOUND asset asset_uses_texture
    RETURN {
      asset_name: asset.name,
      texture_filename: texture.filename,
      texture_type: texture.texture_type,
      file_size_kb: texture.size_bytes / 1024,
      udim_tile: texture.udim_tile
    }
```

### Find which materials use a specific texture
```aql
FOR texture IN textures
  FILTER texture.filename == "helicopter_BaseColor.1001.png"
  FOR material IN INBOUND texture material_uses_texture
    FOR asset IN INBOUND material asset_has_material
      RETURN {
        texture: texture.filename,
        material: material.material_name,
        asset: asset.name,
        shader_type: material.shader_type
      }
```

### Get complete asset breakdown with all dependencies
```aql
FOR asset IN assets
  FILTER asset._key == "C0D6B8F1"
  LET textures = (
    FOR texture IN OUTBOUND asset asset_uses_texture
      RETURN {
        filename: texture.filename,
        type: texture.texture_type,
        size_mb: ROUND(texture.size_bytes / 1048576, 2)
      }
  )
  LET materials = (
    FOR material IN OUTBOUND asset asset_has_material
      LET material_textures = (
        FOR tex IN OUTBOUND material material_uses_texture
          RETURN tex.filename
      )
      RETURN {
        name: material.material_name,
        shader: material.shader_type,
        textures: material_textures
      }
  )
  LET geometry = (
    FOR geo IN OUTBOUND asset asset_uses_geometry
      RETURN {
        filename: geo.filename,
        type: geo.file_type,
        polygons: geo.polygon_count
      }
  )
  RETURN {
    asset: asset.name,
    complexity_score: asset.complexity_score,
    textures: textures,
    materials: materials,
    geometry: geometry,
    total_texture_size_mb: SUM(textures[*].size_mb)
  }
```

## Asset Discovery Queries

### Find assets similar to a given asset (by texture usage patterns)
```aql
FOR target_asset IN assets
  FILTER target_asset._key == "C0D6B8F1"
  LET target_texture_types = (
    FOR texture IN OUTBOUND target_asset asset_uses_texture
      RETURN texture.texture_type
  )
  
  FOR other_asset IN assets
    FILTER other_asset._key != target_asset._key
    LET other_texture_types = (
      FOR texture IN OUTBOUND other_asset asset_uses_texture
        RETURN texture.texture_type
    )
    
    LET similarity = LENGTH(INTERSECTION(target_texture_types, other_texture_types)) / LENGTH(UNION(target_texture_types, other_texture_types))
    FILTER similarity > 0.5  // At least 50% similarity
    
    SORT similarity DESC
    RETURN {
      similar_asset: other_asset.name,
      similarity_score: ROUND(similarity * 100, 1),
      shared_texture_types: INTERSECTION(target_texture_types, other_texture_types)
    }
```

### Find unused textures (potential cleanup candidates)
```aql
FOR texture IN textures
  LET usage_count = LENGTH(
    FOR material IN INBOUND texture material_uses_texture
      FOR asset IN INBOUND material asset_has_material
        RETURN 1
  )
  FILTER usage_count == 0
  RETURN {
    unused_texture: texture.filename,
    file_path: texture.file_path,
    size_mb: ROUND(texture.size_bytes / 1048576, 2),
    created_at: texture.created_at
  }
```

### Find duplicate textures by filename
```aql
FOR texture IN textures
  COLLECT filename = texture.filename WITH COUNT INTO count
  FILTER count > 1
  LET duplicates = (
    FOR t IN textures
      FILTER t.filename == filename
      RETURN {
        _key: t._key,
        file_path: t.file_path,
        size_bytes: t.size_bytes,
        asset_context: t.asset_context
      }
  )
  RETURN {
    filename: filename,
    duplicate_count: count,
    duplicates: duplicates,
    total_wasted_space_mb: ROUND(SUM(duplicates[*].size_bytes) / 1048576, 2)
  }
```

## Project and User Analytics

### Project asset complexity analysis
```aql
FOR project IN projects
  FILTER project._key == "under_armour_7v7"
  FOR asset IN OUTBOUND project project_contains_asset
    LET texture_count = LENGTH(FOR texture IN OUTBOUND asset asset_uses_texture RETURN 1)
    LET material_count = LENGTH(FOR material IN OUTBOUND asset asset_has_material RETURN 1)
    LET geometry_count = LENGTH(FOR geo IN OUTBOUND asset asset_uses_geometry RETURN 1)
    
    RETURN {
      project: project.project_name,
      asset: asset.name,
      complexity_score: asset.complexity_score,
      resource_counts: {
        textures: texture_count,
        materials: material_count,
        geometry: geometry_count
      },
      created_by: asset.created_by,
      created_at: asset.created_at
    }
```

### User productivity analysis
```aql
FOR user IN users
  FILTER user.username == "alex.parks"
  LET created_assets = (
    FOR asset IN OUTBOUND user user_created_asset
      LET texture_count = LENGTH(FOR texture IN OUTBOUND asset asset_uses_texture RETURN 1)
      RETURN {
        asset_name: asset.name,
        complexity: asset.complexity_score,
        textures: texture_count,
        created_at: asset.created_at
      }
  )
  
  RETURN {
    user: user.full_name,
    total_assets_created: LENGTH(created_assets),
    average_complexity: ROUND(AVERAGE(created_assets[*].complexity), 1),
    total_textures_handled: SUM(created_assets[*].textures),
    assets: created_assets
  }
```

### Find most reused assets across projects
```aql
FOR asset IN assets
  LET project_usage = (
    FOR project IN INBOUND asset project_contains_asset
      RETURN project.project_name
  )
  FILTER LENGTH(project_usage) > 1
  
  SORT LENGTH(project_usage) DESC
  RETURN {
    reusable_asset: asset.name,
    used_in_projects: project_usage,
    reuse_count: LENGTH(project_usage),
    complexity_score: asset.complexity_score
  }
```

## Performance and Optimization Queries

### Find assets with high texture memory usage
```aql
FOR asset IN assets
  LET total_texture_size = SUM(
    FOR texture IN OUTBOUND asset asset_uses_texture
      RETURN texture.size_bytes
  )
  FILTER total_texture_size > 50000000  // > 50MB
  
  SORT total_texture_size DESC
  RETURN {
    memory_heavy_asset: asset.name,
    total_texture_size_mb: ROUND(total_texture_size / 1048576, 1),
    texture_count: LENGTH(FOR texture IN OUTBOUND asset asset_uses_texture RETURN 1),
    complexity_score: asset.complexity_score
  }
```

### Identify UDIM sequences for optimization
```aql
FOR texture IN textures
  FILTER texture.is_udim_sequence == true
  FOR material IN INBOUND texture material_uses_texture
    FOR asset IN INBOUND material asset_has_material
      COLLECT asset_name = asset.name, material_name = material.material_name INTO udim_groups
      LET tile_count = LENGTH(udim_groups[0].texture.udim_tiles)
      
      RETURN {
        asset: asset_name,
        material: material_name,
        udim_tile_count: tile_count,
        estimated_memory_mb: ROUND(tile_count * 4, 1),  // Assume 4MB per tile
        optimization_potential: tile_count > 6 ? "HIGH" : "MEDIUM"
      }
```

### Find broken material assignments
```aql
FOR material IN materials
  LET texture_count = LENGTH(FOR texture IN OUTBOUND material material_uses_texture RETURN 1)
  LET asset_usage = LENGTH(FOR asset IN INBOUND material asset_has_material RETURN 1)
  
  FILTER texture_count == 0 OR asset_usage == 0
  
  RETURN {
    problematic_material: material.material_name,
    node_path: material.node_path,
    texture_count: texture_count,
    used_by_assets: asset_usage,
    issue: texture_count == 0 ? "NO_TEXTURES" : "NOT_USED"
  }
```

## Advanced Graph Traversals

### Find shortest dependency path between two assets
```aql
FOR path IN OUTBOUND SHORTEST_PATH
  "assets/helicopter_scene" TO "assets/C0D6B8F1"
  asset_depends_on, project_contains_asset
  
  RETURN {
    path_length: LENGTH(path.edges),
    dependency_chain: [
      FOR vertex IN path.vertices
        RETURN vertex.name
    ],
    relationship_types: [
      FOR edge IN path.edges
        RETURN edge._key
    ]
  }
```

### Find all assets within 2 degrees of a material
```aql
FOR material IN materials
  FILTER material._key == "helicopter_body_material"
  FOR asset IN 1..2 ANY material 
    material_uses_texture, asset_has_material, asset_uses_texture
    FILTER IS_SAME_COLLECTION(assets, asset)
    
    RETURN DISTINCT {
      related_asset: asset.name,
      relation_distance: LENGTH(path.edges),
      connection_via: path.vertices[1].filename || path.vertices[1].material_name
    }
```

### Community detection - find asset clusters
```aql
FOR asset IN assets
  LET shared_textures = (
    FOR other_asset IN assets
      FILTER other_asset._key != asset._key
      LET asset_textures = (FOR tex IN OUTBOUND asset asset_uses_texture RETURN tex._key)
      LET other_textures = (FOR tex IN OUTBOUND other_asset asset_uses_texture RETURN tex._key)
      LET shared = INTERSECTION(asset_textures, other_textures)
      FILTER LENGTH(shared) > 0
      RETURN {
        other_asset: other_asset.name,
        shared_texture_count: LENGTH(shared)
      }
  )
  
  FILTER LENGTH(shared_textures) > 0
  SORT LENGTH(shared_textures) DESC
  LIMIT 10
  
  RETURN {
    hub_asset: asset.name,
    connected_assets: shared_textures
  }
```

## Quality Control Queries

### Find assets missing required texture types
```aql
FOR asset IN assets
  LET texture_types = (
    FOR texture IN OUTBOUND asset asset_uses_texture
      RETURN DISTINCT texture.texture_type
  )
  
  LET required_types = ["basecolor", "normal", "roughness"]
  LET missing_types = MINUS(required_types, texture_types)
  
  FILTER LENGTH(missing_types) > 0
  
  RETURN {
    incomplete_asset: asset.name,
    has_texture_types: texture_types,
    missing_texture_types: missing_types,
    quality_score: ROUND((LENGTH(required_types) - LENGTH(missing_types)) / LENGTH(required_types) * 100, 1)
  }
```

### Identify version conflicts
```aql
FOR asset IN assets
  FOR other_asset IN assets
    FILTER asset._key != other_asset._key
    FILTER CONTAINS(asset.name, other_asset.name) OR CONTAINS(other_asset.name, asset.name)
    FILTER asset.created_at != other_asset.created_at
    
    RETURN {
      potential_versions: [asset.name, other_asset.name],
      dates: [asset.created_at, other_asset.created_at],
      creators: [asset.created_by, other_asset.created_by],
      recommendation: asset.created_at > other_asset.created_at ? 
        CONCAT("Keep ", asset.name, ", review ", other_asset.name) :
        CONCAT("Keep ", other_asset.name, ", review ", asset.name)
    }
```

These queries demonstrate how ArangoDB's graph capabilities can transform your asset management from simple file storage into an intelligent, queryable relationship system that provides insights into usage patterns, optimization opportunities, and quality control.