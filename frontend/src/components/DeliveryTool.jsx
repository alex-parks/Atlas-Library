// frontend/src/components/DeliveryTool.jsx - COMPLETE FIXED VERSION
import React, { useState, useRef } from 'react';
import { Upload, Download, FileText, CheckCircle, AlertCircle, Eye, Trash2, Settings, FolderOpen, Play } from 'lucide-react';
import ManualDeliveryCreator from './ManualDeliveryCreator';

const DeliveryTool = () => {
  const [rawJsonData, setRawJsonData] = useState(null);
  const [cleanedData, setCleanedData] = useState(null);
  const [ttgFiles, setTtgFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [outputPath, setOutputPath] = useState('');
  const [previewSlate, setPreviewSlate] = useState(null);
  const [previewFormat, setPreviewFormat] = useState('readable'); // 'readable' or 'ttg'
  const [showPreview, setShowPreview] = useState(false);
  const [showManualCreator, setShowManualCreator] = useState(false);
  const [parseError, setParseError] = useState(null);
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

  // Enhanced platform to aspect ratio mapping
  const platformMapping = {
    'YouTube': '16x9',
    'Youtube': '16x9',
    'TikTok + YouTube Shorts': '9x16',
    'TikTok': '9x16',
    'Stories (Vertical)': '9x16',
    'IG Stories': '9x16',
    'Instagram Stories': '9x16',
    'Meta 1:1': '1x1',
    'Meta': '1x1',
    'Facebook': '1x1',
    'Pinterest': '4x5',
    'OTT SPECS': '16x9',
    'OTT': '16x9',
    'Youtube Specs (For Google)': '16x9',
    'Google': '16x9',
    'Under 100 mb': '16x9',
    'TV': '16x9',
    'Broadcast': '16x9',
    'Web': '16x9'
  };

  // Function to parse TTG content into readable format
  const parseTTGContent = (ttgContent) => {
    const lines = ttgContent.split('\n');

    const asciiToText = (asciiCodes) => {
      return asciiCodes.split(' ').map(code => String.fromCharCode(parseInt(code))).join('');
    };

    const textFields = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      if (line.startsWith('TextLength ')) {
        const nextLine = lines[i + 1]?.trim();

        if (nextLine && nextLine.startsWith('Text ')) {
          const asciiCodes = nextLine.substring(5);
          try {
            const text = asciiToText(asciiCodes);
            textFields.push(text);
          } catch (error) {
            textFields.push('N/A');
          }
        }
      }
    }

    const fieldLabels = [
      'Agency',
      'Client',
      'Product',
      'Title / Version',
      'ISCI / AD-ID',
      'Duration',
      'Audio Mix',
      'Date',
      'Copyright'
    ];

    const parsedData = {};
    fieldLabels.forEach((label, index) => {
      parsedData[label] = textFields[index] || 'N/A';
    });

    return parsedData;
  };

  // ENHANCED JSON PARSER with better debugging and error handling
  // Generic parseAndCleanDeliveryJSON - finds actual values from any JSON structure
  // Excel-to-JSON parser - handles your exact spreadsheet structure
const parseAndCleanDeliveryJSON = (data) => {
  const deliveries = [];
  let currentTitle = '';

  // In your JSON, you have 2 columns:
  // Column A: "Venmo 'Venmo Everything'"
  // Column B: "" (empty string key)
  const columnA = Object.keys(data[0])[0]; // First column key
  const columnB = Object.keys(data[0])[1]; // Second column key (empty string)

  // Extract slate information from the structure you described
  let headerInfo = {
    agency: '',      // Row 3 (index 2) - look for actual value
    client: '',      // Row 4 (index 3) - look for actual value
    product: '',     // Row 5 (index 4) - look for actual value
    title: '',       // Will be extracted per video
    isci: '',        // Will be extracted per delivery
    duration: '',    // Will be extracted from video titles
    audio: '',       // Will be extracted per delivery
    copyright: ''    // Row 11 (index 10) - look for actual value
  };

  // EXTRACT SLATE INFORMATION
  // Based on your description: rows 3-12 (indices 2-11) contain slate info

  // Row 3 (index 2): Agency
  if (data[2] && data[2][columnA] && data[2][columnA].includes('Agency:')) {
    // Look for value in column B or C (but your JSON only has A and B)
    const agencyValue = data[2][columnB] || '';
    if (agencyValue.trim()) {
      headerInfo.agency = agencyValue.trim();
    } else {
      // If no value in column B, look in next rows for the actual agency
      for (let i = 3; i <= 6; i++) {
        if (data[i] && data[i][columnB] && data[i][columnB].trim() &&
            !data[i][columnB].includes(':') && data[i][columnB].length < 50) {
          headerInfo.agency = data[i][columnB].trim();
          break;
        }
      }
    }
  }

  // Row 4 (index 3): Client
  if (data[3] && data[3][columnA] && data[3][columnA].includes('Client:')) {
    const clientValue = data[3][columnB] || '';
    if (clientValue.trim()) {
      headerInfo.client = clientValue.trim();
    } else {
      // Extract from column name if empty (like "Venmo 'Venmo Everything'" -> "Venmo")
      if (columnA && columnA.includes("'")) {
        headerInfo.client = columnA.split("'")[0].trim();
      } else if (columnA && columnA.includes(' ')) {
        headerInfo.client = columnA.split(' ')[0].trim();
      }
    }
  }

  // Row 5 (index 4): Product
  if (data[4] && data[4][columnA] && data[4][columnA].includes('Product:')) {
    const productValue = data[4][columnB] || '';
    if (productValue.trim()) {
      headerInfo.product = productValue.trim();
    } else if (headerInfo.client) {
      headerInfo.product = `${headerInfo.client} Campaign`;
    }
  }

  // Row 11 (index 10): Copyright
  if (data[10] && data[10][columnA] && data[10][columnA].includes('Copyright:')) {
    const copyrightValue = data[10][columnB] || '';
    if (copyrightValue.trim()) {
      headerInfo.copyright = copyrightValue.trim();
    } else if (headerInfo.client) {
      headerInfo.copyright = `©${new Date().getFullYear()} ${headerInfo.client}. All rights reserved.`;
    }
  }

  // Set defaults if we found a client but other fields are empty
  if (headerInfo.client && !headerInfo.agency) {
    headerInfo.agency = 'Agency TBD';
  }
  if (headerInfo.client && !headerInfo.product) {
    headerInfo.product = `${headerInfo.client} Campaign`;
  }
  if (headerInfo.client && !headerInfo.copyright) {
    headerInfo.copyright = `©${new Date().getFullYear()} ${headerInfo.client}. All rights reserved.`;
  }

  // PARSE DELIVERIES
  // Start from row 14 (index 13) as per your description
  for (let i = 13; i < data.length; i++) {
    const row = data[i];
    const colAValue = (row[columnA] || '').toString().trim();
    const colBValue = (row[columnB] || '').toString().trim();

    // Skip empty rows
    if (!colAValue && !colBValue) continue;

    // Check if this is a title row (contains duration pattern like :15, :30, :68)
    if (colAValue && /:[0-9]+/.test(colAValue) && (!colBValue || colBValue.length < 5)) {
      currentTitle = colAValue;
      continue;
    }

    // Check if this is a delivery row (has date in column A and specs in column B)
    if (colAValue && colBValue && colBValue.length > 3) {
      // Skip ProRes Unslated items
      if (colBValue.toLowerCase().includes('prores unslated')) {
        continue;
      }

      // Skip rows with empty specs
      if (!colBValue.trim()) {
        continue;
      }

      let shipDate = colAValue;
      const specs = colBValue;

      // Parse date formats
      let formattedDate = shipDate;
      if (shipDate.includes('2025-') || shipDate.includes('2024-')) {
        // ISO format: 2025-05-27T07:00:00.000Z -> 2025-05-27
        formattedDate = shipDate.split('T')[0];
      } else if (shipDate.includes('/')) {
        // MM/DD format -> 2025-MM-DD
        const parts = shipDate.split('/');
        if (parts.length >= 2) {
          const month = parts[0].padStart(2, '0');
          const day = parts[1].padStart(2, '0');
          formattedDate = `2025-${month}-${day}`;
        }
      }

      // Extract duration from current title
      let duration = '';
      if (currentTitle) {
        const durationMatch = currentTitle.match(/:(\d+)/);
        if (durationMatch) {
          duration = `:${durationMatch[1]}`;
        }
      }

      // Determine format based on specs
      let suggestedFormat = '16x9'; // default
      let platform = 'Other';

      // Check for explicit aspect ratio in specs
      if (/aspect.ratio[:\s]*16[:\s]*9|16x9|16:9/i.test(specs)) {
        suggestedFormat = '16x9';
      } else if (/aspect.ratio[:\s]*9[:\s]*16|9x16|9:16/i.test(specs)) {
        suggestedFormat = '9x16';
      } else if (/aspect.ratio[:\s]*1[:\s]*1|1x1|1:1/i.test(specs)) {
        suggestedFormat = '1x1';
      } else if (/aspect.ratio[:\s]*4[:\s]*5|4x5|4:5/i.test(specs)) {
        suggestedFormat = '4x5';
      } else {
        // Platform-based mapping
        const platformMapping = {
          'YouTube': '16x9', 'Youtube': '16x9',
          'TikTok + YouTube Shorts': '9x16', 'TikTok': '9x16',
          'Stories (Vertical)': '9x16', 'IG Stories': '9x16',
          'Meta 1:1': '1x1', 'Meta': '1x1',
          'Pinterest': '4x5',
          'OTT SPECS': '16x9', 'OTT': '16x9',
          'Under 100 mb': '16x9',
          'Youtube Specs (For Google)': '16x9'
        };

        for (const [platformName, format] of Object.entries(platformMapping)) {
          if (specs.toLowerCase().includes(platformName.toLowerCase())) {
            suggestedFormat = format;
            platform = platformName;
            break;
          }
        }
      }

      // Extract clean platform name
      if (platform === 'Other') {
        if (specs.toLowerCase().includes('youtube')) platform = 'YouTube';
        else if (specs.toLowerCase().includes('tiktok')) platform = 'TikTok';
        else if (specs.toLowerCase().includes('stories')) platform = 'Stories';
        else if (specs.toLowerCase().includes('meta')) platform = 'Meta';
        else if (specs.toLowerCase().includes('pinterest')) platform = 'Pinterest';
        else if (specs.toLowerCase().includes('ott')) platform = 'OTT';
        else platform = specs.split(' ')[0] || 'Other';
      }

      // Create delivery
      const videoTitle = currentTitle || `Video ${deliveries.length + 1}`;
      const formattedTitle = `${videoTitle} ${suggestedFormat}`;

      deliveries.push({
        id: deliveries.length + 1,
        video_title: formattedTitle,
        original_title: videoTitle,
        ship_date: formattedDate,
        platform: platform,
        specs: specs,
        aspect_ratio: suggestedFormat,
        suggested_slate_format: suggestedFormat,
        duration: duration,
        agency: headerInfo.agency || 'Agency TBD',
        client: headerInfo.client || 'Client TBD',
        product: headerInfo.product || 'Product TBD',
        isci: 'N/A', // Not in your current JSON structure
        audio: 'Web Stereo', // Default since not in your JSON structure
        copyright: headerInfo.copyright || `©${new Date().getFullYear()} All rights reserved.`
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

  // Handle manual creation save
  const handleManualSave = (manualData) => {
    setCleanedData(manualData);
    setRawJsonData({ manual: true });
    setShowManualCreator(false);
    setParseError(null);
    console.log('Manual delivery data created:', manualData);
  };

  // Handle manual creation cancel
  const handleManualCancel = () => {
    setShowManualCreator(false);
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setParseError(null);

    if (file.name.endsWith('.json')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          setRawJsonData(data);
          console.log('Raw JSON loaded:', data);

          try {
            const cleaned = parseAndCleanDeliveryJSON(data);
            setCleanedData(cleaned);
            console.log('Successfully parsed:', cleaned);
          } catch (parseErr) {
            console.error('Parse error:', parseErr);
            setParseError(parseErr.message);
            setCleanedData(null);
          }
        } catch (error) {
          console.error('JSON parse error:', error);
          setParseError('Invalid JSON file. Please check the file format.');
          setRawJsonData(null);
          setCleanedData(null);
        }
      };
      reader.readAsText(file);
    } else {
      setParseError('Please upload a JSON file.');
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

    const textToAsciiCodes = (text) => {
      return Array.from(text).map(char => char.charCodeAt(0)).join(' ');
    };

    const todaysDate = new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });

    const slateFields = [
      { value: delivery.agency || 'N/A' },
      { value: delivery.client || 'N/A' },
      { value: delivery.product || 'N/A' },
      { value: delivery.video_title || 'N/A' },
      { value: delivery.isci || 'N/A' },
      { value: delivery.duration || 'N/A' },
      { value: delivery.audio || 'N/A' },
      { value: todaysDate },
      { value: delivery.copyright || 'N/A' }
    ];

    let paragraphSections = '';

    slateFields.forEach((field, index) => {
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
      if ('showDirectoryPicker' in window) {
        const dirHandle = await window.showDirectoryPicker();
        const fullPath = dirHandle.name;
        setOutputPath(fullPath);
        window.selectedDirectoryHandle = dirHandle;
      } else {
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
    a.style.display = 'none';
    a.target = '_self';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const downloadAllTTG = async () => {
    if (ttgFiles.length === 0) return;

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
      }
    }

    try {
      const JSZip = (await import('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js')).default;
      const zip = new JSZip();

      ttgFiles.forEach(file => {
        zip.file(file.filename, file.content);
      });

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

      {/* Parse Error Display */}
      {parseError && (
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-3 mb-2">
            <AlertCircle className="text-red-400" size={20} />
            <h3 className="text-red-400 font-medium">Parse Error</h3>
          </div>
          <p className="text-red-300 text-sm mb-3">{parseError}</p>
          <details className="text-xs text-red-200">
            <summary className="cursor-pointer">Debug Info</summary>
            <pre className="mt-2 p-2 bg-red-900/30 rounded text-xs overflow-auto">
              {rawJsonData ? JSON.stringify(rawJsonData.slice ? rawJsonData.slice(0, 5) : rawJsonData, null, 2) : 'No raw data'}
            </pre>
          </details>
        </div>
      )}

      {/* Step 1: Upload OR Manual Creation */}
      {!showManualCreator ? (
        <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-8 mb-8">
          <h2 className="text-xl font-semibold text-white mb-6 text-center">Upload Delivery Schedule or Create Manually</h2>

          <div className="flex flex-col items-center max-w-2xl mx-auto">
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

            {!rawJsonData && (
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

            {rawJsonData && (
              <div className="w-full">
                <div className="flex items-center justify-between bg-neutral-600 rounded-lg p-4">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="text-green-400" size={24} />
                    <div>
                      <p className="text-white font-medium">
                        {rawJsonData.manual ? 'Manual Deliverables Created' : 'JSON File Loaded'}
                      </p>
                      <p className="text-neutral-400 text-sm">{cleanedData?.deliverables.length || 0} deliverables ready</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setRawJsonData(null);
                      setCleanedData(null);
                      setTtgFiles([]);
                      setParseError(null);
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

          {cleanedData && (
            <div className="bg-neutral-600 rounded-lg p-6 mt-6 max-w-2xl mx-auto">
              <h3 className="text-white font-medium mb-4 text-center">
                {rawJsonData?.manual ? 'Manual Entry Summary' : 'Parsed Summary'}
              </h3>
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
      ) : (
        <ManualDeliveryCreator
          onSave={handleManualSave}
          onCancel={handleManualCancel}
        />
      )}

      {/* Step 2: Output Path */}
      {cleanedData && !showManualCreator && (
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
      {cleanedData && !showManualCreator && (
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
      {ttgFiles.length > 0 && !showManualCreator && (
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

      {/* Enhanced Preview Modal with Toggle */}
      {previewSlate && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6 max-w-4xl max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">Preview: {previewSlate.filename}</h3>
              <div className="flex items-center gap-4">
                {/* Format Toggle Switch */}
                <div className="flex items-center gap-3">
                  <span className={`text-sm ${previewFormat === 'readable' ? 'text-blue-400 font-medium' : 'text-neutral-400'}`}>
                    Readable
                  </span>
                  <button
                    onClick={() => setPreviewFormat(previewFormat === 'ttg' ? 'readable' : 'ttg')}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                      previewFormat === 'ttg' ? 'bg-blue-600' : 'bg-neutral-500'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        previewFormat === 'ttg' ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                  <span className={`text-sm ${previewFormat === 'ttg' ? 'text-blue-400 font-medium' : 'text-neutral-400'}`}>
                    TTG
                  </span>
                </div>
                <button
                  onClick={() => setPreviewSlate(null)}
                  className="text-neutral-400 hover:text-white"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="bg-neutral-800 rounded-lg p-4">
              {previewFormat === 'readable' ? (
                // Readable Format Display
                <div className="space-y-4">
                  {(() => {
                    const parsedData = parseTTGContent(previewSlate.content);
                    return Object.entries(parsedData).map(([label, value]) => (
                      <div key={label} className="flex items-start gap-4 py-2 border-b border-neutral-600 last:border-b-0">
                        <div className="w-32 flex-shrink-0">
                          <span className="text-blue-400 font-medium text-sm">{label}:</span>
                        </div>
                        <div className="flex-1">
                          <span className="text-white text-sm">"{value}"</span>
                        </div>
                      </div>
                    ));
                  })()}

                  {/* Additional Technical Info */}
                  <div className="mt-6 pt-4 border-t border-neutral-600">
                    <h4 className="text-neutral-400 text-xs font-medium mb-3 uppercase tracking-wide">Technical Details</h4>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Template:</span>
                        <span className="text-purple-400">{previewSlate.template}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">File Size:</span>
                        <span className="text-green-400">{Math.round(previewSlate.size / 1024)} KB</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Aspect Ratio:</span>
                        <span className="text-orange-400">{previewSlate.delivery.suggested_slate_format}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-neutral-400">Ship Date:</span>
                        <span className="text-cyan-400">{previewSlate.delivery.ship_date}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                // TTG Format Display (Original)
                <pre className="text-green-400 text-sm font-mono whitespace-pre-wrap max-h-96 overflow-auto">
                  {previewSlate.content}
                </pre>
              )}
            </div>

            <div className="mt-4 flex gap-2">
              <button
                onClick={() => downloadSingleTTG(previewSlate)}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center gap-2"
              >
                <Download size={16} />
                Download TTG
              </button>
              {previewFormat === 'readable' && (
                <button
                  onClick={() => {
                    const parsedData = parseTTGContent(previewSlate.content);
                    const readableText = Object.entries(parsedData)
                      .map(([label, value]) => `${label}: "${value}"`)
                      .join('\n');

                    navigator.clipboard.writeText(readableText).then(() => {
                      console.log('Readable format copied to clipboard');
                    });
                  }}
                  className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg flex items-center gap-2"
                >
                  📋 Copy Readable
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeliveryTool;