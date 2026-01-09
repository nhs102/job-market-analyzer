import streamlit as st
import pandas as pd
import plotly.express as px
import ast
import os
import sys

# 프로젝트 루트 경로를 sys.path에 추가하여 모듈 인식 문제 해결
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.processing.matcher import parse_resume_pdf, calculate_match_score, extract_skills

st.set_page_config(page_title="Job Market Analyzer", layout="wide")

st.title("📊 Job Market Trends Analyzer")
st.markdown("Monitor job market trends, top skills, and salary distributions.")

sidebar = st.sidebar
sidebar.header("Filter Options")

# Load Data
DATA_PATH = "data/processed/jobs_with_skills.csv"

@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        return None
    df = pd.read_csv(DATA_PATH)
    # Convert string representation of list to actual list
    if 'skills' in df.columns:
        df['skills'] = df['skills'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
    return df

df = load_data()

# --- Resume Upload Section ---
sidebar.markdown("---")
sidebar.header("📄 Resume Matcher")
uploaded_file = sidebar.file_uploader("Upload your Resume (PDF)", type=['pdf'])

user_skills = []
if uploaded_file is not None:
    # 1. Parse Resume
    resume_text = parse_resume_pdf(uploaded_file)
    # 2. Extract Skills
    user_skills = extract_skills(resume_text)
    
    sidebar.success(f"Extracted {len(user_skills)} skills!")
    with sidebar.expander("View Your Skills"):
        st.write(user_skills)

if df is None:
    st.error("Processed data not found! Please run the scraper and processor first.")
    st.code("python src/ingestion/scraper.py\npython src/processing/extractor.py", language="bash")
else:
    # Calculate Match Score if resume is uploaded
    if user_skills:
        df['match_score'] = df['skills'].apply(lambda job_skills: calculate_match_score(job_skills, user_skills))
        # Sort by match score
        df = df.sort_values(by='match_score', ascending=False)
    else:
        df['match_score'] = 0

    # Sidebar Filters
    all_roles = df['title'].unique() if 'title' in df.columns else []
    
    roles_filter = ["Data Scientist", "Data Engineer", "Analyst", "All"]
    selected_role_type = sidebar.selectbox("Select Role Type", roles_filter, index=3) # Default All

    filtered_df = df.copy()
    if selected_role_type != "All":
        filtered_df = filtered_df[filtered_df['title'].str.contains(selected_role_type, case=False, na=False)]

    st.metric(label="Total Jobs Analyzed", value=len(filtered_df))

    # --- Match Results View ---
    if user_skills:
        st.subheader("🎯 Top Matched Jobs for You")
        
        for i, row in filtered_df.head(5).iterrows():
            with st.expander(f"{row['match_score']}% Match: {row['title']} @ {row['company']}"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.write(f"**Location:** {row['location']}")
                    st.write(f"**Score:** {row['match_score']}/100")
                    st.markdown(f"[Apply Link]({row['link']})")
                with col2:
                    # Visualizing missing vs matched skills
                    job_skills = set(row['skills'])
                    my_skills = set(user_skills)
                    
                    matched = job_skills.intersection(my_skills)
                    missing = job_skills.difference(my_skills)
                    
                    st.write("**✅ Matched Skills:**")
                    st.info(", ".join(matched) if matched else "None")
                    
                    st.write("**❌ Missing Skills:**")
                    st.warning(", ".join(missing) if missing else "None")

    # --- Skill Analysis ---
    st.divider()
    st.subheader(f"🔥 Top Skills in Demand ({selected_role_type})")

    
    if not filtered_df.empty:
        # Flatten the list of skills
        all_skills = [skill for skills_list in filtered_df['skills'] for skill in skills_list]
        skill_counts = pd.Series(all_skills).value_counts().reset_index()
        skill_counts.columns = ['Skill', 'Count']
        
        # Display Bar Chart
        if not skill_counts.empty:
            fig = px.bar(skill_counts.head(15), x='Skill', y='Count', 
                         title=f"Most In-Demand Skills for {selected_role_type}",
                         color='Count', color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
            
            # Show Data Table
            with st.expander("See Raw Data"):
                st.dataframe(filtered_df[['title', 'company', 'location', 'skills', 'link']])
        else:
            st.warning("No skills extracted from the current data. Check the extractor logic or data quality.")
    else:
        st.info("No jobs found for the selected filter.")

