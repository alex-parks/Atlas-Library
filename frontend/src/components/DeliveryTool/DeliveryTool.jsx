// frontend/src/components/DeliveryTool/DeliveryTool.jsx

import React, { useState, useRef, useEffect } from 'react';
import { parseDeliverableSheetWithMode } from './utils/csvParser';
import { generateTTGContent, ttgTemplates, parseTTGContent } from './utils/ttgTemplates';
import UploadSection from './components/UploadSection';
import OutputPathSection from './components/OutputPathSection';
import GroupSelection from './components/GroupSelection';
import PreviewSection from './components/PreviewSection';
import GeneratedFiles from './components/GeneratedFiles';
import PreviewModal from './components/PreviewModal';

const DeliveryTool = () => {
  // State management
  const [rawCsvData, setRawCsvData] = useState(null);
  const [cleanedData, setCleanedData] = useState(null);
  const [ttgFiles, setTtgFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [outputPath, setOutputPath] = useState('');
  const [previewSlate, setPreviewSlate] = useState(null);
  const [previewFormat, setPreviewFormat] = useState('readable');
  const [enabledGroups, setEnabledGroups] = useState(new Set());
  const [enabledDeliverables, setEnabledDeliverables] = useState(new Set());
  const [slatedOnlyMode, setSlatedOnlyMode] = useState(true);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef(null);

  // Set up manual data handler
  useEffect(() => {
    window.setManualData = (manualData) => {
      setRawCsvData("manual_entry");
      setCleanedData(manualData);
      // Initialize all groups as enabled by default
      setEnabledGroups(new Set(manualData.deliverable_groups.map(group => group.groupTitle)));
      setEnabledDeliverables(new Set());
      console.log('Manual data loaded:', manualData);
    };

    return () => {
      delete window.setManualData;
    };
  }, []);

  // File upload handler
  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (file.name.endsWith('.csv')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const csvData = e.target.result;
          setRawCsvData(csvData);
          reprocessData(csvData, slatedOnlyMode);
        } catch (error) {
          alert('Invalid CSV file. Please check the format.');
        }
      };
      reader.readAsText(file);
    } else {
      alert('Please upload a CSV file.');
    }
  };

  // Function to reprocess data when toggle changes
  const reprocessData = (csvData, slatedOnly) => {
    // Don't reprocess manual data
    if (csvData === "manual_entry") {
      return;
    }

    const cleaned = parseDeliverableSheetWithMode(csvData, slatedOnly);
    setCleanedData(cleaned);
    // Initialize all groups as enabled by default
    setEnabledGroups(new Set(cleaned.deliverable_groups.map(group => group.groupTitle)));
    // Initialize individual deliverables as DISABLED by default
    setEnabledDeliverables(new Set());
    console.log('Cleaned data:', cleaned);
  };

  // Generate TTG files
  const generateAllTTGFiles = () => {
    if (!cleanedData || !cleanedData.deliverable_groups.length) {
      alert('Please upload and process a delivery CSV file first.');
      return;
    }

    // Get deliverables based on group/individual selection
    let enabledDeliverablesList = [];

    cleanedData.deliverable_groups.forEach(group => {
      if (enabledGroups.has(group.groupTitle)) {
        // Entire group is enabled, include all deliverables
        enabledDeliverablesList.push(...group.deliverables);
      } else {
        // Check individual deliverables
        const individualEnabled = group.deliverables.filter(d => enabledDeliverables.has(d.id));
        enabledDeliverablesList.push(...individualEnabled);
      }
    });

    if (enabledDeliverablesList.length === 0) {
      alert('Please enable at least one deliverable group or individual deliverable.');
      return;
    }

    setIsProcessing(true);

    setTimeout(() => {
      const generatedFiles = enabledDeliverablesList.map((delivery, index) => {
        const ttgContent = generateTTGContent(delivery, delivery.suggested_slate_format);
        const safeTitle = delivery.video_title.replace(/[^a-zA-Z0-9\-_]/g, '_');
        const safePlatform = delivery.platform.replace(/[^a-zA-Z0-9\-_]/g, '_');

        return {
          id: index + 1,
          filename: `${safeTitle}_${safePlatform}_${delivery.suggested_slate_format}_slate.ttg`,
          content: ttgContent,
          delivery: delivery,
          template: ttgTemplates[delivery.suggested_slate_format].name,
          size: new Blob([ttgContent]).size
        };
      });

      setTtgFiles(generatedFiles);
      setIsProcessing(false);
    }, 2000);
  };

  // Clear all data
  const clearAllData = () => {
    setRawCsvData(null);
    setCleanedData(null);
    setTtgFiles([]);
    setEnabledGroups(new Set());
    setEnabledDeliverables(new Set());
    setSlatedOnlyMode(false);
  };

  return (
    <div className="p-6 bg-neutral-800 min-h-full text-white">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Delivery Tool</h1>
        <p className="text-gray-400">Upload delivery schedule CSV, auto-parse, and generate TTG slate files for Flame</p>
      </div>

      {/* Step 1: Upload Section */}
      <UploadSection
        rawCsvData={rawCsvData}
        cleanedData={cleanedData}
        slatedOnlyMode={slatedOnlyMode}
        fileInputRef={fileInputRef}
        handleFileUpload={handleFileUpload}
        setSlatedOnlyMode={setSlatedOnlyMode}
        reprocessData={reprocessData}
        clearAllData={clearAllData}
      />

      {/* Step 2: Output Path - Only show when CSV is loaded */}
      {cleanedData && (
        <OutputPathSection
          outputPath={outputPath}
          setOutputPath={setOutputPath}
        />
      )}

      {/* Step 3: Deliverable Groups Selection */}
      {cleanedData && (
        <GroupSelection
          cleanedData={cleanedData}
          enabledGroups={enabledGroups}
          setEnabledGroups={setEnabledGroups}
          enabledDeliverables={enabledDeliverables}
          setEnabledDeliverables={setEnabledDeliverables}
        />
      )}

      {/* Step 4: Preview & Generate */}
      {cleanedData && (enabledGroups.size > 0 || enabledDeliverables.size > 0) && (
        <PreviewSection
          cleanedData={cleanedData}
          enabledGroups={enabledGroups}
          enabledDeliverables={enabledDeliverables}
          showPreview={showPreview}
          setShowPreview={setShowPreview}
          isProcessing={isProcessing}
          generateAllTTGFiles={generateAllTTGFiles}
        />
      )}

      {/* Generated Files */}
      {ttgFiles.length > 0 && (
        <GeneratedFiles
          ttgFiles={ttgFiles}
          outputPath={outputPath}
          setPreviewSlate={setPreviewSlate}
        />
      )}

      {/* Preview Modal */}
      {previewSlate && (
        <PreviewModal
          previewSlate={previewSlate}
          previewFormat={previewFormat}
          setPreviewFormat={setPreviewFormat}
          setPreviewSlate={setPreviewSlate}
          parseTTGContent={parseTTGContent}
        />
      )}
    </div>
  );
};

export default DeliveryTool;