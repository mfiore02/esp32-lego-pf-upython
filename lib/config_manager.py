"""
Configuration Manager with Filesystem Storage

Uses JSON files in /config directory instead of NVS.
More reliable and easier to debug than NVS.

Example usage:
    config = ConfigManager("controller")
    config.set("paired", True)
    config.save()
"""

import json
import os


class ConfigManager:
    """Manages versioned configuration storage using filesystem."""

    VERSION = 1
    CONFIG_DIR = "/config"

    # Device type constants
    DEVICE_CONTROLLER = "controller"
    DEVICE_RECEIVER = "receiver"

    # Default configurations for each device type
    DEFAULTS = {
        "controller": {
            "version": VERSION,
            "device_type": "controller",
            "paired": False,
            "train_mac": None,
            "pot_calibration": {
                "min": 500,
                "max": 3995,
                "zero_band": 50
            }
        },
        "receiver": {
            "version": VERSION,
            "device_type": "receiver",
            "paired": False,
            "controller_mac": None,
            "motor_config": {
                "deadband": 10,
                "reverse_motor1": False,
                "reverse_motor2": False
            }
        }
    }

    def __init__(self, device_type):
        """
        Initialize configuration manager.

        Args:
            device_type: "controller" or "receiver"
        """
        if device_type not in self.DEFAULTS:
            raise ValueError("Invalid device_type: " + device_type)

        self.device_type = device_type
        self._config = None
        self._config_file = self.CONFIG_DIR + "/" + device_type + ".json"

        # Ensure config directory exists
        try:
            os.mkdir(self.CONFIG_DIR)
        except OSError:
            pass  # Directory already exists

        # Load configuration
        self.load()

    def load(self):
        """Load configuration from file, or initialize with defaults."""
        try:
            with open(self._config_file, 'r') as f:
                config_str = f.read()
                self._config = json.loads(config_str)
                self._migrate()
        except (OSError, ValueError, KeyError) as e:
            # File doesn't exist or is corrupted
            print("Config load failed: " + str(e) + ", using defaults")
            self._config = self._get_default_config()

    def save(self):
        """Save current configuration to file."""
        try:
            config_str = json.dumps(self._config)
            with open(self._config_file, 'w') as f:
                f.write(config_str)
        except OSError as e:
            print("Config save failed: " + str(e))
            raise

    def get(self, key, default=None):
        """
        Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., "pot_calibration.min")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key, value):
        """
        Set a configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value

    def reset(self):
        """Reset configuration to defaults."""
        self._config = self._get_default_config()

    def erase(self):
        """Erase configuration file and reset to defaults."""
        try:
            os.remove(self._config_file)
        except OSError:
            pass  # File doesn't exist

        self._config = self._get_default_config()

    def get_all(self):
        """
        Get entire configuration dictionary.

        Returns:
            Copy of configuration dict
        """
        return dict(self._config)

    def _get_default_config(self):
        """Get default configuration for device type."""
        # Return a deep copy of defaults
        default = self.DEFAULTS[self.device_type]
        return json.loads(json.dumps(default))

    def _migrate(self):
        """Migrate configuration to current version if needed."""
        current_version = self._config.get("version", 0)

        if current_version < self.VERSION:
            print("Migrating config from v" + str(current_version) + " to v" + str(self.VERSION))

            # Perform version-specific migrations
            if current_version < 1:
                self._migrate_to_v1()

            # Update version
            self._config["version"] = self.VERSION
            self.save()

    def _migrate_to_v1(self):
        """Migrate to version 1 (initial version)."""
        # Ensure all default keys exist
        default = self._get_default_config()

        for key, value in default.items():
            if key not in self._config:
                self._config[key] = value
