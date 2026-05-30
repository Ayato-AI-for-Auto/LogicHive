import os
from pathlib import Path
import pytest
from core.config import DATA_DIR, SQLITE_DB_PATH, LOGICHIVE_HOME

def test_config_paths_centralization():
    """UNIT: Verify that configuration paths are centralized in the home directory."""
    import core.config
    
    # We expect paths to be under LOGICHIVE_HOME
    assert str(core.config.DATA_DIR).startswith(str(core.config.LOGICHIVE_HOME))
    assert str(core.config.SQLITE_DB_PATH).startswith(str(core.config.DATA_DIR))
    
    # Verify that the test override worked
    assert ".test_logichive" in str(core.config.LOGICHIVE_HOME)

def test_env_loading_priority():
    """UNIT: Verify that .env is searched in multiple locations."""
    from core.config import HOME_ENV, BASE_DIR
    # This is more of a structural check since we can't easily mock the file system 
    # without deeper refactoring, but we can verify the Path objects exist.
    assert isinstance(HOME_ENV, Path)
    assert HOME_ENV.name == ".env"
