"""File utilities and helpers for Doggo."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Set, Dict, Any
from PIL import Image, UnidentifiedImageError


# Supported image formats
SUPPORTED_EXTENSIONS = {'.jpeg', '.png', '.gif', '.webp'}


def is_image_file(file_path: Path) -> bool:
    """Check if a file is a supported image format."""
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS


def get_file_hash(file_path: Path) -> str:
    """Generate a unique hash for a file based on path and modification time."""
    stat = file_path.stat()
    content = f"{file_path.absolute()}:{stat.st_mtime}:{stat.st_size}"
    return hashlib.md5(content.encode()).hexdigest()


def scan_image_files(directory: Path) -> List[Path]:
    """Recursively scan directory for image files."""
    image_files = []
    
    if not directory.exists():
        return image_files
    
    for file_path in directory.rglob('*'):
        if file_path.is_file() and is_image_file(file_path):
            image_files.append(file_path)
    
    return sorted(image_files)


def extract_file_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract metadata from an image file."""
    stat = file_path.stat()
    
    return {
        "file_path": str(file_path.absolute()),
        "file_name": file_path.name,
        "file_type": file_path.suffix.lower().lstrip('.'),
        "file_size": stat.st_size,
        "modified_time": int(stat.st_mtime),
        "file_hash": get_file_hash(file_path)
    }


def validate_image_file(file_path: Path) -> bool:
    """Validate that a file is a readable image."""
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def open_in_native_previewer(file_path: Path) -> bool:
    """Open a file in the native system previewer.
    
    Args:
        file_path: Path to the file to open.
        
    Returns:
        True if the file was opened successfully, False otherwise.
    """
    try:
        if sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(file_path)], check=True)
        elif sys.platform == "win32":  # Windows
            subprocess.run(["start", str(file_path)], shell=True, check=True)
        else:  # Linux and other Unix-like systems
            subprocess.run(["xdg-open", str(file_path)], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False 