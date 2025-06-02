import React, { useState, useEffect } from 'react';

const AssetLibrary = () => {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);

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

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-4xl font-bold text-blue-500 mb-8">
        Blacksmith Atlas - Asset Library
      </h1>

      {loading ? (
        <div className="text-gray-400">Loading assets...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {assets.map(asset => (
            <div key={asset.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700 hover:border-blue-500 transition-colors">
              <h3 className="text-xl font-semibold text-white mb-2">{asset.name}</h3>
              <p className="text-gray-400 mb-4">{asset.description}</p>
              <div className="space-y-2 text-sm text-gray-500">
                <div>Type: <span className="text-blue-400">{asset.asset_type}</span></div>
                <div>Artist: <span className="text-green-400">{asset.artist}</span></div>
                <div>Size: {Math.round(asset.file_size / 1024)} KB</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AssetLibrary;