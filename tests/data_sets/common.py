from tests.data_generators.objects import get_object_attrs, get_test_object_data
from tests.data_generators.searchables import get_test_searchable
from tests.data_generators.sessions import get_test_session
from tests.data_generators.tags import get_test_tag
from tests.data_generators.users import get_test_user

from tests.db_operations.objects import insert_objects, insert_links
from tests.db_operations.searchables import insert_searchables
from tests.db_operations.sessions import insert_sessions
from tests.db_operations.tags import insert_tags
from tests.db_operations.users import insert_users


def insert_data_for_successful_requests(db_cursor):
    """ Inserts a dataset, which is required to successfully send a request to each of app's routes. """
    obj_list = [get_object_attrs(object_id=i, object_type="link") for i in range(100, 102)]
    obj_list.append(get_object_attrs(99999, object_type="composite"))
    l_list = [get_test_object_data(i, object_type="link") for i in range(100, 102)]
    insert_objects(obj_list, db_cursor)
    insert_links(l_list, db_cursor)

    tag_list = [get_test_tag(i) for i in range(100, 102)]
    insert_tags(tag_list, db_cursor)

    insert_searchables([get_test_searchable(object_id=101, text_a="word")], db_cursor)

    insert_users([get_test_user(999, pop_keys=["password_repeat"])], db_cursor)
    insert_sessions([get_test_session(999, access_token=logging_out_user_access_token)], db_cursor)


logging_out_user_access_token = "second_user_access_token"
headers_logging_out_user_token = {"Authorization": f"Bearer {logging_out_user_access_token}"}
