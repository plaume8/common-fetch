import os
from typing import Any

import requests
from dotenv import load_dotenv

from cfl.data_cache import _get_cache


def authenticate(api_key: str) -> None:
    """
    Before calling any data loading functionality, an API key must be provided.

    Args:
        api_key (str): API key.
    """

    load_dotenv()
    os.environ["CFL-API-KEY"] = api_key


def set_host(host: str) -> None:
    """
    Before calling any data loading functionality, a data server host address must be provided.

    Args:
        host (str): data server host address; form: 'http://{HOST_ADDRESS}:{DATA_SERVER_PORT}'
    """

    load_dotenv()
    os.environ["CFL-HOST"] = host


def _get_host() -> str:
    load_dotenv()
    host = os.environ.get("CFL-HOST", "")
    if not host:
        raise ValueError("No host defined. Use set_host() first.")
    return host


def _get_api_key() -> str:
    load_dotenv()
    api_key = os.environ.get("CFL-API-KEY", "")
    if not api_key:
        raise ValueError("No API key provided. Use authenticate() first.")
    return api_key


def get_available_dataset_ids() -> list[str]:
    """
    Fetch all available dataset ids.

    Returns:
        list[str]: List of all available dataset ids.
    """

    # request
    url = f"{_get_host()}/dataset_ids"
    headers = {"CFL-API-KEY": _get_api_key()}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    # parse
    data = response.json()
    if not isinstance(data, list) or not all(isinstance(d, str) for d in data):
        raise ValueError("Fetched dataset ids have an invalid format.")
    return data


def get_request_schema(dataset_id: str) -> dict[str, Any]:
    """
    Fetch the request schema for the given dataset id.

    Args:
        dataset_id (str): Unique id of the dataset.

    Returns:
        dict[str, Any]: Request schema as a dict.
    """

    # request
    url = f"{_get_host()}/schema/{dataset_id}"
    headers = {"CFL-API-KEY": _get_api_key()}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    # parse
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError(f"Schema for '{dataset_id}' not found.")
    return data


def clear_cache() -> None:
    """Clears local data cache. All cached data will be permanently deleted."""
    _get_cache().clear()
