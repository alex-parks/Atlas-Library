// frontend/src/components/DeliveryTool/utils/ttgTemplates.js

export const ttgTemplates = {
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

export const generateTTGContent = (delivery, templateKey) => {
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

  // Build the text fields for slate
  const slateFields = [
    { value: delivery.agency || 'N/A' },           // Agency from CSV header
    { value: delivery.client || 'N/A' },           // Client from CSV header
    { value: delivery.product || 'N/A' },          // Product from CSV header
    { value: delivery.video_title || 'N/A' },      // Title / Version
    { value: delivery.isci || 'N/A' },             // ISCI / AD-ID from CSV header
    { value: delivery.duration || 'N/A' },         // Duration
    { value: delivery.audio || 'N/A' },            // Audio Mix from CSV header
    { value: todaysDate },                         // Today's date
    { value: delivery.copyright || 'N/A' }         // Copyright from CSV header
  ];

  // Generate paragraph sections for each field
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

  // Generate the complete TTG content
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

// Function to parse TTG content into readable format
export const parseTTGContent = (ttgContent) => {
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