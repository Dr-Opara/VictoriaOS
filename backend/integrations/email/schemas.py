from pydantic import BaseModel

class EmailRequest(BaseModel):
    recipient: str
    subject: str
    body: str