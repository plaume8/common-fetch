import shutil
import tempfile
from pathlib import Path


TEMP_DIR_DEFAULT_NAME = 'emt-dataloader-cache-k4wJx1o9'


class DataCache:
    """
    The DataCache caches and manages loaded data of the EMT data_loader package, thereby avoiding unnecessary reloads.
    The stored data is saved in the background in a dedicated temp directory and remains available even after closing
    the terminal, environment, etc.
    """

    def __init__(self) -> None:
        """
        Initializes the DataCache instance by setting up the necessary dedicated tmp directory,
        where the given data files will be cached
        """
        self._cache_dir_path = None
        self._init_cache_dir()

    @property
    def cache_dir_path(self) -> Path:
        return self._cache_dir_path

    def is_file_cached(self, file_name: str) -> bool:
        """Check if file in cache exists."""
        file_path = self._cache_dir_path / file_name
        return file_path.exists() and file_path.is_file()

    def clear(self) -> None:
        """Clear entire cache. All cached data will be deleted."""
        shutil.rmtree(self._cache_dir_path, ignore_errors=True)
        self._init_cache_dir()

    def _init_cache_dir(self):
        """
        Init the cached data dir.
        Note: we are not using the built-in 'tempfile.mkdtemp(...)' functionality since it creates a temp directory
        with a specific prefix and a random code as the name, ensuring the folder is unique. However, since we want to
        access the data even after the program ends and have no way to securely store this name, we use a fixed name
        and ensure by adding the last 8 random chars (see TEMP_DIR_DEFAULT_NAME) that there is nearly no chance
        any other program will override or require that tmp dir.
        """
        sys_tmp_dir_path = Path(tempfile.gettempdir())
        self._cache_dir_path = sys_tmp_dir_path / TEMP_DIR_DEFAULT_NAME
        try:
            self._cache_dir_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create cache directory: {e}")
