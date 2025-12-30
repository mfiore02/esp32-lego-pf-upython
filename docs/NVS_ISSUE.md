# NVS Testing Issue (Resolved)

## Summary

During development, we initially thought ESP32 NVS had persistence issues. **This was actually a testing methodology problem**, not an NVS bug. NVS likely works fine.

## The Testing Bug

Our initial tests had **auto-cleanup** that ran too early:

1. **Hard reboot**: ESP32 boots, test runs automatically
2. **Test finds persisted data**: Prints "SUCCESS!"
3. **Test auto-cleans up**: Erases data immediately
4. **We connect to REPL**: Data already gone
5. **We soft reset**: Sees no data, starts over

**Result**: We never saw the SUCCESS message, assumed NVS was broken!

## Actual Status

- ✅ **NVS probably works fine** (untested after fixing the test bug)
- ✅ **Filesystem definitely works** (verified with corrected tests)

## Why Filesystem Storage Instead?

Even though NVS probably works, we chose filesystem storage for pragmatic reasons:

**Advantages of Filesystem Storage:**
- ✅ **Human-readable**: JSON files you can inspect/edit
- ✅ **Easy debugging**: `mpremote fs cat /config/controller.json`
- ✅ **Standard API**: Regular file I/O, no special knowledge needed
- ✅ **No surprises**: Well-tested, widely used
- ✅ **Already done**: Tests passing, code working

## Implementation

See `lib/config_manager.py` for the working filesystem-based implementation.

Config files are stored as:
- `/config/controller.json`
- `/config/receiver.json`

## Testing

Verified working with:
- Unit tests: `tests/test_config_manager.py` (8/8 passing)
- HWIL test: `hwil/test_config_manager_hwil.py` (persistence verified across hard reboots)

## Hard Reboot Testing Pattern

We created a reusable helper for future HWIL tests: `hwil/reboot_test_helper.py`

**Key insight**: Tests that verify persistence must NOT auto-cleanup, or you'll miss the SUCCESS message after hard reboot.

**Pattern**:
- Use a marker file (`.cleanup`) for on-demand cleanup
- Show SUCCESS message persistently
- Keep test data for inspection
- See `hwil/test_config_manager_hwil.py` for example

## Lessons Learned

1. **Auto-cleanup in HWIL tests is dangerous** - can make working code look broken
2. **Always verify assumptions** - what looks like a bug might be test methodology
3. **Filesystem storage is often better** - simpler, more debuggable than special APIs
4. **Hard reboot testing needs special care** - can't see output from automatic boot
