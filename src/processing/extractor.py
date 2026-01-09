import pandas as pd
import re
import logging
import ast

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define a dictionary of skills to look for.
# Using categories can help with analysis later.
SKILLS_DB = {
    "Languages": ["Python", "R", "SQL", "Java", "Scala", "C++", "C#", "Go", "Rust", "Julia", "SAS", "MATLAB", "JavaScript", "TypeScript"],
    "Cloud": ["AWS", "Azure", "GCP", "Google Cloud", "Amazon Web Services"],
    "Data Engineering": ["Spark", "Hadoop", "Kafka", "Airflow", "dbt", "Snowflake", "BigQuery", "Redshift", "Databricks", "Hive", "Flink"],
    "Machine Learning": ["TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost", "LightGBM", "CatBoost", "Hugging Face", "LLM", "NLP", "Computer Vision", "MLflow"],
    "Data Viz & BI": ["Tableau", "Power BI", "Looker", "Plotly", "Matplotlib", "Seaborn", "Excel"],
    "DevOps & Tools": ["Docker", "Kubernetes", "Git", "GitHub", "GitLab", "Jenkins", "Linux", "Bash", "Jira"]
}

# Flatten the list for regex generation, but keep map for categorization if needed
ALL_SKILLS = [skill for category in SKILLS_DB.values() for skill in category]

def extract_skills(text):
    """
    Extracts skills from text using regex boundaries to ensure exact matches.
    (e.g., prevents matching 'Go' in 'Good')
    """
    if not isinstance(text, str):
        return []
    
    found_skills = set()
    
    # Pre-process text slightly
    text_lower = text.lower()
    
    # Iterate through all skills
    for category, skills in SKILLS_DB.items():
        for skill in skills:
            # Create regex pattern for the skill
            # \b ensures word boundaries. 
            # re.escape is safer for terms like C++
            pattern = re.compile(r'\b' + re.escape(skill.lower()) + r'\b')
            
            # Special handling for C++ or C# which might have issues with word boundaries
            if skill.lower() in ['c++', 'c#']:
                pattern = re.compile(re.escape(skill.lower()))
                
            if pattern.search(text_lower):
                found_skills.add(skill) # Add the original case name
                
    return list(found_skills)

def process_data(input_file="data/raw/jobs.csv", output_file="data/processed/jobs_with_skills.csv"):
    try:
        logger.info(f"Loading data from {input_file}...")
        df = pd.read_csv(input_file)
        
        if 'description' not in df.columns:
            logger.error("Column 'description' not found in input data.")
            return

        logger.info("Extracting skills from job descriptions...")
        # Apply extraction
        df['skills'] = df['description'].apply(extract_skills)
        df['skill_count'] = df['skills'].apply(len)
        
        # Save processed data
        # Check if output directory exists
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        df.to_csv(output_file, index=False)
        logger.info(f"Processed data saved to {output_file}. Sample:")
        print(df[['title', 'skills']].head())
        
    except FileNotFoundError:
        logger.error(f"Input file {input_file} not found. Run the scraper first!")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    process_data()
