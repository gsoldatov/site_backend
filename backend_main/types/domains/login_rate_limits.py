from pydantic import BaseModel

from backend_main.types.common import Datetime
    

class LoginRateLimit(BaseModel):
    """ Login rate limit data. """
    ip_address: str
    failed_login_attempts: int
    cant_login_until: Datetime
