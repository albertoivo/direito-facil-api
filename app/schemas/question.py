from pydantic import BaseModel


class Question(BaseModel):
    text: str
    category: str = None
