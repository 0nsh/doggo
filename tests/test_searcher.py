"""Tests for the searcher module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from doggo.searcher import (
    generate_query_embedding,
    search_similar_images,
    get_top_result_preview
)


class TestGenerateQueryEmbedding:
    """Test query embedding generation."""
    
    @patch('doggo.searcher.load_config')
    @patch('doggo.searcher.openai.OpenAI')
    def test_generate_query_embedding_success(self, mock_openai, mock_load_config):
        """Test successful query embedding generation."""
        # Mock config
        mock_load_config.return_value = {"openai_api_key": "test-key"}
        
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test
        result = generate_query_embedding("test query")
        
        # Assertions
        assert result == [0.1, 0.2, 0.3]
        mock_client.embeddings.create.assert_called_once_with(
            model="text-embedding-3-small",
            input="test query"
        )
    
    @patch('doggo.searcher.load_config')
    def test_generate_query_embedding_no_api_key(self, mock_load_config):
        """Test query embedding generation without API key."""
        mock_load_config.return_value = {}
        
        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            generate_query_embedding("test query")


class TestSearchSimilarImages:
    """Test similarity search functionality."""
    
    @patch('doggo.searcher.generate_query_embedding')
    @patch('doggo.searcher.get_images_collection')
    def test_search_similar_images_success(self, mock_get_collection, mock_generate_embedding):
        """Test successful similarity search."""
        # Mock query embedding
        mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Mock collection and results
        mock_collection = Mock()
        mock_collection.query.return_value = {
            'ids': [['file1', 'file2']],
            'documents': [['desc1', 'desc2']],
            'metadatas': [[
                {'file_path': '/path1', 'file_name': 'file1.jpg'},
                {'file_path': '/path2', 'file_name': 'file2.png'}
            ]],
            'distances': [[0.1, 0.3]]
        }
        mock_get_collection.return_value = mock_collection
        
        # Test
        results = search_similar_images("test query", limit=2)
        
        # Assertions
        assert len(results) == 2
        assert results[0]['id'] == 'file1'
        assert results[0]['description'] == 'desc1'
        assert results[0]['similarity_score'] == 0.9  # 1 - 0.1
        assert results[1]['similarity_score'] == 0.7  # 1 - 0.3
        
        mock_collection.query.assert_called_once_with(
            query_embeddings=[[0.1, 0.2, 0.3]],
            n_results=2,
            include=['documents', 'metadatas', 'distances']
        )
    
    def test_search_similar_images_empty_query(self):
        """Test search with empty query."""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            search_similar_images("")
    
    def test_search_similar_images_invalid_limit(self):
        """Test search with invalid limit."""
        with pytest.raises(ValueError, match="Limit must be positive"):
            search_similar_images("test", limit=0)
        
        with pytest.raises(ValueError, match="Limit must be positive"):
            search_similar_images("test", limit=-1)


class TestGetTopResultPreview:
    """Test preview generation for search results."""
    
    def test_get_top_result_preview_small_file(self):
        """Test preview generation for small file."""
        result = {
            'metadata': {
                'file_path': '/test/path/image.jpg',
                'file_name': 'image.jpg',
                'file_size': 1024
            },
            'similarity_score': 0.85,
            'description': 'A beautiful sunset over the ocean'
        }
        
        preview = get_top_result_preview(result)
        
        assert '📁 File: image.jpg' in preview
        assert '📍 Path: /test/path/image.jpg' in preview
        assert '📏 Size: 1024 B' in preview
        assert '🎯 Similarity: 85.0%' in preview
        assert '📝 Description: A beautiful sunset over the ocean' in preview
    
    def test_get_top_result_preview_large_file(self):
        """Test preview generation for large file."""
        result = {
            'metadata': {
                'file_path': '/test/path/large.jpg',
                'file_name': 'large.jpg',
                'file_size': 5 * 1024 * 1024  # 5MB
            },
            'similarity_score': 0.92,
            'description': 'High resolution landscape photo'
        }
        
        preview = get_top_result_preview(result)
        
        assert '📏 Size: 5.0 MB' in preview
        assert '🎯 Similarity: 92.0%' in preview
    
    def test_get_top_result_preview_missing_metadata(self):
        """Test preview generation with missing metadata."""
        result = {
            'metadata': {},
            'similarity_score': 0.75,
            'description': 'Test description'
        }
        
        preview = get_top_result_preview(result)
        
        assert '📁 File: Unknown' in preview
        assert '📍 Path: Unknown' in preview
        assert '📏 Size: 0 B' in preview
        assert '🎯 Similarity: 75.0%' in preview 