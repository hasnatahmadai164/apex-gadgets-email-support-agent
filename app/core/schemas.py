from pydantic import BaseModel


class EmailMessage(BaseModel):
    sender: str
    subject: str
    body: str
