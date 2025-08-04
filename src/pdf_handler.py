"""
PDF Text Extraction Handler

Handles extraction of text from PDF files for the Text-to-JSON converter.
Supports multiple extraction methods for different PDF types.
"""

import fitz  # PyMuPDF
import pdfplumber
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class PDFHandler:
    """Handle PDF text extraction with multiple fallback methods."""
    
    @staticmethod
    def extract_text(pdf_path: Path, method: str = "auto") -> str:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            method: Extraction method ("pymupdf", "pdfplumber", "auto")
            
        Returns:
            Extracted text as string
            
        Raises:
            ValueError: If PDF cannot be read
        """
        if method == "auto":
            # Try PyMuPDF first (usually better for academic papers)
            try:
                text = PDFHandler._extract_with_pymupdf(pdf_path)
                if text and len(text.strip()) > 100:  # Ensure meaningful content
                    console.print("[green]✓[/green] Extracted text using PyMuPDF")
                    return text
            except Exception as e:
                console.print(f"[yellow]PyMuPDF failed: {e}, trying pdfplumber...[/yellow]")
            
            # Fallback to pdfplumber (better for tables/structured content)
            try:
                text = PDFHandler._extract_with_pdfplumber(pdf_path)
                if text and len(text.strip()) > 100:
                    console.print("[green]✓[/green] Extracted text using pdfplumber")
                    return text
            except Exception as e:
                console.print(f"[red]pdfplumber also failed: {e}[/red]")
                raise ValueError(f"Could not extract text from PDF: {pdf_path}")
        
        elif method == "pymupdf":
            return PDFHandler._extract_with_pymupdf(pdf_path)
        elif method == "pdfplumber":
            return PDFHandler._extract_with_pdfplumber(pdf_path)
        else:
            raise ValueError(f"Unknown extraction method: {method}")
    
    @staticmethod
    def _extract_with_pymupdf(pdf_path: Path) -> str:
        """Extract text using PyMuPDF (fitz)."""
        text_parts = []
        
        with fitz.open(str(pdf_path)) as doc:
            for page_num, page in enumerate(doc, 1):
                # Extract text from page
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{text}")
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def _extract_with_pdfplumber(pdf_path: Path) -> str:
        """Extract text using pdfplumber."""
        text_parts = []
        
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract text from page
                text = page.extract_text()
                if text and text.strip():
                    text_parts.append(f"--- Page {page_num} ---\n{text}")
                
                # Also try to extract tables if present
                tables = page.extract_tables()
                for table in tables:
                    # Convert table to readable format
                    table_text = "\n".join(["\t".join(str(cell) if cell else "" for cell in row) for row in table])
                    if table_text.strip():
                        text_parts.append(f"--- Table on Page {page_num} ---\n{table_text}")
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def is_pdf(file_path: Path) -> bool:
        """Check if file is a PDF based on extension."""
        return file_path.suffix.lower() == '.pdf'
    
    @staticmethod
    def preprocess_academic_paper(text: str) -> str:
        """
        Preprocess text from academic papers.
        
        Handles common issues like:
        - References section (often too long for context)
        - Repeated headers/footers
        - Excessive whitespace
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        # Skip lines that are likely headers/footers (short, repeated)
        seen_lines = {}
        for line in lines:
            line = line.strip()
            if len(line) < 100:  # Short lines
                if line in seen_lines:
                    seen_lines[line] += 1
                    if seen_lines[line] > 3:  # Skip if repeated more than 3 times
                        continue
                else:
                    seen_lines[line] = 1
            
            cleaned_lines.append(line)
        
        # Join and clean up
        text = '\n'.join(cleaned_lines)
        
        # Optionally truncate references section if it's too long
        # (This is a simple heuristic - could be improved)
        ref_markers = ['References', 'REFERENCES', 'Bibliography', 'BIBLIOGRAPHY']
        for marker in ref_markers:
            if marker in text:
                parts = text.split(marker)
                if len(parts) > 1 and len(parts[-1]) > len(parts[0]):
                    # References section is longer than main content
                    # Keep only first part of references
                    text = parts[0] + marker + '\n' + parts[-1][:2000] + '\n... (references truncated)'
        
        return text
    
    @staticmethod
    def preprocess_resume(text: str) -> str:
        """
        Preprocess text from resume PDFs.
        
        Handles:
        - Multiple columns (common in resumes)
        - Bullet points and special characters
        - Contact information formatting
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Replace common bullet point characters
        bullet_chars = ['•', '●', '○', '■', '□', '▪', '▫', '-', '*']
        for char in bullet_chars:
            text = text.replace(char, '• ')
        
        # Clean up excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Keep non-empty lines
                # Fix common OCR issues in resumes
                line = line.replace('|', ' | ')  # Space around pipes
                line = ' '.join(line.split())  # Normalize whitespace
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines) 