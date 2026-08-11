import pandas as pd

from emtl.basics import get_request_schema
from emtl.data import get_data_files, delete_files

DATASET_ID = 'wpuq'
TEMPORAL_RESOLUTIONS = ['1min', '15min', '60min']
YEARS = list(range(2018, 2021))


def get_description() -> str:
    """
    Get general information of the WPuQ dataset.

    Returns:
        str: Textual description and more detailed information about the datasource.

    """
    schema = get_request_schema(DATASET_ID)
    return schema['description']


def get_household_load_data(year: int, temporal_resolution: str,
                                 only_pv: bool = False, only_no_pv: bool = False,
                                 cache: bool = True) -> pd.DataFrame:
    """
    Retrieve WPuQ household electricity load data.

    Loads household electricity consumption data for all available single-family households for the given year and
    temporal resolution. Data can optionally be filtered to include only households with photovoltaic (PV) systems
    or only households without PV systems.

    Args:
        year (int):
            Year for which the data should be retrieved. Must be one of {2018, 2019, 2020}.
        temporal_resolution (str):
            Temporal resolution of the load data. Must be one of {'1min', '15min', '60min'}.
        only_pv (bool, optional):
            If True, only data from households equipped with PV systems is returned. Defaults to False.
        only_no_pv (bool, optional):
            If True, only data from households without PV systems is returned. Defaults to False.
        cache (bool, optional):
            Whether to use locally cached data files if available.
            If False, downloaded files are deleted after loading. Defaults to True.

    Returns:
        pd.DataFrame:
            Concatenated household load data for all matching households.
            Each row represents a single time step and household.

    """
    return _get_wpuq_load_data('HOUSEHOLD', year, temporal_resolution,
                               only_pv=only_pv, only_no_pv=only_no_pv, cache=cache)


def get_heatpump_load_data(year: int, temporal_resolution: str,
                                only_pv: bool = False, only_no_pv: bool = False,
                                cache: bool = True) -> pd.DataFrame:
    """
    Retrieve WPuQ heat pump electricity load data.

    Loads electricity consumption data of heat pumps installed in single-family households for the given year
    and temporal resolution. Data can optionally be filtered to include only households with photovoltaic (PV)
    systems or only households without PV systems.

    Args:
        year (int):
            Year for which the data should be retrieved. Must be one of {2018, 2019, 2020}.
        temporal_resolution (str):
            Temporal resolution of the load data. Must be one of {'1min', '15min', '60min'}.
        only_pv (bool, optional):
            If True, only data from households equipped with PV systems is returned. Defaults to False.
        only_no_pv (bool, optional):
            If True, only data from households without PV systems is returned. Defaults to False.
        cache (bool, optional):
            Whether to use locally cached data files if available.
            If False, downloaded files are deleted after loading. Defaults to True.

    Returns:
        pd.DataFrame:
            Concatenated heat pump load data for all matching households.
            Each row represents a single time step and household.
    """
    return _get_wpuq_load_data('HEATPUMP', year, temporal_resolution,
                               only_pv=only_pv, only_no_pv=only_no_pv, cache=cache)


def _get_wpuq_load_data(load_key: str, year: int, temporal_resolution: str,
                        only_pv: bool = False, only_no_pv: bool = False,
                        cache: bool = True) -> pd.DataFrame:
    """
    Internal helper function to retrieve WPuQ load data.
    Fetches and concatenates load data (e.g. household or heat pump loads) for all matching households for the given
    year and temporal resolution. This function performs input validation, builds the request schema, fetches the
    corresponding data files, and returns the combined result.
    """

    # param checking
    if only_pv and only_no_pv:
        raise ValueError('error: only_pv and only_no_pv cannot be True simultaneously.')
    if temporal_resolution not in TEMPORAL_RESOLUTIONS:
        raise ValueError(f'error: temporal_resolution must be one of {TEMPORAL_RESOLUTIONS}.')
    if year not in YEARS:
        raise ValueError(f'error: year must between {YEARS[0]} and {YEARS[-1]} (inclusive).')
    # build request schema
    request_schema = get_request_schema(DATASET_ID)
    request_schema['request']['year'] = year
    request_schema['request']['file_name'] = f'data_{temporal_resolution}'
    request_schema['request']['top_level_nodes'] = ['WITH_PV'] if only_pv else ['NO_PV'] if only_no_pv else ['WITH_PV',
                                                                                                             'NO_PV']
    request_schema['request']['mid_level_nodes'] = []  # all nodes
    request_schema['request']['low_level_nodes'] = [load_key.upper()]
    # fetch and concat data
    data_file_paths = get_data_files(request_schema)
    data_dfs = [pd.read_csv(f) for f in data_file_paths]
    if not cache:
        delete_files(data_file_paths)
    return pd.concat(data_dfs, axis=0, ignore_index=True)


def get_misc_data(year: int, temporal_resolution: str, cache: bool = True) -> pd.DataFrame:
    """
    Retrieve MISC data. Measurements of the PV system close-by,
    including electrical substation (ES1) and the PV system (PV1).

    Args:
        year (int):
            Year for which the data should be retrieved. Must be one of {2018, 2019, 2020}.
        temporal_resolution (str):
            Temporal resolution, must be one of {'1min', '15min', '60min'}.
        cache (bool, optional):
            Whether to keep downloaded data files in the local cache.
            If False, files are deleted after loading. Defaults to True.

    Returns:
        pd.DataFrame:
            Concatenated data for the specified year.
    """
    # param checking
    if year not in YEARS:
        raise ValueError(f'error: year must between {YEARS[0]} and {YEARS[-1]} (inclusive).')
    if temporal_resolution not in TEMPORAL_RESOLUTIONS:
        raise ValueError(f'error: temporal_resolution must be one of {TEMPORAL_RESOLUTIONS}.')
    # build request schema
    request_schema = get_request_schema(DATASET_ID)
    request_schema['request']['year'] = year
    request_schema['request']['file_name'] = f'data_{temporal_resolution}'
    request_schema['request']['top_level_nodes'] = ['MISC']
    request_schema['request']['mid_level_nodes'] = []
    request_schema['request']['low_level_nodes'] = []
    # fetch and concat data
    data_file_paths = get_data_files(request_schema)
    data_dfs = [pd.read_csv(f) for f in data_file_paths]
    if not cache:
        delete_files(data_file_paths)
    return pd.concat(data_dfs, axis=0, ignore_index=True)


def get_weather_data(year: int, cache: bool = True) -> pd.DataFrame:
    """
    Retrieve WPuQ weather data.
    Loads weather data provided by the associated weather service for the given year. The returned data includes
    temperature-related measurements and is aggregated across all available weather data sources.

    Args:
        year (int):
            Year for which the data should be retrieved. Must be one of {2018, 2019, 2020}.
        cache (bool, optional):
            Whether to keep downloaded data files in the local cache.
            If False, files are deleted after loading. Defaults to True.

    Returns:
        pd.DataFrame:
            Concatenated weather data for the specified year.
            Each row represents a single time step of weather measurements.
    """
    # param checking
    if year not in YEARS:
        raise ValueError(f'error: year must between {YEARS[0]} and {YEARS[-1]} (inclusive).')
    # build request schema
    request_schema = get_request_schema(DATASET_ID)
    request_schema['request']['year'] = year
    request_schema['request']['file_name'] = 'weather'
    request_schema['request']['top_level_nodes'] = ['WEATHER_SERVICE']
    request_schema['request']['mid_level_nodes'] = ['IN']
    request_schema['request']['low_level_nodes'] = []
    # fetch and concat data
    data_file_paths = get_data_files(request_schema)
    data_dfs = [pd.read_csv(f) for f in data_file_paths]
    if not cache:
        delete_files(data_file_paths)
    return pd.concat(data_dfs, axis=0, ignore_index=True)


def get_district_heating_grid_data(year: int, cache: bool = True) -> pd.DataFrame:
    """
    Retrieve WPuQ district heating grid data.
    Loads heating grid data, including flow and return temperature of the district heating grid.

    Args:
        year (int):
            Year for which the data should be retrieved. Must be one of {2018, 2019, 2020}.
        cache (bool, optional):
            Whether to keep downloaded data files in the local cache.
            If False, files are deleted after loading. Defaults to True.

    Returns:
        pd.DataFrame:
            Concatenated data for the specified year.
    """
    # param checking
    if year not in YEARS:
        raise ValueError(f'error: year must between {YEARS[0]} and {YEARS[-1]} (inclusive).')
    # build request schema
    request_schema = get_request_schema(DATASET_ID)
    request_schema['request']['year'] = year
    request_schema['request']['file_name'] = 'district_heating_grid'
    request_schema['request']['top_level_nodes'] = ['DH_GRID']
    request_schema['request']['mid_level_nodes'] = ['IN']
    request_schema['request']['low_level_nodes'] = []
    # fetch and concat data
    data_file_paths = get_data_files(request_schema)
    data_dfs = [pd.read_csv(f) for f in data_file_paths]
    if not cache:
        delete_files(data_file_paths)
    return pd.concat(data_dfs, axis=0, ignore_index=True)
