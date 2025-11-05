#!/usr/bin/env python3
"""
Test script to compare ImageMagick and Pillow thumbnail generation.

This script helps validate that the Pillow implementation produces
comparable results to the ImageMagick implementation.
"""

import os
import sys
import time
from pathlib import Path

# Import both implementations
try:
    import thumbnail as thumbnail_imagemagick
    IMAGEMAGICK_AVAILABLE = True
except Exception as e:
    print(f"Warning: ImageMagick implementation not available: {e}")
    IMAGEMAGICK_AVAILABLE = False

try:
    import thumbnail_pillow
    PILLOW_AVAILABLE = True
except Exception as e:
    print(f"Warning: Pillow implementation not available: {e}")
    print("Install with: pip install Pillow PyMuPDF")
    PILLOW_AVAILABLE = False


def test_image_thumbnail(input_file, output_dir="test_output"):
    """Test thumbnail generation for an image file."""
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = Path(input_file).stem
    ext = Path(input_file).suffix
    
    print(f"\n{'='*60}")
    print(f"Testing: {input_file}")
    print(f"{'='*60}")
    
    # Test options for both Alma and CollectionBuilder modes
    test_cases = [
        {
            'name': 'Alma (200x200)',
            'options': {'width': 200, 'height': 200, 'quality': 85, 'trim': False},
            'suffix': '_alma'
        },
        {
            'name': 'CollectionBuilder Thumbnail (400x400)',
            'options': {'width': 400, 'height': 400, 'quality': 85, 'trim': False},
            'suffix': '_cb_thumb'
        },
        {
            'name': 'CollectionBuilder Small (800x800)',
            'options': {'width': 800, 'height': 800, 'quality': 85, 'trim': False},
            'suffix': '_cb_small'
        },
        {
            'name': 'With Trim',
            'options': {'width': 400, 'height': 400, 'quality': 85, 'trim': True},
            'suffix': '_trim'
        }
    ]
    
    for test in test_cases:
        print(f"\n{test['name']}:")
        
        # Test ImageMagick
        if IMAGEMAGICK_AVAILABLE:
            output_im = os.path.join(output_dir, f"{base_name}{test['suffix']}_imagemagick.jpg")
            start = time.time()
            success_im = thumbnail_imagemagick.generate_thumbnail(
                input_file, output_im, test['options']
            )
            time_im = time.time() - start
            
            if success_im:
                size_im = os.path.getsize(output_im) / 1024  # KB
                print(f"  ImageMagick: ✅ Success ({time_im:.3f}s, {size_im:.1f}KB)")
            else:
                print(f"  ImageMagick: ❌ Failed")
        
        # Test Pillow
        if PILLOW_AVAILABLE:
            output_pil = os.path.join(output_dir, f"{base_name}{test['suffix']}_pillow.jpg")
            start = time.time()
            success_pil = thumbnail_pillow.generate_thumbnail(
                input_file, output_pil, test['options']
            )
            time_pil = time.time() - start
            
            if success_pil:
                size_pil = os.path.getsize(output_pil) / 1024  # KB
                print(f"  Pillow:      ✅ Success ({time_pil:.3f}s, {size_pil:.1f}KB)")
            else:
                print(f"  Pillow:      ❌ Failed")


def test_pdf_thumbnail(input_file, output_dir="test_output"):
    """Test thumbnail generation for a PDF file."""
    os.makedirs(output_dir, exist_ok=True)
    
    base_name = Path(input_file).stem
    
    print(f"\n{'='*60}")
    print(f"Testing PDF: {input_file}")
    print(f"{'='*60}")
    
    options = {'width': 400, 'height': 400, 'quality': 85}
    
    # Test ImageMagick
    if IMAGEMAGICK_AVAILABLE:
        output_im = os.path.join(output_dir, f"{base_name}_pdf_imagemagick.jpg")
        start = time.time()
        success_im = thumbnail_imagemagick.generate_pdf_thumbnail(
            input_file, output_im, options
        )
        time_im = time.time() - start
        
        if success_im:
            size_im = os.path.getsize(output_im) / 1024  # KB
            print(f"  ImageMagick: ✅ Success ({time_im:.3f}s, {size_im:.1f}KB)")
        else:
            print(f"  ImageMagick: ❌ Failed")
    
    # Test Pillow
    if PILLOW_AVAILABLE:
        output_pil = os.path.join(output_dir, f"{base_name}_pdf_pillow.jpg")
        start = time.time()
        success_pil = thumbnail_pillow.generate_pdf_thumbnail(
            input_file, output_pil, options
        )
        time_pil = time.time() - start
        
        if success_pil:
            size_pil = os.path.getsize(output_pil) / 1024  # KB
            print(f"  Pillow:      ✅ Success ({time_pil:.3f}s, {size_pil:.1f}KB)")
        else:
            print(f"  Pillow:      ❌ Failed")


def main():
    """Main test function."""
    print("Thumbnail Generation Test Suite")
    print("================================\n")
    
    if not IMAGEMAGICK_AVAILABLE and not PILLOW_AVAILABLE:
        print("ERROR: Neither implementation is available!")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python test_thumbnails.py <image_file> [<image_file2> ...]")
        print("\nExample:")
        print("  python test_thumbnails.py sample.jpg sample.tif sample.pdf")
        print("\nSupported formats:")
        print("  Images: .jpg, .jpeg, .png, .tif, .tiff, .gif, .bmp")
        print("  PDFs: .pdf")
        sys.exit(1)
    
    # Process each input file
    for input_file in sys.argv[1:]:
        if not os.path.exists(input_file):
            print(f"\n⚠️  File not found: {input_file}")
            continue
        
        ext = Path(input_file).suffix.lower()
        
        if ext == '.pdf':
            test_pdf_thumbnail(input_file)
        elif ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.gif', '.bmp']:
            test_image_thumbnail(input_file)
        else:
            print(f"\n⚠️  Unsupported file type: {input_file}")
    
    print(f"\n{'='*60}")
    print("Test complete! Check the 'test_output' directory for results.")
    print("Compare the ImageMagick and Pillow versions visually.")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
