from emtl.data_cache import DataCache


SERVER_BASE_URL = 'http://emtl-data-loader-server.10.152.14.66.nip.io'  # 'http://127.0.0.1:8000'
CACHE = None


def _get_base_url() -> str:
    return SERVER_BASE_URL


def _get_cache() -> DataCache:
    global CACHE
    if CACHE is None:
        CACHE = DataCache()
    return CACHE


def _set_server_base_url(url: str) -> None:
    global SERVER_BASE_URL
    SERVER_BASE_URL = url
