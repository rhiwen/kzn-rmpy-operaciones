# app/schemas.py
from pydantic import BaseModel

class EmailRequest(BaseModel):
    send_email: bool = True