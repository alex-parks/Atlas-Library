import React, { useState, useRef } from 'react';
import { Upload, Download, FileText, CheckCircle, AlertCircle, Eye, Trash2, Settings, FolderOpen, Play } from 'lucide-react';

const DeliveryTool = () => {
  const [rawCsvData, setRawCsvData] = useState(null);
  const [cleanedData, setCleanedData] = useState(null);
  const [ttgFiles, setTtgFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [outputPath, setOutputPath] = useState('');
  const [previewSlate, setPreviewSlate] = useState(null);
  const [previewFormat, setPreviewFormat] = useState('readable'); // 'readable' or 'ttg'
  const [enabledGroups, setEnabledGroups] = useState(new Set());
  const [enabledDeliverables, setEnabledDeliverables] = useState(new Set());
  const [slatedOnlyMode, setSlatedOnlyMode] = useState(true); // New toggle state
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

  // Function to parse TTG content into readable format
  const parseTTGContent = (ttgContent) => {
    const lines = ttgContent.split('\n');

    // Extract the slate fields from the TTG content
    // TTG files store text as ASCII codes, so we need to convert them back
    const asciiToText = (asciiCodes) => {
      return asciiCodes.split(' ').map(code => String.fromCharCode(parseInt(code))).join('');
    };

    // Find all text fields in the TTG content
    const textFields = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Look for TextLength indicators
      if (line.startsWith('TextLength ')) {
        const length = parseInt(line.split(' ')[1]);
        const nextLine = lines[i + 1]?.trim();

        if (nextLine && nextLine.startsWith('Text ')) {
          const asciiCodes = nextLine.substring(5); // Remove "Text " prefix
          try {
            const text = asciiToText(asciiCodes);
            textFields.push(text);
          } catch (error) {
            textFields.push('N/A');
          }
        }
      }
    }

    // Map the fields to their labels (based on your slate structure)
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

    // Create the parsed object
    const parsedData = {};
    fieldLabels.forEach((label, index) => {
      parsedData[label] = textFields[index] || 'N/A';
    });

    return parsedData;
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (file.name.endsWith('.csv')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const csvData = e.target.result;
          setRawCsvData(csvData);

          // Parse and set data
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
    const cleaned = parseDeliverableSheetWithMode(csvData, slatedOnly);
    setCleanedData(cleaned);
    // Initialize all groups as enabled by default
    setEnabledGroups(new Set(cleaned.deliverable_groups.map(group => group.groupTitle)));
    // Initialize individual deliverables as DISABLED by default (they start unchecked)
    setEnabledDeliverables(new Set());
    console.log('Cleaned data:', cleaned);
  };

  // FIXED PARSING FUNCTION - Main fix here
  const parseDeliverableSheetWithMode = (csvData, slatedOnly) => {
    const lines = csvData.split('\n');
    const data = lines.map(line => {
      // Simple CSV parsing - handles quoted fields
      const result = [];
      let current = '';
      let inQuotes = false;

      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
          inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
          result.push(current.trim());
          current = '';
        } else {
          current += char;
        }
      }
      result.push(current.trim());
      return result;
    });

    // Extract header information (rows 4-12, columns B+C)
    const headerInfo = {
      agency: data[3] ? data[3][1] || 'N/A' : 'N/A',
      client: data[4] ? data[4][1] || 'N/A' : 'N/A',
      product: data[5] ? data[5][1] || 'N/A' : 'N/A',
      title: data[6] ? data[6][1] || 'N/A' : 'N/A',
      isci: data[7] ? data[7][1] || 'N/A' : 'N/A',
      duration: data[8] ? data[8][1] || 'N/A' : 'N/A',
      audio: data[9] ? data[9][1] || 'N/A' : 'N/A',
      date: new Date().toLocaleDateString('en-US'),
      copyright: data[11] ? data[11][1] || 'N/A' : 'N/A'
    };

    // Parse deliverables starting from row 15 (index 14)
    const deliverableGroups = [];
    let currentGroup = null;
    let totalRowsProcessed = 0;
    let slatedFilteredOut = 0;

    console.log('=== PARSING DEBUG INFO ===');
    console.log(`Slated Only Mode: ${slatedOnly}`);
    console.log(`Total CSV rows: ${data.length}`);

    for (let i = 14; i < data.length; i++) {
      const row = data[i];
      if (!row || !row[0]) continue;

      const firstCol = row[0].toString();
      totalRowsProcessed++;

      // CORRECT GROUP DETECTION: Real groups are single-column titles only
      if (!firstCol.match(/^\d+\/\d+/) && firstCol !== "Ship Date " && firstCol.trim() !== '') {
        // Real groups are ONLY single-column titles with empty B and C columns
        const isRealGroup = (row[1] === '' || row[1] === undefined) &&
                           (row[2] === '' || row[2] === undefined) &&
                           (row[12] === '' || row[12] === undefined) &&
                           !firstCol.includes('NEW CASH BACK DISCLAIMER') &&
                           !firstCol.includes('PWV:') &&
                           !firstCol.includes('RESOULTION') &&
                           !firstCol.includes('ProRes422');

        if (isRealGroup) {
          // Save previous group if exists
          if (currentGroup && currentGroup.deliverables.length > 0) {
            deliverableGroups.push(currentGroup);
          }

          // Start new group
          currentGroup = {
            groupTitle: firstCol,
            deliverables: [],
            enabled: true
          };
          console.log(`📁 New Group: "${firstCol}"`);
        } else {
          // This might be a deliverable row that spans A:C (disclaimer + specs)
          if (currentGroup && (row[1] !== '' || row[2] !== '')) {
            console.log(`📋 Multi-column deliverable info row: "${firstCol.substring(0, 50)}..."`);
          } else {
            console.log(`⚠️ Skipping non-group row: "${firstCol.substring(0, 50)}..."`);
          }
        }
      } else if (firstCol.match(/^\d+\/\d+/) && currentGroup) {
        // This is a spec row for the current group
        const spec = {
          shipDate: row[0] || '',
          shipped: row[1] === 'TRUE' || row[1] === true || row[1] === 'true',
          version: row[2] || '',
          platform: row[3] || '',
          isciAdId: row[4] || '',
          fileName: row[5] || '',
          length: row[6] || '',
          subtitles: row[7] || '',
          frameRate: row[8] || '',
          aspectRatio: row[9] || '',
          audioMix: row[10] || '',
          legal: row[11] || '',
          slated: row[12] || '', // Column M - "Slated / Unslated"
          flameExports: row[13] || '',
          reviewedBy: row[14] || '',
          specs: row[15] || ''
        };

        console.log(`📝 Processing row ${i}: Version="${spec.version}", Slated="${spec.slated}", Platform="${spec.platform}"`);

        // DETAILED DEBUG FOR VENMO GROUP
        if (currentGroup && currentGroup.groupTitle.includes('Venmo Everything')) {
          console.log(`🔍 VENMO DEBUG - Row ${i}:`);
          console.log(`   - Version: "${spec.version}"`);
          console.log(`   - Slated Status: "${spec.slated}"`);
          console.log(`   - Platform: "${spec.platform}"`);
          console.log(`   - Ship Date: "${spec.shipDate}"`);
          console.log(`   - Specs: "${spec.specs}"`);
          console.log(`   - All row data:`, row);
        }

        // FIXED SLATED LOGIC: Check slated status properly
        const slatedValue = spec.slated.toLowerCase().trim();
        let shouldInclude = false;

        if (slatedOnly) {
          // Only include items that are exactly "slated" (not "unslated" or "slated and unslated")
          shouldInclude = slatedValue === 'slated';
        } else {
          // Include anything that has slating info - "slated", "unslated", "slated and unslated"
          shouldInclude = slatedValue === 'slated' ||
                         slatedValue === 'unslated' ||
                         slatedValue.includes('slated and unslated') ||
                         slatedValue.includes('slated & unslated');
        }

        // DETAILED DEBUG FOR VENMO FILTERING
        if (currentGroup && currentGroup.groupTitle.includes('Venmo Everything')) {
          console.log(`🔍 VENMO FILTER CHECK - Row ${i}:`);
          console.log(`   - Slated Value: "${slatedValue}"`);
          console.log(`   - Slated Only Mode: ${slatedOnly}`);
          console.log(`   - Should Include: ${shouldInclude}`);
        }

        if (!shouldInclude) {
          console.log(`❌ FILTERED OUT (Slated): "${spec.version}" - Slated value: "${spec.slated}"`);
          slatedFilteredOut++;
          continue;
        }

        console.log(`✅ INCLUDED: "${spec.version}" - Slated: "${spec.slated}"`);

        // Use the individual title from Column C (Title / Version) - DEFAULT TO GROUP TITLE IF EMPTY
        const individualTitle = spec.version || currentGroup.groupTitle || 'Untitled';

        // Get aspect ratio ONLY from Column J (Aspect Ratio column) - NO SPECS COLUMN CHECKING
        let suggestedFormat = '16x9'; // default
        let platform = spec.platform || 'N/A';

        // ONLY use the dedicated Aspect Ratio column (Column J)
        if (spec.aspectRatio && spec.aspectRatio.trim() !== '') {
          const aspectRatio = spec.aspectRatio.toString().toLowerCase().trim();
          console.log(`🔍 Aspect Ratio from Column J: "${aspectRatio}"`);

          if (aspectRatio.includes('16x9') || aspectRatio.includes('16:9')) {
            suggestedFormat = '16x9';
          } else if (aspectRatio.includes('9x16') || aspectRatio.includes('9:16')) {
            suggestedFormat = '9x16';
          } else if (aspectRatio.includes('1x1') || aspectRatio.includes('1:1')) {
            suggestedFormat = '1x1';
          } else if (aspectRatio.includes('4x5') || aspectRatio.includes('4:5')) {
            suggestedFormat = '4x5';
          } else {
            console.log(`⚠️ Unknown aspect ratio format: "${aspectRatio}", using default 16x9`);
            suggestedFormat = '16x9';
          }
        } else {
          // If aspect ratio column is empty, just use default 16x9
          console.log(`⚠️ No aspect ratio in Column J, using default 16x9`);
          suggestedFormat = '16x9';
        }

        // Parse ship date - KEEP EVEN IF EMPTY
        let shipDate = spec.shipDate || 'N/A';
        if (shipDate !== 'N/A') {
          if (shipDate.includes('2025-')) {
            shipDate = shipDate.split('T')[0]; // Remove time part
          } else if (shipDate.includes('/')) {
            const [month, day] = shipDate.split('/');
            shipDate = `2025-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
          }
        }

        // Use length column for duration - DEFAULT TO N/A IF EMPTY
        let duration = spec.length ? `${spec.length}s` : 'N/A';

        // Create unique ID for this deliverable
        const deliverableId = `${deliverableGroups.length}_${currentGroup.deliverables.length}`;

        currentGroup.deliverables.push({
          id: deliverableId,
          video_title: individualTitle,
          original_title: currentGroup.groupTitle || 'Untitled Group',
          ship_date: shipDate,
          platform: platform,
          specs: spec.specs || 'N/A',
          aspect_ratio: spec.aspectRatio || 'N/A',
          suggested_slate_format: suggestedFormat,
          duration: duration,
          shipped: spec.shipped,
          slated_status: spec.slated || 'N/A',
          agency: headerInfo.agency,
          client: headerInfo.client,
          product: headerInfo.product,
          isci: headerInfo.isci,
          audio: headerInfo.audio,
          copyright: headerInfo.copyright
        });
      }
    }

    // Don't forget the last group
    if (currentGroup && currentGroup.deliverables.length > 0) {
      deliverableGroups.push(currentGroup);
    }

    // Debug summary
    console.log('=== PARSING SUMMARY ===');
    console.log(`Total rows processed: ${totalRowsProcessed}`);
    console.log(`Filtered out by slated status: ${slatedFilteredOut}`);
    console.log(`Groups found: ${deliverableGroups.length}`);
    console.log(`Total deliverables included: ${deliverableGroups.reduce((sum, g) => sum + g.deliverables.length, 0)}`);

    // Flatten deliverables for summary
    const allDeliverables = deliverableGroups.flatMap(group =>
      group.enabled ? group.deliverables : []
    );

    // Create summary
    const formatCounts = {};
    allDeliverables.forEach(d => {
      formatCounts[d.suggested_slate_format] = (formatCounts[d.suggested_slate_format] || 0) + 1;
    });

    const uniquePlatforms = [...new Set(allDeliverables.map(d => d.platform))];
    const uniqueVideos = [...new Set(allDeliverables.map(d => d.original_title))];

    return {
      project_info: headerInfo,
      deliverable_groups: deliverableGroups,
      summary: {
        total_slated_deliverables: allDeliverables.length,
        total_videos: uniqueVideos.length,
        date_range: allDeliverables.length > 0 ?
          `${Math.min(...allDeliverables.map(d => d.ship_date))} to ${Math.max(...allDeliverables.map(d => d.ship_date))}` : '',
        formats_needed: formatCounts,
        platforms: uniquePlatforms
      }
    };
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
      { value: delivery.agency || 'N/A' },           // Agency from CSV header
      { value: delivery.client || 'N/A' },           // Client from CSV header
      { value: delivery.product || 'N/A' },          // Product from CSV header
      { value: delivery.video_title || 'N/A' },      // Title / Version (e.g., "SIP IT TEASER :15 9x16")
      { value: delivery.isci || 'N/A' },             // ISCI / AD-ID from CSV header
      { value: delivery.duration || 'N/A' },         // Duration (e.g., "15s")
      { value: delivery.audio || 'N/A' },            // Audio Mix from CSV header
      { value: todaysDate },                         // Today's date (not ship date!)
      { value: delivery.copyright || 'N/A' }         // Copyright from CSV header
    ];

    // Generate paragraph sections for each field - exact format match
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
        <p className="text-gray-400">Upload delivery schedule CSV, auto-parse, and generate TTG slate files for Flame</p>
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
              {rawCsvData ? '✅ CSV file loaded' : 'Click to upload CSV file'}
            </p>
            <p className="text-neutral-400 text-sm">
              {cleanedData ? `${cleanedData.summary.total_slated_deliverables} slated deliverables found` : 'Upload your Blacksmith delivery schedule'}
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

          {/* Cancel/Clear CSV Button - Only show when CSV is loaded */}
          {rawCsvData && (
            <div className="w-full">
              <div className="flex items-center justify-between bg-neutral-600 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <CheckCircle className="text-green-400" size={24} />
                  <div>
                    <p className="text-white font-medium">CSV File Loaded</p>
                    <p className="text-neutral-400 text-sm">{cleanedData?.summary.total_slated_deliverables || 0} slated deliverables ready</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setRawCsvData(null);
                    setCleanedData(null);
                    setTtgFiles([]);
                    setEnabledGroups(new Set());
                    setEnabledDeliverables(new Set());
                    setSlatedOnlyMode(true); // Reset toggle
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

        {/* Parsed Summary - Only show when CSV is loaded */}
        {cleanedData && (
          <div className="bg-neutral-600 rounded-lg p-6 mt-6 max-w-2xl mx-auto">
            <h3 className="text-white font-medium mb-4 text-center">Parsed Summary</h3>

            {/* Slated Only Toggle */}
            <div className="flex items-center justify-center mb-4 p-3 bg-neutral-700 rounded-lg">
              <div className="flex items-center gap-3">
                <span className={`text-sm ${!slatedOnlyMode ? 'text-blue-400 font-medium' : 'text-neutral-400'}`}>
                  All Slated Items
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
                {slatedOnlyMode ? 'Excludes "Unslated" items - VERY RESTRICTIVE' : 'Includes both "Slated" and "Unslated" items'}
              </div>
            </div>

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

      {/* Step 2: Output Path - Only show when CSV is loaded */}
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

      {/* Step 3: Deliverable Groups Selection */}
      {cleanedData && (
        <div className="bg-neutral-700 border border-neutral-600 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">3. Select Deliverable Groups</h2>

          <div className="space-y-4">
            {cleanedData.deliverable_groups.map((group, index) => {
              const isGroupEnabled = enabledGroups.has(group.groupTitle);
              const shippedCount = group.deliverables.filter(d => d.shipped).length;
              const totalCount = group.deliverables.length;
              const individualEnabledCount = group.deliverables.filter(d => enabledDeliverables.has(d.id)).length;

              return (
                <div key={index} className={`border rounded-lg p-4 transition-all ${
                  isGroupEnabled ? 'border-blue-500 bg-blue-900/20' : 
                  individualEnabledCount > 0 ? 'border-yellow-500 bg-yellow-900/20' :
                  'border-neutral-500 bg-neutral-600'
                }`}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={isGroupEnabled}
                        onChange={(e) => {
                          const newEnabledGroups = new Set(enabledGroups);
                          if (e.target.checked) {
                            newEnabledGroups.add(group.groupTitle);
                            // When enabling group, disable individual selections for this group
                            const newEnabledDeliverables = new Set(enabledDeliverables);
                            group.deliverables.forEach(d => newEnabledDeliverables.delete(d.id));
                            setEnabledDeliverables(newEnabledDeliverables);
                          } else {
                            newEnabledGroups.delete(group.groupTitle);
                          }
                          setEnabledGroups(newEnabledGroups);
                        }}
                        className="mt-1 h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <div>
                        <h3 className="text-lg font-medium text-white">{group.groupTitle}</h3>
                        <div className="flex items-center gap-4 text-sm text-neutral-300 mt-1">
                          <span>{totalCount} deliverables</span>
                          <span className="flex items-center gap-1">
                            <span className={`inline-block w-2 h-2 rounded-full ${
                              shippedCount === totalCount ? 'bg-green-400' : 
                              shippedCount > 0 ? 'bg-yellow-400' : 'bg-red-400'
                            }`}></span>
                            {shippedCount}/{totalCount} shipped
                          </span>
                          {!isGroupEnabled && individualEnabledCount > 0 && (
                            <span className="text-yellow-400">
                              {individualEnabledCount} selected individually
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-sm text-neutral-400">
                        Formats: {[...new Set(group.deliverables.map(d => d.suggested_slate_format))].join(', ')}
                      </div>
                    </div>
                  </div>

                  {/* Deliverable Details */}
                  <div className="ml-8 space-y-2">
                    {group.deliverables.map((deliverable, deliverableIndex) => (
                      <div key={deliverableIndex} className="flex items-center justify-between bg-neutral-800/50 rounded p-3 text-sm">
                        <div className="flex items-center gap-3">
                          {/* Individual checkbox - only show when group is not enabled */}
                          {!isGroupEnabled && (
                            <input
                              type="checkbox"
                              checked={enabledDeliverables.has(deliverable.id)}
                              onChange={(e) => {
                                const newEnabledDeliverables = new Set(enabledDeliverables);
                                if (e.target.checked) {
                                  newEnabledDeliverables.add(deliverable.id);
                                } else {
                                  newEnabledDeliverables.delete(deliverable.id);
                                }
                                setEnabledDeliverables(newEnabledDeliverables);
                              }}
                              className="h-4 w-4 text-yellow-600 focus:ring-yellow-500 border-gray-300 rounded"
                            />
                          )}

                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            deliverable.shipped ? 'bg-green-600 text-white' : 'bg-yellow-600 text-white'
                          }`}>
                            {deliverable.shipped ? 'Shipped' : 'Not Shipped'}
                          </span>
                          <span className="text-white font-medium">{deliverable.video_title}</span>
                          <span className="text-neutral-400">{deliverable.platform}</span>
                          <span className="text-neutral-400">{deliverable.duration}</span>
                          <span className={`px-2 py-1 rounded text-xs text-white ${
                            deliverable.suggested_slate_format === '16x9' ? 'bg-blue-600' :
                            deliverable.suggested_slate_format === '9x16' ? 'bg-green-600' :
                            deliverable.suggested_slate_format === '1x1' ? 'bg-purple-600' :
                            'bg-orange-600'
                          }`}>
                            {deliverable.suggested_slate_format}
                          </span>
                        </div>
                        <div className="text-neutral-400 text-xs">
                          {deliverable.ship_date} • {deliverable.slated_status}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="mt-6 flex gap-3">
            <button
              onClick={() => {
                setEnabledGroups(new Set(cleanedData.deliverable_groups.map(g => g.groupTitle)));
                setEnabledDeliverables(new Set()); // Clear individual selections
              }}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg text-white transition-colors"
            >
              Enable All Groups
            </button>
            <button
              onClick={() => {
                setEnabledGroups(new Set());
                setEnabledDeliverables(new Set());
              }}
              className="bg-neutral-600 hover:bg-neutral-500 px-4 py-2 rounded-lg text-white transition-colors"
            >
              Disable All
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Preview & Generate */}
      {cleanedData && (enabledGroups.size > 0 || enabledDeliverables.size > 0) && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">4. Preview & Generate TTG Files</h2>
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
                {(() => {
                  let previewDeliverables = [];
                  cleanedData.deliverable_groups.forEach(group => {
                    if (enabledGroups.has(group.groupTitle)) {
                      previewDeliverables.push(...group.deliverables);
                    } else {
                      const individualEnabled = group.deliverables.filter(d => enabledDeliverables.has(d.id));
                      previewDeliverables.push(...individualEnabled);
                    }
                  });

                  return previewDeliverables.map((delivery, index) => {
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
                            delivery.shipped ? 'bg-green-600' : 'bg-yellow-600'
                          }`}>
                            {delivery.shipped ? 'Shipped' : 'Not Shipped'}
                          </span>
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
                  });
                })()}
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
                      // You could add a toast notification here
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