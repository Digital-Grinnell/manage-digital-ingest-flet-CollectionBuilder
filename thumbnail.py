"""
Thumbnail Generation Module using Pillow and PyMuPDF

This module provides functionality for generating image thumbnails using Pillow (PIL)
and PyMuPDF (fitz), replacing the ImageMagick dependency for better cross-platform compatibility.

Benefits over ImageMagick:
- Pure Python implementation - easier to install and maintain
- No external binary dependencies (everything via pip install)
- Better cross-platform support (Windows, macOS, Linux)
- More predictable behavior across different environments
- Better error handling and memory management

For PDF processing:
- Uses PyMuPDF (fitz) - pure Python PDF library with no external dependencies
- Faster than pdf2image/poppler
- Better rendering quality
- More control over PDF processing
- No need to install poppler-utils or Ghostscript
"""

import os
import io
import logging
from PIL import Image
from PIL import ImageOps
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def generate_thumbnail(input_path, output_path, options):
    """
    Generate a thumbnail from an image file using Pillow.
    
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
        
        logger.info(f"Generating thumbnail from {input_path}")
        logger.info(f"Target size: {width}x{height}, Quality: {quality}, Trim: {trim}")
        
        # Open the image
        with Image.open(input_path) as img:
            # Handle EXIF orientation
            img = ImageOps.exif_transpose(img)
            
            # Trim whitespace if requested
            if trim:
                # Convert to RGB if necessary for trimming
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                # Get bounding box of non-white areas
                bg = Image.new(img.mode, img.size, (255, 255, 255))
                diff = ImageOps.difference(img, bg)
                bbox = diff.getbbox()
                if bbox:
                    img = img.crop(bbox)
                    logger.info(f"Trimmed image to bbox: {bbox}")
            
            # Convert to RGB if necessary (for JPEG output)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                img = background
            elif img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Create thumbnail maintaining aspect ratio
            # thumbnail() modifies the image in-place and maintains aspect ratio
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            logger.info(f"Thumbnail size after resize: {img.size}")
            
            # Save as JPEG
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            logger.info(f"Successfully created thumbnail: {output_path}")
            return True
            
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        return False
    except PermissionError:
        logger.error(f"Permission denied accessing: {input_path}")
        return False
    except Exception as e:
        logger.error(f"Exception in generate_thumbnail: {str(e)}", exc_info=True)
        return False


def generate_pdf_thumbnail(input_path, output_path, options):
    """
    Generate a thumbnail from a PDF file using PyMuPDF and Pillow.
    Uses the first page of the PDF.
    
    Args:
        input_path: Path to the input PDF file
        output_path: Path where the thumbnail should be saved
        options: Dictionary containing thumbnail generation options:
            - width: Target width in pixels
            - height: Target height in pixels
            - quality: JPEG quality (0-100)
            - dpi: DPI for PDF rendering (default: 150, PyMuPDF uses matrix scaling)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        width = options.get('width', 400)
        height = options.get('height', 400)
        quality = options.get('quality', 85)
        dpi = options.get('dpi', 150)
        
        logger.info(f"Generating thumbnail from PDF: {input_path}")
        logger.info(f"Target size: {width}x{height}, Quality: {quality}, DPI: {dpi}")
        
        # Open the PDF
        pdf_document = fitz.open(input_path)
        
        if pdf_document.page_count == 0:
            logger.error(f"PDF has no pages: {input_path}")
            pdf_document.close()
            return False
        
        # Get first page
        page = pdf_document[0]
        
        # Calculate zoom factor to achieve desired DPI
        # PyMuPDF default is 72 DPI, so zoom = desired_dpi / 72
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        # Render page to pixmap (raster image)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        
        logger.info(f"PDF page rendered, size: {pix.width}x{pix.height}")
        
        # Convert pixmap to PIL Image
        img_data = pix.tobytes("jpeg")
        img = Image.open(io.BytesIO(img_data))
        
        # Close PDF
        pdf_document.close()
        
        logger.info(f"PDF converted to image, size: {img.size}")
        
        # Create thumbnail maintaining aspect ratio
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        
        logger.info(f"Thumbnail size after resize: {img.size}")
        
        # Save as JPEG
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
        
        logger.info(f"Successfully created PDF thumbnail: {output_path}")
        return True
        
    except FileNotFoundError:
        logger.error(f"Input PDF file not found: {input_path}")
        return False
    except fitz.FileDataError as e:
        logger.error(f"Invalid or corrupted PDF file: {str(e)}")
        return False
    except PermissionError:
        logger.error(f"Permission denied accessing: {input_path}")
        return False
    except Exception as e:
        logger.error(f"Exception in generate_pdf_thumbnail: {str(e)}", exc_info=True)
        return False


def get_image_info(input_path):
    """
    Get information about an image file.
    
    Args:
        input_path: Path to the input image file
        
    Returns:
        dict: Dictionary containing image information (size, format, mode) or None on error
    """
    try:
        with Image.open(input_path) as img:
            return {
                'size': img.size,
                'format': img.format,
                'mode': img.mode,
                'width': img.width,
                'height': img.height
            }
    except Exception as e:
        logger.error(f"Error getting image info: {str(e)}")
        return None
