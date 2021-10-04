from pydantic import BaseModel
from typing import List

class PyCandidate(BaseModel):
    first_name: str
    last_name: str
    email: str

class PyStartAssessment(BaseModel):
    candidate_id: int

class PyExercise(BaseModel):
    exercise_id: int

class PySession(BaseModel):
    unique_session_id: str
    answers: List[PyExercise] = []
    text_response: str = ''
