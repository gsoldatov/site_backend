import os
import asyncio
from datetime import datetime
from copy import deepcopy
import pytest

from backend_main.validation.types import HiddenString


def ensure_equal_collection_elements(expected: list | set, received: list | set, message: str = "Expected ids check"):
    """
        Ensures `expected` and `received` collections (lists or sets) contain the same elements.
        Different sort order is allowed.
    """
    expected = deepcopy(expected)
    received = deepcopy(received)
    
    for r in received:
        try:
            expected.remove(r)
        except (KeyError, ValueError):
            pytest.fail(message + f" > received unexpected list element {r}.")
    if len(expected) > 0:
        pytest.fail(message + f" > expected list elements not found: {expected}.")


def get_test_name(name, test_uuid):
    """
    Returns `name` with concatenated `TEST_POSTFIX` and `test_uuid`.
    If `name` is an instance of `HiddenValue`, returns a new `HiddenValue`. Otherwise return a string.
    """
    if type(name) == HiddenString:
        return HiddenString(name.value + TEST_POSTFIX + test_uuid, replacement_string=name._replacement_string)
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


async def wait_for(fn, timeout = 1, interval = 0.1, msg = "Timeout expired.", *args, **kwargs):
    """
    Waits for callable `fn` to return True on completion.
    Sleeps for a specified `interval` between calls.
    If `timeout` is reached before True is returned, fails the test with the provided message `msg`.
    `fn` arguments can be passed via `*args` and `**kwargs`.
    """
    async def awaitable_wrapper():
        while not fn(*args, **kwargs):
            await asyncio.sleep(interval)
    
    try:
        await asyncio.wait_for(awaitable_wrapper(), timeout=timeout)
    except asyncio.TimeoutError:
        pytest.fail(msg)


def run_pytest_tests(file):
    """Runs pytest tests in the provided `file`"""
    os.system(f'pytest "{os.path.abspath(file)}" -v --asyncio-mode=auto')
