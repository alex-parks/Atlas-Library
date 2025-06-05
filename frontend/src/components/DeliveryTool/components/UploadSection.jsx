// frontend/src/components/DeliveryTool/components/UploadSection.jsx

import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, Trash2 } from 'lucide-react';
import ManualDeliveryCreator from './ManualDeliveryCreator';

const UploadSection = ({
  rawCsvData,
  cleanedData,
  slatedOnlyMode,
  fileInputRef,
  handleFileUpload,
  setSlatedOnlyMode,
  reprocessData,
  clearAllData
}) => {
  const [showManualCreator, setShowManualCreator] = useState(false);

  const handleManualSave = (manualData) => {
    // Set the manual data as if it was parsed from CSV
    // This converts manual input to the same format as CSV parser
    const fakeRawData = "manual_entry_data";

    // Update the parent component states
    clearAllData(); // Clear any existing data first

    // Simulate setting CSV data and cleaned data
    setTimeout(() => {
      // This mimics the CSV upload process but with manual data
      window.manualDeliveryData = manualData;

      // Close manual creator
      setShowManualCreator(false);

      // Trigger the parent to use this manual data
      if (window.setManualData) {
        window.setManualData(manualData);
      }
    }, 100);
  };

  const handleManualCancel = () => {
    setShowManualCreator(false);
  };

  // If showing manual creator, render that instead
  if (showManualCreator) {
    return (
      <ManualDeliveryCreator
        onSave={handleManualSave}
        onCancel={handleManualCancel}
      />
    );
  }

  return (
    <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-8 mb-8">
      <h2 className="text-xl font-semibold text-white mb-6 text-center">Upload Delivery Schedule or Create Manually</h2>

      <div className="flex flex-col items-center max-w-2xl mx-auto">
        {/* Centered Upload Area */}
        <div
          className="border-2 border-dashed border-neutral-500 rounded-lg p-12 text-center hover:border-blue-500 transition-colors cursor-pointer w-full mb-6"
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload className="mx-auto text-neutral-400 mb-4" size={64} />
          <p className="text-white font-medium mb-2 text-lg">
            {rawCsvData ? '✅ CSV file loaded' : 'Click to upload CSV file'}
          </p>
          <p className="text-neutral-400 text-sm">
            {cleanedData ? `${cleanedData.summary.total_slated_deliverables} deliverables found` : 'Upload your Blacksmith delivery schedule'}
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>

        {/* Manual Creation Button - Only show when no CSV is loaded */}
        {!rawCsvData && (
          <div className="w-full">
            <div className="flex items-center mb-4">
              <div className="flex-1 h-px bg-neutral-500"></div>
              <span className="px-4 text-neutral-400 text-sm">OR</span>
              <div className="flex-1 h-px bg-neutral-500"></div>
            </div>

            <button
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 px-6 rounded-lg flex items-center justify-center gap-3 transition-colors text-lg font-medium"
              onClick={() => setShowManualCreator(true)}
            >
              <FileText size={24} />
              Manual Creation
            </button>
            <p className="text-neutral-400 text-xs text-center mt-2">
              Create delivery slates manually without uploading a file
            </p>
          </div>
        )}

        {/* Cancel/Clear CSV Button - Only show when CSV is loaded */}
        {rawCsvData && (
          <div className="w-full">
            <div className="flex items-center justify-between bg-neutral-600 rounded-lg p-4">
              <div className="flex items-center gap-3">
                <CheckCircle className="text-green-400" size={24} />
                <div>
                  <p className="text-white font-medium">CSV File Loaded</p>
                  <p className="text-neutral-400 text-sm">{cleanedData?.summary.total_slated_deliverables || 0} deliverables ready</p>
                </div>
              </div>
              <button
                onClick={clearAllData}
                className="bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg flex items-center gap-2 transition-colors"
              >
                <Trash2 size={16} />
                Clear
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Parsed Summary - Only show when CSV is loaded */}
      {cleanedData && (
        <div className="bg-neutral-600 rounded-lg p-6 mt-6 max-w-2xl mx-auto">
          <h3 className="text-white font-medium mb-4 text-center">Parsed Summary</h3>

          {/* Slated Only Toggle */}
          <div className="flex items-center justify-center mb-4 p-3 bg-neutral-700 rounded-lg">
            <div className="flex items-center gap-3">
              <span className={`text-sm ${!slatedOnlyMode ? 'text-blue-400 font-medium' : 'text-neutral-400'}`}>
                All Deliverables
              </span>
              <button
                onClick={() => {
                  const newMode = !slatedOnlyMode;
                  setSlatedOnlyMode(newMode);
                  // Reprocess the data with new mode
                  if (rawCsvData) {
                    reprocessData(rawCsvData, newMode);
                  }
                }}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                  slatedOnlyMode ? 'bg-blue-600' : 'bg-neutral-500'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    slatedOnlyMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className={`text-sm ${slatedOnlyMode ? 'text-blue-400 font-medium' : 'text-neutral-400'}`}>
                Only "Slated"
              </span>
            </div>
            <div className="ml-4 text-xs text-neutral-400">
              {slatedOnlyMode ? 'Shows only items marked as "Slated"' : 'Shows ALL items with titles (RECOMMENDED)'}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-neutral-400">Total Videos:</span>
                <span className="text-blue-400">{cleanedData.summary.total_videos}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Total Deliverables:</span>
                <span className="text-green-400">{cleanedData.summary.total_slated_deliverables}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-neutral-400">Client:</span>
                <span className="text-purple-400">{cleanedData.project_info.client}</span>
              </div>
            </div>
            <div>
              <span className="text-neutral-400 block mb-2">Formats Needed:</span>
              <div className="space-y-1">
                {Object.entries(cleanedData.summary.formats_needed).map(([format, count]) => (
                  <div key={format} className="flex justify-between text-xs">
                    <span className="text-neutral-300">{format}:</span>
                    <span className="text-orange-400">{count} files</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadSection;