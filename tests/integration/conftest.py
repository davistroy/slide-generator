"""
Integration test configuration.

All tests in this directory are automatically marked with @pytest.mark.integration.
"""

import pytest


def pytest_collection_modifyitems(items):
    """Automatically add integration marker to all tests in this directory."""
    for item in items:
        # Check if test is in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            # Also mark as slow since integration tests typically take longer
            item.add_marker(pytest.mark.slow)


@pytest.fixture
def integration_test_output_dir(tmp_path):
    """Temporary directory for integration test outputs."""
    output_dir = tmp_path / "integration_output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def skip_without_api_keys(has_api_keys):
    """Skip test if API keys are not available."""
    if not has_api_keys:
        pytest.skip("API keys not available")
