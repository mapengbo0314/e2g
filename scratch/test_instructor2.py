import instructor
from google import genai
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

client = genai.Client() # needs auth, so I'll just see if it compiles
try:
    instructor_client = instructor.from_gemini(client, mode=instructor.Mode.GEMINI_JSON)
    print("from_gemini success")
except Exception as e:
    print(f"from_gemini failed: {e}")
