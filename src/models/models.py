from pydantic import BaseModel

class Conversation(BaseModel):
    user: str
    question: str
    answer: str