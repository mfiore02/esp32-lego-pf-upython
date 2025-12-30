"""
Reusable Helper for Hard Reboot Testing

Problem: When testing persistence across hard reboots, auto-running tests
can clean up data before you see the SUCCESS message.

Solution: Use a marker file to trigger cleanup mode.

## Cleanup Pattern

Trigger cleanup from host machine:
```bash
mpremote connect COM3 exec "open('/.cleanup', 'w').close()"
mpremote connect COM3 soft-reset
```

## Usage in HWIL Tests

```python
import sys
import os
sys.path.append('/lib')

# Check for cleanup marker
cleanup_mode = False
try:
    os.stat('/.cleanup')
    cleanup_mode = True
    os.remove('/.cleanup')  # Remove marker after reading
except:
    pass

if cleanup_mode:
    # Cleanup and exit
    cleanup_test_data()
    print("✓ Cleaned up")
else:
    # Normal test flow
    if test_data_exists():
        print("SUCCESS! Data persisted!")
    else:
        write_test_data()
        print("Unplug/replug to verify")
```

See `test_config_manager_hwil.py` for complete example.

## Helper Function

For convenience, you can use the helper function:
"""

import os


def check_cleanup_mode():
    """
    Check if cleanup marker file exists.

    Returns True if cleanup requested, False otherwise.
    Automatically removes the marker file after reading.

    Usage:
        if check_cleanup_mode():
            cleanup_and_exit()
        else:
            run_normal_test()
    """
    try:
        os.stat('/.cleanup')
        os.remove('/.cleanup')
        return True
    except:
        return False
