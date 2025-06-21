"""Tests for the config module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

from doggo.config import (
    get_config_dir,
    get_config_file,
    create_config_dir,
    get_default_config,
    create_default_config,
    load_config,
    save_config,
    initialize_doggo,
    validate_api_key,
    set_api_key,
    get_config_summary
)


class TestConfigPaths:
    """Test configuration path functions."""
    
    def test_get_config_dir(self):
        """Test getting config directory path."""
        config_dir = get_config_dir()
        assert isinstance(config_dir, Path)
        assert config_dir.name == ".doggo"
        assert config_dir.parent == Path.home()
    
    def test_get_config_file(self):
        """Test getting config file path."""
        config_file = get_config_file()
        assert isinstance(config_file, Path)
        assert config_file.name == "config.json"
        assert config_file.parent == get_config_dir()


class TestConfigDirectory:
    """Test config directory creation."""
    
    @patch('doggo.config.Path.home')
    def test_create_config_dir(self, mock_home):
        """Test creating config directory."""
        # Setup mock home directory
        temp_dir = Path(tempfile.mkdtemp())
        mock_home.return_value = temp_dir
        
        config_dir = temp_dir / ".doggo"
        
        # Directory should not exist initially
        assert not config_dir.exists()
        
        # Create directory
        create_config_dir()
        
        # Directory should now exist
        assert config_dir.exists()
        assert config_dir.is_dir()


class TestDefaultConfig:
    """Test default configuration functions."""
    
    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()
        
        assert isinstance(config, dict)
        assert "openai_api_key" in config
        assert "indexed_paths" in config
        assert "last_reindex" in config
        assert "version" in config
        
        assert config["openai_api_key"] == ""
        assert config["indexed_paths"] == []
        assert config["last_reindex"] is None
        assert config["version"] == "0.1.0"
    
    @patch('doggo.config.get_config_file')
    @patch('doggo.config.save_config')
    def test_create_default_config_new_file(self, mock_save, mock_get_file):
        """Test creating default config when file doesn't exist."""
        # Setup mock
        mock_file = Path("/fake/path/config.json")
        mock_get_file.return_value = mock_file
        
        # Mock file doesn't exist
        with patch.object(Path, 'exists', return_value=False):
            create_default_config()
        
        # Should call save_config with default config
        mock_save.assert_called_once()
        saved_config = mock_save.call_args[0][0]
        assert saved_config == get_default_config()
    
    @patch('doggo.config.get_config_file')
    @patch('doggo.config.save_config')
    def test_create_default_config_existing_file(self, mock_save, mock_get_file):
        """Test creating default config when file already exists."""
        # Setup mock
        mock_file = Path("/fake/path/config.json")
        mock_get_file.return_value = mock_file
        
        # Mock file exists
        with patch.object(Path, 'exists', return_value=True):
            create_default_config()
        
        # Should not call save_config
        mock_save.assert_not_called()


class TestConfigFileOperations:
    """Test config file loading and saving."""
    
    def test_load_config_existing_file(self):
        """Test loading config from existing file."""
        test_config = {
            "openai_api_key": "sk-test123",
            "indexed_paths": ["/path1", "/path2"],
            "last_reindex": "2023-01-01",
            "version": "0.1.0"
        }
        
        with patch('doggo.config.get_config_file') as mock_get_file:
            mock_file = Path("/fake/path/config.json")
            mock_get_file.return_value = mock_file
            
            with patch.object(Path, 'exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                    config = load_config()
        
        assert config == test_config
    
    def test_load_config_missing_file(self):
        """Test loading config when file doesn't exist."""
        with patch('doggo.config.get_config_file') as mock_get_file:
            mock_file = Path("/fake/path/config.json")
            mock_get_file.return_value = mock_file
            
            with patch.object(Path, 'exists', return_value=False):
                config = load_config()
        
        # Should return default config
        assert config == get_default_config()
    
    def test_save_config(self):
        """Test saving config to file."""
        test_config = {
            "openai_api_key": "sk-test123",
            "indexed_paths": ["/path1"],
            "last_reindex": None,
            "version": "0.1.0"
        }
        
        with patch('doggo.config.get_config_file') as mock_get_file:
            mock_file = Path("/fake/path/config.json")
            mock_get_file.return_value = mock_file
            
            # Create a mock that properly captures written data
            mock_file_open = mock_open()
            with patch('builtins.open', mock_file_open):
                save_config(test_config)
        
        # Should open file in write mode
        mock_file_open.assert_called_once_with(mock_file, 'w')
        
        # Get the written data from the mock
        handle = mock_file_open()
        # The write method might be called multiple times, so we need to get all calls
        write_calls = handle.write.call_args_list
        written_data = ''.join([call[0][0] for call in write_calls])
        
        # Parse the written JSON
        parsed_data = json.loads(written_data)
        assert parsed_data == test_config


class TestInitialization:
    """Test the main initialization function."""
    
    @patch('doggo.config.create_config_dir')
    @patch('doggo.config.create_default_config')
    def test_initialize_doggo(self, mock_create_config, mock_create_dir):
        """Test the main initialization function."""
        initialize_doggo()
        
        # Should call both functions
        mock_create_dir.assert_called_once()
        mock_create_config.assert_called_once()


class TestIntegration:
    """Integration tests for config operations."""
    
    def test_full_initialization_flow(self):
        """Test the complete initialization flow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('doggo.config.Path.home') as mock_home:
                mock_home.return_value = Path(temp_dir)
                
                # Initialize
                initialize_doggo()
                
                # Check directory was created
                config_dir = Path(temp_dir) / ".doggo"
                assert config_dir.exists()
                assert config_dir.is_dir()
                
                # Check config file was created
                config_file = config_dir / "config.json"
                assert config_file.exists()
                assert config_file.is_file()
                
                # Check config content
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                assert config == get_default_config() 


class TestAPIKey:
    """Test API key validation and setting."""
    
    def test_validate_api_key_valid(self):
        assert validate_api_key("sk-1234567890abcdef")
        assert validate_api_key("sk-testkey-1234567890")
    
    def test_validate_api_key_invalid(self):
        assert not validate_api_key("")
        assert not validate_api_key("sk-")
        assert not validate_api_key("1234567890abcdef")
        assert not validate_api_key(None)
    
    def test_set_api_key_valid(self):
        with patch('doggo.config.save_config') as mock_save, \
             patch('doggo.config.load_config', return_value={"openai_api_key": "", "indexed_paths": [], "last_reindex": None, "version": "0.1.0"}):
            set_api_key("sk-1234567890abcdef")
            args = mock_save.call_args[0][0]
            assert args["openai_api_key"] == "sk-1234567890abcdef"
    
    def test_set_api_key_invalid(self):
        with pytest.raises(ValueError):
            set_api_key("invalid-key")
    
    def test_get_config_summary(self):
        with patch('doggo.config.load_config', return_value={
            "openai_api_key": "sk-1234567890abcdef",
            "indexed_paths": ["/a", "/b"],
            "last_reindex": "2024-01-01",
            "version": "0.1.0"
        }):
            summary = get_config_summary()
            assert summary["OpenAI API Key"].startswith("sk-123")
            assert summary["OpenAI API Key"].endswith("cdef")
            assert summary["Indexed Paths"] == 2
            assert summary["Last Reindex"] == "2024-01-01"
            assert summary["Version"] == "0.1.0"
        # Test with no API key
        with patch('doggo.config.load_config', return_value={
            "openai_api_key": "",
            "indexed_paths": [],
            "last_reindex": None,
            "version": "0.1.0"
        }):
            summary = get_config_summary()
            assert summary["OpenAI API Key"] == "(not set)" 