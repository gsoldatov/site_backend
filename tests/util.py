import pytest
from copy import deepcopy


def check_ids(expected, received, message = "Expected ids check"):
    expected = deepcopy(expected)
    received = deepcopy(received)
    
    for r in received:
        try:
            expected.remove(r)
        except KeyError:
            pytest.fail(message + f" > received unexpected id {r}.")
    if len(expected) > 0:
        pytest.fail(message + f" > expected ids {expected} not found.")


def get_test_name(name, test_uuid):
    """Returns `name` with concatenated `TEST_POSTFIX` and `test_uuid`."""
    return name + TEST_POSTFIX + test_uuid


TEST_POSTFIX = "_test_"