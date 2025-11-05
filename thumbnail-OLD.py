"""
Thumbnail Generation Module

This module provides functionality for generating image thumbnails using ImageMagick.
"""

import os
import logging
from subprocess import call

logger = logging.getLogger(__name__)


def generate_thumbnail(input_path, output_path, options):
    """
    Generate a thumbnail from an image file using ImageMagick.
    
    Args:
        input_path: Path to the input image file
        output_path: Path where the thumbnail should be saved
        options: Dictionary containing thumbnail generation options:
            - width: Target width in pixels
            - height: Target height in pixels
            - quality: JPEG quality (0-100)
            - trim: Whether to trim whitespace (boolean)
            - type: Type of derivative ('thumbnail', etc.)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        width = options.get('width', 400)
        height = options.get('height', 400)
        quality = options.get('quality', 85)
        trim = options.get('trim', False)
        
        # Build the ImageMagick command
        # Use -thumbnail for faster processing and automatic orientation
        if trim:
            cmd = f'magick "{input_path}" -trim -thumbnail {width}x{height} -quality {quality} "{output_path}"'
        else:
            cmd = f'magick "{input_path}" -thumbnail {width}x{height} -quality {quality} "{output_path}"'
        
        logger.info(f"Executing thumbnail command: {cmd}")
        
        # Execute the command
        return_code = call(cmd, shell=True)
        
        if return_code == 0:
            logger.info(f"Successfully created thumbnail: {output_path}")
            return True
        else:
            logger.error(f"Failed to create thumbnail. Command returned: {return_code}")
            return False
            
    except Exception as e:
        logger.error(f"Exception in generate_thumbnail: {str(e)}")
        return False


def generate_pdf_thumbnail(input_path, output_path, options):
    """
    Generate a thumbnail from a PDF file using ImageMagick.
    Uses the first page of the PDF [0].
    
    Args:
        input_path: Path to the input PDF file
        output_path: Path where the thumbnail should be saved
        options: Dictionary containing thumbnail generation options:
            - width: Target width in pixels
            - height: Target height in pixels
            - quality: JPEG quality (0-100)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        width = options.get('width', 400)
        height = options.get('height', 400)
        quality = options.get('quality', 85)
        
        # Build command for PDF - extract first page and resize
        cmd = f'magick "{input_path}[0]" -thumbnail {width}x{height} -quality {quality} "{output_path}"'
        
        logger.info(f"Executing PDF thumbnail command: {cmd}")
        
        # Execute the command
        return_code = call(cmd, shell=True)
        
        if return_code == 0:
            logger.info(f"Successfully created PDF thumbnail: {output_path}")
            return True
        else:
            logger.error(f"Failed to create PDF thumbnail. Command returned: {return_code}")
            return False
            
    except Exception as e:
        logger.error(f"Exception in generate_pdf_thumbnail: {str(e)}")
        return False
