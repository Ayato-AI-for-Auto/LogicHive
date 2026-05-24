import os
import shutil
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch
import importlib

# Access the function directly from the module if possible, or simulate it
import core.config

def test_config_resolution_priority():
    """
    Test the priority of configuration resolution:
    Local .env > Home .env > Environment Variable
    """
    with tempfile.TemporaryDirectory() as tmp_root:
        root_path = Path(tmp_root)
        home_path = root_path / "fake_home"
        logichive_home = home_path / ".logichive"
        logichive_home.mkdir(parents=True)
        
        local_env = root_path / ".env"
        home_env = logichive_home / ".env"
        
        # Mock Path.home and BASE_DIR
        with patch("core.config.BASE_DIR", root_path), \
             patch("pathlib.Path.home", return_value=home_path):
            
            # Re-initialize path constants in the module for this test
            importlib.reload(core.config)
            
            from core.config import _load_config, LOCAL_ENV, HOME_ENV
            
            # Verify paths are mocked correctly
            assert str(LOCAL_ENV) == str(local_env)
            assert str(HOME_ENV) == str(home_env)
            
            # 1. No files, No Env -> Should use defaults
            with patch("dotenv.load_dotenv") as mock_load, \
                 patch("os.getenv", return_value=None):
                source = _load_config()
                assert "None" in source

            # 2. No files, but Env exists
            with patch("dotenv.load_dotenv") as mock_load, \
                 patch("os.getenv", side_effect=lambda k, d=None: "key" if k == "GEMINI_API_KEY" else d):
                source = _load_config()
                assert "System Environment Variables" in source

            # 3. Home file exists
            home_env.write_text("GEMINI_API_KEY=home_key")
            with patch("dotenv.load_dotenv") as mock_load:
                source = _load_config()
                assert "Home" in source
                mock_load.assert_called_with(home_env)

            # 4. Local file exists (Should override Home)
            local_env.write_text("GEMINI_API_KEY=local_key")
            with patch("dotenv.load_dotenv") as mock_load:
                source = _load_config()
                assert "Local" in source
                mock_load.assert_called_with(local_env)

if __name__ == "__main__":
    pytest.main([__file__])
