import importlib
import pkgutil

from core.logging_config import get_logger

from .base import BaseExecutor

logger = get_logger(__name__)


class ExecutorFactory:
    """Registry and factory for code executors with dynamic loading."""

    _executors: dict[str, BaseExecutor] = {}
    _loaded = False

    @classmethod
    def _load_plugins(cls):
        """Dynamically discovers and loads all executor plugins in the current package."""
        if cls._loaded:
            return

        logger.debug("ExecutorFactory: Starting dynamic plugin discovery...")
        try:
            # Package is src.core.execution
            package_name = __package__
            package = importlib.import_module(package_name)

            for _loader, name, _is_pkg in pkgutil.walk_packages(
                package.__path__, package.__name__ + "."
            ):
                if name.endswith("__init__") or name.endswith(".base") or name.endswith(".factory"):
                    continue
                try:
                    importlib.import_module(name)
                    logger.debug(f"ExecutorFactory: Loaded executor module {name}")
                except Exception as e:
                    logger.error(
                        f"ExecutorFactory: Failed to load module {name}: {e}", exc_info=True
                    )
            cls._loaded = True
            logger.info(
                "ExecutorFactory: Plugin discovery finished. "
                f"Loaded languages: {list(cls._executors.keys())}"
            )
        except Exception as e:
            logger.error(
                f"ExecutorFactory: Critical failure during plugin discovery: {e}", exc_info=True
            )

    @classmethod
    def register(cls, language: str, executor: BaseExecutor):
        cls._executors[language.lower()] = executor
        logger.debug(f"ExecutorFactory: Registered executor for {language}")

    @classmethod
    def get_executor(cls, language: str) -> BaseExecutor | None:
        cls._load_plugins()
        lang = language.lower()

        executor = cls._executors.get(lang)
        if not executor:
            logger.warning(f"ExecutorFactory: No executor found for language '{language}'")
        else:
            logger.debug(f"ExecutorFactory: Found executor for '{language}'")
        return executor
