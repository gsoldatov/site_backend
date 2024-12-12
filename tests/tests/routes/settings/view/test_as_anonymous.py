if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.db_operations.settings import set_setting


async def test_view_private_setting(cli, db_cursor):
    set_setting(db_cursor, "non_admin_registration_allowed", is_public=False)
    
    body = {"setting_names": ["non_admin_registration_allowed"]}
    resp = await cli.post("settings/view", json=body)
    assert resp.status == 401


async def test_view_all_settings(cli):
    body = {"view_all": True}
    resp = await cli.post("settings/view", json=body)
    assert resp.status == 401


async def test_view_non_admin_registration_as_admin_and_anonymous(cli, db_cursor):
    body = {"setting_names": ["non_admin_registration_allowed"]}
    resp = await cli.post("settings/view", json=body)
    assert resp.status == 200
    data = await resp.json()
    
    assert type(data) == dict
    
    assert "settings" in data
    assert type(data["settings"]) == dict
    
    assert data["settings"].get("non_admin_registration_allowed") == False

    set_setting(db_cursor, "non_admin_registration_allowed", "TRUE")
    resp = await cli.post("settings/view", json=body)
    assert resp.status == 200
    data = await resp.json()
    
    assert data["settings"].get("non_admin_registration_allowed") == True


if __name__ == "__main__":
    run_pytest_tests(__file__)
