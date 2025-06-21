"""Tests for the indexer module."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from PIL import Image

from doggo.indexer import (
    generate_image_description,
    generate_embedding,
    process_single_image,
    index_directory
)


class TestAIIntegration:
    """Test AI integration functions."""
    
    @patch('doggo.indexer.load_config')
    @patch('doggo.indexer.openai.OpenAI')
    def test_generate_image_description(self, mock_openai, mock_load_config):
        """Test image description generation."""
        # Mock config
        mock_load_config.return_value = {"openai_api_key": "sk-test123"}
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "A beautiful sunset over the ocean"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create test image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (100, 100), color='red')
            img.save(f.name, 'JPEG')
            image_path = Path(f.name)
        
        try:
            description = generate_image_description(image_path)
            assert description == "A beautiful sunset over the ocean"
            
            # Verify API call
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            
            assert call_args[1]["model"] == "gpt-4o"
            assert call_args[1]["max_tokens"] == 150
            
            # Check message content
            messages = call_args[1]["messages"][0]["content"]
            assert len(messages) == 2
            assert messages[0]["type"] == "text"
            assert "Describe this image" in messages[0]["text"]
            assert messages[1]["type"] == "image_url"
        finally:
            image_path.unlink()
    
    @patch('doggo.indexer.load_config')
    @patch('doggo.indexer.openai.OpenAI')
    def test_generate_image_description_no_api_key(self, mock_openai, mock_load_config):
        """Test image description generation without API key."""
        mock_load_config.return_value = {"openai_api_key": ""}
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            img = Image.new('RGB', (10, 10), color='red')
            img.save(f.name, 'JPEG')
            image_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError, match="OpenAI API key not configured"):
                generate_image_description(image_path)
        finally:
            image_path.unlink()
    
    @patch('doggo.indexer.load_config')
    @patch('doggo.indexer.openai.OpenAI')
    def test_generate_embedding(self, mock_openai, mock_load_config):
        """Test embedding generation."""
        # Mock config
        mock_load_config.return_value = {"openai_api_key": "sk-test123"}
        
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.data[0].embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_client.embeddings.create.return_value = mock_response
        
        embedding = generate_embedding("test text")
        
        assert embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Verify API call
        mock_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input="test text"
        )


class TestImageProcessing:
    """Test single image processing."""
    
    @patch('doggo.indexer.validate_image_file')
    @patch('doggo.indexer.extract_file_metadata')
    @patch('doggo.indexer.generate_image_description')
    @patch('doggo.indexer.generate_embedding')
    def test_process_single_image(self, mock_embedding, mock_description, mock_metadata, mock_validate):
        """Test processing a single image."""
        # Mock all dependencies
        mock_validate.return_value = True
        mock_metadata.return_value = {
            "file_hash": "test_hash_123",
            "file_path": "/test/image.jpg",
            "file_name": "image.jpg"
        }
        mock_description.return_value = "A beautiful sunset"
        mock_embedding.return_value = [0.1, 0.2, 0.3]
        
        image_path = Path("/test/image.jpg")
        result = process_single_image(image_path)
        
        assert result["file_hash"] == "test_hash_123"
        assert result["description"] == "A beautiful sunset"
        assert result["embedding"] == [0.1, 0.2, 0.3]
        assert result["metadata"]["file_path"] == "/test/image.jpg"
        
        # Verify calls
        mock_validate.assert_called_once_with(image_path)
        mock_metadata.assert_called_once_with(image_path)
        mock_description.assert_called_once_with(image_path)
        mock_embedding.assert_called_once_with("A beautiful sunset image.jpg")
    
    @patch('doggo.indexer.validate_image_file')
    def test_process_single_image_invalid(self, mock_validate):
        """Test processing an invalid image."""
        mock_validate.return_value = False
        
        image_path = Path("/test/invalid.jpg")
        
        with pytest.raises(ValueError, match="Invalid or corrupted image"):
            process_single_image(image_path)


class TestDirectoryIndexing:
    """Test directory indexing functionality."""
    
    @patch('doggo.indexer.scan_image_files')
    @patch('doggo.indexer.get_indexed_files')
    @patch('doggo.indexer.extract_file_metadata')
    def test_index_directory_empty(self, mock_metadata, mock_indexed, mock_scan):
        """Test indexing empty directory."""
        mock_scan.return_value = []
        mock_indexed.return_value = []
        
        result = index_directory(Path("/test/dir"))
        
        assert result["total_found"] == 0
        assert result["processed"] == 0
        assert result["skipped"] == 0
        assert result["errors"] == 0
    
    @patch('doggo.indexer.scan_image_files')
    @patch('doggo.indexer.get_indexed_files')
    @patch('doggo.indexer.extract_file_metadata')
    def test_index_directory_dry_run(self, mock_metadata, mock_indexed, mock_scan):
        """Test dry run indexing."""
        # Mock found files
        mock_scan.return_value = [Path("/test/image1.jpg"), Path("/test/image2.png")]
        mock_indexed.return_value = ["existing_hash"]
        
        # Mock metadata for files
        def mock_metadata_side_effect(path):
            if "image1" in str(path):
                return {"file_hash": "new_hash_1"}
            else:
                return {"file_hash": "existing_hash"}
        
        mock_metadata.side_effect = mock_metadata_side_effect
        
        result = index_directory(Path("/test/dir"), dry_run=True)
        
        assert result["total_found"] == 2
        assert result["processed"] == 0
        assert result["skipped"] == 1
        assert result["would_process"] == 1
        assert result["errors"] == 0
    
    @patch('doggo.indexer.scan_image_files')
    @patch('doggo.indexer.get_indexed_files')
    @patch('doggo.indexer.extract_file_metadata')
    @patch('doggo.indexer.process_single_image')
    @patch('doggo.indexer.add_image_to_index')
    def test_index_directory_success(self, mock_add, mock_process, mock_metadata, mock_indexed, mock_scan):
        """Test successful indexing."""
        # Mock found files
        mock_scan.return_value = [Path("/test/image1.jpg")]
        mock_indexed.return_value = []
        
        # Mock metadata
        mock_metadata.return_value = {"file_hash": "new_hash_1"}
        
        # Mock processing result
        mock_process.return_value = {
            "file_hash": "new_hash_1",
            "embedding": [0.1, 0.2, 0.3],
            "description": "A beautiful image",
            "metadata": {"file_path": "/test/image1.jpg"}
        }
        
        result = index_directory(Path("/test/dir"))
        
        assert result["total_found"] == 1
        assert result["processed"] == 1
        assert result["skipped"] == 0
        assert result["errors"] == 0
        
        # Verify processing was called
        mock_process.assert_called_once_with(Path("/test/image1.jpg"))
        mock_add.assert_called_once()
    
    @patch('doggo.indexer.scan_image_files')
    @patch('doggo.indexer.get_indexed_files')
    @patch('doggo.indexer.extract_file_metadata')
    @patch('doggo.indexer.process_single_image')
    @patch('doggo.indexer.add_image_to_index')
    def test_index_directory_with_errors(self, mock_add, mock_process, mock_metadata, mock_indexed, mock_scan):
        """Test indexing with processing errors."""
        # Mock found files
        mock_scan.return_value = [Path("/test/image1.jpg"), Path("/test/image2.jpg")]
        mock_indexed.return_value = []
        
        # Mock metadata
        mock_metadata.return_value = {"file_hash": "test_hash"}
        
        # Mock processing to fail for second image
        def mock_process_side_effect(path):
            if "image2" in str(path):
                raise Exception("Processing failed")
            return {
                "file_hash": "test_hash",
                "embedding": [0.1, 0.2, 0.3],
                "description": "A beautiful image",
                "metadata": {"file_path": str(path)}
            }
        
        mock_process.side_effect = mock_process_side_effect
        
        result = index_directory(Path("/test/dir"))
        
        assert result["total_found"] == 2
        assert result["processed"] == 1
        assert result["skipped"] == 0
        assert result["errors"] == 1
        assert len(result["errors_list"]) == 1
        assert "Processing failed" in result["errors_list"][0] 