import yaml
import logging

from typing import Optional, Any
from pathlib import Path

from cf_server.utils import filename_sanity_check


logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent


def get_schema(dataset_id: str) -> Optional[dict[str, Any]]:
    """Loads the schema YAML file associated with the specified dataset_id and returns its contents as a dictionary."""

    if not filename_sanity_check(dataset_id):
        return None

    schema_path = BASE_DIR / "retrievers" / "schemas" / f"{dataset_id}.yaml"
    if not schema_path.is_file():
        return None
    try:
        with schema_path.open("r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
            if not isinstance(schema, dict):
                return None
            return schema
    except Exception as e:
        logger.exception(f"get_schema failed unexpectedly; {e}")
        return None


def get_available_dataset_ids() -> list[str]:
    """Retrieve all available dataset_ids for which a schema file exists."""

    return sorted([p.stem for p in (BASE_DIR / "retrievers" / "schemas").glob("*.yaml")])
