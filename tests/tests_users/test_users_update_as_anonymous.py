if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.data_generators.users import get_update_user_request_body


async def test_correct_update(cli, config):
    body = get_update_user_request_body(token_owner_password=config["app"]["default_user"]["password"].value)
    resp = await cli.put("/users/update", json=body)
    assert resp.status == 401


if __name__ == "__main__":
    run_pytest_tests(__file__)
