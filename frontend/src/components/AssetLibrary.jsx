import React, { useState, useEffect } from 'react';
import { Search, Grid3X3, List, Filter, Upload, Download, Eye } from 'lucide-react';

const AssetLibrary = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');

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

  const filteredAssets = assets.filter(asset =>
    asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    asset.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-3xl font-bold text-blue-400">
            Blacksmith Atlas
          </h1>
          <div className="flex gap-2">
            <button className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2">
              <Upload size={20} />
              Upload Asset
            </button>
          </div>
        </div>

        {/* Search and Controls */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search assets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex items-center gap-2 bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-600' : 'hover:bg-gray-600'}`}
            >
              <Grid3X3 size={18} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-600' : 'hover:bg-gray-600'}`}
            >
              <List size={18} />
            </button>
          </div>

          <button className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg flex items-center gap-2">
            <Filter size={18} />
            Filter
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-400 text-lg">Loading assets...</div>
          </div>
        ) : (
          <>
            {/* Stats Bar */}
            <div className="bg-gray-800 rounded-lg p-4 mb-6">
              <div className="flex items-center gap-8 text-sm text-gray-400">
                <span>{filteredAssets.length} assets found</span>
                <span>Total size: {Math.round(filteredAssets.reduce((sum, asset) => sum + asset.file_size, 0) / 1024 / 1024)} MB</span>
                <span>Last updated: Today</span>
              </div>
            </div>

            {/* Assets Grid/List */}
            {viewMode === 'grid' ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredAssets.map(asset => (
                  <div key={asset.id} className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-blue-500 transition-all duration-200 hover:shadow-lg hover:shadow-blue-500/20">
                    {/* Thumbnail */}
                    <div className="h-48 bg-gray-700 flex items-center justify-center">
                      <div className="text-gray-500 text-4xl">🎨</div>
                    </div>

                    {/* Content */}
                    <div className="p-4">
                      <h3 className="text-lg font-semibold text-white mb-2 truncate">{asset.name}</h3>
                      <p className="text-gray-400 text-sm mb-3 line-clamp-2">{asset.description}</p>

                      <div className="space-y-2 text-xs text-gray-500">
                        <div className="flex justify-between">
                          <span>Type:</span>
                          <span className="text-blue-400 font-medium">{asset.asset_type}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Artist:</span>
                          <span className="text-green-400 font-medium">{asset.artist}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Size:</span>
                          <span>{Math.round(asset.file_size / 1024)} KB</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Format:</span>
                          <span className="text-purple-400 font-medium">{asset.file_format}</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 mt-4">
                        <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded text-sm flex items-center justify-center gap-1">
                          <Eye size={14} />
                          Preview
                        </button>
                        <button className="bg-gray-700 hover:bg-gray-600 text-white py-2 px-3 rounded text-sm">
                          <Download size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-gray-800 rounded-lg overflow-hidden">
                <div className="grid grid-cols-12 gap-4 p-4 border-b border-gray-700 text-sm font-medium text-gray-400">
                  <div className="col-span-4">Name</div>
                  <div className="col-span-2">Type</div>
                  <div className="col-span-2">Artist</div>
                  <div className="col-span-2">Size</div>
                  <div className="col-span-2">Actions</div>
                </div>
                {filteredAssets.map(asset => (
                  <div key={asset.id} className="grid grid-cols-12 gap-4 p-4 border-b border-gray-700 hover:bg-gray-750 transition-colors">
                    <div className="col-span-4">
                      <div className="font-medium text-white">{asset.name}</div>
                      <div className="text-sm text-gray-400 truncate">{asset.description}</div>
                    </div>
                    <div className="col-span-2 text-blue-400">{asset.asset_type}</div>
                    <div className="col-span-2 text-green-400">{asset.artist}</div>
                    <div className="col-span-2 text-gray-300">{Math.round(asset.file_size / 1024)} KB</div>
                    <div className="col-span-2 flex gap-2">
                      <button className="bg-blue-600 hover:bg-blue-700 text-white py-1 px-3 rounded text-sm">
                        Preview
                      </button>
                      <button className="bg-gray-700 hover:bg-gray-600 text-white py-1 px-3 rounded text-sm">
                        <Download size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {filteredAssets.length === 0 && !loading && (
              <div className="text-center py-12">
                <div className="text-gray-400 text-lg mb-2">No assets found</div>
                <div className="text-gray-500">Try adjusting your search or upload some assets to get started</div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AssetLibrary;