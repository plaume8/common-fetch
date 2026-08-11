import pandas as pd

from emtl.basics import get_request_schema
from emtl.data import get_data_files, delete_files


DATASET_ID = 'opsd'


def get_description() -> str:
    """
    Get general information of the OPSD (Open Power System Data) household load dataset.

    Returns:
        str: Textual description and more detailed information about the datasource.
    """
    schema = get_request_schema(DATASET_ID)
    return schema['description']


def get_household_data(temporal_resolution: str, cache: bool = True) -> pd.DataFrame:
    """
    Retrieve household load and solar generation data for in minutely to hourly resolution.
    (Detailed column descriptions: https://data.open-power-system-data.org/household_data/latest/README.md)

    Args:
        temporal_resolution (str):
            Temporal resolution of the data. Must be one of {'1min', '15min', '60min'}.
        cache (bool, optional):
            Whether to use locally cached data files if available.
            If False, downloaded files are deleted after loading. Defaults to True.

    Returns:
        pd.DataFrame:
            All household load and solar generation data.
    """

    # param checking
    if temporal_resolution not in ['1min', '15min', '60min']:
        raise ValueError(f"error: temporal_resolution must be one of ['1min', '15min', '60min']")
    # build request schema
    request_schema = get_request_schema(DATASET_ID)
    request_schema['request']['temporal_resolution'] = temporal_resolution
    # fetch and concat data
    data_file_paths = get_data_files(request_schema)
    data_df = pd.read_csv(data_file_paths[0])
    if not cache:
        delete_files(data_file_paths)
    return data_df
