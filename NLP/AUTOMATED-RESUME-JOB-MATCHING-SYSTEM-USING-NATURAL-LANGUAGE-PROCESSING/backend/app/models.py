from pydantic import BaseModel
from typing import List

class JobDescription(BaseModel):
    title: str
    description: str

class MatchResponse(BaseModel):
    candidate_name: str
    match_score: float
    extracted_skills: List[str]
