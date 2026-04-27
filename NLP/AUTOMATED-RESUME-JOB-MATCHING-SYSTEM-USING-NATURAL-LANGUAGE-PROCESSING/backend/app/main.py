from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from .models import MatchResponse, JobDescription
from .nlp.extractor import extract_text
from .nlp.preprocessor import extract_skills, extract_name
from .nlp.matcher import calculate_match
from .evaluation import run_full_evaluation

app = FastAPI(title="Resume-Job Matching API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Resume-Job Matching API"}

@app.get("/metrics")
def get_metrics(threshold: float = Query(50.0, description="Score threshold for match classification")):
    """Run full evaluation pipeline and return all metrics."""
    return run_full_evaluation(threshold=threshold)

@app.post("/match", response_model=List[MatchResponse])
async def match_resumes(
    job_description: str = Form(...),
    files: List[UploadFile] = File(...)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    
    for file in files:
        # 1. Extract text from the resume
        text = await extract_text(file)
        if not text:
            continue
            
        # 2. Extract skills from text
        skills = extract_skills(text)
        
        # 3. Calculate semantic match
        score = calculate_match(text, job_description)
        
        # 4. Extract Name
        extracted_name = extract_name(text)
        candidate_name = extracted_name if extracted_name else file.filename
        
        # Build response
        results.append(MatchResponse(
            candidate_name=candidate_name,
            match_score=score,
            extracted_skills=skills
        ))
        
    # Sort results by match score descending
    results.sort(key=lambda x: x.match_score, reverse=True)
    return results
