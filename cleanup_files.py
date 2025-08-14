#!/usr/bin/env python3
"""
Script to delete all files in the current directory except those referenced
in the input.json file where key="location" and value contains file paths.
"""

import json
import os
import sys
from pathlib import Path

def extract_location_files(json_file_path):
    """
    Extract all file paths from JSON where key="location", key="filename", or field="file"
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}")
        return set(), set(), set()
    
    location_files = set()
    filename_files = set()
    file_field_files = set()
    
    def traverse_json(obj):
        """Recursively traverse JSON to find location, filename, and direct file entries"""
        if isinstance(obj, dict):
            # Check if this is a location entry (key-value pair)
            if obj.get("key") == "location" and "value" in obj:
                file_path = obj["value"]
                if isinstance(file_path, str) and file_path.strip():
                    location_files.add(file_path)
            
            # Check if this is a filename entry (key-value pair)
            elif obj.get("key") == "filename" and "value" in obj:
                file_name = obj["value"]
                if isinstance(file_name, str) and file_name.strip():
                    filename_files.add(file_name)
            
            # Check if this object has a direct "file" field
            if "file" in obj and isinstance(obj["file"], str) and obj["file"].strip():
                file_field_files.add(obj["file"])
            
            # Recursively check all values in the dict
            for value in obj.values():
                traverse_json(value)
                
        elif isinstance(obj, list):
            # Recursively check all items in the list
            for item in obj:
                traverse_json(item)
    
    traverse_json(data)
    return location_files, filename_files, file_field_files

def get_protected_files():
    """
    Get a set of files that should never be deleted
    """
    return {
        'input.json',
        'cleanup_files.py',
        'poc.json',
        '.git',
        '.gitignore',
        'README.md',
        'pom.xml',
        'mvnw',
        'mvnw.cmd'
    }

def normalize_path(file_path):
    """
    Normalize file path to handle different path formats
    """
    # Remove leading './' if present
    if file_path.startswith('./'):
        file_path = file_path[2:]
    
    # Convert to Path object for better handling
    return Path(file_path)

def find_files_to_delete(location_files, filename_files, file_field_files, protected_files):
    """
    Find all files in current directory that should be deleted
    """
    current_dir = Path('.')
    all_files = set()
    
    # Get all files recursively
    for item in current_dir.rglob('*'):
        if item.is_file():
            # Convert to relative path string
            rel_path = str(item.relative_to(current_dir))
            all_files.add(rel_path)
    
    # Normalize location files for comparison (full paths)
    normalized_location_files = set()
    for loc_file in location_files:
        normalized_path = normalize_path(loc_file)
        normalized_location_files.add(str(normalized_path))
        
        # Also add the filename only (in case path structure differs)
        filename_only = normalized_path.name
        if filename_only:
            normalized_location_files.add(filename_only)
    
    # Normalize file field files for comparison (full paths)
    normalized_file_field_files = set()
    for file_field in file_field_files:
        normalized_path = normalize_path(file_field)
        normalized_file_field_files.add(str(normalized_path))
        
        # Also add the filename only (in case path structure differs)
        filename_only = normalized_path.name
        if filename_only:
            normalized_file_field_files.add(filename_only)
    
    # Add filename files (just filenames) to protected set
    normalized_filename_files = set()
    for filename in filename_files:
        if filename.strip():
            normalized_filename_files.add(filename.strip())
    
    # Files to keep: protected files + location files + filename files + file field files
    files_to_keep = protected_files.union(normalized_location_files).union(normalized_filename_files).union(normalized_file_field_files)
    
    # Find files to delete
    files_to_delete = []
    for file_path in all_files:
        path_obj = Path(file_path)
        should_keep = False
        
        # Check if this file should be kept
        for keep_file in files_to_keep:
            keep_path = Path(keep_file)
            
            # Exact match (full path)
            if str(path_obj) == str(keep_path):
                should_keep = True
                break
            
            # Filename match (just the filename part)
            if path_obj.name == keep_path.name:
                should_keep = True
                break
                
            # Direct filename match (for filename entries)
            if path_obj.name == keep_file:
                should_keep = True
                break
            
            # Check if file is in a protected directory
            if str(path_obj).startswith('.git/'):
                should_keep = True
                break
        
        if not should_keep:
            files_to_delete.append(file_path)
    
    return files_to_delete, files_to_keep
def main():
    """
    Main function
    """
    print("🔍 Analyzing input.json for file locations, filenames, and file fields...")
    
    # Extract location, filename, and file field files from JSON
    location_files, filename_files, file_field_files = extract_location_files('input.json')
    
    if not location_files and not filename_files and not file_field_files:
        print("❌ No location, filename, or file field entries found in input.json")
        return
    
    print(f"� Found {len(location_files)} location entries (full paths):")
    for loc_file in sorted(location_files):
        print(f"   • {loc_file}")
    
    print(f"\n📄 Found {len(filename_files)} filename entries (filenames only):")
    for filename in sorted(filename_files):
        print(f"   • {filename}")
    
    print(f"\n� Found {len(file_field_files)} file field entries (full paths):")
    for file_field in sorted(file_field_files):
        print(f"   • {file_field}")
    
    # Get protected files
    protected_files = get_protected_files()
    
    print(f"\n🛡️  Protected files (will not be deleted):")
    for prot_file in sorted(protected_files):
        print(f"   • {prot_file}")
    
    # Find files to delete
    files_to_delete, files_to_keep = find_files_to_delete(location_files, filename_files, file_field_files, protected_files)
    
    print(f"\n📂 Total files to keep: {len(files_to_keep)}")
    print(f"🗑️  Files that would be deleted: {len(files_to_delete)}")
    
    if not files_to_delete:
        print("✅ No files need to be deleted.")
        return
    
    print("\n📋 Files that would be deleted:")
    for file_path in sorted(files_to_delete):
        print(f"   • {file_path}")
    
    # Ask for confirmation
    response = input(f"\n⚠️  Are you sure you want to delete {len(files_to_delete)} files? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        deleted_count = 0
        error_count = 0
        
        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                print(f"✅ Deleted: {file_path}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Error deleting {file_path}: {e}")
                error_count += 1
        
        print(f"\n📊 Summary:")
        print(f"   • Successfully deleted: {deleted_count} files")
        print(f"   • Errors: {error_count} files")
        print(f"   • Files kept: {len(files_to_keep)} files")
        
    else:
        print("🚫 Operation cancelled.")

if __name__ == "__main__":
    main()
