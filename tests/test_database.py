"""Tests for the database module."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY
import pytest

from doggo.database import (
    get_chroma_db_dir,
    create_chroma_db_dir,
    initialize_chroma_db,
    get_chroma_client,
    get_images_collection,
    add_image_to_index,
    get_indexed_files,
    get_index_stats
)


class TestChromaDBPaths:
    """Test ChromaDB path functions."""
    
    def test_get_chroma_db_dir(self):
        """Test getting ChromaDB directory path."""
        chroma_dir = get_chroma_db_dir()
        assert isinstance(chroma_dir, Path)
        assert chroma_dir.name == "chroma_db"
        assert chroma_dir.parent.name == ".doggo"
        assert chroma_dir.parent.parent == Path.home()


class TestChromaDBDirectory:
    """Test ChromaDB directory creation."""
    
    @patch('doggo.database.Path.home')
    def test_create_chroma_db_dir(self, mock_home):
        """Test creating ChromaDB directory."""
        # Setup mock home directory
        temp_dir = Path(tempfile.mkdtemp())
        mock_home.return_value = temp_dir
        
        chroma_dir = temp_dir / ".doggo" / "chroma_db"
        
        # Directory should not exist initially
        assert not chroma_dir.exists()
        
        # Create directory
        create_chroma_db_dir()
        
        # Directory should now exist
        assert chroma_dir.exists()
        assert chroma_dir.is_dir()
    
    @patch('doggo.database.Path.home')
    def test_create_chroma_db_dir_parents(self, mock_home):
        """Test creating ChromaDB directory when parent doesn't exist."""
        # Setup mock home directory
        temp_dir = Path(tempfile.mkdtemp())
        mock_home.return_value = temp_dir
        
        chroma_dir = temp_dir / ".doggo" / "chroma_db"
        
        # Neither parent nor target directory should exist
        assert not (temp_dir / ".doggo").exists()
        assert not chroma_dir.exists()
        
        # Create directory (should create parent too)
        create_chroma_db_dir()
        
        # Both directories should now exist
        assert (temp_dir / ".doggo").exists()
        assert chroma_dir.exists()
        assert chroma_dir.is_dir()
    
    @patch('doggo.database.Path.home')
    def test_create_chroma_db_dir_already_exists(self, mock_home):
        """Test creating ChromaDB directory when it already exists."""
        # Setup mock home directory
        temp_dir = Path(tempfile.mkdtemp())
        mock_home.return_value = temp_dir
        
        chroma_dir = temp_dir / ".doggo" / "chroma_db"
        
        # Create directory first time
        create_chroma_db_dir()
        assert chroma_dir.exists()
        
        # Create directory again (should not fail)
        create_chroma_db_dir()
        assert chroma_dir.exists()


class TestInitialization:
    """Test the main initialization function."""
    
    @patch('doggo.database.create_chroma_db_dir')
    def test_initialize_chroma_db(self, mock_create_dir):
        """Test the main ChromaDB initialization function."""
        initialize_chroma_db()
        
        # Should call create_chroma_db_dir
        mock_create_dir.assert_called_once()


class TestIntegration:
    """Integration tests for database operations."""
    
    def test_full_chroma_db_initialization_flow(self):
        """Test the complete ChromaDB initialization flow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('doggo.database.Path.home') as mock_home:
                mock_home.return_value = Path(temp_dir)
                
                # Initialize
                initialize_chroma_db()
                
                # Check directory was created
                chroma_dir = Path(temp_dir) / ".doggo" / "chroma_db"
                assert chroma_dir.exists()
                assert chroma_dir.is_dir()
                
                # Check parent directory was created
                parent_dir = Path(temp_dir) / ".doggo"
                assert parent_dir.exists()
                assert parent_dir.is_dir() 


class TestChromaDBOperations:
    """Test ChromaDB operations."""
    
    @patch('doggo.database.chromadb.PersistentClient')
    @patch('doggo.database.get_chroma_db_dir')
    def test_get_chroma_client(self, mock_get_dir, mock_client):
        """Test ChromaDB client creation."""
        mock_dir = Path("/fake/chroma/dir")
        mock_get_dir.return_value = mock_dir
        
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        client = get_chroma_client()
        
        assert client == mock_client_instance
        mock_client.assert_called_once_with(
            path=str(mock_dir),
            settings=ANY
        )
    
    @patch('doggo.database.get_chroma_client')
    def test_get_images_collection_new(self, mock_get_client):
        """Test getting images collection when it doesn't exist."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock that collection doesn't exist
        mock_client.get_collection.side_effect = Exception("Collection not found")
        
        collection = get_images_collection()
        
        # Should create new collection
        mock_client.create_collection.assert_called_once_with(
            name="images",
            metadata={"description": "Semantic search for images"}
        )
    
    @patch('doggo.database.get_chroma_client')
    def test_get_images_collection_existing(self, mock_get_client):
        """Test getting images collection when it exists."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock that collection exists
        mock_collection = MagicMock()
        mock_client.get_collection.return_value = mock_collection
        
        collection = get_images_collection()
        
        # Should get existing collection
        mock_client.get_collection.assert_called_once_with("images")
        assert collection == mock_collection


class TestImageIndexing:
    """Test image indexing operations."""
    
    @patch('doggo.database.get_images_collection')
    def test_add_image_to_index(self, mock_get_collection):
        """Test adding an image to the index."""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        
        file_hash = "test_hash_123"
        embedding = [0.1, 0.2, 0.3]
        description = "A beautiful sunset"
        metadata = {"file_path": "/test/image.jpg", "file_name": "image.jpg"}
        
        add_image_to_index(file_hash, embedding, description, metadata)
        
        # Should add to collection with indexed_time
        mock_collection.add.assert_called_once()
        call_args = mock_collection.add.call_args
        
        assert call_args[1]["embeddings"] == [embedding]
        assert call_args[1]["documents"] == [description]
        assert call_args[1]["ids"] == [file_hash]
        
        # Check metadata has indexed_time
        added_metadata = call_args[1]["metadatas"][0]
        assert added_metadata["file_path"] == "/test/image.jpg"
        assert "indexed_time" in added_metadata
    
    @patch('doggo.database.get_images_collection')
    def test_get_indexed_files(self, mock_get_collection):
        """Test getting list of indexed files."""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        
        mock_collection.get.return_value = {"ids": ["hash1", "hash2", "hash3"]}
        
        indexed_files = get_indexed_files()
        
        assert indexed_files == ["hash1", "hash2", "hash3"]
        mock_collection.get.assert_called_once_with(include=[])
    
    @patch('doggo.database.get_images_collection')
    def test_get_index_stats(self, mock_get_collection):
        """Test getting index statistics."""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        
        mock_collection.count.return_value = 42
        
        stats = get_index_stats()
        
        assert stats["total_images"] == 42
        assert stats["collection_name"] == "images"
        mock_collection.count.assert_called_once() 