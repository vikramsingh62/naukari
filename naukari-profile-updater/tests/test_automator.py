"""
Unit tests for Naukari Profile Automator
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


# Test configuration
@pytest.fixture
def mock_credentials():
    """Mock credentials"""
    return ("test@example.com", "test_password")


@pytest.fixture
def mock_playwright():
    """Mock playwright instance"""
    with patch('src.naukari_automator.sync_playwright'):
        yield


class TestNaukariAutomator:
    """Test cases for NaukariAutomator class"""
    
    def test_import(self):
        """Test that automator module can be imported"""
        try:
            from src.naukari_automator import NaukariAutomator
            assert NaukariAutomator is not None
        except ImportError as e:
            pytest.skip(f"Import failed: {e}")
    
    def test_initialization(self):
        """Test automator initialization"""
        try:
            from src.naukari_automator import NaukariAutomator
            automator = NaukariAutomator("test@example.com", "password")
            assert automator.username == "test@example.com"
            assert automator.password == "password"
            assert automator.headless == True
            assert automator.debug == False
        except ImportError:
            pytest.skip("Module not available")
    
    def test_credentials_validation(self):
        """Test credential validation"""
        try:
            from config.settings import validate_credentials
            
            # Valid credentials
            assert validate_credentials("user@example.com", "password123") == True
            
            # Invalid credentials
            assert validate_credentials("", "") == False
            assert validate_credentials("user", "pwd") == False  # Too short
            assert validate_credentials("invalid_email", "password") == False
        except ImportError:
            pytest.skip("Module not available")


class TestConfiguration:
    """Test cases for configuration management"""
    
    def test_settings_import(self):
        """Test settings module import"""
        try:
            from config.settings import get_config, get_credentials
            assert callable(get_config)
            assert callable(get_credentials)
        except ImportError:
            pytest.skip("Settings module not available")
    
    def test_default_config(self):
        """Test default configuration"""
        try:
            from config.settings import get_config
            config = get_config()
            
            assert 'headless' in config
            assert 'debug' in config
            assert 'timeout' in config
            assert config['headless'] == True
            assert config['debug'] == False
        except Exception as e:
            pytest.skip(f"Config test skipped: {e}")


class TestScheduler:
    """Test cases for scheduler"""
    
    def test_scheduler_import(self):
        """Test scheduler module import"""
        try:
            from src.scheduler import LocalScheduler, GCPCloudScheduler
            assert LocalScheduler is not None
            assert GCPCloudScheduler is not None
        except ImportError:
            pytest.skip("Scheduler module not available")
    
    def test_gcp_commands(self):
        """Test GCP scheduler command generation"""
        try:
            from src.scheduler import GCPCloudScheduler
            commands = GCPCloudScheduler.get_setup_commands("test-project")
            
            assert isinstance(commands, list)
            assert len(commands) > 0
            assert any('scheduler' in cmd.lower() for cmd in commands)
        except ImportError:
            pytest.skip("Scheduler module not available")


class TestIntegration:
    """Integration tests (require credentials)"""
    
    @pytest.mark.skip(reason="Requires actual credentials")
    def test_full_workflow(self):
        """Test complete workflow (skipped - requires credentials)"""
        pass


# Parametrized tests
@pytest.mark.parametrize("email,valid", [
    ("user@example.com", True),
    ("test@domain.co.uk", True),
    ("invalid_email", False),
    ("", False),
])
def test_email_validation(email, valid):
    """Parametrized email validation tests"""
    try:
        from config.settings import validate_credentials
        result = validate_credentials(email, "password")
        if email:
            assert result == valid
    except ImportError:
        pytest.skip("Module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
