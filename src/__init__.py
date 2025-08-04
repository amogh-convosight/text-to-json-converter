"""
Universal Text-to-JSON Converter

A unified pipeline for converting any unstructured text to JSON
following any schema using Instructor and OpenAI GPT models.
"""

from .converter import UniversalTextToJSONConverter

__version__ = "1.0.0"
__all__ = ["UniversalTextToJSONConverter"] 