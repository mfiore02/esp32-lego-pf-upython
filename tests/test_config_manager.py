"""
Unit tests for ConfigManager

Run with: python -m pytest tests/test_config_manager.py -v
"""

import sys
import json
import os
import tempfile
import shutil
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

# Need to temporarily modify ConfigManager to support test directory
import config_manager
original_config_dir = config_manager.ConfigManager.CONFIG_DIR


class TestConfigManagerFS:
    """Test filesystem-based configuration manager."""

    def setup_method(self):
        """Create temporary directory for each test."""
        self.test_dir = tempfile.mkdtemp()
        # Override the CONFIG_DIR class variable
        config_manager.ConfigManager.CONFIG_DIR = self.test_dir

    def teardown_method(self):
        """Clean up temporary directory after each test."""
        config_manager.ConfigManager.CONFIG_DIR = original_config_dir
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_controller_defaults(self):
        """Test controller default configuration."""
        from config_manager import ConfigManager

        config = ConfigManager(ConfigManager.DEVICE_CONTROLLER)
        assert config.get("device_type") == "controller"
        assert config.get("paired") is False
        assert config.get("train_mac") is None
        assert config.get("pot_calibration.min") == 100

    def test_receiver_defaults(self):
        """Test receiver default configuration."""
        from config_manager import ConfigManager

        config = ConfigManager(ConfigManager.DEVICE_RECEIVER)
        assert config.get("device_type") == "receiver"
        assert config.get("paired") is False
        assert config.get("controller_mac") is None

    def test_save_and_load(self):
        """Test saving and loading configuration."""
        from config_manager import ConfigManager

        # Create and modify config
        config1 = ConfigManager(ConfigManager.DEVICE_CONTROLLER)
        config1.set("paired", True)
        config1.set("train_mac", [0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF])
        config1.save()

        # Load in new instance
        config2 = ConfigManager(ConfigManager.DEVICE_CONTROLLER)
        assert config2.get("paired") is True
        assert config2.get("train_mac") == [0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]

    def test_nested_keys(self):
        """Test nested key access."""
        from config_manager import ConfigManager

        config = ConfigManager(ConfigManager.DEVICE_CONTROLLER)
        config.set("pot_calibration.min", 250)
        assert config.get("pot_calibration.min") == 250

    def test_erase(self):
        """Test erasing configuration."""
        from config_manager import ConfigManager

        config = ConfigManager(ConfigManager.DEVICE_CONTROLLER)
        config.set("paired", True)
        config.save()

        config.erase()
        assert config.get("paired") is False

    def test_persistence_across_instances(self):
        """Test that config persists across multiple instances."""
        from config_manager import ConfigManager

        # Write with first instance
        config1 = ConfigManager(ConfigManager.DEVICE_CONTROLLER)
        config1.set("paired", True)
        config1.set("pot_calibration.max", 4000)
        config1.save()

        # Read with second instance
        config2 = ConfigManager(ConfigManager.DEVICE_CONTROLLER)
        assert config2.get("paired") is True
        assert config2.get("pot_calibration.max") == 4000

    def test_get_all(self):
        """Test get_all method."""
        from config_manager import ConfigManager

        config = ConfigManager(ConfigManager.DEVICE_CONTROLLER)
        all_config = config.get_all()
        assert isinstance(all_config, dict)
        assert "device_type" in all_config
        assert "pot_calibration" in all_config

    def test_invalid_device_type(self):
        """Test invalid device type raises error."""
        from config_manager import ConfigManager

        try:
            ConfigManager("invalid")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid device_type" in str(e)

print("Tests updated for filesystem-based config manager")
