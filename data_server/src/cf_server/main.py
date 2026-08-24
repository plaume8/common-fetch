import logging
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from slowapi.errors import RateLimitExceeded
from starlette.responses import FileResponse
from starlette.status import HTTP_403_FORBIDDEN

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

from cf_server.auth.api_keys_management import verify_key
from cf_server.errors import RetrieverRequestError, GeneralInternalServerError
from cf_server.retriever_dispatcher import execute_retriever
from cf_server.schema_lookup import get_available_dataset_ids, get_schema
from cf_server.utils import filename_sanity_check

"""
This is the main FastAPI configuration file that comprises all endpoints.
For more, check out the official FastAPI docs: https://fastapi.tiangolo.com/#installation
"""

logger = logging.getLogger(__name__)
RUNTIME_DATA_OUTBOX: Path | None = None
TEMP_DIR_DEFAULT_NAME = 'cf-dataloader-server-outbox-u4J1tpq8'

# -------- LIFESPAN SETUP --------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global RUNTIME_DATA_OUTBOX

    # startup logic
    # all workers should access the same outbox directory -> therefore, a static name is used
    sys_tmp_dir_path = Path(tempfile.gettempdir())
    RUNTIME_DATA_OUTBOX = sys_tmp_dir_path / TEMP_DIR_DEFAULT_NAME
    RUNTIME_DATA_OUTBOX.mkdir(parents=True, exist_ok=True)
    logger.info("Runtime tmp dir connected: %s", RUNTIME_DATA_OUTBOX)

    try:
        # yield to let the app run
        yield

    finally:
        # shutdown logic
        pass


# -------- API KEY HEADER SETUP --------


API_KEY_NAME = "CFL-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    if not verify_key(api_key):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid or missing CFL-API-KEY (in header)."
        )
    return api_key


app = FastAPI(lifespan=lifespan)

# rate limits
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# -------- BASIC ENDPOINTS --------


@app.get("/", response_model=str)
def read_root():
    return "Welcome to the Common-Fetch Data Loader Server."


@app.get("/schema/{dataset_id}", response_model=dict[str, Any])
def read_schema(dataset_id: str, api_key: str = Depends(verify_api_key)):
    """Get the corresponding schema for the given dataset id."""

    schema = get_schema(dataset_id)
    if schema is None:
        raise HTTPException(status_code=404, detail=f"Schema not found.")
    return schema


@app.get("/dataset_ids", response_model=list[str])
def read_dataset_ids(api_key: str = Depends(verify_api_key)):
    """Get all available dataset ids."""

    return get_available_dataset_ids()


# -------- DATA DOWNLOAD ENDPOINTS --------


class DataRequest(BaseModel):
    dataset_id: str
    request: Optional[Dict[str, Any]] = None


@app.post("/data", response_model=list[str])
def process_data_request(data_request: DataRequest, api_key: str = Depends(verify_api_key)):
    """
    Calls the corresponding retriever for the given `dataset_id`
    and returns the names of all files generated in the outbox.
    """

    # call retriever to set up to be transferred data files
    try:
        data_files: list[str] = execute_retriever(
            data_request.dataset_id,
            RUNTIME_DATA_OUTBOX,
            data_request.request
        )
    except RetrieverRequestError as e:
        logger.exception(f"RetrieverRequestError for /data request with body: {data_request}.")
        raise HTTPException(status_code=400, detail=f"{e}")
    except GeneralInternalServerError as e:
        logger.exception(f"GeneralInternalServerError for /data request with body: {data_request}.")
        raise HTTPException(status_code=500)
    except Exception as e:
        logger.exception(f"Exception for /data request with body: {data_request}.")
        raise HTTPException(status_code=500)

    # double check if files are present
    data_files_paths = [RUNTIME_DATA_OUTBOX / f for f in data_files]
    if any(not p.is_file() for p in data_files_paths):
        logger.exception(f"Exception for /data request with body: {data_request}. Files {data_files_paths} missing.")
        raise HTTPException(status_code=500)

    return data_files


@app.get("/data/download/{data_file}", response_class=FileResponse)
def download_data_file(data_file: str, api_key: str = Depends(verify_api_key)):
    """
    Streams the specified data file back to the client.
    The file must exist in the 'outbox' directory.
    """

    # data_file sanity check
    if not filename_sanity_check(data_file):
        raise HTTPException(status_code=404, detail="File not found.")

    # check if data_file exists in outbox
    # also checks if the file is exclusively in outbox,
    # filename_sanity_check already prevents it but check it again from another "perspective"!
    data_file_path = RUNTIME_DATA_OUTBOX / data_file
    try:
        if not data_file_path.resolve().is_relative_to(RUNTIME_DATA_OUTBOX.resolve()):
            raise HTTPException(status_code=404, detail="File not found.")
    except Exception:
        raise HTTPException(status_code=404, detail="File not found.")
    if not data_file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    # transfer data_file
    return FileResponse(
        path=data_file_path,
        media_type="application/octet-stream",
        filename=data_file,
    )


if __name__ == "__main__":
    sys_tmp_dir_path = Path(tempfile.gettempdir())
    RUNTIME_DATA_OUTBOX = sys_tmp_dir_path / TEMP_DIR_DEFAULT_NAME
    print(f"RUNTIME_DATA_OUTBOX: {RUNTIME_DATA_OUTBOX}")
