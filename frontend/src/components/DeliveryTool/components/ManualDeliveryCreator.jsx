// frontend/src/components/DeliveryTool/components/ManualDeliveryCreator.jsx

import React, { useState } from 'react';
import { Plus, Trash2, Save, ArrowLeft } from 'lucide-react';

const ManualDeliveryCreator = ({ onSave, onCancel }) => {
  // Universal slate information (applies to all deliverables)
  const [slateInfo, setSlateInfo] = useState({
    agency: '',
    client: '',
    product: '',
    copyright: ''
  });

  // Individual deliverables table
  const [deliverables, setDeliverables] = useState([
    {
      id: 1,
      title: '',
      duration: '',
      shipDate: new Date().toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' }),
      platform: 'YouTube',
      aspectRatio: '16x9',
      isci: '',
      audio: 'Web Stereo'
    }
  ]);

  // Available options
  const platformOptions = [
    'YouTube',
    'TikTok',
    'Meta',
    'IG Stories',
    'Google',
    'Pinterest',
    'OTT',
    'Custom'
  ];

  const aspectRatioOptions = [
    { value: '16x9', label: '16:9 (Widescreen)' },
    { value: '9x16', label: '9:16 (Vertical)' },
    { value: '1x1', label: '1:1 (Square)' },
    { value: '4x5', label: '4:5 (Portrait)' }
  ];

  const audioOptions = [
    'Web Stereo',
    'Broadcast Stereo',
    'Mono',
    'Surround 5.1',
    'Custom'
  ];

  // Add new deliverable row
  const addDeliverable = () => {
    const newId = Math.max(...deliverables.map(d => d.id)) + 1;
    setDeliverables([...deliverables, {
      id: newId,
      title: '',
      duration: '',
      shipDate: new Date().toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' }),
      platform: 'YouTube',
      aspectRatio: '16x9',
      isci: '',
      audio: 'Web Stereo'
    }]);
  };

  // Remove deliverable row
  const removeDeliverable = (id) => {
    if (deliverables.length > 1) {
      setDeliverables(deliverables.filter(d => d.id !== id));
    }
  };

  // Update deliverable field
  const updateDeliverable = (id, field, value) => {
    setDeliverables(deliverables.map(d =>
      d.id === id ? { ...d, [field]: value } : d
    ));
  };

  // Update slate info field
  const updateSlateInfo = (field, value) => {
    setSlateInfo({ ...slateInfo, [field]: value });
  };

  // Validate and save
  const handleSave = () => {
    // Validation
    const errors = [];

    if (!slateInfo.agency.trim()) errors.push('Agency is required');
    if (!slateInfo.client.trim()) errors.push('Client is required');
    if (!slateInfo.product.trim()) errors.push('Product is required');

    const invalidDeliverables = deliverables.filter(d =>
      !d.title.trim() || !d.shipDate.trim()
    );

    if (invalidDeliverables.length > 0) {
      errors.push('All deliverables must have a title and ship date');
    }

    if (errors.length > 0) {
      alert('Please fix the following errors:\n' + errors.join('\n'));
      return;
    }

    // Convert to the same format as CSV parser output
    const manualData = {
      project_info: {
        agency: slateInfo.agency,
        client: slateInfo.client,
        product: slateInfo.product,
        copyright: slateInfo.copyright || `©${new Date().getFullYear()} ${slateInfo.client}. All rights reserved.`,
        title: 'Manual Entry',
        isci: 'N/A',
        duration: 'Various',
        audio: 'Various'
      },
      deliverable_groups: [{
        groupTitle: 'Manual Deliverables',
        deliverables: deliverables.map((d, index) => ({
          id: `manual_${index}`,
          video_title: d.title,
          original_title: 'Manual Deliverables',
          ship_date: d.shipDate,
          platform: d.platform === 'Custom' ? (d.customPlatform || 'Custom') : d.platform,
          specs: d.platform === 'Custom' ? (d.customPlatform || 'Custom') : d.platform,
          aspect_ratio: d.aspectRatio,
          suggested_slate_format: d.aspectRatio,
          duration: d.duration ? `${d.duration}s` : 'N/A',
          shipped: false,
          slated_status: 'Manual',
          agency: slateInfo.agency,
          client: slateInfo.client,
          product: slateInfo.product,
          isci: d.isci || 'N/A',
          audio: d.audio === 'Custom' ? (d.customAudio || 'Custom') : d.audio,
          copyright: slateInfo.copyright || `©${new Date().getFullYear()} ${slateInfo.client}. All rights reserved.`
        })),
        enabled: true
      }],
      summary: {
        total_slated_deliverables: deliverables.length,
        total_videos: [...new Set(deliverables.map(d => d.title))].length,
        date_range: deliverables.length > 0 ?
          `${Math.min(...deliverables.map(d => d.shipDate))} to ${Math.max(...deliverables.map(d => d.shipDate))}` : '',
        formats_needed: deliverables.reduce((acc, d) => {
          acc[d.aspectRatio] = (acc[d.aspectRatio] || 0) + 1;
          return acc;
        }, {}),
        platforms: [...new Set(deliverables.map(d => d.platform))]
      }
    };

    onSave(manualData);
  };

  return (
    <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Manual Delivery Creation</h2>
        <button
          onClick={onCancel}
          className="bg-neutral-600 hover:bg-neutral-500 text-white py-2 px-4 rounded-lg flex items-center gap-2 transition-colors"
        >
          <ArrowLeft size={16} />
          Back to Upload
        </button>
      </div>

      {/* Universal Slate Information */}
      <div className="bg-neutral-600 rounded-lg p-6 mb-6">
        <h3 className="text-lg font-medium text-white mb-4">Universal Slate Information</h3>
        <p className="text-neutral-400 text-sm mb-4">This information will be applied to all generated slates</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">
              Agency <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={slateInfo.agency}
              onChange={(e) => updateSlateInfo('agency', e.target.value)}
              placeholder="e.g., 72andSunny"
              className="w-full bg-neutral-500 border border-neutral-400 rounded-lg px-3 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-300 mb-2">
              Client <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={slateInfo.client}
              onChange={(e) => updateSlateInfo('client', e.target.value)}
              placeholder="e.g., Nike"
              className="w-full bg-neutral-500 border border-neutral-400 rounded-lg px-3 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-neutral-300 mb-2">
              Product <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={slateInfo.product}
              onChange={(e) => updateSlateInfo('product', e.target.value)}
              placeholder="e.g., Air Jordan Campaign"
              className="w-full bg-neutral-500 border border-neutral-400 rounded-lg px-3 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-neutral-300 mb-2">
              Copyright
            </label>
            <input
              type="text"
              value={slateInfo.copyright}
              onChange={(e) => updateSlateInfo('copyright', e.target.value)}
              placeholder={`©${new Date().getFullYear()} ${slateInfo.client || 'Client'}. All rights reserved.`}
              className="w-full bg-neutral-500 border border-neutral-400 rounded-lg px-3 py-2 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Deliverables Table */}
      <div className="bg-neutral-600 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-white">Deliverables</h3>
          <button
            onClick={addDeliverable}
            className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg flex items-center gap-2 transition-colors"
          >
            <Plus size={16} />
            Add Deliverable
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-neutral-500">
                <th className="text-left py-3 px-2 text-neutral-300 font-medium">Title *</th>
                <th className="text-left py-3 px-2 text-neutral-300 font-medium">Duration</th>
                <th className="text-left py-3 px-2 text-neutral-300 font-medium">Ship Date *</th>
                <th className="text-left py-3 px-2 text-neutral-300 font-medium">Platform</th>
                <th className="text-left py-3 px-2 text-neutral-300 font-medium">Aspect Ratio</th>
                <th className="text-left py-3 px-2 text-neutral-300 font-medium">ISCI</th>
                <th className="text-left py-3 px-2 text-neutral-300 font-medium">Audio</th>
                <th className="text-left py-3 px-2 text-neutral-300 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {deliverables.map((deliverable) => (
                <tr key={deliverable.id} className="border-b border-neutral-500">
                  <td className="py-3 px-2">
                    <input
                      type="text"
                      value={deliverable.title}
                      onChange={(e) => updateDeliverable(deliverable.id, 'title', e.target.value)}
                      placeholder="Video Title"
                      className="w-full bg-neutral-500 border border-neutral-400 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                    />
                  </td>
                  <td className="py-3 px-2">
                    <input
                      type="text"
                      value={deliverable.duration}
                      onChange={(e) => updateDeliverable(deliverable.id, 'duration', e.target.value)}
                      placeholder="30"
                      className="w-full bg-neutral-500 border border-neutral-400 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                    />
                  </td>
                  <td className="py-3 px-2">
                    <input
                      type="text"
                      value={deliverable.shipDate}
                      onChange={(e) => updateDeliverable(deliverable.id, 'shipDate', e.target.value)}
                      placeholder="MM/DD/YYYY"
                      className="w-full bg-neutral-500 border border-neutral-400 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                    />
                  </td>
                  <td className="py-3 px-2">
                    {deliverable.platform === 'Custom' ? (
                      <input
                        type="text"
                        value={deliverable.customPlatform || ''}
                        onChange={(e) => updateDeliverable(deliverable.id, 'customPlatform', e.target.value)}
                        placeholder="Enter custom platform..."
                        className="w-full bg-neutral-500 border border-neutral-400 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                      />
                    ) : (
                      <select
                        value={deliverable.platform}
                        onChange={(e) => updateDeliverable(deliverable.id, 'platform', e.target.value)}
                        className="w-full bg-neutral-500 border border-neutral-400 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                      >
                        {platformOptions.map(platform => (
                          <option key={platform} value={platform}>{platform}</option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td className="py-3 px-2">
                    <select
                      value={deliverable.aspectRatio}
                      onChange={(e) => updateDeliverable(deliverable.id, 'aspectRatio', e.target.value)}
                      className="w-full bg-neutral-500 border border-neutral-400 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                    >
                      {aspectRatioOptions.map(option => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                      ))}
                    </select>
                  </td>
                  <td className="py-3 px-2">
                    <input
                      type="text"
                      value={deliverable.isci}
                      onChange={(e) => updateDeliverable(deliverable.id, 'isci', e.target.value)}
                      placeholder="ISCI/AD-ID"
                      className="w-full bg-neutral-500 border border-neutral-400 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                    />
                  </td>
                  <td className="py-3 px-2">
                    {deliverable.audio === 'Custom' ? (
                      <input
                        type="text"
                        value={deliverable.customAudio || ''}
                        onChange={(e) => updateDeliverable(deliverable.id, 'customAudio', e.target.value)}
                        placeholder="Enter custom audio..."
                        className="w-full bg-neutral-500 border border-neutral-400 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                      />
                    ) : (
                      <select
                        value={deliverable.audio}
                        onChange={(e) => updateDeliverable(deliverable.id, 'audio', e.target.value)}
                        className="w-full bg-neutral-500 border border-neutral-400 rounded px-2 py-1 text-white text-sm focus:outline-none focus:border-blue-500"
                      >
                        {audioOptions.map(audio => (
                          <option key={audio} value={audio}>{audio}</option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td className="py-3 px-2">
                    <button
                      onClick={() => removeDeliverable(deliverable.id)}
                      disabled={deliverables.length === 1}
                      className={`p-1 rounded transition-colors ${
                        deliverables.length === 1
                          ? 'text-neutral-500 cursor-not-allowed'
                          : 'text-red-400 hover:text-red-300 hover:bg-red-900/20'
                      }`}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary */}
        <div className="mt-6 p-4 bg-neutral-500 rounded-lg">
          <h4 className="text-white font-medium mb-2">Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-neutral-400">Total Deliverables:</span>
              <div className="text-blue-400 font-medium">{deliverables.length}</div>
            </div>
            <div>
              <span className="text-neutral-400">Unique Titles:</span>
              <div className="text-green-400 font-medium">
                {[...new Set(deliverables.map(d => d.title).filter(t => t.trim()))].length}
              </div>
            </div>
            <div>
              <span className="text-neutral-400">16:9 Format:</span>
              <div className="text-purple-400 font-medium">
                {deliverables.filter(d => d.aspectRatio === '16x9').length}
              </div>
            </div>
            <div>
              <span className="text-neutral-400">9:16 Format:</span>
              <div className="text-orange-400 font-medium">
                {deliverables.filter(d => d.aspectRatio === '9x16').length}
              </div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleSave}
            className="bg-green-600 hover:bg-green-700 text-white py-3 px-6 rounded-lg flex items-center gap-2 transition-colors font-medium"
          >
            <Save size={18} />
            Create Deliverables
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManualDeliveryCreator;