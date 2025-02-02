import json
import re

from psycopg2.errors import ForeignKeyViolation

from typing import Any


class AppException(Exception):
    """
    Custom base class for application exceptions,
    which provide `msg` and `details` props used by loggers.

    `msg` is generated from casting exception to string, e.g.:
    AppException("msg text", details="details").msg -> "msg text"

    `details` can be provided as a string of JSON-serializable dict.
    """
    def __init__(self, *args, details: dict[str, Any] | str = ""):
        super().__init__(*args)
        self._details = details
    
    @property
    def msg(self) -> str:
        return super().__str__()
    
    @property
    def details(self) -> str:
        if isinstance(self._details, dict): return json.dumps(self._details)
        return self._details
    
    def __str__(self) -> str:
        return self.msg


class IncorrectCredentialsException(AppException):
    """
    Raised when a login attempts has failed.
    Required to commit login_rate_limits into the database.
    """
    pass


class ObjectsNotFound(AppException):
    """ Raised when a database operation is performed on non-existing objects. """
    pass


class ObjectIsNotComposite(AppException):
    """ Raised when a db operations expecting composite objects receives another object type(-s). """
    pass


class TagsNotFound(AppException):
    """ Raised when a database operation is performed on non-existing tags. """
    pass


class ForeignKeyViolationException(AppException):
    """
    Parses aiopg ForeignKeyViolation exception text for field and value, which caused the exception.

    NOTE: `msg` & `details` properties should be adjusted in subclasses to use data provided by this class.
    """
    def __init__(self, e: ForeignKeyViolation, *args, details: dict[Any, Any] | str = ""):
        super().__init__(str(e), *args, details=details)

        match = re.findall(r"\((.*?)\)", str(e))
        self.field = match[0]
        self.id = match[1]


class ObjectsTagsNotFound(ForeignKeyViolationException):
    """ Raised when adding objects' tags fails due to a foreign key violation. """
    @property
    def msg(self) -> str:
        return "Can't add an object tag pair containing a non-existing item."

    @property
    def details(self) -> str:
        return json.dumps({"field": self.field, "id": self.id})


class UserNotFound(ForeignKeyViolationException):
    """ Raised, when a database operation involving non-existing users is performed. """
    @property
    def msg(self) -> str:
        return "User not found."

    @property
    def details(self) -> str:
        return json.dumps({"user_id": self.id})


class RequestValidationException(Exception):
    """ Raised by additional validation checks, which complement JSONSchema validators. """
    pass


class InitDBException(Exception):
    """ Raised in `backend_main.db` module. """
    pass
