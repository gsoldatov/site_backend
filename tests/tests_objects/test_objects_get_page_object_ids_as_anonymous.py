from copy import deepcopy

if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..", "..")))
    from tests.util import run_pytest_tests

from tests.fixtures.objects import insert_data_for_view_objects_as_anonymous


pagination_info = {
    "pagination_info": {
        "page": 1, 
        "items_per_page": 2, 
        "order_by": "object_name", 
        "sort_order": "asc", 
        "filter_text": "", 
        "object_types": ["link"], 
        "tags_filter": [],
        "show_only_displayed_in_feed": False
}}
required_attributes = ("page", "items_per_page", "order_by", "sort_order")


async def test_correct_request(cli, db_cursor):
    insert_data_for_view_objects_as_anonymous(cli, db_cursor)
    expected_object_ids = [i for i in range(1, 11) if i % 2 == 0]

    # Get all objects on one page (and receive only published)
    pi = deepcopy(pagination_info)
    pi["pagination_info"]["items_per_page"] = 10
    resp = await cli.post("/objects/get_page_object_ids", json=pi)
    assert resp.status == 200
    data = await resp.json()
    assert data["pagination_info"]["total_items"] == len(expected_object_ids)
    assert sorted(data["pagination_info"]["object_ids"]) == expected_object_ids
    

if __name__ == "__main__":
    run_pytest_tests(__file__)
