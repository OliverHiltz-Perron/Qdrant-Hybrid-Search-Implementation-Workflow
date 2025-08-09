"""FFPSA Data Extraction Package

This package provides tools for extracting structured data from 
Family First Prevention Services Act (FFPSA) state prevention plans.
"""

__version__ = "0.1.0"

from .document_processor import DocumentProcessor
from .extraction_engine import ExtractionEngine
from .validators import DataValidator

__all__ = ["DocumentProcessor", "ExtractionEngine", "DataValidator"]