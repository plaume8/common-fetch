import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from time import sleep

import requests

PROJECT_ROOT = Path(__file__).parent.parent
DATA_SERVER_ROOT = PROJECT_ROOT / "data_server" / "src"
DATA_LOADER_ROOT = PROJECT_ROOT / "data_loader" / "src"

LOCAL_HOST = "0.0.0.0"
DATA_SERVER_PORT = "8001"
DATA_SERVER_URL = f"http://{LOCAL_HOST}:{DATA_SERVER_PORT}"

_server_process = None


def pytest_sessionstart(session):
    """Called before test session starts."""
    _run_data_server()
    _setup_data_loader()
    print("")


def pytest_sessionfinish(session, exitstatus):
    """Called after test session finishes."""
    print("")
    _stop_data_server()
    _tear_down_data_loader()


def _setup_data_loader() -> None:
    """
    Make sure PYTHONPATH env is set to data_loader root.
    Also ensure the data_loader endpoint is set to locally run data_server.
    """
    sys.path.insert(0, str(DATA_LOADER_ROOT))
    os.environ['PYTHONPATH'] = str(DATA_LOADER_ROOT)
    print("Data loader setup successful.")


def _tear_down_data_loader() -> None:
    """
    Make sure data_loader local cache is cleared.
    """
    sys_tmp_dir_path = Path(tempfile.gettempdir())
    shutil.rmtree((sys_tmp_dir_path / 'cf-dataloader-cache-k4wJx1o9'), ignore_errors=True)
    print("Data loader teardown successful.")


def _run_data_server() -> None:
    """Start FastAPI data server in seperate process."""

    global _server_process
    env = os.environ.copy()
    env['PYTHONPATH'] = str(DATA_SERVER_ROOT)
    _server_process = subprocess.Popen(
        ["uvicorn", "cf_server.main:app", "--host", LOCAL_HOST, "--port", DATA_SERVER_PORT],
        env=env,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # additional logging when server failed on start
    if _server_process.poll() is not None:
        stdout, stderr = _server_process.communicate()
        raise RuntimeError(
            f"Server process died immediately.\n\n"
            f"STDOUT:\n{stdout}\n\n"
            f"STDERR:\n{stderr}"
        )

    # wait for server start
    for _ in range(10):
        try:
            response = requests.get(f"{DATA_SERVER_URL}", timeout=1)
            if response.status_code == 200:
                print("Data server has started successfully.")
                return
        except Exception:
            sleep(1)

    _server_process.terminate()
    raise RuntimeError("Data server failed to start.")


def _stop_data_server() -> None:
    """Stop FastAPI data server."""
    global _server_process
    _server_process.terminate()
    _server_process = None
    print("Data server has stopped gracefully.")
