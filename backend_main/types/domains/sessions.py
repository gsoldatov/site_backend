from pydantic import BaseModel

from backend_main.validation.types import PositiveInt, Datetime
    

class Session(BaseModel):
    """ User session data. """
    user_id: PositiveInt
    access_token: str
    expiration_time: Datetime
