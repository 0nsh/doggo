"""Tests for the utils module."""

import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from PIL import Image

from doggo.utils import (
    is_image_file,
    get_file_hash,
    scan_image_files,
    extract_file_metadata,
    validate_image_file,
    SUPPORTED_EXTENSIONS
)


class TestImageDetection:
    """Test image file detection."""
    
    def test_is_image_file_supported_formats(self):
        """Test detection of supported image formats."""
        for ext in SUPPORTED_EXTENSIONS:
            file_path = Path(f"test{ext}")
            assert is_image_file(file_path)
    
    def test_is_image_file_unsupported_formats(self):
        """Test detection of unsupported formats."""
        unsupported = ['.txt', '.pdf', '.doc', '.mp4', '.mp3']
        for ext in unsupported:
            file_path = Path(f"test{ext}")
            assert not is_image_file(file_path)
    
    def test_is_image_file_case_insensitive(self):
        """Test that file detection is case insensitive."""
        assert is_image_file(Path("test.PNG"))
        assert is_image_file(Path("test.jpeg"))


class TestFileHash:
    """Test file hash generation."""
    
    def test_get_file_hash_consistent(self):
        """Test that file hash is consistent for same file."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test content")
            file_path = Path(f.name)
        
        try:
            hash1 = get_file_hash(file_path)
            hash2 = get_file_hash(file_path)
            assert hash1 == hash2
        finally:
            file_path.unlink()
    
    def test_get_file_hash_different_files(self):
        """Test that different files have different hashes."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f1:
            f1.write(b"content 1")
            file_path1 = Path(f1.name)
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f2:
            f2.write(b"content 2")
            file_path2 = Path(f2.name)
        
        try:
            hash1 = get_file_hash(file_path1)
            hash2 = get_file_hash(file_path2)
            assert hash1 != hash2
        finally:
            file_path1.unlink()
            file_path2.unlink()


class TestFileScanning:
    """Test directory scanning for image files."""
    
    def test_scan_image_files_empty_directory(self):
        """Test scanning empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            image_files = scan_image_files(Path(temp_dir))
            assert image_files == []
    
    def test_scan_image_files_with_images(self):
        """Test scanning directory with image files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create some test files
            (temp_path / "image1.jpeg").touch()
            (temp_path / "image2.png").touch()
            (temp_path / "document.txt").touch()
            (temp_path / "subdir").mkdir()
            (temp_path / "subdir" / "image3.webp").touch()
            
            image_files = scan_image_files(temp_path)
            
            # Should find 3 image files
            assert len(image_files) == 3
            assert any("image1.jpeg" in str(f) for f in image_files)
            assert any("image2.png" in str(f) for f in image_files)
            assert any("image3.webp" in str(f) for f in image_files)
    
    def test_scan_image_files_nonexistent_directory(self):
        """Test scanning nonexistent directory."""
        image_files = scan_image_files(Path("/nonexistent/path"))
        assert image_files == []


class TestMetadataExtraction:
    """Test file metadata extraction."""
    
    def test_extract_file_metadata(self):
        """Test metadata extraction from a file."""
        with tempfile.NamedTemporaryFile(suffix='.jpeg', delete=False) as f:
            f.write(b"fake image data")
            file_path = Path(f.name)
        
        try:
            metadata = extract_file_metadata(file_path)
            
            assert metadata["file_path"] == str(file_path.absolute())
            assert metadata["file_name"] == file_path.name
            assert metadata["file_type"] == "jpeg"
            assert metadata["file_size"] > 0
            assert metadata["modified_time"] > 0
            assert len(metadata["file_hash"]) == 32  # MD5 hash length
        finally:
            file_path.unlink()


class TestImageValidation:
    """Test image file validation."""
    
    def test_validate_image_file_valid(self):
        """Test validation of a valid image file."""
        # Create a simple test image
        with tempfile.NamedTemporaryFile(suffix='.jpeg', delete=False) as f:
            img = Image.new('RGB', (10, 10), color='red')
            img.save(f.name, 'PNG')
            file_path = Path(f.name)
        
        try:
            assert validate_image_file(file_path)
        finally:
            file_path.unlink()
    
    def test_validate_image_file_invalid(self):
        """Test validation of an invalid image file."""
        with tempfile.NamedTemporaryFile(suffix='.jpeg', delete=False) as f:
            f.write(b"not an image file")
            file_path = Path(f.name)
        
        try:
            assert not validate_image_file(file_path)
        finally:
            file_path.unlink()
    
    def test_validate_image_file_nonexistent(self):
        """Test validation of nonexistent file."""
        file_path = Path("/nonexistent/image.jpeg")
        assert not validate_image_file(file_path) 