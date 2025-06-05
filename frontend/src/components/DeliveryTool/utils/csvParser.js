// frontend/src/components/DeliveryTool/utils/csvParser.js

/**
 * FIXED CSV Parser - Captures ALL deliverables with titles
 * Key fix: Create deliverables based on TITLES, not slated status
 */

export const parseDeliverableSheetWithMode = (csvData, slatedOnly = false) => {
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
  let totalDeliverables = 0;

  console.log('=== FIXED PARSING DEBUG INFO ===');
  console.log(`Slated Only Mode: ${slatedOnly}`);
  console.log(`Total CSV rows: ${data.length}`);

  for (let i = 14; i < data.length; i++) {
    const row = data[i];
    if (!row || !row[0]) continue;

    const firstCol = row[0].toString().trim();
    totalRowsProcessed++;

    // GROUP DETECTION: Real groups are single-column titles only
    if (!firstCol.match(/^\d+\/\d+/) && firstCol !== "Ship Date " && firstCol !== '') {
      // Real groups are ONLY single-column titles with empty B and C columns
      const isRealGroup = (row[1] === '' || row[1] === undefined) &&
                         (row[2] === '' || row[2] === undefined) &&
                         !firstCol.includes('NEW CASH BACK DISCLAIMER') &&
                         !firstCol.includes('PWV:') &&
                         !firstCol.includes('RESOLUTION') &&
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
        console.log(`⚠️ Skipping non-group row: "${firstCol.substring(0, 50)}..."`);
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

      // CRITICAL FIX: Create deliverable if there's a TITLE (Column C), regardless of slated status
      const hasTitle = spec.version && spec.version.trim() !== '';

      if (!hasTitle) {
        console.log(`❌ SKIPPED (No Title): Row ${i} - No title in Column C`);
        continue;
      }

      // OPTIONAL: Apply slated filter ONLY if slatedOnly mode is enabled
      let shouldInclude = true;

      if (slatedOnly) {
        const slatedValue = spec.slated.toLowerCase().trim();
        shouldInclude = slatedValue === 'slated';

        if (!shouldInclude) {
          console.log(`❌ FILTERED OUT (Slated Only): "${spec.version}" - Slated value: "${spec.slated}"`);
          continue;
        }
      }

      console.log(`✅ INCLUDED: "${spec.version}" - Slated: "${spec.slated}"`);

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
        isci: headerInfo.isci,
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