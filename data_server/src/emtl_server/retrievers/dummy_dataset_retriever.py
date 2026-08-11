import shutil
from pathlib import Path
from typing import Optional, Any

from emtl_server.errors import RetrieverRequestError


"""
All System Tests.
"""

BASE_DIR = Path(__file__).resolve().parent.parent


def retrieve(outbox: Path, request: Optional[dict[str, Any]]) -> list[str]:
    """
    Retriever for dummy test data.
    Based on the provided request, it selects the corresponding test data file and copies it to the outbox directory.
    
    Args:
        outbox (Path): Path to the outbox directory where the retrieved data files will be stored.
        request (Optional[dict[str, Any]]): Request object containing all parameters that specify which data should be retrieved, following the corresponding schema (yaml file).

    Returns:
        list[str]: List of filenames of the generated data files stored in the outbox directory.

    Raises:
        RetrieverRequestError: Indicates that the request could not be processed. The corresponding error message is returned to the end user.
        GeneralInternalServerError: Indicates an unexpected failure during data retrieval. The corresponding error message is logged for debugging purposes, while a generic error response is returned to the end user to avoid exposing implementation details.
    """

    # request checks
    if request is None:
        raise RetrieverRequestError()
    if 'year' not in request:
        raise RetrieverRequestError()
    year = request['year']
    if year not in range(2024, 2026):
        raise RetrieverRequestError()

    # cache checks (check if data already copied to outbox previously)
    data_file_name = f"dummy_data_{year}.txt"
    if (outbox / data_file_name).is_file():
        return [data_file_name]

    # retrieve data
    raw_data_dir = BASE_DIR / 'retrievers' / 'raw_data' / 'dummy_dataset'
    shutil.copy(raw_data_dir / data_file_name, outbox / data_file_name)
    return [data_file_name]
