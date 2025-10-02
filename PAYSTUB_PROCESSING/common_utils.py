#!/usr/bin/env python3
"""
Common utility functions for paystub processing scripts.
"""

import os
import glob
from typing import Optional


def get_default_pdf_path() -> str:
    """
    Get the default PDF path by finding the first available PDF file in test-files directory.
    
    Returns:
        str: Path to the default PDF file
        
    Raises:
        FileNotFoundError: If no PDF files are found in test-files directory
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_files_dir = os.path.join(script_dir, "test-files")
    
    # Look for any PDF files in the test-files directory
    pdf_files = glob.glob(os.path.join(test_files_dir, "*.pdf"))
    
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {test_files_dir}")
    
    # Sort to get consistent behavior and return the first one
    pdf_files.sort()
    return pdf_files[0]


def get_pdf_path(provided_path: Optional[str] = None) -> str:
    """
    Get the PDF path to use, either from provided argument or default.
    
    Args:
        provided_path: Optional path provided by user
        
    Returns:
        str: Path to the PDF file to use
        
    Raises:
        FileNotFoundError: If the provided path doesn't exist or no default is available
    """
    if provided_path:
        if os.path.exists(provided_path):
            return provided_path
        else:
            raise FileNotFoundError(f"Provided PDF path does not exist: {provided_path}")
    
    return get_default_pdf_path()


def setup_output_directory(output_dir: Optional[str] = None) -> str:
    """
    Set up the output directory, creating it if it doesn't exist.
    
    Args:
        output_dir: Optional output directory path
        
    Returns:
        str: Path to the output directory
    """
    if output_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "result-files")
    
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def get_pdf_filename_without_extension(pdf_path: str) -> str:
    """
    Get the filename from PDF path without extension.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        str: Filename without extension
    """
    return os.path.splitext(os.path.basename(pdf_path))[0]