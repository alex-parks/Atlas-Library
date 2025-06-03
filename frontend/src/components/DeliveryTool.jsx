// frontend/src/components/DeliveryTool.jsx
import React, { useState, useRef } from 'react';
import { Upload, Download, FileText, CheckCircle, AlertCircle, Eye, Trash2, Settings, FolderOpen, Play } from 'lucide-react';

const DeliveryTool = () => {
  const [rawJsonData, setRawJsonData] = useState(null);
  const [cleanedData, setCleanedData] = useState(null);
  const [ttgFiles, setTtgFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [outputPath, setOutputPath] = useState('');
  const [previewSlate, setPreviewSlate] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const fileInputRef = useRef(null);

  // TTG Templates based on your actual files
  const ttgTemplates = {
    '1x1': {
      name: "Slate 1x1 (Square)",
      frameWidth: 1080,
      frameHeight: 1080,
      aspectRatio: 1,
      translationX: -337,
      translationY: 130,
      description: "Square format for Meta 1:1"
    },
    '4x5': {
      name: "Slate 4x5 (Portrait)",
      frameWidth: 864,
      frameHeight: 1080,
      aspectRatio: 0.800000012,
      translationX: -244,
      translationY: 130,
      description: "Portrait format for Pinterest"
    },
    '9x16': {
      name: "Slate 9x16 (Vertical)",
      frameWidth: 1080,
      frameHeight: 1920,
      aspectRatio: 0.5625,
      translationX: -342,
      translationY: 128.111115,
      description: "Vertical format for TikTok/Stories"
    },
    '16x9': {
      name: "Slate 16x9 (Widescreen)",
      frameWidth: 1920,
      frameHeight: 1080,
      aspectRatio: 1.77777779,
      translationX: -440,
      translationY: 130,
      description: "Widescreen format for YouTube/OTT"
    }
  };

  // Platform to aspect ratio mapping
  const platformMapping = {
    'YouTube': '16x9',
    'Youtube': '16x9',
    'TikTok + YouTube Shorts': '9x16',
    'Stories (Vertical)': '9x16',
    'Meta 1:1': '1x1',
    'Meta': '1x1',
    'Pinterest': '4x5',
    'OTT SPECS': '16x9',
    'Youtube Specs (For Google)': '16x9',
    'Under 100 mb': '16x9'
  };

  const parseAndCleanDeliveryJSON = (data) => {
    const deliveries = [];
    let currentTitle = '';
    let headerInfo = {
      agency: 'N/A',
      client: 'N/A',
      product: 'N/A',
      title: 'N/A',
      isci: 'N/A',
      duration: 'N/A',
      audio: 'N/A',
      copyright: 'N/A'
    };

    // Dynamically detect column names from the first row
    const firstRow = data[0] || {};
    const columnNames = Object.keys(firstRow);
    const mainColumn = columnNames[0] || ''; // First column (usually the project name)
    const specsColumn = columnNames[1] || ''; // Second column (usually specs)

    console.log('Detected columns:', columnNames);
    console.log('Main column:', mainColumn);
    console.log('Specs column:', specsColumn);

    // Extract header information (rows 2-11) - Parse the SLATE INFORMATION section
    for (let i = 2; i <= 11; i++) {
      if (data[i]) {
        const key = data[i][mainColumn];
        if (key && key.includes(':')) {
          const [field, value] = key.split(':');
          const cleanField = field.trim().toLowerCase();
          const cleanValue = value ? value.trim() : 'N/A';

          if (cleanField === 'agency') headerInfo.agency = cleanValue || 'N/A';
          if (cleanField === 'client') headerInfo.client = cleanValue || 'N/A';
          if (cleanField === 'product') headerInfo.product = cleanValue || 'N/A';
          if (cleanField === 'title') headerInfo.title = cleanValue || 'N/A';
          if (cleanField === 'isci') headerInfo.isci = cleanValue || 'N/A';
          if (cleanField === 'duration') headerInfo.duration = cleanValue || 'N/A';
          if (cleanField === 'audio') headerInfo.audio = cleanValue || 'N/A';
          if (cleanField === 'copyright') headerInfo.copyright = cleanValue || 'N/A';
        }
      }
    }

    // Parse delivery items (starting from row 14)
    for (let i = 14; i < data.length; i++) {
      const row = data[i];
      const col1 = row[mainColumn] || '';
      const col2 = row[specsColumn] || '';
      const aspectRatioCol = row["Aspect Ratio"] || '';

      // Skip empty rows
      if (!col1 && !col2) continue;

      // Check if this is a title row (contains duration like :30, :15, etc.)
      if (col1 && (col1.includes(':') && /:\d+/.test(col1)) && !col2) {
        currentTitle = col1;
        continue;
      }

      // Check if this is a delivery item (has ship date and specs)
      if (col1 && col2 && currentTitle) {
        // Skip ProRes Unslated items
        if (col2.includes('ProRes Unslated')) {
          continue;
        }

        let shipDate = col1;
        const specs = col2;

        // Parse date formats
        if (shipDate.includes('2025-')) {
          shipDate = shipDate.split('T')[0]; // Remove time part
        } else if (shipDate.includes('/')) {
          const [month, day] = shipDate.split('/');
          shipDate = `2025-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        }

        // Extract duration from current title (e.g., ":15" from "SIP IT TEASER :15")
        let duration = 'N/A';
        const durationMatch = currentTitle.match(/:(\d+)/);
        if (durationMatch) {
          duration = `:${durationMatch[1]}`;
        }

        // Determine suggested format from specs (parsing ASPECT RATIO from specs text)
        let suggestedFormat = '16x9'; // default
        let platform = 'Other';

        // Look for aspect ratio in the specs text
        if (specs.includes('ASPECT RATIO: 16x9') || specs.includes('16x9')) {
          suggestedFormat = '16x9';
        } else if (specs.includes('ASPECT RATIO: 9x16') || specs.includes('9x16')) {
          suggestedFormat = '9x16';
        } else if (specs.includes('ASPECT RATIO: 1x1') || specs.includes('1x1') || specs.includes('1:1')) {
          suggestedFormat = '1x1';
        } else if (specs.includes('ASPECT RATIO: 4x5') || specs.includes('4x5') || specs.includes('4:5')) {
          suggestedFormat = '4x5';
        } else {
          // Fallback to platform mapping
          for (const [platformName, format] of Object.entries(platformMapping)) {
            if (specs.includes(platformName)) {
              suggestedFormat = format;
              platform = platformName;
              break;
            }
          }
        }

        // Extract platform from specs for display
        for (const [platformName] of Object.entries(platformMapping)) {
          if (specs.includes(platformName)) {
            platform = platformName;
            break;
          }
        }

        // Create formatted title with aspect ratio (e.g., "SIP IT TEASER :15 16x9")
        const formattedTitle = `${currentTitle} ${suggestedFormat}`;

        deliveries.push({
          id: deliveries.length + 1,
          video_title: formattedTitle,
          original_title: currentTitle,
          ship_date: shipDate,
          platform: platform,
          specs: specs,
          aspect_ratio: aspectRatioCol,
          suggested_slate_format: suggestedFormat,
          duration: duration,
          agency: headerInfo.agency,
          client: headerInfo.client,
          product: headerInfo.product,
          isci: headerInfo.isci,
          audio: headerInfo.audio,
          copyright: headerInfo.copyright
        });
      }
    }

    // Create summary
    const formatCounts = {};
    deliveries.forEach(d => {
      formatCounts[d.suggested_slate_format] = (formatCounts[d.suggested_slate_format] || 0) + 1;
    });

    const uniquePlatforms = [...new Set(deliveries.map(d => d.platform))];
    const uniqueVideos = [...new Set(deliveries.map(d => d.original_title))];

    return {
      project_info: headerInfo,
      deliverables: deliveries,
      summary: {
        total_slated_deliverables: deliveries.length,
        total_videos: uniqueVideos.length,
        date_range: deliveries.length > 0 ?
          `${Math.min(...deliveries.map(d => d.ship_date))} to ${Math.max(...deliveries.map(d => d.ship_date))}` : '',
        formats_needed: formatCounts,
        platforms: uniquePlatforms
      }
    };
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (file.name.endsWith('.json')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          setRawJsonData(data);

          const cleaned = parseAndCleanDeliveryJSON(data);
          setCleanedData(cleaned);
          console.log('Cleaned data:', cleaned);
        } catch (error) {
          alert('Invalid JSON file. Please check the format.');
        }
      };
      reader.readAsText(file);
    } else {
      alert('Please upload a JSON file.');
    }
  };

  const generateTTGContent = (delivery, templateKey) => {
    const template = ttgTemplates[templateKey];
    const currentDate = new Date().toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      second: '2-digit',
      year: 'numeric'
    });

    // Helper function to convert text to ASCII codes
    const textToAsciiCodes = (text) => {
      return Array.from(text).map(char => char.charCodeAt(0)).join(' ');
    };

    // Format today's date for slate (e.g., "June 3 2025")
    const todaysDate = new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });

    // Build the text fields for slate - exact field mapping as requested
    const slateFields = [
      { value: delivery.agency || 'N/A' },           // Agency from JSON header
      { value: delivery.client || 'N/A' },           // Client from JSON header
      { value: delivery.product || 'N/A' },          // Product from JSON header
      { value: delivery.video_title || 'N/A' },      // Title / Version (e.g., "SIP IT TEASER :15 16x9")
      { value: delivery.isci || 'N/A' },             // ISCI / AD-ID from JSON header
      { value: delivery.duration || 'N/A' },         // Duration (e.g., ":15")
      { value: delivery.audio || 'N/A' },            // Audio Mix from JSON header
      { value: todaysDate },                         // Today's date (not ship date!)
      { value: delivery.copyright || 'N/A' }         // Copyright from JSON header
    ];

    // Generate paragraph sections for each field - exact format match
    let paragraphSections = '';

    slateFields.forEach((field, index) => {
      const isLast = index === slateFields.length - 1;
      const asciiCodes = textToAsciiCodes(field.value);

      paragraphSections += `TextLength ${field.value.length}
Text ${asciiCodes}
ParagraphType Inside

#
# layer paragraph channels
#
Channel leading
	Extrapolation constant
	Value 17.5
	End
ChannelEnd
TransformHasOffset no
End
#
# layer paragraph ruler
#
Justification Justify_Left
LeftMargin 0
LeftIndent 0
RightMargin 1535
End
`;
    });

    // Generate the complete TTG content - exact format match
    const ttgContent = `Module Text
Program Flame
Version 2025.2.2
FileVersion 4.19999981
CreationDate ${currentDate}

FrameWidth ${template.frameWidth}
FrameHeight ${template.frameHeight}
FrameAspectRatio ${template.aspectRatio}

	CurrentFrame 55
	MaxFrames -1
	UpdateMode yes
	PlayLockMode no
	UndoLevels 10
	FieldRenderingModeAuto 0
	GaussianBlur yes
	GlobalBlur yes
	BlurOn no
	BlurLevel 5
	AntiAliasingLevel 0
	AntiAliasingSoftness 1
	MultiSample 0
	PreRender 1
	CropBox no
	CropLeft 0
	CropRight 1919
	CropBottom 0
	CropTop 1079
	MatteKey yes
End
NumberOfLayer 1

#
# text layer channels
#
Channel translation/x
	Extrapolation constant
	Value ${template.translationX}
	Uncollapsed
	End
Channel translation/y
	Extrapolation constant
	Value ${template.translationY}
	Uncollapsed
	End
Channel translation/speed
	Extrapolation linear
	Value 0
	Uncollapsed
	End
Channel shear/x
	Extrapolation linear
	Value 0
	End
Channel shear/y
	Extrapolation linear
	Value 0
	End
Channel scale/x
	Extrapolation linear
	Value 100
	Uncollapsed
	End
Channel scale/y
	Extrapolation linear
	Value 100
	Uncollapsed
	End
Channel rotation
	Extrapolation linear
	Value 0
	Uncollapsed
	End
ChannelEnd
TransformHasOffset no
End

#
# text layer data
#
ExtraChannels
Channel transparency
	Extrapolation linear
	Value 100
	Uncollapsed
	End
ChannelEnd
BlurShadow no
BlurShadowFactor 5
DocWidth 1535
DocHeight 0
LayerAxisLocked no
DocBackground no
ColourBack 100 100 100 100
DocInterpType 0
FontType 0
FontName /opt/Autodesk/font/Discreet
FontSize 25
UnderlineWidth 50
FontStyle Fill
ColourFill 100 100 100 50
ColourOut 0 0 100 100
ColourDrop 0 0 0 100
ColorUnderline 100 100 100 100
${paragraphSections}FontSize 50
ColourFill 100 100 100 100
ColourOut 0 0 100 100
ColourDrop 0 0 0 50
ColorUnderline 100 100 100 100
ParagraphType Last

#
# layer paragraph channels
#
Channel leading
	Extrapolation constant
	Value 17.5
	End
ChannelEnd
TransformHasOffset no
End
#
# layer paragraph ruler
#
Justification Justify_Left
LeftMargin 0
LeftIndent 0
RightMargin 1535
End
EndLayer
EndGen`;

    return ttgContent;
  };

  const generateAllTTGFiles = () => {
    if (!cleanedData || !cleanedData.deliverables.length) {
      alert('Please upload and process a delivery JSON file first.');
      return;
    }

    setIsProcessing(true);

    setTimeout(() => {
      const generatedFiles = cleanedData.deliverables.map((delivery, index) => {
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

  const selectOutputFolder = async () => {
    try {
      // Use the File System Access API for modern browsers
      if ('showDirectoryPicker' in window) {
        const dirHandle = await window.showDirectoryPicker();
        // Try to get the full path if possible
        const fullPath = dirHandle.name;
        setOutputPath(fullPath);
        console.log('Selected folder:', dirHandle);

        // Store the directory handle for later use
        window.selectedDirectoryHandle = dirHandle;
      } else {
        // Fallback: use input element with webkitdirectory
        const input = document.createElement('input');
        input.type = 'file';
        input.webkitdirectory = true;
        input.onchange = (e) => {
          const files = e.target.files;
          if (files.length > 0) {
            const firstFile = files[0];
            const pathParts = firstFile.webkitRelativePath.split('/');
            const folderPath = firstFile.path || pathParts[0];
            setOutputPath(folderPath);
          }
        };
        input.click();
      }
    } catch (error) {
      console.log('Folder selection cancelled or failed:', error);
    }
  };

  const downloadSingleTTG = (ttgFile) => {
    const blob = new Blob([ttgFile.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = ttgFile.filename;

    // Add attributes to prevent popup
    a.style.display = 'none';
    a.target = '_self';

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadAllTTG = async () => {
    if (ttgFiles.length === 0) return;

    // Try to write directly to selected folder if possible
    if (window.selectedDirectoryHandle && 'showDirectoryPicker' in window) {
      try {
        let successCount = 0;

        for (const file of ttgFiles) {
          try {
            const fileHandle = await window.selectedDirectoryHandle.getFileHandle(file.filename, { create: true });
            const writable = await fileHandle.createWritable();
            await writable.write(file.content);
            await writable.close();
            successCount++;
          } catch (error) {
            console.error(`Failed to write ${file.filename}:`, error);
          }
        }

        if (successCount === ttgFiles.length) {
          alert(`Successfully saved ${successCount} TTG files to ${outputPath}`);
          return;
        } else {
          alert(`Saved ${successCount} of ${ttgFiles.length} files. Some files may have failed.`);
          return;
        }
      } catch (error) {
        console.error('Direct folder write failed:', error);
        // Fall back to download method
      }
    }

    // Fallback: Create a single ZIP file to avoid multiple popups
    try {
      // Import JSZip dynamically
      const JSZip = (await import('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js')).default;
      const zip = new JSZip();

      // Add each TTG file to the zip
      ttgFiles.forEach(file => {
        zip.file(file.filename, file.content);
      });

      // Generate and download the zip
      const zipBlob = await zip.generateAsync({type: 'blob'});
      const url = URL.createObjectURL(zipBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `TTG_Files_${new Date().toISOString().split('T')[0]}.zip`;
      a.style.display = 'none';

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      if (outputPath) {
        alert(`ZIP file downloaded. Please extract to: ${outputPath}`);
      } else {
        alert(`ZIP file downloaded with ${ttgFiles.length} TTG files.`);
      }

    } catch (error) {
      console.error('ZIP creation failed:', error);
      alert('Failed to create ZIP file. Please try again or contact support.');
    }
  };

  const previewTTG = (ttgFile) => {
    setPreviewSlate(ttgFile);
  };

  return (
    <div className="p-6 bg-neutral-800 min-h-full text-white">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Delivery Tool</h1>
        <p className="text-gray-400">Upload delivery schedule JSON, auto-parse, and generate TTG slate files for Flame</p>
      </div>

      {/* Step 1: Upload - Centered */}
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
              {rawJsonData ? '✅ JSON file loaded' : 'Click to upload JSON file'}
            </p>
            <p className="text-neutral-400 text-sm">
              {cleanedData ? `${cleanedData.deliverables.length} slated deliverables found` : 'Upload your Blacksmith delivery schedule'}
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>

          {/* Manual Creation Button - Only show when no JSON is loaded */}
          {!rawJsonData && (
            <div className="w-full">
              <div className="flex items-center mb-4">
                <div className="flex-1 h-px bg-neutral-500"></div>
                <span className="px-4 text-neutral-400 text-sm">OR</span>
                <div className="flex-1 h-px bg-neutral-500"></div>
              </div>

              <button
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 px-6 rounded-lg flex items-center justify-center gap-3 transition-colors text-lg font-medium"
                onClick={() => {/* TODO: Implement manual creation */}}
              >
                <FileText size={24} />
                Manual Creation
              </button>
              <p className="text-neutral-400 text-xs text-center mt-2">
                Create delivery slates manually without uploading a file
              </p>
            </div>
          )}

          {/* Cancel/Clear JSON Button - Only show when JSON is loaded */}
          {rawJsonData && (
            <div className="w-full">
              <div className="flex items-center justify-between bg-neutral-600 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <CheckCircle className="text-green-400" size={24} />
                  <div>
                    <p className="text-white font-medium">JSON File Loaded</p>
                    <p className="text-neutral-400 text-sm">{cleanedData?.deliverables.length || 0} deliverables ready</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setRawJsonData(null);
                    setCleanedData(null);
                    setTtgFiles([]);
                  }}
                  className="bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <Trash2 size={16} />
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Parsed Summary - Only show when JSON is loaded */}
        {cleanedData && (
          <div className="bg-neutral-600 rounded-lg p-6 mt-6 max-w-2xl mx-auto">
            <h3 className="text-white font-medium mb-4 text-center">Parsed Summary</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-neutral-400">Total Videos:</span>
                  <span className="text-blue-400">{cleanedData.summary.total_videos}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">Slated Deliverables:</span>
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

      {/* Step 2: Output Path - Only show when JSON is loaded */}
      {cleanedData && (
        <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">2. Set Output Path</h2>
          <div className="flex gap-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Click Browse to select output folder..."
                value={outputPath}
                onChange={(e) => setOutputPath(e.target.value)}
                className="w-full bg-neutral-600 border border-neutral-500 rounded-lg px-4 py-3 text-white placeholder-neutral-400 focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              onClick={selectOutputFolder}
              className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg flex items-center gap-2 transition-colors text-white"
            >
              <FolderOpen size={18} />
              Browse
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Preview & Generate */}
      {cleanedData && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">3. Preview & Generate TTG Files</h2>
            <div className="flex gap-3">
              <button
                onClick={() => setShowPreview(!showPreview)}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
              >
                <Eye size={18} />
                {showPreview ? 'Hide Preview' : 'Show Preview'}
              </button>
              <button
                onClick={generateAllTTGFiles}
                disabled={isProcessing}
                className={`px-6 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  isProcessing
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {isProcessing ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Generating...
                  </>
                ) : (
                  <>
                    <Play size={18} />
                    Generate All TTG Files
                  </>
                )}
              </button>
            </div>
          </div>

          {/* File Preview */}
          {showPreview && (
            <div className="bg-neutral-600 rounded-lg p-4 mb-6">
              <h3 className="text-white font-medium mb-3">Files that will be generated:</h3>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {cleanedData.deliverables.map((delivery, index) => {
                  const safeTitle = delivery.video_title.replace(/[^a-zA-Z0-9\-_]/g, '_');
                  const safePlatform = delivery.platform.replace(/[^a-zA-Z0-9\-_]/g, '_');
                  const filename = `${safeTitle}_${safePlatform}_${delivery.suggested_slate_format}_slate.ttg`;

                  return (
                    <div key={index} className="flex items-center justify-between bg-neutral-500 rounded p-3">
                      <div className="flex items-center gap-3">
                        <FileText className="text-blue-400" size={16} />
                        <span className="text-white text-sm font-mono">{filename}</span>
                      </div>
                      <div className="flex items-center gap-3 text-xs">
                        <span className="text-neutral-400">{delivery.ship_date}</span>
                        <span className={`px-2 py-1 rounded text-white ${
                          delivery.suggested_slate_format === '16x9' ? 'bg-blue-600' :
                          delivery.suggested_slate_format === '9x16' ? 'bg-green-600' :
                          delivery.suggested_slate_format === '1x1' ? 'bg-purple-600' :
                          'bg-orange-600'
                        }`}>
                          {delivery.suggested_slate_format}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Generated Files */}
      {ttgFiles.length > 0 && (
        <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">
              Generated TTG Files ({ttgFiles.length})
            </h2>
            <button
              onClick={downloadAllTTG}
              className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Download size={18} />
              Download All
            </button>
          </div>

          <div className="space-y-3 max-h-96 overflow-y-auto">
            {ttgFiles.map((file) => (
              <div key={file.id} className="bg-neutral-600 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <FileText className="text-blue-400" size={24} />
                  <div>
                    <h3 className="text-white font-medium text-sm">{file.filename}</h3>
                    <p className="text-neutral-400 text-xs">
                      {file.delivery.video_title} • {file.delivery.platform} • {file.template} • {Math.round(file.size / 1024)} KB
                    </p>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => previewTTG(file)}
                    className="bg-neutral-500 hover:bg-neutral-400 text-white p-2 rounded-lg transition-colors"
                    title="Preview"
                  >
                    <Eye size={16} />
                  </button>
                  <button
                    onClick={() => downloadSingleTTG(file)}
                    className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors"
                    title="Download"
                  >
                    <Download size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {previewSlate && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">Preview: {previewSlate.filename}</h3>
              <button
                onClick={() => setPreviewSlate(null)}
                className="text-neutral-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="bg-neutral-800 rounded-lg p-4">
              <pre className="text-green-400 text-sm font-mono whitespace-pre-wrap max-h-96 overflow-auto">
                {previewSlate.content}
              </pre>
            </div>

            <div className="mt-4 flex gap-2">
              <button
                onClick={() => downloadSingleTTG(previewSlate)}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2"
              >
                <Download size={16} />
                Download
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeliveryTool;