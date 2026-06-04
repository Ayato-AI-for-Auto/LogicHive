import importlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

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
        with (
            patch("core.config.BASE_DIR", root_path),
            patch("pathlib.Path.home", return_value=home_path),
        ):
            # Re-initialize path constants in the module for this test
            importlib.reload(core.config)

            # Manually override paths to ensure they use the temp directory
            core.config.BASE_DIR = root_path
            core.config.LOCAL_ENV = root_path / ".env"
            core.config.HOME_DIR = logichive_home
            core.config.HOME_ENV = logichive_home / ".env"

            from core.config import HOME_ENV, LOCAL_ENV, _load_config

            # Verify paths are mocked correctly
            assert str(LOCAL_ENV) == str(local_env)
            assert str(HOME_ENV) == str(home_env)

            # 1. No files, No Env -> Should use defaults
            with (
                patch("core.config.load_dotenv") as mock_load,
                patch("os.getenv", return_value=None),
            ):
                source = _load_config()
                assert "None" in source

            # 2. No files, but Env exists
            with (
                patch("core.config.load_dotenv") as mock_load,
                patch(
                    "os.getenv", side_effect=lambda k, d=None: "key" if k == "GEMINI_API_KEY" else d
                ),
            ):
                source = _load_config()
                assert "System Environment Variables" in source

            # 3. Home file exists
            home_env.write_text("GEMINI_API_KEY=home_key")      
            with patch("core.config.load_dotenv") as mock_load: 
                source = _load_config()
                assert "Home" in source
                mock_load.assert_called_with(home_env, override=True)

            # 4. Local file exists (Should override Home)
            local_env.write_text("GEMINI_API_KEY=local_key")
            with patch("core.config.load_dotenv") as mock_load:
                source = _load_config()
                assert "Local" in source
                mock_load.assert_called_with(local_env, override=True)


if __name__ == "__main__":
    pytest.main([__file__])
