import os
import instructor
from pydantic import BaseModel
from google import genai

class User(BaseModel):
    name: str
    age: int

# We need a client. We can use a mock or see what it does.
# But we can just inspect the instructor source or try to mock it.
