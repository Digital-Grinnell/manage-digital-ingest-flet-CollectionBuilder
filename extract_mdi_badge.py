#!/usr/bin/env python3
"""
Extract the MDI badge from favicon.ico and create a transparent PNG
with just the blue and white MDI badge (removing the yellow CB logo).
"""

from PIL import Image
import sys

def extract_mdi_badge(input_path, output_path):
    """
    Extract MDI badge from favicon, removing the yellow CollectionBuilder logo.
    """
    try:
        # Load the favicon (will load the largest size available)
        img = Image.open(input_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        print(f"Loaded image: {img.size[0]}x{img.size[1]} pixels, mode: {img.mode}")
        
        # Get pixel data
        pixels = img.load()
        width, height = img.size
        
        # Create a new transparent image
        new_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        new_pixels = new_img.load()
        
        # Analyze the image to identify yellow pixels (CB logo)
        # Yellow typically has high R, high G, low B
        # We'll keep blue/white pixels (MDI badge) and make yellow transparent
        
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                
                # Skip already transparent pixels
                if a < 10:
                    continue
                
                # Detect yellow pixels (high R, high G, low B)
                # Typical yellow: R>200, G>180, B<100
                is_yellow = (r > 180 and g > 160 and b < 120)
                
                # Detect orange/warm tones that might be part of CB logo
                is_orange = (r > 200 and g > 140 and g < 200 and b < 140)
                
                # Keep blue, white, and dark pixels (likely part of MDI badge)
                # Blue: B > R and B > G
                # White: R, G, B all high and similar
                # Dark: R, G, B all low
                is_blue = (b > r + 30 and b > g + 30)
                is_white = (r > 200 and g > 200 and b > 200)
                is_dark = (r < 80 and g < 80 and b < 80)
                is_gray = (abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30 and r > 80 and r < 200)
                
                # Keep pixels that are part of the MDI badge
                if (is_blue or is_white or is_dark or is_gray) and not (is_yellow or is_orange):
                    new_pixels[x, y] = (r, g, b, a)
        
        # Save as PNG
        new_img.save(output_path, 'PNG')
        print(f"Created MDI badge image: {output_path}")
        print(f"Image size: {new_img.size[0]}x{new_img.size[1]} pixels")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    input_file = '/Users/mcfatem/GitHub/manage-digital-ingest-flet-CollectionBuilder/assets/favicon.ico'
    output_file = '/Users/mcfatem/GitHub/manage-digital-ingest-flet-CollectionBuilder/assets/mdi_badge.png'
    
    success = extract_mdi_badge(input_file, output_file)
    sys.exit(0 if success else 1)
