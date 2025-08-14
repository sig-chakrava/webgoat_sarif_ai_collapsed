#!/usr/bin/env python3
"""
Script to generate a shell script that will delete all files in the current directory 
except those referenced in the input.json file where key="location".
This version creates a shell script for review before execution.
"""

import json
import os
import sys
from pathlib import Path

def extract_location_files(json_file_path):
    """
    Extract all file paths from JSON where key is "location"
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON file: {e}")
        return set()
    
    location_files = set()
    
    def traverse_json(obj):
        """Recursively traverse JSON to find location entries"""
        if isinstance(obj, dict):
            # Check if this is a location entry
            if obj.get("key") == "location" and "value" in obj:
                file_path = obj["value"]
                if isinstance(file_path, str) and file_path.strip():
                    location_files.add(file_path)
            
            # Recursively check all values in the dict
            for value in obj.values():
                traverse_json(value)
                
        elif isinstance(obj, list):
            # Recursively check all items in the list
            for item in obj:
                traverse_json(item)
    
    traverse_json(data)
    return location_files

def get_protected_files():
    """
    Get a set of files that should never be deleted
    """
    return {
        'input.json',
        'cleanup_files.py',
        'generate_cleanup_script.py',
        'cleanup_script.sh',
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
    if file_path.startswith('./'):
        file_path = file_path[2:]
    return Path(file_path)

def find_files_to_delete(location_files, protected_files):
    """
    Find all files in current directory that should be deleted
    """
    current_dir = Path('.')
    all_files = set()
    
    # Get all files recursively
    for item in current_dir.rglob('*'):
        if item.is_file():
            rel_path = str(item.relative_to(current_dir))
            all_files.add(rel_path)
    
    # Normalize location files for comparison
    normalized_location_files = set()
    for loc_file in location_files:
        normalized_path = normalize_path(loc_file)
        normalized_location_files.add(str(normalized_path))
        
        # Also add the filename only
        filename_only = normalized_path.name
        if filename_only:
            normalized_location_files.add(filename_only)
    
    # Files to keep
    files_to_keep = protected_files.union(normalized_location_files)
    
    # Find files to delete
    files_to_delete = []
    for file_path in all_files:
        path_obj = Path(file_path)
        should_keep = False
        
        for keep_file in files_to_keep:
            keep_path = Path(keep_file)
            
            if (str(path_obj) == str(keep_path) or 
                path_obj.name == keep_path.name or 
                str(path_obj).startswith('.git/')):
                should_keep = True
                break
        
        if not should_keep:
            files_to_delete.append(file_path)
    
    return files_to_delete, files_to_keep

def generate_shell_script(files_to_delete, files_to_keep):
    """
    Generate a shell script to delete the specified files
    """
    script_content = f"""#!/bin/bash

# Generated cleanup script
# This script will delete files not referenced in input.json location fields

echo "🔍 Cleanup Script Generated from input.json analysis"
echo "📊 Files to keep: {len(files_to_keep)}"
echo "🗑️  Files to delete: {len(files_to_delete)}"
echo ""

# Files that will be kept (for reference):
echo "📂 Files that will be KEPT:"
"""

    # Add kept files as comments
    for file_path in sorted(files_to_keep):
        script_content += f'echo "   • {file_path}"\n'
    
    script_content += '\necho ""\necho "🗑️  Files that will be DELETED:"\n'
    
    # Add files to delete as comments first
    for file_path in sorted(files_to_delete):
        script_content += f'echo "   • {file_path}"\n'
    
    script_content += f'''
echo ""
read -p "⚠️  Are you sure you want to delete {len(files_to_delete)} files? (yes/no): " confirm

if [[ $confirm == "yes" || $confirm == "y" ]]; then
    echo "🗑️  Starting deletion..."
    deleted_count=0
    error_count=0
    
'''
    
    # Add deletion commands
    for file_path in sorted(files_to_delete):
        # Escape special characters for shell
        escaped_path = file_path.replace("'", "'\"'\"'")
        script_content += f"""    if [ -f '{escaped_path}' ]; then
        if rm '{escaped_path}'; then
            echo "✅ Deleted: {file_path}"
            ((deleted_count++))
        else
            echo "❌ Error deleting: {file_path}"
            ((error_count++))
        fi
    else
        echo "⚠️  File not found: {file_path}"
    fi
    
"""
    
    script_content += f'''    echo ""
    echo "📊 Summary:"
    echo "   • Successfully deleted: $deleted_count files"
    echo "   • Errors: $error_count files"
    echo "   • Files kept: {len(files_to_keep)} files"
else
    echo "🚫 Operation cancelled."
fi
'''
    
    return script_content

def main():
    """
    Main function
    """
    print("🔍 Analyzing input.json for file locations...")
    
    # Extract location files from JSON
    location_files = extract_location_files('input.json')
    
    if not location_files:
        print("❌ No location files found in input.json")
        return
    
    print(f"📍 Found {len(location_files)} location entries:")
    for loc_file in sorted(location_files):
        print(f"   • {loc_file}")
    
    # Get protected files
    protected_files = get_protected_files()
    
    print(f"\n🛡️  Protected files (will not be deleted):")
    for prot_file in sorted(protected_files):
        print(f"   • {prot_file}")
    
    # Find files to delete
    files_to_delete, files_to_keep = find_files_to_delete(location_files, protected_files)
    
    print(f"\n📂 Total files to keep: {len(files_to_keep)}")
    print(f"🗑️  Files that would be deleted: {len(files_to_delete)}")
    
    if not files_to_delete:
        print("✅ No files need to be deleted.")
        return
    
    # Generate shell script
    script_content = generate_shell_script(files_to_delete, files_to_keep)
    
    script_filename = 'cleanup_script.sh'
    with open(script_filename, 'w') as f:
        f.write(script_content)
    
    # Make script executable
    os.chmod(script_filename, 0o755)
    
    print(f"\n✅ Generated shell script: {script_filename}")
    print("📋 To review the script: cat cleanup_script.sh")
    print("🚀 To execute the script: ./cleanup_script.sh")
    print("\n⚠️  IMPORTANT: Please review the script before executing!")

if __name__ == "__main__":
    main()
