#!/usr/bin/env python3
"""
Simple verification script to show which files will be kept vs deleted
"""

import json
import os
from pathlib import Path

def extract_location_files(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return set()
    
    location_files = set()
    
    def traverse_json(obj):
        if isinstance(obj, dict):
            if obj.get("key") == "location" and "value" in obj:
                file_path = obj["value"]
                if isinstance(file_path, str) and file_path.strip():
                    location_files.add(file_path)
            for value in obj.values():
                traverse_json(value)
        elif isinstance(obj, list):
            for item in obj:
                traverse_json(item)
    
    traverse_json(data)
    return location_files

def main():
    print("📋 File Analysis Report")
    print("=" * 50)
    
    # Get location files from JSON
    location_files = extract_location_files('input.json')
    protected_files = {
        'input.json', 'cleanup_files.py', 'generate_cleanup_script.py', 
        'verify_files.py', 'cleanup_script.sh', 'poc.json', '.git', 
        '.gitignore', 'README.md', 'pom.xml', 'mvnw', 'mvnw.cmd'
    }
    
    print(f"\n🔍 Files referenced in input.json locations ({len(location_files)}):")
    for f in sorted(location_files):
        exists = "✅" if Path(f).exists() else "❌"
        print(f"   {exists} {f}")
    
    print(f"\n🛡️  Protected files ({len(protected_files)}):")
    for f in sorted(protected_files):
        exists = "✅" if Path(f).exists() else "❌"
        print(f"   {exists} {f}")
    
    # Count total files
    current_dir = Path('.')
    all_files = []
    for item in current_dir.rglob('*'):
        if item.is_file():
            all_files.append(str(item.relative_to(current_dir)))
    
    print(f"\n📊 Summary:")
    print(f"   • Total files in directory: {len(all_files)}")
    print(f"   • Files referenced in JSON: {len(location_files)}")
    print(f"   • Protected files: {len(protected_files)}")
    print(f"   • Estimated files to be deleted: {len(all_files) - len(location_files) - len(protected_files)}")

if __name__ == "__main__":
    main()
