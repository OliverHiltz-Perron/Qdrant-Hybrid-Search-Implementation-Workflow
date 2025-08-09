#!/usr/bin/env python3
"""Fix encoding issues in JSON files."""

import json
import argparse
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_json_encoding(input_path, output_path=None):
    """Fix encoding issues in a JSON file."""
    if output_path is None:
        output_path = input_path
    
    # Try different encodings
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'windows-1252', 'cp1252']
    
    data = None
    for encoding in encodings:
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # Replace common problematic characters
            replacements = {
                '\x92': "'",   # Right single quotation mark
                '\x93': '"',   # Left double quotation mark
                '\x94': '"',   # Right double quotation mark
                '\x96': '-',   # En dash
                '\x97': '--',  # Em dash
                '\x91': "'",   # Left single quotation mark
                '\x85': '...',  # Ellipsis
                '\xa0': ' ',   # Non-breaking space
                '\u2019': "'", # Right single quotation mark (Unicode)
                '\u201c': '"', # Left double quotation mark (Unicode)
                '\u201d': '"', # Right double quotation mark (Unicode)
                '\u2013': '-', # En dash (Unicode)
                '\u2014': '--', # Em dash (Unicode)
            }
            
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            # Try to parse JSON
            data = json.loads(content)
            logger.info(f"Successfully loaded and cleaned JSON with {encoding} encoding")
            break
            
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            logger.debug(f"Failed with {encoding}: {e}")
            continue
    
    if data is None:
        # Last resort: load with error replacement
        try:
            with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            data = json.loads(content)
            logger.warning("Loaded JSON with replacement characters")
        except Exception as e:
            logger.error(f"Failed to load JSON file: {e}")
            raise
    
    # Save with clean encoding
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=True)
    
    logger.info(f"Fixed JSON saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Fix encoding issues in JSON files')
    parser.add_argument('input_file', help='Input JSON file with encoding issues')
    parser.add_argument('-o', '--output', help='Output file (default: overwrite input)')
    
    args = parser.parse_args()
    
    fix_json_encoding(args.input_file, args.output)


if __name__ == "__main__":
    main()