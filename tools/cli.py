#!/usr/bin/env python3
"""
ESP32 Configuration CLI

Interactive serial-based configuration tool for ESP32 devices.
Uses mpremote to execute commands on the remote device.

Usage:
    python tools/cli.py COM3
    python tools/cli.py /dev/ttyUSB0

Example session:
    >>> config.show()
    >>> config.set('pot_calibration.min', 150)
    >>> config.unpair()
    >>> exit()
"""

import argparse
import json
import subprocess
import sys
import shlex


class ESP32CLI:
    """Interactive CLI for ESP32 device configuration."""

    def __init__(self, port):
        """
        Initialize CLI for specified port.

        Args:
            port: Serial port (e.g., 'COM3' or '/dev/ttyUSB0')
        """
        self.port = port
        self.device_type = None

    def connect(self):
        """Verify connection and detect device type."""
        print(f"Connecting to {self.port}...")

        # Verify device is connected
        try:
            result = subprocess.run(
                ['mpremote', 'connect', self.port, 'exec', 'print("OK")'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0 or 'OK' not in result.stdout:
                print(f"Error: Could not connect to device on {self.port}")
                print(f"Make sure the device is connected and mpremote is installed.")
                return False

        except subprocess.TimeoutExpired:
            print(f"Error: Connection timeout on {self.port}")
            return False
        except FileNotFoundError:
            print("Error: mpremote not found. Install with: pip install mpremote")
            return False

        # Auto-detect device type
        self.device_type = self._detect_device_type()
        if not self.device_type:
            print("Error: Could not detect device type")
            print("Make sure ConfigManager is deployed to the device")
            return False

        print(f"Detected: {self.device_type}\n")
        return True

    def _detect_device_type(self):
        """
        Detect device type by reading config.

        Returns:
            'controller' or 'receiver', or None if detection fails
        """
        # Try to read existing config files to determine device type
        code = (
            "try:\n"
            "    import os\n"
            "    # Check if config directory exists\n"
            "    if 'config' in os.listdir('/'):\n"
            "        config_files = os.listdir('/config')\n"
            "        if 'controller.json' in config_files:\n"
            "            print('controller')\n"
            "        elif 'receiver.json' in config_files:\n"
            "            print('receiver')\n"
            "        else:\n"
            "            print('none')\n"
            "    else:\n"
            "        print('no_config_dir')\n"
            "except Exception as e:\n"
            "    print('error:', str(e))\n"
        )

        result = self._execute_remote(code)
        if result:
            result = result.strip()
            if result in ['controller', 'receiver']:
                return result
            elif result == 'none':
                print("Note: /config directory exists but no device config file found")
                print("You may need to run the controller or receiver application first")
            elif result == 'no_config_dir':
                print("Note: /config directory does not exist")
                print("You need to deploy and run the controller or receiver application")

        return None

    def _execute_remote(self, python_code):
        """
        Execute Python code on remote device.

        Args:
            python_code: Python code string to execute

        Returns:
            Output string from device, or None on error
        """
        try:
            result = subprocess.run(
                ['mpremote', 'connect', self.port, 'exec', python_code],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                # Check for specific error messages
                if 'could not enter raw repl' in result.stderr.lower():
                    print("Error: Device not responding (may be running a program)")
                    print("Try: Press Ctrl+C in device REPL or reset the device")
                elif result.stderr.strip():
                    print(f"Error: {result.stderr.strip()}")
                return None

            return result.stdout

        except subprocess.TimeoutExpired:
            print("Error: Command timeout")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def cmd_show(self):
        """Display entire configuration."""
        code = (
            f"from config_manager import ConfigManager; "
            f"import json; "
            f"c = ConfigManager('{self.device_type}'); "
            f"print(json.dumps(c.get_all()))"
        )

        result = self._execute_remote(code)
        if result:
            # Pretty-print the JSON on the host side
            try:
                config_data = json.loads(result.strip())
                print(json.dumps(config_data, indent=2))
            except json.JSONDecodeError:
                # If parsing fails, just print raw output
                print(result.strip())

    def cmd_get(self, key):
        """
        Get a configuration value.

        Args:
            key: Configuration key (supports dot notation)
        """
        code = (
            f"from config_manager import ConfigManager; "
            f"c = ConfigManager('{self.device_type}'); "
            f"print(repr(c.get('{key}')))"
        )

        result = self._execute_remote(code)
        if result:
            print(result.strip())

    def cmd_set(self, key, value):
        """
        Set a configuration value and save.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set (will be evaluated as Python literal)
        """
        # Value is already a Python literal (int, str, bool, etc.)
        code = (
            f"from config_manager import ConfigManager; "
            f"c = ConfigManager('{self.device_type}'); "
            f"c.set('{key}', {value}); "
            f"c.save(); "
            f"print('OK')"
        )

        result = self._execute_remote(code)
        if result:
            print(result.strip())

    def cmd_unpair(self):
        """Clear pairing information."""
        # Determine which MAC address key to clear based on device type
        mac_key = 'train_mac' if self.device_type == 'controller' else 'controller_mac'

        code = (
            f"from config_manager import ConfigManager; "
            f"c = ConfigManager('{self.device_type}'); "
            f"c.set('paired', False); "
            f"c.set('{mac_key}', None); "
            f"c.save(); "
            f"print('Unpaired')"
        )

        result = self._execute_remote(code)
        if result:
            print(result.strip())

    def cmd_save(self):
        """Explicitly save configuration (set() auto-saves)."""
        code = (
            f"from config_manager import ConfigManager; "
            f"c = ConfigManager('{self.device_type}'); "
            f"c.save(); "
            f"print('Saved')"
        )

        result = self._execute_remote(code)
        if result:
            print(result.strip())

    def cmd_reset(self):
        """Reset configuration to defaults (in memory, not saved)."""
        code = (
            f"from config_manager import ConfigManager; "
            f"c = ConfigManager('{self.device_type}'); "
            f"c.reset(); "
            f"print('Reset to defaults (not saved - use config.save() to persist)')"
        )

        result = self._execute_remote(code)
        if result:
            print(result.strip())

    def cmd_erase(self):
        """Erase configuration file and reset to defaults."""
        code = (
            f"from config_manager import ConfigManager; "
            f"c = ConfigManager('{self.device_type}'); "
            f"c.erase(); "
            f"print('Configuration erased and reset to defaults')"
        )

        result = self._execute_remote(code)
        if result:
            print(result.strip())

    def cmd_help(self):
        """Display help information."""
        help_text = """
Available commands:

  config.show()                    Display entire configuration
  config.get('key')                Get a configuration value
  config.set('key', value)         Set a value and save
  config.unpair()                  Clear pairing information
  config.save()                    Save configuration
  config.reset()                   Reset to defaults (not saved)
  config.erase()                   Erase config file

  help                             Show this help
  exit() or Ctrl+D                 Exit CLI

Examples:
  config.set('pot_calibration.min', 150)
  config.set('paired', True)
  config.get('device_type')

Keys support dot notation (e.g., 'pot_calibration.min')
        """
        print(help_text.strip())

    def parse_command(self, line):
        """
        Parse and execute a command line.

        Args:
            line: User input line

        Returns:
            True to continue REPL, False to exit
        """
        line = line.strip()

        # Empty line
        if not line:
            return True

        # Exit commands
        if line in ['exit()', 'exit', 'quit()', 'quit']:
            return False

        # Help command
        if line == 'help':
            self.cmd_help()
            return True

        # Config commands
        if line.startswith('config.'):
            cmd_part = line[7:]  # Remove 'config.'

            # show()
            if cmd_part == 'show()':
                self.cmd_show()

            # get('key')
            elif cmd_part.startswith('get(') and cmd_part.endswith(')'):
                args = cmd_part[4:-1].strip()
                # Remove quotes from key
                key = args.strip('\'"')
                self.cmd_get(key)

            # set('key', value)
            elif cmd_part.startswith('set(') and cmd_part.endswith(')'):
                args = cmd_part[4:-1]
                # Parse arguments: 'key', value
                try:
                    parts = args.split(',', 1)
                    if len(parts) != 2:
                        print("Error: set() requires 2 arguments: key and value")
                        return True

                    key = parts[0].strip().strip('\'"')
                    value = parts[1].strip()
                    self.cmd_set(key, value)
                except Exception as e:
                    print(f"Error parsing set() arguments: {e}")

            # unpair()
            elif cmd_part == 'unpair()':
                self.cmd_unpair()

            # save()
            elif cmd_part == 'save()':
                self.cmd_save()

            # reset()
            elif cmd_part == 'reset()':
                self.cmd_reset()

            # erase()
            elif cmd_part == 'erase()':
                self.cmd_erase()

            else:
                print(f"Unknown config command: {cmd_part}")
                print("Type 'help' for available commands")

        else:
            print(f"Unknown command: {line}")
            print("Type 'help' for available commands")

        return True

    def run(self):
        """Run the interactive REPL."""
        # Try to enable readline for command history
        try:
            import readline
        except ImportError:
            pass  # readline not available on Windows without extra setup

        print("ESP32 Configuration CLI")
        print("Type 'help' for available commands, 'exit' to quit\n")

        while True:
            try:
                line = input(">>> ")
                if not self.parse_command(line):
                    break

            except EOFError:
                # Ctrl+D
                print()  # Newline for clean exit
                break
            except KeyboardInterrupt:
                # Ctrl+C
                print()  # Newline
                continue

        print("Goodbye!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='ESP32 Configuration CLI',
        epilog='Example: python cli.py COM3'
    )
    parser.add_argument(
        'port',
        help='Serial port (e.g., COM3, /dev/ttyUSB0)'
    )

    args = parser.parse_args()

    cli = ESP32CLI(args.port)

    if not cli.connect():
        sys.exit(1)

    cli.run()


if __name__ == '__main__':
    main()
