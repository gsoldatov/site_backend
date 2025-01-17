import os
import asyncio
import pytest

from backend_main.types.common import HiddenString


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
