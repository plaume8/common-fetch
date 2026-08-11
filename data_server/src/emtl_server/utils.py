import re


FILENAME_SANITY_CHECK_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def filename_sanity_check(filename) -> bool:
    """Perform a simple filename sanity check. Return true if the filename is valid."""

    if not filename or not isinstance(filename, str):
        return False
    if "/" in filename or "\\" in filename:
        return False
    if filename.startswith(".") or filename == ".." or filename == ".":
        return False
    return FILENAME_SANITY_CHECK_RE.match(filename) is not None