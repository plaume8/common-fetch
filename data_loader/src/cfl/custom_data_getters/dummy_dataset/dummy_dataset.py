from pathlib import Path

from cfl.basics import get_request_schema
from cfl.data import get_data_files, delete_files

DATASET_ID = 'dummy_dataset'
YEARS = []


def get_description() -> str:
    """
    Get general information of the dummy dataset.

    Returns:
        str: Textual description and more detailed information about the datasource.
    """
    schema = get_request_schema(DATASET_ID)
    return schema['description']


def get_dummy_data(year: int, cache: bool = True) -> str:
    """
    Retrieve the dummy data for the given year.

    Args:
        year (int):
            Test data is available for 2024 and 2025.
        cache (bool, optional):
            Whether to use locally cached data files if available.
            If False, downloaded files are deleted after loading. Defaults to True.

    Returns:
        list:
            Dummy data as a string.
    """

    # param checking
    if year not in [2024, 2025]:
        raise ValueError(f'error: year must be 2024 or 2025.')
    # build request schema
    request_schema = get_request_schema(DATASET_ID)
    request_schema['request']['year'] = year
    # fetch and concat data
    data_file_paths = get_data_files(request_schema)
    data = Path(data_file_paths[0]).read_text(encoding="utf-8")
    if not cache:
        delete_files(data_file_paths)
    return data
