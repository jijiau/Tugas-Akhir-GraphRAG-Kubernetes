"""
Base class untuk semua analisis EDA.
Mengimplementasikan Template Method Pattern untuk konsistensi workflow.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class EDABase(ABC):
    """Abstract base class untuk Kubernetes Swagger EDA."""
    
    def __init__(self, swagger_path: str):
        self.swagger_path = swagger_path
        self.data: Dict[str, Any] = {}
        self.definitions: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        
    def load(self) -> None:
        """Load swagger.json sekali, reusable untuk semua analisis."""
        if not self.data:
            logger.info(f"Loading swagger from {self.swagger_path}")
            with open(self.swagger_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            self.definitions = self.data.get('definitions', {})
            logger.info(f"Loaded {len(self.definitions)} definitions")
    
    @abstractmethod
    def extract(self) -> Dict[str, Any]:
        """Extract metrics dari definitions. Override di subclass."""
        pass
    
    @abstractmethod
    def visualize(self, output_path: Optional[str] = None) -> None:
        """Generate visualisasi. Override di subclass."""
        pass
    
    def run(self, output_dir: str = "output/eda") -> Dict[str, Any]:
        """Template method: pipeline lengkap EDA."""
        self.load()
        self.results = self.extract()
        self.visualize(output_path=f"{output_dir}/{self.__class__.__name__}")
        return self.results