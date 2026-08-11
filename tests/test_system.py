import yaml

from conftest import DATA_SERVER_URL, DATA_SERVER_ROOT
from cfl.basics import set_host, get_available_dataset_ids, get_request_schema, clear_cache, authenticate
from cfl.data import get_data_files
from cfl.data_cache import _get_cache

"""
All System Test.
Basically, all low-level API functions from the pip package are called and verified using the dummy_data.
"""

set_host(DATA_SERVER_URL)

# ATTENTION: make sure a test api key exists in the emtl_server_auth api_keys.csv
# can be generated locally by calling:
# `python auth/api_keys_management.py generate_key --name "TestUser" --mail "test@test.com" --others ""`
API_KEY = "emt-dataloader-..."  # TODO


def test_get_available_dataset_ids():
    """Test pip package `get_available_dataset_ids` functionality."""

    authenticate(API_KEY)
    schemas_dir = DATA_SERVER_ROOT / "emtl_server" / "retrievers" / "schemas"
    expected_dataset_ids = [p.stem for p in schemas_dir.glob("*.yaml")]
    fetched_dataset_ids = get_available_dataset_ids()

    assert all(d in expected_dataset_ids for d in fetched_dataset_ids)
    assert all(d in fetched_dataset_ids for d in expected_dataset_ids)


def test_get_request_schema():
    """Test pip package `get_request_schema` functionality."""

    authenticate(API_KEY)
    dataset_id = 'dummy_dataset'
    schema_path = DATA_SERVER_ROOT / "emtl_server" / "retrievers" / "schemas" / f"{dataset_id}.yaml"
    with schema_path.open("r", encoding="utf-8") as f:
        expected_schema = yaml.safe_load(f)
    fetched_schema = get_request_schema(dataset_id)

    assert expected_schema == fetched_schema


def test_get_data_files():
    """Test pip package `get_data_files` functionality."""

    authenticate(API_KEY)
    request = {
        'dataset_id': 'dummy_dataset',
        'request': {'year': 2024}
    }
    fetched_file_paths = get_data_files(request)
    expected_file_path = DATA_SERVER_ROOT / "emtl_server" / "retrievers" / "raw_data" / "dummy_dataset" / f"dummy_data_2024.txt"

    assert len(fetched_file_paths) == 1
    assert fetched_file_paths[0].read_text() == expected_file_path.read_text()


def test_cache():
    """Test local cache functionality."""

    cache = _get_cache()
    cache_dir = cache.cache_dir_path
    expected_file_name = f"dummy_data_2024.txt"
    clear_cache()

    # test fetching caching
    authenticate(API_KEY)
    request = {
        'dataset_id': 'dummy_dataset',
        'request': {'year': 2024}
    }
    get_data_files(request)
    assert cache.is_file_cached(expected_file_name)
    assert len([f for f in cache_dir.glob("*") if f.is_file()]) == 1

    # test clearing
    clear_cache()
    assert not cache.is_file_cached(expected_file_name)
    assert len([f for f in cache_dir.glob("*") if f.is_file()]) == 0
