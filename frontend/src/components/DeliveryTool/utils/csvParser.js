// frontend/src/components/DeliveryTool/utils/csvParser.js

/**
 * FIXED CSV Parser - Captures ALL deliverables with titles
 * Key fix: Create deliverables based on TITLES, not slated status
 */

export const parseDeliverableSheetWithMode = (csvData, slatedOnly = false) => {
  // Enhanced CSV parsing to handle multiline quoted fields
  const data = [];
  let currentRow = [];
  let currentField = '';
  let inQuotes = false;
  let i = 0;

  while (i < csvData.length) {
    const char = csvData[i];
    
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      currentRow.push(currentField.trim());
      currentField = '';
    } else if ((char === '\n' || char === '\r') && !inQuotes) {
      // End of row - add the last field and push the row
      currentRow.push(currentField.trim());
      if (currentRow.length > 0 && currentRow.some(field => field !== '')) {
        data.push(currentRow);
      }
      currentRow = [];
      currentField = '';
      // Skip \r\n combinations
      if (char === '\r' && csvData[i + 1] === '\n') {
        i++;
      }
    } else {
      currentField += char;
    }
    i++;
  }
  
  // Don't forget the last row if file doesn't end with newline
  if (currentRow.length > 0 || currentField !== '') {
    currentRow.push(currentField.trim());
    data.push(currentRow);
  }

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

  // Parse deliverables starting from row 13 (index 12)
  const deliverableGroups = [];
  let currentGroup = null;
  let totalRowsProcessed = 0;
  let totalDeliverables = 0;

  console.log('=== PARSING START ===');
  console.log(`Slated Only Mode: ${slatedOnly}, Total CSV rows: ${data.length}`);
  
  // Debug rows 12-20 to find the issue
  console.log('=== ROWS 12-20 DEBUG ===');
  for (let debugIdx = 12; debugIdx <= 20 && debugIdx < data.length; debugIdx++) {
    const row = data[debugIdx];
    console.log(`Row ${debugIdx}: "${row ? row[0] : 'EMPTY'}" | "${row ? row[1] : ''}" | "${row ? row[2] : ''}" | Cols: ${row ? row.length : 0}`);
  }
  
  for (let i = 12; i < data.length; i++) {
    const row = data[i];
    if (!row || !row[0]) continue;

    const firstCol = row[0].toString().trim();
    totalRowsProcessed++;

    // GROUP DETECTION: Real groups are single-column titles only
    if (!firstCol.match(/^\d+\/\d+/) && firstCol !== "Ship Date " && firstCol !== '') {
      console.log(`🔍 GROUP CHECK Row ${i}: "${firstCol}"`);
      console.log(`   Has date pattern: ${firstCol.match(/^\d+\/\d+/) ? 'YES' : 'NO'}`);
      console.log(`   Is Ship Date: ${firstCol === "Ship Date " ? 'YES' : 'NO'}`);
      console.log(`   Column B: "${row[1] || 'EMPTY'}"`);
      console.log(`   Column C: "${row[2] || 'EMPTY'}"`);
      
      // Real groups are titles that don't have dates and aren't disclaimer text
      // Check if this looks like a group title (not a deliverable with a date)
      const isRealGroup = !firstCol.includes('NEW CASH BACK DISCLAIMER') &&
                         !firstCol.includes('PWV:') &&
                         !firstCol.includes('RESOLUTION') &&
                         !firstCol.includes('RESOULTION') &&
                         !firstCol.includes('ProRes422') &&
                         // If Column C has content, check if it's NOT a title (deliverable)
                         (row[2] === '' || row[2] === undefined || row[2] === 'Title / Version');

      console.log(`   Is Real Group: ${isRealGroup ? 'YES' : 'NO'}`);

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
        console.log(`📁 NEW GROUP DETECTED: "${firstCol}" (Row ${i})`);
      } else {
        // This might be a deliverable row that spans A:C (disclaimer + specs)
        console.log(`⚠️ Skipping non-group row: "${firstCol.substring(0, 50)}..."`);
      }
    } else if ((firstCol.match(/^\d+\/\d+/) || (row[2] && row[2].trim() !== '')) && currentGroup) {
      // This is a spec row for the current group (either has a date OR has a title in Column C)
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
        legal: 'N/A', // Ignore Column L (Legal) completely
        slated: row[12] || '', // Column M - "Slated / Unslated"
        flameExports: row[13] || '',
        reviewedBy: row[14] || '',
        specs: row[15] || ''
      };

      // CRITICAL FIX: Create deliverable if there's a TITLE (Column C), regardless of slated status
      const hasTitle = spec.version && spec.version.trim() !== '';

      if (!hasTitle) {
        continue;
      }

      // OPTIONAL: Apply slated filter ONLY if slatedOnly mode is enabled
      let shouldInclude = true;

      if (slatedOnly) {
        const slatedValue = spec.slated.toLowerCase().trim();
        
        // Check if the slated field contains slated keywords (more robust for multiline content)
        const containsSlated = slatedValue.includes('slated');
        const containsUnslated = slatedValue.includes('unslated');
        const containsAmpersand = slatedValue.includes('&');
        const containsAnd = slatedValue.includes(' and ');
        
        // Include if:
        // 1. Contains "slated" but NOT "unslated" (pure "Slated")
        // 2. Contains "slated & unslated" 
        // 3. Contains "slated and unslated"
        shouldInclude = (containsSlated && !containsUnslated) ||
                       (containsSlated && containsUnslated && containsAmpersand) ||
                       (containsSlated && containsUnslated && containsAnd);

        if (!shouldInclude) {
          continue;
        }
        
        console.log(`✅ SLATED: "${spec.version}" - Group: "${currentGroup?.groupTitle}"`);
      }

      // Use the individual title from Column C (Title / Version)
      const individualTitle = spec.version;

      // Get aspect ratio from Column J
      let suggestedFormat = '16x9'; // default
      let platform = spec.platform || 'N/A';

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
        }
      }

      // Parse ship date
      let shipDate = spec.shipDate || 'N/A';
      if (shipDate !== 'N/A') {
        if (shipDate.includes('2025-')) {
          shipDate = shipDate.split('T')[0]; // Remove time part
        } else if (shipDate.includes('/')) {
          const [month, day] = shipDate.split('/');
          shipDate = `2025-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        }
      }

      // Use length column for duration
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
        isci: spec.isciAdId || 'N/A',
        audio: headerInfo.audio,
        copyright: headerInfo.copyright
      });

      totalDeliverables++;
    }
  }

  // Don't forget the last group
  if (currentGroup && currentGroup.deliverables.length > 0) {
    deliverableGroups.push(currentGroup);
  }

  // Debug summary
  console.log('=== FIXED PARSING SUMMARY ===');
  console.log(`Total rows processed: ${totalRowsProcessed}`);
  console.log(`Groups found: ${deliverableGroups.length}`);
  console.log(`Total deliverables created: ${totalDeliverables}`);

  // Detailed group breakdown
  deliverableGroups.forEach((group, index) => {
    console.log(`Group ${index + 1}: "${group.groupTitle}" - ${group.deliverables.length} deliverables`);
    group.deliverables.forEach((deliverable, idx) => {
      console.log(`  ${idx + 1}. "${deliverable.video_title}" (${deliverable.suggested_slate_format}) - Slated: ${deliverable.slated_status}`);
    });
  });

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