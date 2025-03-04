if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 6)))
    from tests.util import run_pytest_tests

from tests.data_generators.sessions import headers_admin_token
from tests.db_operations.settings import set_setting


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.post("/settings/view", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Required attributes missing
    resp = await cli.post("settings/view", json={}, headers=headers_admin_token)
    assert resp.status == 400
    
    # Incorrect attribute values
    incorrect_attributes = {
        "setting_names": [None, False, 1, "str", {}],
        "view_all": [None, 2, "str", {}, []]
    }
    for attr, values in incorrect_attributes.items():
        for value in values:
            body = {attr: value}
            resp = await cli.post("settings/view", json=body, headers=headers_admin_token)
            assert resp.status == 400
    
    # Unallowed attribute combination
    body = {"setting_names": ["some name"], "view_all": True}
    resp = await cli.post("settings/view", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Unallowed attributes
    for attr, value in [("setting_names", "some name"), ("view_all", True)]:
        body = {attr: value, "unallowed": "unallowed"}
        resp = await cli.post("settings/view", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_non_existing_setting_name(cli):
    body = {"setting_names": ["non-existing setting name"]}
    resp = await cli.post("settings/view", json=body, headers=headers_admin_token)
    assert resp.status == 404


async def test_view_non_admin_registration(cli, db_cursor):
    body = {"setting_names": ["non_admin_registration_allowed"]}
    resp = await cli.post("settings/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    
    assert type(data) == dict
    
    assert "settings" in data
    assert type(data["settings"]) == dict
    
    assert data["settings"].get("non_admin_registration_allowed") == False

    set_setting(db_cursor, "non_admin_registration_allowed", "TRUE")
    resp = await cli.post("settings/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    
    assert data["settings"].get("non_admin_registration_allowed") == True


async def test_view_all(cli):
    body = {"view_all": True}
    resp = await cli.post("settings/view", json=body, headers=headers_admin_token)
    assert resp.status == 200
    data = await resp.json()
    
    assert type(data) == dict
    
    assert "settings" in data
    assert type(data["settings"]) == dict
    assert len(data["settings"]) == 1

    assert data["settings"].get("non_admin_registration_allowed") == False


if __name__ == "__main__":
    run_pytest_tests(__file__)
