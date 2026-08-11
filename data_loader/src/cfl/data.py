from pathlib import Path
from typing import Any, Optional
import requests
from requests import RequestException
from tqdm import tqdm
from yaspin import yaspin

from cfl.basics import _get_api_key, _get_host
from cfl.data_cache import _get_cache


CHUNK_SIZE = 8192  # 8 KB


def get_data_files(request: dict[str, Any], detailed_progress_bar: bool = False) -> list[Path]:
    """
    Fetches all data files, given a request dict that represents a valid filled-out schema.

    Args:
        request (dict[str, Any]): A valid filled-out dataset request schema.
        detailed_progress_bar (bool): Show progress bar for each file download rather than overall progress only; default is False.

    Returns:
        list[Path]: Paths to all fetched and stored data files are returned.
    """

    # query /data endpoint with request schema to trigger data retrievers
    headers = {"CFL-API-KEY": _get_api_key()}
    url_retrievers = f"{_get_host()}/data"
    spinner = yaspin(text="Data server: Collecting and preparing data...")
    spinner.start()
    response = requests.post(url_retrievers, headers=headers, json=request)
    response.raise_for_status()
    spinner.stop()
    data_file_names = response.json()
    if not isinstance(data_file_names, list) or not all(isinstance(d, str) for d in data_file_names):
        raise ValueError(f"Data request failed; returned list of data file names are not in expected format.")
    print(f"Data server successfully prepared {len(data_file_names)} data file(s) for download.")

    # given the created data files on the server side -> check if they are already cached -> download if not
    data_cache = _get_cache()
    cache_dir_path = data_cache.cache_dir_path
    data_file_paths = list()
    files_cached_count = 0
    progress: Optional[tqdm] = None
    if not detailed_progress_bar:  # show overall progress bar only if detailed_progress_bar is not activated
        progress = tqdm(total=len(data_file_names), unit="file", desc="Downloading data file(s)")
    for d in data_file_names:
        if data_cache.is_file_cached(d):
            data_file_paths.append(cache_dir_path / d)
            files_cached_count += 1
            if detailed_progress_bar:
                print(f"{d}: loaded from cache")
        else:
            data_file_paths.append(_retrieve_data_file(d, cache_dir_path, detailed_progress_bar))
        if not detailed_progress_bar:
            progress.update(1)

    # finalize
    if progress is not None:
        progress.close()
    print(f"Successfully downloaded {len(data_file_names) - files_cached_count} file(s) "
          f"({files_cached_count} were locally cached).")
    return data_file_paths


def delete_files(file_paths: list[Path]) -> None:
    """Simply deletes all data files."""
    for f in file_paths:
        f.unlink(missing_ok=True)


def _retrieve_data_file(file_name: str, dir_path: Path, show_progress_bar: bool = False) -> Path:
    """
    Download the given file_name into dir_path.

    Args:
        file_name (str): Name of the file to download.
        dir_path (Path): Path to the local directory.
        show_progress_bar (bool): Print progress bar; default is False.

    Returns:
        Path: Path to the downloaded file (in the local cache directory).
    """

    file_name_path = dir_path / file_name
    url_download = f"{_get_host()}/data/download/{file_name}"
    progress: Optional[tqdm] = None
    headers = {"CFL-API-KEY": _get_api_key()}

    try:
        with requests.get(url_download, headers=headers, stream=True) as r:
            r.raise_for_status()

            # get total expected file size
            total_size = int(r.headers.get("Content-Length", 0))
            if total_size == 0:
                raise RequestException("Server did not provide file size (Content-Length missing)")

            # progress bar
            if show_progress_bar:
                progress = tqdm(total=total_size, unit="B", unit_scale=True, unit_divisor=1024, desc=file_name)

            # download file and validate file size
            downloaded_size = 0
            with file_name_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    if show_progress_bar:
                        progress.update(len(chunk))
            if downloaded_size != total_size:
                raise RequestException(f"Download incomplete: expected {total_size}B, got {downloaded_size}B")

            return file_name_path

    except Exception as e:
        # make sure the partially downloaded file is deleted on exception
        file_name_path.unlink(missing_ok=True)
        raise e

    finally:
        if progress is not None:
            progress.close()
