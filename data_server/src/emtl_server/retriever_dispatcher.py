from pathlib import Path
import importlib.util
from typing import Optional, Any

from emtl_server.errors import RetrieverRequestError, GeneralInternalServerError
from emtl_server.utils import filename_sanity_check

BASE_DIR = Path(__file__).resolve().parent


def execute_retriever(dataset_id: str, outbox: Path, request: Optional[dict[str, Any]]) -> list[str]:
    """
    Based on the provided `dataset_id`, the corresponding `retriever` is executed,
    passing the `outbox` and `request` object to retrieve the data.

    Args:
        dataset_id (str): Unique id of the dataset, which is used to determine and invoke the corresponding retriever.
        outbox (Path): Path to the outbox directory where the retrieved data files will be stored.
        request (Optional[dict[str, Any]]): Request object containing all parameters that specify which data should be retrieved, following the corresponding schema (yaml file).

    Returns:
        list[str]: List of filenames of the generated data files stored in the outbox directory.

    Raises:
        RetrieverRequestError: Indicates that the request could not be processed. The corresponding error message is returned to the end user.
        GeneralInternalServerError: Indicates an unexpected failure during data retrieval. The corresponding error message is logged for debugging purposes, while a generic error response is returned to the end user to avoid exposing implementation details.
    """

    # dataset_id sanity check
    if not filename_sanity_check(dataset_id):
        raise RetrieverRequestError("Invalid dataset_id.")

    # check if a corresponding retriever file for the dataset_id exists
    retrievers_py_file = BASE_DIR / "retrievers" / f"{dataset_id}_retriever.py"
    if not retrievers_py_file.is_file():
        raise RetrieverRequestError(f"Retriever for {dataset_id} does not exist.")

    # import corresponding 'retrieve' function
    # create module spec from file
    spec = importlib.util.spec_from_file_location('retriever', retrievers_py_file)
    if spec is None or spec.loader is None:
        raise GeneralInternalServerError(f"Could not load spec for {retrievers_py_file}.")
    # create an empty module object and execute the module code inside the module object
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # ensure the file defines 'retrieve'
    if not hasattr(module, "retrieve"):
        raise GeneralInternalServerError(f"Retriever {retrievers_py_file} does not define a function 'retrieve'.")
    retrieve_fn = getattr(module, "retrieve")

    # execute retriever
    try:
        return retrieve_fn(outbox, request)
    except (RetrieverRequestError, GeneralInternalServerError):
        raise
    except Exception as e:
        raise GeneralInternalServerError(str(e)) from e
