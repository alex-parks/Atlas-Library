# backend/core/base_atlas_object.py
import uuid
from datetime import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAtlasObject(ABC):
    """Base class for all Atlas objects following the design document architecture"""

    def __init__(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        self.id = self.generate_uuid()
        self.name = name
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def generate_uuid(self) -> str:
        return str(uuid.uuid4())

    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """Update metadata and timestamp"""
        self.metadata.update(updates)
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize object to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @abstractmethod
    def validate(self) -> bool:
        """Validate the object's data"""
        pass