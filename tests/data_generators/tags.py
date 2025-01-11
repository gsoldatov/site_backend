from datetime import datetime, timezone


def get_test_tag(
    tag_id,
    tag_name: str | None = None,
    tag_description: str | None = None,
    is_published: bool | None = None,
    created_at: datetime | None = None,
    modified_at: datetime | None = None,
    pop_keys: list[str] = []
):
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
