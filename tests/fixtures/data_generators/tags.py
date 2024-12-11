from datetime import datetime, timezone


def get_test_tag(tag_id, tag_name = None, tag_description = None, is_published = None, created_at = None, modified_at = None, pop_keys = []):
    """
    Returns a new dictionary for tags table with attributes specified in pop_keys popped from it.
    """
    curr_time = datetime.now(tz=timezone.utc)

    tag = {
        "tag_id": tag_id,
        "created_at": created_at if created_at is not None else curr_time,
        "modified_at": modified_at if modified_at is not None else curr_time,
        "tag_name": tag_name if tag_name is not None else f"Tag name {tag_id}",
        "tag_description": tag_description if tag_description is not None else f"Tag description {tag_id}",
        "is_published": is_published if is_published is not None else True
    }

    for k in pop_keys:
        tag.pop(k, None)
    
    return tag
