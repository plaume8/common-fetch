import shutil
from pathlib import Path
from typing import Optional, Any

from emtl_server.errors import RetrieverRequestError


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'retrievers' / 'raw_data' / 'deddiag'


def retrieve(outbox: Path, request: Optional[dict[str, Any]]) -> list[str]:
    """
    Retriever for the DEDDIAG data:
    - This retriever accesses the original tsv files and retrieves the requested data according to the given request objects.
    - paper: https://www.nature.com/articles/s41597-021-00963-2
    - raw data: https://figshare.com/articles/dataset/DEDDIAG_a_domestic_electricity_demand_dataset_of_individual_appliances_in_Germany/13615073/1

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
    required_request_params = ["house_id", "data_type", "item_data_type"]
    missing = [k for k in required_request_params if k not in request]
    if missing:
        raise RetrieverRequestError(f"Missing request parameter(s): {', '.join(missing)}")

    # sanity checks
    house_id = request["house_id"]
    if house_id < 0 or house_id > 14:
        raise RetrieverRequestError(f"Invalid house_id. House ID must be between 0 and 14.")

    # retrieve data
    data_type = request["data_type"]
    house_dir = DATA_DIR / f"house_{house_id:02d}"
    if data_type == "house_description":
        return _copy_file_to_outbox(house_dir, ["house.tsv"], outbox, house_id)
    elif data_type == "item_description":
        return _copy_file_to_outbox(house_dir, ["items.tsv"], outbox, house_id)
    elif data_type == "item_data":
        item_data_type = request["item_data_type"]
        if item_data_type == "annotations":
            file_names = _filter_item_files(house_dir, "_annotations.tsv")
            return _copy_file_to_outbox(house_dir, file_names, outbox, house_id)
        elif item_data_type == "annotation_labels":
            file_names = _filter_item_files(house_dir, "_annotation_labels.tsv")
            return _copy_file_to_outbox(house_dir, file_names, outbox, house_id)
        elif item_data_type == "data":
            file_names = _filter_item_files(house_dir, "_data.tsv.gz")
            return _copy_file_to_outbox(house_dir, file_names, outbox, house_id)
        else:
            raise RetrieverRequestError(
                f"Invalid item_data_type. Item_data_type must be either 'annotations', 'annotation_labels' or 'data'")
    raise RetrieverRequestError(
        f"Invalid data_type. Data_type must be either 'house_description', 'item_description' or 'item_data_type'")


def _copy_file_to_outbox(file_dir: Path, file_names: list[str], outbox: Path, house_id: int) -> list[str]:
    """
    Copies all files to the outbox, adds a 'deddiag_{house_id}_' prefix and returns the new file names on success.
    """

    new_file_names = list()
    for file_name in file_names:
        # cache checks (check if file already copied to outbox previously)
        new_file_name = f"deddiag_{house_id:02d}_{file_name}"
        if not (outbox / new_file_name).is_file():
            # copy file
            shutil.copy(file_dir / file_name, outbox / new_file_name)
        new_file_names.append(new_file_name)
    return new_file_names


def _filter_item_files(house_dir: Path, suffix: str) -> list[str]:
    """Get all file names with the given suffix."""

    return [
        f.name for f in house_dir.iterdir()
        if f.is_file() and f.name.endswith(suffix)
    ]
