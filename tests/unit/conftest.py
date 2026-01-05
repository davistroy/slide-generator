"""
Unit test configuration.

All tests in this directory are automatically marked with @pytest.mark.unit.
"""

import pytest


def pytest_collection_modifyitems(items):
    """Automatically add unit marker to all tests in this directory."""
    for item in items:
        # Check if test is in unit directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
