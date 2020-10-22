import pytest


def check_ids(received, expected, message = "Expected ids check"):
    for r in received:
        try:
            expected.remove(r)
        except KeyError:
            pytest.fail(message, f"> received unexpected id {r}.")
    if len(expected) > 0:
        pytest.fail(message, f"> expected ids {expected} not found.")