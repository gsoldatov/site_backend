if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.sessions import headers_admin_token


async def test_incorrect_request_body(cli):
    # Incorrect request body
    resp = await cli.put("/settings/update", data="not a JSON document.", headers=headers_admin_token)
    assert resp.status == 400

    # Required attributes missing
    resp = await cli.put("settings/update", json={}, headers=headers_admin_token)
    assert resp.status == 400
    
    # Unallowed attributes
    body = {"settings": {"non_admin_registration_allowed": True}}
    body["unallowed"] = "unallowed"
    resp = await cli.put("/settings/update", json=body, headers=headers_admin_token)
    assert resp.status == 400
    
    # Incorrect attribute values
    for attr, value in [("settings", 1), ("settings", "str"), ("settings", True), ("settings", []), ("settings", {})]:
        body = {attr: value}
        resp = await cli.put("/settings/update", json=body, headers=headers_admin_token)
        assert resp.status == 400


async def test_incorrect_setting_names_and_values(cli):    
    # Incorrect setting name
    body = {"settings": {"incorrect name": True}}
    resp = await cli.put("/settings/update", json=body, headers=headers_admin_token)
    assert resp.status == 400

    # Incorrect setting values
    for name, value in [("non_admin_registration_allowed", 1), ("non_admin_registration_allowed", "str"), ("non_admin_registration_allowed", [])]:
        body = {"settings": {name: value}}
        resp = await cli.put("/settings/update", json=body, headers=headers_admin_token)
        assert resp.status == 400
    

async def test_correct_update(cli, db_cursor):
    for new_value in [True, False]:
        body = {"settings": {"non_admin_registration_allowed": new_value}}
        resp = await cli.put("/settings/update", json=body, headers=headers_admin_token)
        assert resp.status == 200

        db_cursor.execute("SELECT setting_name, setting_value, is_public FROM settings WHERE setting_name = 'non_admin_registration_allowed'")
        result = db_cursor.fetchall()
        assert len(result) == 1
        assert result[0] == ("non_admin_registration_allowed", "TRUE" if new_value else "FALSE", True)


if __name__ == "__main__":
    run_pytest_tests(__file__)
