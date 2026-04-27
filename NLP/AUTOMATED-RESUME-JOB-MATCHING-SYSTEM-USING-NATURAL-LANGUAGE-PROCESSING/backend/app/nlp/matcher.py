from sentence_transformers import SentenceTransformer, util
import torch

# Load the model
# all-MiniLM-L6-v2 is a great balance of size and performance
model = None

def get_model():
    global model
    if model is None:
        # NOTE: Depending on your environment, you might want to specify device='cpu' or device='cuda'
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
    return model

def calculate_match(resume_text: str, job_description: str) -> float:
    """
    Calculate the semantic similarity score between a resume and a job description.
    Returns a percentage (0 to 100).
    """
    transformer = get_model()
    
    # Encode the sentences to get embeddings
    embeddings1 = transformer.encode(resume_text, convert_to_tensor=True)
    embeddings2 = transformer.encode(job_description, convert_to_tensor=True)
    
    # Compute cosine similarity
    cosine_scores = util.cos_sim(embeddings1, embeddings2)
    
    # Convert tensor scalar to float and calculate percentage
    score_val = cosine_scores.item()
    
    # Ensure it's between 0 and 1
    score_val = max(0.0, min(1.0, score_val))
    
    return round(score_val * 100, 2)
