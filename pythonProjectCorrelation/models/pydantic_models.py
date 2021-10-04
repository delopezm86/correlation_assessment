from pydantic import BaseModel

class PyCandidate(BaseModel):
    first_name: str
    last_name: str
    email: str

class PyStartAssessment(BaseModel):
    candidate_id: int

class PyGetQuestion(BaseModel):
    unique_session_id: str