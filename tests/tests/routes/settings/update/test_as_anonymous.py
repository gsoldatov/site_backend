if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests


async def test_correct_update_as_anonymous(cli):
    body = {"settings": {"non_admin_registration_allowed": True}}
    resp = await cli.put("/settings/update", json=body)
    assert resp.status == 401


if __name__ == "__main__":
    run_pytest_tests(__file__)
