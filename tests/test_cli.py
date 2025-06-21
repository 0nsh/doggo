"""Tests for the CLI module."""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
import re

from doggo.cli import main


class TestCLIInit:
    """Test the init command."""
    
    def setup_method(self):
        """Setup test runner."""
        self.runner = CliRunner()
    
    @patch('doggo.cli.initialize_doggo')
    @patch('doggo.cli.initialize_chroma_db')
    def test_init_success(self, mock_init_chroma, mock_init_doggo):
        """Test successful init command."""
        result = self.runner.invoke(main, ['init'])
        
        # Should succeed
        assert result.exit_code == 0
        
        # Should call both initialization functions
        mock_init_doggo.assert_called_once()
        mock_init_chroma.assert_called_once()
        
        # Should show success message
        assert "Doggo initialized successfully" in result.output
        assert "Configuration directory" in result.output
        assert "ChromaDB directory" in result.output
        assert "Next steps" in result.output
    
    @patch('doggo.cli.initialize_doggo')
    @patch('doggo.cli.initialize_chroma_db')
    def test_init_handles_doggo_error(self, mock_init_chroma, mock_init_doggo):
        """Test init command handles doggo initialization error."""
        # Mock doggo initialization to raise an error
        mock_init_doggo.side_effect = Exception("Config error")
        
        result = self.runner.invoke(main, ['init'])
        
        # Should fail
        assert result.exit_code != 0
        
        # Should show error message
        assert "Failed to initialize Doggo" in result.output
        assert "Config error" in result.output
    
    @patch('doggo.cli.initialize_doggo')
    @patch('doggo.cli.initialize_chroma_db')
    def test_init_handles_chroma_error(self, mock_init_chroma, mock_init_doggo):
        """Test init command handles ChromaDB initialization error."""
        # Mock ChromaDB initialization to raise an error
        mock_init_chroma.side_effect = Exception("Database error")
        
        result = self.runner.invoke(main, ['init'])
        
        # Should fail
        assert result.exit_code != 0
        
        # Should show error message
        assert "Failed to initialize Doggo" in result.output
        assert "Database error" in result.output
    
    def test_init_help(self):
        """Test init command help."""
        result = self.runner.invoke(main, ['init', '--help'])
        
        # Should show help
        assert result.exit_code == 0
        assert "Initialize Doggo configuration and directories" in result.output


class TestCLIHelp:
    """Test CLI help and general functionality."""
    
    def setup_method(self):
        """Setup test runner."""
        self.runner = CliRunner()
    
    def test_main_help(self):
        """Test main command help."""
        result = self.runner.invoke(main, ['--help'])
        
        # Should show help
        assert result.exit_code == 0
        assert "Doggo - Semantic file search using AI" in result.output
        assert "init" in result.output
    
    def test_main_no_args(self):
        """Test main command with no arguments."""
        result = self.runner.invoke(main, [])
        
        # Click groups exit with code 2 when no subcommand is provided
        assert result.exit_code == 2
        assert "Doggo - Semantic file search using AI" in result.output


class TestCLIIntegration:
    """Integration tests for CLI with actual file system."""
    
    def setup_method(self):
        """Setup test runner."""
        self.runner = CliRunner()
    
    @patch('doggo.config.Path.home')
    def test_init_creates_actual_directories(self, mock_home):
        """Test init command creates actual directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_home.return_value = Path(temp_dir)
            
            result = self.runner.invoke(main, ['init'])
            
            # Should succeed
            assert result.exit_code == 0
            
            # Check directories were created
            config_dir = Path(temp_dir) / ".doggo"
            chroma_dir = config_dir / "chroma_db"
            config_file = config_dir / "config.json"
            
            assert config_dir.exists()
            assert config_dir.is_dir()
            assert chroma_dir.exists()
            assert chroma_dir.is_dir()
            assert config_file.exists()
            assert config_file.is_file()
    
    @patch('doggo.config.Path.home')
    def test_init_idempotent(self, mock_home):
        """Test init command is idempotent."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_home.return_value = Path(temp_dir)
            
            # Run init twice
            result1 = self.runner.invoke(main, ['init'])
            result2 = self.runner.invoke(main, ['init'])
            
            # Both should succeed
            assert result1.exit_code == 0
            assert result2.exit_code == 0
            
            # Should show success message both times
            assert "Doggo initialized successfully" in result1.output
            assert "Doggo initialized successfully" in result2.output


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""
    
    def setup_method(self):
        """Setup test runner."""
        self.runner = CliRunner()
    
    @patch('doggo.config.Path.home')
    def test_init_permission_error(self, mock_home):
        """Test init command handles permission errors."""
        # Mock home to a directory that can't be written to
        mock_home.return_value = Path("/root")  # Usually requires permissions
        
        result = self.runner.invoke(main, ['init'])
        
        # Should fail with permission error
        assert result.exit_code != 0
        assert "Failed to initialize Doggo" in result.output 


class TestCLIConfig:
    """Test the config CLI commands."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    @patch('doggo.config.set_api_key')
    def test_config_set_key_valid(self, mock_set_key):
        result = self.runner.invoke(main, ['config', 'set-key', 'sk-1234567890abcdef'])
        assert result.exit_code == 0
        assert "OpenAI API key set successfully" in result.output
        mock_set_key.assert_called_once_with('sk-1234567890abcdef')
    
    @patch('doggo.config.set_api_key', side_effect=ValueError("Invalid OpenAI API key format."))
    def test_config_set_key_invalid(self, mock_set_key):
        result = self.runner.invoke(main, ['config', 'set-key', 'invalid-key'])
        assert result.exit_code != 0
        assert "Invalid API Key" in result.output
        assert "Invalid OpenAI API key format" in result.output
    
    @patch('doggo.config.get_config_summary')
    def test_config_show(self, mock_summary):
        mock_summary.return_value = {
            "OpenAI API Key": "sk-1234...cdef",
            "Indexed Paths": 2,
            "Last Reindex": "2024-01-01",
            "Version": "0.1.0"
        }
        result = self.runner.invoke(main, ['config', 'show'])
        assert result.exit_code == 0
        assert "Doggo Configuration" in result.output
        assert "sk-1234...cdef" in result.output
        assert "Indexed Paths" in result.output
        assert "2" in result.output
        assert "2024-01-01" in result.output
        assert "0.1.0" in result.output
    
    @patch('doggo.config.get_config_summary', side_effect=Exception("Config error"))
    def test_config_show_error(self, mock_summary):
        result = self.runner.invoke(main, ['config', 'show'])
        assert result.exit_code != 0
        assert "Failed to load configuration" in result.output
        assert "Config error" in result.output 


class TestCLIIndex:
    """Test the index CLI command."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    @patch('doggo.cli.index_directory')
    @patch('doggo.cli.get_index_stats')
    def test_index_success(self, mock_stats, mock_index):
        mock_index.return_value = {
            "total_found": 5,
            "processed": 3,
            "skipped": 2,
            "errors": 0,
            "errors_list": []
        }
        mock_stats.return_value = {"total_images": 10}
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(main, ['index', temp_dir])
            assert result.exit_code == 0
            assert f"Indexing {temp_dir}" in result.output
            assert "Indexing completed!" in result.output
            assert "Total images found: 5" in result.output
            assert "Processed: 3" in result.output
            assert "Skipped (already indexed): 2" in result.output
            assert "Total indexed images: 10" in result.output
            mock_index.assert_called_once_with(Path(temp_dir), dry_run=False)
    
    @patch('doggo.cli.index_directory')
    def test_index_dry_run(self, mock_index):
        mock_index.return_value = {
            "total_found": 5,
            "processed": 0,
            "skipped": 2,
            "errors": 0,
            "errors_list": [],
            "would_process": 3
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(main, ['index', temp_dir, '--dry-run'])
            assert result.exit_code == 0
            # Accept line break between prefix and path
            assert "Dry run: Would index images in" in result.output
            assert temp_dir in result.output
            assert "Dry Run Results" in result.output
            assert "Total images found: 5" in result.output
            assert "Would skip (already indexed): 2" in result.output
            assert "Would process: 3" in result.output
            mock_index.assert_called_once_with(Path(temp_dir), dry_run=True)
    
    @patch('doggo.cli.index_directory')
    @patch('doggo.cli.get_index_stats')
    def test_index_with_errors(self, mock_stats, mock_index):
        mock_index.return_value = {
            "total_found": 3,
            "processed": 1,
            "skipped": 1,
            "errors": 1,
            "errors_list": ["/test/image.jpg: Processing failed"]
        }
        mock_stats.return_value = {"total_images": 5}
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(main, ['index', temp_dir])
            assert result.exit_code == 0
            assert "Errors encountered" in result.output or "❌ Errors" in result.output
            assert "Processing failed" in result.output
    
    @patch('doggo.cli.index_directory')
    def test_index_failure(self, mock_index):
        mock_index.side_effect = Exception("Indexing failed")
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(main, ['index', temp_dir])
            assert result.exit_code != 0
            assert "Failed to index directory" in result.output
            assert "Indexing failed" in result.output
    
    def test_index_nonexistent_path(self):
        result = self.runner.invoke(main, ['index', '/nonexistent/path'])
        assert result.exit_code != 0
        assert "does not exist" in result.output
    
    def test_index_help(self):
        result = self.runner.invoke(main, ['index', '--help'])
        assert result.exit_code == 0
        assert "Index images in the specified directory" in result.output
        assert "--dry-run" in result.output 


class TestCLISearch:
    """Test the search CLI command."""
    
    def setup_method(self):
        self.runner = CliRunner()
    
    @patch('doggo.cli.search_similar_images')
    def test_search_success(self, mock_search):
        """Test successful search command."""
        # Mock search results
        mock_search.return_value = [
            {
                'id': 'file1',
                'description': 'A beautiful sunset over the ocean',
                'metadata': {
                    'file_path': '/test/path/image1.jpg',
                    'file_name': 'image1.jpg'
                },
                'similarity_score': 0.85
            },
            {
                'id': 'file2', 
                'description': 'Ocean waves crashing on the shore',
                'metadata': {
                    'file_path': '/test/path/image2.jpg',
                    'file_name': 'image2.jpg'
                },
                'similarity_score': 0.72
            }
        ]
        
        result = self.runner.invoke(main, ['search', 'sunset beach'])
        
        # Should succeed
        assert result.exit_code == 0
        
        # Should show search query
        assert "Searching for: 'sunset beach'" in result.output
        
        # Should show results table
        assert "Search Results for 'sunset beach'" in result.output
        assert "image1.jpg" in result.output
        assert "image2.jpg" in result.output
        assert "85.0%" in result.output
        assert "72.0%" in result.output
        
        # Should show summary
        assert "Found 2 results" in result.output
        assert "Top similarity: 85.0%" in result.output
        
        # Should call search function
        mock_search.assert_called_once_with("sunset beach", limit=5)
    
    @patch('doggo.cli.search_similar_images')
    def test_search_with_preview(self, mock_search):
        """Test search command with preview flag."""
        # Mock search results
        mock_search.return_value = [
            {
                'id': 'file1',
                'description': 'A beautiful sunset over the ocean',
                'metadata': {
                    'file_path': '/test/path/image1.jpg',
                    'file_name': 'image1.jpg',
                    'file_size': 1024000
                },
                'similarity_score': 0.85
            }
        ]
        
        result = self.runner.invoke(main, ['search', 'sunset', '--preview'])
        
        # Should succeed
        assert result.exit_code == 0
        
        # Should show preview
        assert "Top Result Preview" in result.output
        assert "📁 File: image1.jpg" in result.output
        assert "📍 Path: /test/path/image1.jpg" in result.output
        assert "🎯 Similarity: 85.0%" in result.output
        assert "📝 Description: A beautiful sunset over the ocean" in result.output
        
        # Should call search function
        mock_search.assert_called_once_with("sunset", limit=5)
    
    @patch('doggo.cli.search_similar_images')
    def test_search_with_limit(self, mock_search):
        """Test search command with custom limit."""
        mock_search.return_value = []
        
        result = self.runner.invoke(main, ['search', 'test', '--limit', '5'])
        
        # Should succeed
        assert result.exit_code == 0
        
        # Should call search function with custom limit
        mock_search.assert_called_once_with("test", limit=5)
    
    @patch('doggo.cli.search_similar_images')
    def test_search_no_results(self, mock_search):
        """Test search command with no results."""
        mock_search.return_value = []
        
        result = self.runner.invoke(main, ['search', 'nonexistent'])
        
        # Should succeed
        assert result.exit_code == 0
        
        # Should show no results message
        assert "No results found for your query" in result.output
        assert "Try:" in result.output
        assert "Using different keywords" in result.output
        assert "Checking if you have indexed any images" in result.output
        assert "Running 'doggo index <path>'" in result.output
    
    @patch('doggo.cli.search_similar_images')
    def test_search_empty_query(self, mock_search):
        """Test search command with empty query."""
        mock_search.side_effect = ValueError("Search query cannot be empty")
        
        result = self.runner.invoke(main, ['search', ''])
        
        # Should fail
        assert result.exit_code != 0
        
        # Should show error message
        assert "Search Error" in result.output
        assert "Search query cannot be empty" in result.output
    
    @patch('doggo.cli.search_similar_images')
    def test_search_api_error(self, mock_search):
        """Test search command with API error."""
        mock_search.side_effect = ValueError("OpenAI API key not configured")
        
        result = self.runner.invoke(main, ['search', 'test'])
        
        # Should fail
        assert result.exit_code != 0
        
        # Should show error message
        assert "Search Error" in result.output
        assert "OpenAI API key not configured" in result.output
    
    @patch('doggo.cli.search_similar_images')
    def test_search_general_error(self, mock_search):
        """Test search command with general error."""
        mock_search.side_effect = Exception("Unexpected error")
        
        result = self.runner.invoke(main, ['search', 'test'])
        
        # Should fail
        assert result.exit_code != 0
        
        # Should show error message
        assert "Search Error" in result.output
        assert "Failed to perform search" in result.output
        assert "Unexpected error" in result.output
    
    def test_search_help(self):
        """Test search command help."""
        result = self.runner.invoke(main, ['search', '--help'])
        
        # Should show help
        assert result.exit_code == 0
        assert "Search for images using natural language queries" in result.output
        assert "--limit" in result.output
        assert "--preview" in result.output


if __name__ == "__main__":
    main() 