from pydantic import BaseModel

class Announcement(BaseModel):
    message: str

    