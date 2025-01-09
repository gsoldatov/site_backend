import re

from psycopg2.errors import ForeignKeyViolation


class IncorrectCredentialsException(Exception):
    """
    Raised when a login attempts has failed.
    Required to commit login_rate_limits into the database.
    """
    pass


class ObjectsTagsNotFound(Exception):
    """
    Raised when adding objects' tags fails due to a foreign key violation
    """
    def __init__(self, e: ForeignKeyViolation):
        super().__init__(str(e))

        match = re.findall(r"\((.*?)\)", str(e))
        self.field = match[0]
        self.id = match[1]    

    def __str__(self) -> str:
        return f"Could not add objects tags: {self.field} = {self.id} not found."


class TagNotFound(Exception):
    """
    Raised when a database operation is performed on a non-existing tag.
    """
    pass
