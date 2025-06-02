import React, { useState, useEffect } from 'react';
import { Search, Grid3X3, List, Filter, Upload, Download, Eye, X } from 'lucide-react';

const AssetLibrary = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [showFilterMenu, setShowFilterMenu] = useState(false);
  const [selectedFilters, setSelectedFilters] = useState({
    type: 'all', // 'all', '2d', '3d'
    format: 'all'
  });

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/assets')
      .then(res => res.json())
      .then(data => {
        setAssets(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load assets:', err);
        setLoading(false);
      });
  }, []);

  const filteredAssets = assets.filter(asset => {
    const matchesSearch = asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         asset.description.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesType = selectedFilters.type === 'all' ||
                       (selectedFilters.type === '2d' && ['texture', 'image', 'reference'].includes(asset.asset_type)) ||
                       (selectedFilters.type === '3d' && ['geometry', 'material', 'light_rig'].includes(asset.asset_type));

    return matchesSearch && matchesType;
  });

  const handleFilterChange = (filterType, value) => {
    setSelectedFilters(prev => ({
      ...prev,
      [filterType]: value
    }));
  };

  const clearFilters = () => {
    setSelectedFilters({
      type: 'all',
      format: 'all'
    });
  };

  return (
    <div className="min-h-screen bg-neutral-900 text-white">
      {/* Header */}
      <div className="bg-neutral-800 border-b border-neutral-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-blue-400">
            Asset Library
          </h1>
          <div className="flex gap-2">
            <button className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors">
              <Upload size={20} />
              Upload Asset
            </button>
          </div>
        </div>

        {/* Search and Controls */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400" size={20} />
            <input
              type="text"
              placeholder="Search assets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-neutral-700 border border-neutral-600 rounded-lg pl-10 pr-4 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-2 bg-neutral-700 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded transition-colors ${viewMode === 'grid' ? 'bg-blue-600' : 'hover:bg-neutral-600'}`}
            >
              <Grid3X3 size={18} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded transition-colors ${viewMode === 'list' ? 'bg-blue-600' : 'hover:bg-neutral-600'}`}
            >
              <List size={18} />
            </button>
          </div>

          {/* Filter Button */}
          <div className="relative">
            <button
              onClick={() => setShowFilterMenu(!showFilterMenu)}
              className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                showFilterMenu ? 'bg-blue-600' : 'bg-neutral-700 hover:bg-neutral-600'
              }`}
            >
              <Filter size={18} />
              Filter
              {(selectedFilters.type !== 'all') && (
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              )}
            </button>

            {/* Filter Dropdown */}
            {showFilterMenu && (
              <div className="absolute right-0 top-12 bg-neutral-800 border border-neutral-700 rounded-lg shadow-lg z-10 w-64">
                <div className="p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-white font-medium">Filters</h3>
                    <button
                      onClick={() => setShowFilterMenu(false)}
                      className="text-neutral-400 hover:text-white"
                    >
                      <X size={18} />
                    </button>
                  </div>

                  {/* Asset Type Filter */}
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-neutral-300 mb-2">Asset Type</label>
                    <div className="space-y-2">
                      {[
                        { value: 'all', label: 'All Assets' },
                        { value: '2d', label: '2D Assets' },
                        { value: '3d', label: '3D Assets' }
                      ].map(option => (
                        <label key={option.value} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="radio"
                            name="assetType"
                            value={option.value}
                            checked={selectedFilters.type === option.value}
                            onChange={(e) => handleFilterChange('type', e.target.value)}
                            className="text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-neutral-300 text-sm">{option.label}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Clear Filters */}
                  <button
                    onClick={clearFilters}
                    className="w-full bg-neutral-700 hover:bg-neutral-600 text-white py-2 rounded text-sm transition-colors"
                  >
                    Clear All Filters
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-neutral-400 text-lg">Loading assets...</div>
          </div>
        ) : (
          <>
            {/* Stats Bar */}
            <div className="bg-neutral-800 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-8 text-sm text-neutral-400">
                <span>{filteredAssets.length} assets found</span>
                <span>Total size: {Math.round(filteredAssets.reduce((sum, asset) => sum + asset.file_size, 0) / 1024 / 1024)} MB</span>
                <span>Last updated: Today</span>
                {selectedFilters.type !== 'all' && (
                  <span className="text-blue-400">Filtered by: {selectedFilters.type.toUpperCase()}</span>
                )}
              </div>
            </div>

            {/* Assets Grid/List */}
            {viewMode === 'grid' ? (
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
                {filteredAssets.map(asset => (
                  <div key={asset.id} className="group relative">
                    {/* Asset Card */}
                    <div className="bg-neutral-800 rounded-lg overflow-hidden border border-neutral-700 hover:border-blue-500 transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/10 cursor-pointer">
                      {/* Image/Thumbnail */}
                      <div className="aspect-square bg-neutral-700 flex items-center justify-center relative overflow-hidden">
                        {asset.thumbnail_path ? (
                          <img
                            src={asset.thumbnail_path}
                            alt={asset.name}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="text-neutral-500 text-3xl">
                            {asset.asset_type === 'geometry' ? '🎭' :
                             asset.asset_type === 'material' ? '🎨' :
                             asset.asset_type === 'texture' ? '🖼️' :
                             asset.asset_type === 'light_rig' ? '💡' :
                             asset.asset_type === 'reference' ? '📸' : '📦'}
                          </div>
                        )}

                        {/* Asset Type Badge */}
                        <div className="absolute top-2 right-2">
                          <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                            ['geometry', 'material', 'light_rig'].includes(asset.asset_type)
                              ? 'bg-blue-600/80 text-blue-100' 
                              : 'bg-green-600/80 text-green-100'
                          }`}>
                            {['geometry', 'material', 'light_rig'].includes(asset.asset_type) ? '3D' : '2D'}
                          </span>
                        </div>

                        {/* Hover Actions */}
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                          <div className="flex gap-2">
                            <button className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors">
                              <Eye size={16} />
                            </button>
                            <button className="bg-neutral-700 hover:bg-neutral-600 text-white p-2 rounded-lg transition-colors">
                              <Download size={16} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Hover Details */}
                    <div className="absolute top-full left-0 right-0 mt-2 bg-neutral-800 border border-neutral-700 rounded-lg p-3 opacity-0 group-hover:opacity-100 transition-all duration-200 z-10 shadow-lg">
                      <h3 className="text-white font-semibold text-sm mb-1 truncate">{asset.name}</h3>
                      <p className="text-neutral-400 text-xs mb-2 line-clamp-2">{asset.description}</p>

                      <div className="grid grid-cols-2 gap-2 text-xs text-neutral-500">
                        <div>
                          <span className="text-neutral-400">Type:</span>
                          <div className="text-blue-400 font-medium">{asset.asset_type}</div>
                        </div>
                        <div>
                          <span className="text-neutral-400">Size:</span>
                          <div className="text-neutral-300">{Math.round(asset.file_size / 1024)} KB</div>
                        </div>
                        <div>
                          <span className="text-neutral-400">Artist:</span>
                          <div className="text-green-400 font-medium truncate">{asset.artist}</div>
                        </div>
                        <div>
                          <span className="text-neutral-400">Format:</span>
                          <div className="text-purple-400 font-medium">{asset.file_format}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              // List View (unchanged for now)
              <div className="bg-neutral-800 rounded-lg overflow-hidden">
                <div className="grid grid-cols-12 gap-4 p-4 border-b border-neutral-700 text-sm font-medium text-neutral-400">
                  <div className="col-span-4">Name</div>
                  <div className="col-span-2">Type</div>
                  <div className="col-span-2">Artist</div>
                  <div className="col-span-2">Size</div>
                  <div className="col-span-2">Actions</div>
                </div>
                {filteredAssets.map(asset => (
                  <div key={asset.id} className="grid grid-cols-12 gap-4 p-4 border-b border-neutral-700 hover:bg-neutral-750 transition-colors">
                    <div className="col-span-4">
                      <div className="font-medium text-white">{asset.name}</div>
                      <div className="text-sm text-neutral-400 truncate">{asset.description}</div>
                    </div>
                    <div className="col-span-2 text-blue-400">{asset.asset_type}</div>
                    <div className="col-span-2 text-green-400">{asset.artist}</div>
                    <div className="col-span-2 text-neutral-300">{Math.round(asset.file_size / 1024)} KB</div>
                    <div className="col-span-2 flex gap-2">
                      <button className="bg-blue-600 hover:bg-blue-700 text-white py-1 px-3 rounded text-sm transition-colors">
                        Preview
                      </button>
                      <button className="bg-neutral-700 hover:bg-neutral-600 text-white py-1 px-3 rounded text-sm transition-colors">
                        <Download size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {filteredAssets.length === 0 && !loading && (
              <div className="text-center py-12">
                <div className="text-neutral-400 text-lg mb-2">No assets found</div>
                <div className="text-neutral-500">
                  {selectedFilters.type !== 'all'
                    ? `No ${selectedFilters.type.toUpperCase()} assets match your search`
                    : 'Try adjusting your search or upload some assets to get started'
                  }
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AssetLibrary;