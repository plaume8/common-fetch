import shutil
from pathlib import Path
from typing import Optional, Any

from cf_server.errors import RetrieverRequestError


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'retrievers' / 'raw_data' / 'opsd'


def retrieve(outbox: Path, request: Optional[dict[str, Any]]) -> list[str]:
    """
    Retriever for the OPSD data:
    - This retriever simply selects the correct CSV file for the given temporal resolution.
    - source: https://open-power-system-data.org
    - raw data: https://data.open-power-system-data.org/household_data/latest/
    - detailed column descriptions: https://data.open-power-system-data.org/household_data/latest/README.md

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
        raise RetrieverRequestError("Missing request object.")
    if "temporal_resolution" not in request:
        raise RetrieverRequestError(f"Missing request parameter: temporal_resolution")

    # sanity checks
    temp_res = request["temporal_resolution"]

    # retrieve data
    if temp_res == "1min":
        return [_copy_file_to_outbox("household_data_1min_singleindex.csv", outbox)]
    elif temp_res == "15min":
        return [_copy_file_to_outbox("household_data_15min_singleindex.csv", outbox)]
    elif temp_res == "60min":
        return [_copy_file_to_outbox("household_data_60min_singleindex.csv", outbox)]
    raise RetrieverRequestError(f"Invalid temp_res. Choose a temporal resolution out of ['1min', '15min', '60min'].")


def _copy_file_to_outbox(file_name: str, outbox: Path) -> str:
    """
    Copy file to the outbox, adds an 'opsd_' prefix and returns the new file name on success.
    """

    # cache checks (check if file already copied to outbox previously)
    new_file_name = f"opsd_{file_name}"
    if not (outbox / new_file_name).is_file():
        # copy file
        shutil.copy(DATA_DIR / file_name, outbox / new_file_name)
    return new_file_name
