from pydantic import BaseModel

from backend_main.types.common import PositiveInt, Datetime
    

class Session(BaseModel):
    """ User session data. """
    user_id: PositiveInt
    access_token: str
    expiration_time: Datetime
