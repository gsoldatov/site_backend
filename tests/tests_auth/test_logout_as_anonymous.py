if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests


async def test_logout(cli):
    resp = await cli.post("/auth/logout")
    assert resp.status == 401


if __name__ == "__main__":
    run_pytest_tests(__file__)
