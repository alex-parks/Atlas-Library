"""
Blacksmith Atlas 3D Asset Management

Template-based asset export/import system using Houdini's native
saveChildrenToFile() and loadChildrenFromFile() methods.

Main modules:
- houdiniae: Core template-based exporter/importer classes
- hda_pymodule: HDA PyModule functions for Houdini integration
- demo_template_workflow: Example usage and demonstration
"""

from ..houdini.houdiniae import (
    TemplateAssetExporter,
    TemplateAssetImporter
)

# Additional imports if available
try:
    from ..houdini.houdiniae import save_template, load_template
except ImportError:
    pass

try:
    from ..houdini.houdiniae import export_asset_as_template, import_asset_from_template  
except ImportError:
    pass

__version__ = "2.0.0"
__author__ = "Blacksmith Atlas Team"
__description__ = "Template-based 3D asset management for Houdini"
