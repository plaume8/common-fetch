from pathlib import Path
from typing import Optional, Any

import h5py
import numpy as np
import pandas as pd


from emtl_server.errors import RetrieverRequestError
from emtl_server.utils import filename_sanity_check


BASE_DIR = Path(__file__).resolve().parent.parent


def retrieve(outbox: Path, request: Optional[dict[str, Any]]) -> list[str]:
    """
    Retriever for the WPuQ data:
    - This retriever accesses the original WPuQ hdf5 files and retrieves the requested data according to the given request objects.
    - paper: https://www.nature.com/articles/s41597-022-01156-1
    - raw data: https://zenodo.org/records/5642902

    How the retriever works:
    - For each year (2018–2020), multiple hdf5 files exist that contain the data tables.
    - The WPuQ hdf5 files organize data tables in a three-level tree structure.
    - Each request specifies the top, mid, and low-level nodes for which data should be retrieved.
    - For every valid path combination, the retriever loads the corresponding leaf-node data table and stores it as a csv file in the outbox.
    - If a request contains multiple nodes at any level, all possible path combinations are considered.
    - For example, if top_level_nodes = ['a'], mid_level_nodes = ['m', 'n'], and low_level_nodes = ['l'], the retriever retrieves the data tables for the paths a-m-l and a-n-l.
    - Additionally, if a node level is specified as an empty list (eg, mid_level_nodes = []), the retriever treats this as a wildcard and includes all available nodes at that hierarchy level.

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
    required_request_params = ["year", "file_name", "top_level_nodes", "mid_level_nodes", "low_level_nodes"]
    missing = [k for k in required_request_params if k not in request]
    if missing:
        raise RetrieverRequestError(f"Missing request parameter(s): {', '.join(missing)}")

    # sanity checks
    request_file_name = request['file_name']
    if not filename_sanity_check(request_file_name):
        raise RetrieverRequestError("Invalid file_name.")

    # construct the correct WPuQ hdf5 data file name
    file_name = f"{request['year']}_{request_file_name}.hdf5"
    file_path = BASE_DIR / 'retrievers' / 'raw_data' / 'wpuq' / file_name
    if not file_path.is_file():
        raise RetrieverRequestError(f"year '{request['year']}' or file_name '{request_file_name}' not available")

    # retrieve data
    out_file_names = list()
    try:
        with h5py.File(file_path, "r") as f:

            # go through all tree node levels and path combinations
            top_l_nodes = f.keys() if not request['top_level_nodes'] else request['top_level_nodes']
            for top_l_n in top_l_nodes:
                mid_l_nodes = f[top_l_n].keys() if not request['mid_level_nodes'] else request['mid_level_nodes']
                for mid_l_n in mid_l_nodes:
                    low_l_nodes = f[top_l_n][mid_l_n].keys() if not request['low_level_nodes'] else request['low_level_nodes']
                    for low_l_n in low_l_nodes:

                        # check if data already in outbox
                        out_file_name = f"wpuq_{request['year']}_{request_file_name}_{top_l_n}_{mid_l_n}_{low_l_n}.csv"
                        out_file_names.append(out_file_name)
                        if (outbox / out_file_name).is_file():
                            continue

                        # read data and save as csv in outbox
                        # read data and save as csv in outbox
                        datatable = f[top_l_n][mid_l_n][low_l_n]['table']  # in each leaf the data table is stored under 'table'
                        datatable_df = pd.DataFrame(np.array(datatable))
                        # make sure the additional columns are after the 'index' column (time) but still up front
                        datatable_df.insert(1, "low_level_node", low_l_n)
                        datatable_df.insert(1, "mid_level_node", mid_l_n)
                        datatable_df.insert(1, "top_level_node", top_l_n)
                        datatable_df.insert(1, "file_name", request_file_name)
                        datatable_df.insert(1, "year", request['year'])
                        # each datatable has an 'index' column with a UNIX timestamp -> transfer to df timestamp
                        datatable_df["index"] = datatable_df["index"].apply(normalize_timestamp)
                        datatable_df.to_csv(outbox / out_file_name, index=False)

    except Exception as e:
        # raise a general error to prevent exposing internal implementation details to the end user
        raise RetrieverRequestError(f"WPuQ retriever logic failed.")

    return out_file_names


def normalize_timestamp(ts):
    """Some index entries are formatted in seconds, some in nanoseconds."""

    ts = int(ts)
    if ts > 1e18:        # nanoseconds
        return pd.Timestamp(ts, unit="ns")
    elif ts > 1e15:      # microseconds
        return pd.Timestamp(ts, unit="us")
    elif ts > 1e12:      # milliseconds
        return pd.Timestamp(ts, unit="ms")
    else:                # seconds
        return pd.Timestamp(ts, unit="s")

