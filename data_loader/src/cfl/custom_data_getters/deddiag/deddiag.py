import ast
from copy import deepcopy

import pandas as pd

from emtl.basics import get_request_schema
from emtl.data import get_data_files, delete_files


DATASET_ID = 'deddiag'
HOUSE_IDS = list(range(0, 15))


def get_description() -> str:
    """
    Get general information of the DEDDIAG dataset.

    Returns:
        str: Textual description and more detailed information about the datasource.
    """
    schema = get_request_schema(DATASET_ID)
    return schema['description']


def get_house_description(house_id: int, cache: bool = True) -> list:
    """
    Retrieve the house description for one of the 15 homes of the DEDDIAG dataset.
    It provides demographic data such as number of residents, their age,
    regularity of absence and normal absence duration.

    Args:
        house_id (int):
            ID of the House to retrieve the house description for. Must be in between 0 and 14.
        cache (bool, optional):
            Whether to use locally cached data files if available.
            If False, downloaded files are deleted after loading. Defaults to True.

    Returns:
        list:
            All demographic data.
    """

    # param checking
    if house_id not in HOUSE_IDS:
        raise ValueError(f'error: house_id must be in between 0 and 14.')
    # build request schema
    request_schema = get_request_schema(DATASET_ID)
    request_schema['request']['house_id'] = house_id
    request_schema['request']['data_type'] = 'house_description'
    # fetch and concat data
    data_file_paths = get_data_files(request_schema)
    data_df = pd.read_csv(data_file_paths[0], sep='\t')
    if not cache:
        delete_files(data_file_paths)
    return ast.literal_eval(data_df.at[0, 'persons'])


def get_item_descriptions(house_id: int, cache: bool = True) -> pd.DataFrame:
    """
    Retrieve the item (appliance) descriptions for one of the 15 homes of the DEDDIAG dataset.
    Includes appliances (item) metadata, containing a unique ID, name, device category and house ID.

    Args:
        house_id (int):
            ID of the House to retrieve the item descriptions for. Must be in between 0 and 14.
        cache (bool, optional):
            Whether to use locally cached data files if available.
            If False, downloaded files are deleted after loading. Defaults to True.

    Returns:
        pd.DataFrame:
            All item (appliance) descriptions.

    """
    # param checking
    if house_id not in HOUSE_IDS:
        raise ValueError(f'error: house_id must be in between 0 and 14.')
    # build request schema
    request_schema = get_request_schema(DATASET_ID)
    request_schema['request']['house_id'] = house_id
    request_schema['request']['data_type'] = 'item_description'
    # fetch and concat data
    data_file_paths = get_data_files(request_schema)
    data_df = pd.read_csv(data_file_paths[0], sep='\t')
    if not cache:
        delete_files(data_file_paths)
    return data_df


def get_item_annotations(house_id: int, cache: bool = True) -> pd.DataFrame:
    """
    Retrieve all item (appliance) annotations for one of the 15 homes of the DEDDIAG dataset.
    (All item labels have already been merged into the dataset.)

    Args:
        house_id (int):
            ID of the House to retrieve the item (appliance) annotations for. Must be in between 0 and 14.
        cache (bool, optional):
            Whether to use locally cached data files if available.
            If False, downloaded files are deleted after loading. Defaults to True.

    Returns:
        pd.DataFrame:
            All item (appliance) annotations.
    """
    # param checking
    if house_id not in HOUSE_IDS:
        raise ValueError(f'error: house_id must be in between 0 and 14.')
    # build request schemas
    request_schema_a = get_request_schema(DATASET_ID)
    request_schema_l = deepcopy(request_schema_a)
    request_schema_a['request']['house_id'] = house_id
    request_schema_a['request']['data_type'] = 'item_data'
    request_schema_a['request']['item_data_type'] = 'annotations'
    request_schema_l['request']['house_id'] = house_id
    request_schema_l['request']['data_type'] = 'item_data'
    request_schema_l['request']['item_data_type'] = 'annotation_labels'
    # fetch and concat data
    data_file_paths_a = get_data_files(request_schema_a)
    data_file_paths_l = get_data_files(request_schema_l)
    annotations_dfs = [pd.read_csv(f, sep='\t') for f in data_file_paths_a]
    annotation_labels_dfs = [pd.read_csv(f, sep='\t') for f in data_file_paths_l]
    if not cache:
        delete_files(data_file_paths_a)
        delete_files(data_file_paths_l)
    annotations_df = pd.concat(annotations_dfs, axis=0, ignore_index=True)
    annotation_labels_df = pd.concat(annotation_labels_dfs, axis=0, ignore_index=True)
    annotation_labels_df = annotation_labels_df.add_prefix("label_")
    return pd.merge(annotations_df, annotation_labels_df, left_on='label_id', right_on='label_id', how='left').drop(columns=['label_item_id'])


def get_item_data(house_id: int, cache: bool = True) -> pd.DataFrame:
    """
    Retrieve all item (appliance) measurements for one of the 15 homes of the DEDDIAG dataset.

    Args:
        house_id (int):
            ID of the House to retrieve the item (appliance) annotations for. Must be in between 0 and 14.
        cache (bool, optional):
            Whether to use locally cached data files if available.
            If False, downloaded files are deleted after loading. Defaults to True.

    Returns:
        pd.DataFrame:
            All measurements.
    """
    # param checking
    if house_id not in HOUSE_IDS:
        raise ValueError(f'error: house_id must be in between 0 and 14.')
    # build request schema
    request_schema = get_request_schema(DATASET_ID)
    request_schema['request']['house_id'] = house_id
    request_schema['request']['data_type'] = 'item_data'
    request_schema['request']['item_data_type'] = 'data'
    # fetch and concat data
    data_file_paths = get_data_files(request_schema)
    data_dfs = [pd.read_csv(f, sep='\t', compression='gzip') for f in data_file_paths]
    if not cache:
        delete_files(data_file_paths)
    return pd.concat(data_dfs, axis=0, ignore_index=True)
