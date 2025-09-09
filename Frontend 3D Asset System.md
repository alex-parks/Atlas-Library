# Frontend 3D Asset System Architecture

## Overview

The **Blacksmith Atlas Frontend 3D Asset System** is an Object-Oriented, extensible architecture for displaying different types of 3D assets with customized card layouts. Each asset type has its own specialized card component with unique positioning of overlay elements while maintaining a consistent interface.

## 🏗️ Core Architecture

### Object-Oriented Design Pattern

The system follows a **factory pattern** with inheritance-based design:

```
BaseAsset (Abstract)
├── Asset2D (Future - completely different structure)
└── Asset3D (Current implementation)
    ├── HoudiniAsset (Traditional 3D assets)
    ├── TextureAsset (Uploaded texture files)
    └── HDRIAsset (Environment maps)
```

### Card Component Structure

Each asset type has two specialized components:

1. **Card Component** (`/frontend/src/components/cards/`): Full customizable card layout
2. **Badge Component** (`/frontend/src/components/badges/`): Hover information panel

## 📁 File Structure

```
frontend/src/components/
├── AssetLibrary.jsx                    # Main component with factory logic
├── cards/                              # Full card components
│   ├── HoudiniAssetCard.jsx           # Houdini asset cards
│   ├── TextureCard.jsx                # Texture asset cards
│   └── HDRICard.jsx                   # HDRI asset cards
└── badges/                            # Hover information components
    ├── HoudiniAssetBadge.jsx          # Houdini asset info
    ├── TextureBadge.jsx               # Texture asset info
    └── HDRIBadge.jsx                  # HDRI asset info
```

## 🎯 Asset Type System

### Asset Type Detection Logic

The factory determines asset type through this hierarchy:

1. **asset.asset_type** (from uploads) - highest priority
2. **asset.category** (from existing data)  
3. **Filename inference** (from paths.template_file)
4. **Default fallback** (Houdini Asset)

```javascript
// Asset Card Factory Logic
const getAssetCardComponent = (asset) => {
  let assetType = null;
  
  if (asset.asset_type) {
    assetType = asset.asset_type;
  } else if (asset.category) {
    assetType = asset.category;
  } else {
    // Infer from file paths...
  }
  
  switch (assetType) {
    case 'HDRI':
    case 'HDRIs':
      return HDRICard;
    case 'Textures':
    case 'Texture':
      return TextureCard;
    default:
      return HoudiniAssetCard;
  }
};
```

### Supported Asset Types

| Asset Type | Card Component | Badge Component | Primary Use |
|------------|----------------|-----------------|-------------|
| **Houdini Asset** | `HoudiniAssetCard` | `HoudiniAssetBadge` | Traditional 3D assets, FX, Materials, HDAs |
| **Texture** | `TextureCard` | `TextureBadge` | Uploaded texture maps and materials |
| **HDRI** | `HDRICard` | `HDRIBadge` | Environment lighting maps |

## 🎨 Card Layout Customization

### Design Philosophy

Each asset type has a **completely different card layout** allowing independent positioning of UI elements:

- **Version tags (v001)** can be positioned differently per asset type
- **Overlay elements** are asset-specific (render engines, formats, resolutions)
- **Color themes** match asset type (neutral, purple, orange)
- **Interactive elements** maintain consistent functionality

### Layout Patterns

#### HoudiniAssetCard Layout
- **Theme**: Neutral gray
- **Version Tag**: Bottom-left (standard position)
- **Render Engine**: Bottom-right
- **Branded Badge**: Top-right
- **Info Badge**: Neutral theme with Houdini-specific fields

#### TextureCard Layout  
- **Theme**: Purple accents
- **Format Tag**: Top-left (prominent for textures)
- **Resolution Tag**: Top-right
- **Version Tag**: Bottom-right (different from Houdini)
- **Seamless Indicator**: Bottom-left (when applicable)
- **Info Badge**: Purple theme with texture-specific fields

#### HDRICard Layout
- **Theme**: Orange accents
- **Environment Type**: Top-left
- **Version Tag**: Top-center (**unique position**)
- **Resolution Tag**: Top-right
- **Location Tag**: Bottom-left
- **Format Tag**: Bottom-right
- **Info Badge**: Orange theme with HDRI-specific fields

## 🛠️ Card Component Architecture

### Base Card Structure

Each card component follows this structure:

```jsx
const AssetCard = ({ asset, formatAssetName, formatAssetNameJSX, openPreview }) => {
  // State management for info badge
  const [isExpanded, setIsExpanded] = useState(false);
  
  return (
    <div className="group relative">
      {/* Main Card Container */}
      <div className="bg-neutral-800 rounded-lg overflow-hidden border...">
        
        {/* Square Thumbnail Area */}
        <div className="aspect-square bg-neutral-700 relative overflow-hidden">
          <SequenceThumbnail ... />
          
          {/* Asset-Specific Overlay Elements */}
          {/* Version tags, format indicators, etc. */}
          
          {/* Branded Warning (if applicable) */}
          
          {/* Hover Action Buttons */}
          
        </div>
        
      </div>
      
      {/* Asset Information Badge (Hover) */}
      <div className="absolute bottom-0 left-0 right-0 z-10">
        {/* Expandable info panel */}
      </div>
      
    </div>
  );
};
```

### Required Props

All card components must accept these props:

```javascript
{
  asset,              // Asset data object
  formatAssetName,    // Function: format asset name (string)
  formatAssetNameJSX, // Function: format asset name (JSX)
  openPreview         // Function: open asset preview modal
}
```

### Common Helper Functions

Each card implements these helper functions:

```javascript
const getAssetVersion = () => {
  const assetId = asset.id || asset._key || '';
  if (assetId.length >= 16) {
    return `v${assetId.substring(13)}`; // Last 3 chars
  }
  return 'v001';
};

const getFileSize = () => {
  const totalBytes = asset.file_sizes?.estimated_total_size || 0;
  // Format bytes to KB/MB/GB
};
```

## 📊 Asset Data Structure

### Standard Asset Object

```javascript
{
  id: "CBA8403F4AA001",           // 16-char ID: 11 UID + 2 variant + 3 version
  _key: "CBA8403F4AA001",         // Database key (same as id)
  name: "Asset Name",
  description: "Asset description",
  category: "Assets",              // Category for type detection
  asset_type: "Texture",          // Override type (highest priority)
  dimension: "3D",
  
  metadata: {
    hierarchy: {
      dimension: "3D",
      asset_type: "Assets",
      subcategory: "Blacksmith Asset", 
      render_engine: "Redshift"
    },
    houdini_version: "20.5.445",
    resolution: "4K",
    file_format: "EXR",
    // ... type-specific metadata
  },
  
  paths: {
    asset_folder: "/net/library/atlaslib/3D/Assets/...",
    template_file: "template.hipnc",
    thumbnail: "/path/to/thumbnail/"
  },
  
  file_sizes: {
    estimated_total_size: 1024000
  },
  
  tags: ["tag1", "tag2"],
  created_at: "2025-08-19T23:17:30.230177",
  created_by: "username",
  artist: "Artist Name",
  branded: true,                   // Branded asset flag
  thumbnail_frame: 1015            // Thumbnail frame number
}
```

### ID Structure (16 Characters)

- **Characters 1-11**: Base UID (unique identifier)
- **Characters 12-13**: Variant ID ("AA" = original, "AB" = variant 1, etc.)
- **Characters 14-16**: Version number ("001", "002", etc.)

Example: `CBA8403F4AA001`
- Base: `CBA8403F4`
- Variant: `AA` (original)
- Version: `001`

## 🎭 Badge Component Architecture

### Badge Purpose

Badges provide detailed asset information that appears on hover:

- **Expandable panels** that slide up from bottom
- **Asset-specific information** relevant to each type
- **Consistent interaction** (hover to expand, click to pin)
- **Color-coded themes** matching card types

### Badge Structure

```jsx
const AssetBadge = ({ asset, formatAssetNameJSX }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isClickedOpen, setIsClickedOpen] = useState(false);
  
  return (
    <div className="absolute bottom-0 left-0 right-0 z-10">
      {/* Expanded Content Panel */}
      <div className={`bg-neutral-800/95 ... ${
        isExpanded ? 'max-h-48 opacity-100' : 'max-h-0 opacity-0'
      }`}>
        {/* Asset-specific information grid */}
      </div>
      
      {/* Always Visible Tab */}
      <div className="opacity-0 group-hover:opacity-100 ...">
        {/* Themed tab with icon and chevron */}
      </div>
    </div>
  );
};
```

### Badge Information Layout

Each badge uses a **2x3 grid** layout for information:

```jsx
<div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
  <div>
    <span className="text-neutral-400">Label:</span>
    <div className="text-color-400 font-medium">Value</div>
  </div>
  // ... 5 more fields
</div>
```

## 🔧 Extension Guidelines

### Adding New Asset Types

To add a new asset type (e.g., `ModelAsset`):

1. **Create Card Component** (`/cards/ModelCard.jsx`):
   ```jsx
   const ModelCard = ({ asset, formatAssetName, formatAssetNameJSX, openPreview }) => {
     // Custom layout for model assets
     // Unique overlay positioning
     // Model-specific theme colors
   };
   ```

2. **Create Badge Component** (`/badges/ModelBadge.jsx`):
   ```jsx
   const ModelBadge = ({ asset, formatAssetNameJSX }) => {
     // Model-specific information fields
     // Custom helper functions
     // Themed badge design
   };
   ```

3. **Update Factory Functions** (in `AssetLibrary.jsx`):
   ```javascript
   // Add to imports
   import ModelCard from './cards/ModelCard';
   import ModelBadge from './badges/ModelBadge';
   
   // Update card factory
   case 'Model':
   case 'Models':
     return ModelCard;
   
   // Update badge factory  
   case 'Model':
   case 'Models':
     return ModelBadge;
   ```

4. **Update Backend Asset Types** (`/backend/core/asset_types.py`):
   ```python
   class ModelAsset(Asset3D):
       @property 
       def asset_type(self) -> str:
           return "Model"
       
       def get_badge_type(self) -> str:
           return "ModelBadge"
   ```

### Customization Options

#### Overlay Element Positioning
Position overlays anywhere within the square thumbnail:
```jsx
{/* Top-left */}
<div className="absolute top-2 left-2">

{/* Top-center */}  
<div className="absolute top-2 left-1/2 transform -translate-x-1/2">

{/* Bottom-right */}
<div className="absolute bottom-2 right-2">

{/* Center */}
<div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
```

#### Theme Colors
Each asset type can have unique color themes:
```jsx
// Purple theme (Texture)
className="bg-purple-500/20 text-purple-300"
className="border-purple-500/30 hover:bg-purple-500/20"

// Orange theme (HDRI)  
className="bg-orange-500/20 text-orange-300"
className="border-orange-500/30 hover:bg-orange-500/20"

// Custom theme
className="bg-green-500/20 text-green-300"
```

#### Asset-Specific Indicators
Add custom indicators based on asset properties:
```jsx
{/* Seamless texture indicator */}
{getSeamless() === 'Yes' && (
  <div className="absolute bottom-2 left-2">
    <span className="...">🔄 Seamless</span>
  </div>
)}

{/* High resolution indicator */}
{getResolution().includes('8K') && (
  <div className="absolute top-2 right-2">
    <span className="...">🔥 8K</span>
  </div>
)}
```

## 🔄 Integration Points

### AssetLibrary Integration

The main `AssetLibrary.jsx` component integrates the card system:

```jsx
{viewMode === 'grid' ? (
  <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
    {filteredAssets.map(asset => {
      const CardComponent = getAssetCardComponent(asset);
      return (
        <CardComponent 
          key={asset.id} 
          asset={asset} 
          formatAssetName={formatAssetName}
          formatAssetNameJSX={formatAssetNameJSX}
          openPreview={openPreview}
        />
      );
    })}
  </div>
) : (
  // List view...
)}
```

### Backend Integration

Asset type detection works with the backend Object-Oriented system:

- **Backend** (`/backend/core/asset_types.py`): Defines asset classes and metadata
- **Frontend**: Uses asset data to determine appropriate card component
- **Database**: Stores asset data in ArangoDB `Atlas_Library` collection

## 🎨 Design Principles

### Visual Consistency
- **Square thumbnails**: All cards maintain `aspect-square` ratio
- **Hover interactions**: Consistent hover states and transitions
- **Typography**: Consistent font sizes and weights
- **Spacing**: Uniform padding and margins

### User Experience
- **Immediate recognition**: Different themes help identify asset types instantly
- **Progressive disclosure**: Basic info via overlays, detailed info on hover
- **Contextual actions**: Asset-type-appropriate actions and information
- **Performance**: Lazy loading and efficient rendering

### Accessibility
- **Keyboard navigation**: All interactive elements accessible via keyboard
- **Screen readers**: Proper ARIA labels and semantic HTML
- **Color contrast**: Sufficient contrast ratios for all text
- **Focus indicators**: Clear focus states for all interactive elements

## 🚀 Performance Considerations

### Rendering Optimization
- **Component memoization**: Use `React.memo` for card components when needed
- **Image lazy loading**: Thumbnails load on demand
- **Virtual scrolling**: Consider for large asset collections
- **Efficient re-renders**: Minimize prop drilling and unnecessary updates

### State Management
- **Local state**: Badge expansion state managed locally
- **Global state**: Asset data managed at AssetLibrary level
- **Event delegation**: Efficient handling of card interactions
- **Memory management**: Proper cleanup of event listeners

## 📝 Testing Strategy

### Component Testing
- **Unit tests**: Test each card component in isolation
- **Integration tests**: Test card factory logic
- **Visual regression**: Screenshot testing for layout consistency
- **Accessibility tests**: Automated accessibility checks

### User Acceptance Testing
- **Asset type recognition**: Users can quickly identify asset types
- **Information access**: Users can easily access detailed information
- **Navigation efficiency**: Users can efficiently browse large collections
- **Cross-browser compatibility**: Consistent experience across browsers

## 🎯 Future Enhancements

### Planned Features
- **2D Asset System**: Completely different structure for 2D assets
- **Asset Previews**: Type-specific preview modals (3D viewer, image viewer, etc.)
- **Bulk Operations**: Multi-select and batch operations on cards
- **Drag & Drop**: Asset organization and workflow integration

### Extension Opportunities
- **Animation Assets**: Cards for animated sequences and rigs
- **Audio Assets**: Sound effects and music integration
- **Script Assets**: Code and configuration files
- **Documentation Assets**: Manuals and guides

### Advanced Customization
- **User Themes**: Customizable color schemes
- **Layout Preferences**: User-selectable card layouts
- **Information Density**: Compact vs. detailed view modes
- **Workflow Integration**: Direct integration with DCC applications

## 🔗 Related Documentation

- **Backend Asset Types**: `/backend/core/asset_types.py`
- **Main CLAUDE.md**: Complete project documentation
- **Task Master Integration**: `.taskmaster/CLAUDE.md`
- **API Documentation**: Backend REST API reference
- **Database Schema**: ArangoDB collection structure

---

## 📋 Quick Reference

### Adding New Asset Type Checklist

- [ ] Create card component in `/cards/`
- [ ] Create badge component in `/badges/`
- [ ] Update imports in `AssetLibrary.jsx`
- [ ] Update `getAssetCardComponent()` factory
- [ ] Update `getAssetBadgeComponent()` factory
- [ ] Create backend asset class
- [ ] Add type detection logic
- [ ] Update database schema if needed
- [ ] Test with sample assets
- [ ] Document new asset type

### Common Styling Classes

```css
/* Card containers */
.aspect-square                    /* Square thumbnail ratio */
.group.relative                   /* Card wrapper */

/* Overlay positioning */
.absolute.top-2.left-2           /* Top-left */
.absolute.top-2.right-2          /* Top-right */  
.absolute.bottom-2.left-2        /* Bottom-left */
.absolute.bottom-2.right-2       /* Bottom-right */
.absolute.top-2.left-1/2         /* Top-center */

/* Theme colors */
.text-purple-300                 /* Texture theme */
.text-orange-300                 /* HDRI theme */
.text-neutral-300               /* Houdini theme */

/* Interactive states */
.opacity-0.group-hover:opacity-100  /* Hover reveals */
.transition-all.duration-200        /* Smooth transitions */
```

This documentation provides Claude with comprehensive understanding of the 3D Asset System architecture, enabling confident expansion and modification of the system while maintaining consistency and design principles.