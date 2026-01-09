import pypdf
import logging
from src.processing.extractor import extract_skills

logger = logging.getLogger(__name__)

def parse_resume_pdf(file_byte_stream):
    """
    Extracts text from a PDF file stream.
    """
    try:
        reader = pypdf.PdfReader(file_byte_stream)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        return ""

def calculate_match_score(job_skills, resume_skills):
    """
    Calculates a simple matching score (0-100) based on skill intersection.
    Jaccard Index-ish, but focused on how many job requirements are met.
    """
    if not job_skills:
        return 0
    
    # Convert lists to sets for intersection
    job_set = set(job_skills)
    resume_set = set(resume_skills)
    
    # Intersection: Skills present in both
    match_count = len(job_set.intersection(resume_set))
    
    # Score: (Matched Skills / Total Job Skills) * 100
    # Ensuring we don't divide by zero
    if len(job_set) == 0:
        return 0
        
    score = (match_count / len(job_set)) * 100
    return round(score, 1)
