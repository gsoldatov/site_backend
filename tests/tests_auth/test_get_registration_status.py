import pytest

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))

from tests.fixtures.settings import set_setting
from tests.fixtures.users import headers_admin_token, headers_non_existing_token


@pytest.mark.parametrize("headers", [None, headers_admin_token, headers_non_existing_token])
async def test_get_registration_status(cli, db_cursor, config, headers):
    # Enable non-admin user registration
    set_setting("non_admin_registration_allowed", "TRUE", db_cursor, config)
    
    # Get setting value
    resp = await cli.get("/auth/get_registration_status", headers=headers)
    assert resp.status == 200
    data = await resp.json()
    assert data["registration_allowed"] == True

    # Disable non-admin user registration
    set_setting("non_admin_registration_allowed", "FALSE", db_cursor, config)
    
    # Get setting value
    resp = await cli.get("/auth/get_registration_status", headers=headers)
    assert resp.status == 200
    data = await resp.json()
    assert data["registration_allowed"] == False


if __name__ == "__main__":
    os.system(f'pytest "{os.path.abspath(__file__)}" -v')
