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


def get_added_tag(
    tag_id: int = 1,
    tag_name: str | None = None,
    tag_description: str | None = None,
    is_published: bool | None = None,
    added_object_ids: list[int] | None = None
):
    """
    Returns tag attributes with default or custom values, sent via request to /tags/add route/
    """
    tag = get_test_tag(
        tag_id=tag_id,
        tag_name=tag_name,
        tag_description=tag_description,
        is_published=is_published,
        pop_keys=["tag_id", "created_at", "modified_at"]
    )
    tag["added_object_ids"] = added_object_ids or []
    return tag
