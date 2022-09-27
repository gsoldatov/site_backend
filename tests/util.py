import os
import time
from datetime import datetime
from copy import deepcopy
import pytest

from backend_main.config import HiddenValue


def check_ids(expected, received, message = "Expected ids check"):
    expected = deepcopy(expected)
    received = deepcopy(received)
    
    for r in received:
        try:
            expected.remove(r)
        except (KeyError, ValueError):
            pytest.fail(message + f" > received unexpected id {r}.")
    if len(expected) > 0:
        pytest.fail(message + f" > expected ids {expected} not found.")


def get_test_name(name, test_uuid):
    """
    Returns `name` with concatenated `TEST_POSTFIX` and `test_uuid`.
    If `name` is an instance of `HiddenValue`, returns a new `HiddenValue`. Otherwise return a string.
    """
    if type(name) == HiddenValue:
        return HiddenValue(name.value + TEST_POSTFIX + test_uuid, replacement_string=name._replacement_string)
    else:
        return name + TEST_POSTFIX + test_uuid


TEST_POSTFIX = "_test_"


def parse_iso_timestamp(s, allow_empty_string = False):
    """
    Tries to parse an ISO-formatted string `s` and return a resulting datetime object.
    If `allow_empty_string` is set to True, empty string will be converted into None.
    """
    if allow_empty_string and len(s) == 0: return None
    if s.endswith("Z"): s = s[:-1] # remove Zulu timezone if present to avoid parsing failure
    return datetime.fromisoformat(s)


def wait_for(fn, timeout = 1, interval = 0.1, msg = "Timeout expired.", *args, **kwargs):
    """
    Runs function `fn` until it returns True with a specified `interval` between calls.
    Raises an error if `timeout` is reached before successful function execution.
    """
    end_time = time.time() + timeout

    while time.time() < end_time:
        result = fn(*args, **kwargs)

        if result: return

        time.sleep(interval)
    
    raise TimeoutError(msg)


def run_pytest_tests(file):
    """Runs pytest tests in the provided `file`"""
    os.system(f'pytest "{os.path.abspath(file)}" -v --asyncio-mode=auto')
