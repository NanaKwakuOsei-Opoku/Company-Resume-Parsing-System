import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd

from resume_parser import (
    extract_text_from_pdf,
    extract_name,
    extract_contact_info,
    extract_experience,
    extract_skills,
    match_candidate,
    rank_candidates
)

st.title("Resume Parser & Recommendation System")

# 1. JOB REQUIREMENTS INPUT
st.header("Enter Job Requirements")
required_skills_input = st.text_input(
    "Required Skills (comma-separated)",
    value="Python, Machine Learning, SQL"
)
min_experience_input = st.number_input(
    "Minimum Years of Experience Required",
    min_value=0,
    value=2,
    step=1
)

# Default skills list used by extract_skills function
default_skills_list = ["Python", "Machine Learning", "SQL", "Data Science", "NLP", "Data Analysis"]

# Convert comma-separated string into a list of skills
required_skills = [skill.strip() for skill in required_skills_input.split(",") if skill.strip()]

job_requirements = {
    "skills": required_skills,
    "min_experience": min_experience_input
}

# OPTIONAL: Minimum Match Percentage Filtering
st.header("Filter by Minimum Match Percentage")
min_match_percentage = st.slider(
    "Minimum Match Percentage:",
    min_value=0,
    max_value=100,
    value=60,
    step=1,
    help="Only candidates with a match score equal to or greater than this percentage will be displayed."
)
# Convert percentage to fraction for internal use
min_match_threshold = min_match_percentage / 100.0

# 2. RESUME UPLOAD (Allow multiple files)
st.header("Upload Candidate Resumes")
uploaded_files = st.file_uploader("Upload Resumes (PDF)", type="pdf", accept_multiple_files=True)

if uploaded_files:
    candidates = []  # list to store candidate profiles

    # Process each uploaded resume
    for uploaded_file in uploaded_files:
        # 3. PARSE THE RESUME
        text = extract_text_from_pdf(uploaded_file)
        
        # Extract candidate details using the improved functions
        candidate_name = extract_name(text)
        contact_info = extract_contact_info(text)
        candidate_experience = extract_experience(text)
        candidate_skills = extract_skills(text, default_skills_list)
        
        # Build candidate profile
        candidate_profile = {
            "name": candidate_name,
            "contact": contact_info,
            "experience": candidate_experience,
            "skills": candidate_skills
        }
        
        # 4. MATCHING & SCORING
        match_score = match_candidate(candidate_profile, job_requirements)
        candidate_profile["match_score"] = match_score
        
        candidates.append(candidate_profile)
    
    # Rank candidates based on the match score (sorted descending)
    ranked_candidates = rank_candidates(candidates, job_requirements)
    
    # Filter candidates based on the user-specified minimum match threshold
    filtered_candidates = [c for c in ranked_candidates if c["match_score"] >= min_match_threshold]
    
    # 5. DISPLAY RESULTS AS A LEADERBOARD
    st.subheader("Candidate Leaderboard")
    
    if filtered_candidates:
        leaderboard_data = []
        for idx, candidate in enumerate(filtered_candidates, start=1):
            # Determine placement suffix (1st, 2nd, 3rd, etc.)
            if idx == 1:
                suffix = "st"
            elif idx == 2:
                suffix = "nd"
            elif idx == 3:
                suffix = "rd"
            else:
                suffix = "th"
            
            st.markdown(f"### {idx}{suffix} Place: {candidate['name']} - Match Score: {candidate['match_score']*100:.2f}%")
            st.write(f"**Contact Info:** Email - {candidate['contact']['email']}, Phone - {candidate['contact']['phone']}")
            st.write(f"**Extracted Skills:** {candidate['skills']}")
            st.write(f"**Years of Experience:** {candidate['experience']}")
            st.markdown("---")
            
            # Prepare data for the leaderboard table
            leaderboard_data.append({
                "Rank": idx,
                "Name": candidate["name"],
                "Match Score (%)": round(candidate["match_score"] * 100, 2),
                "Email": candidate["contact"]["email"],
                "Phone": candidate["contact"]["phone"],
                "Experience (Years)": candidate["experience"],
                "Skills": ", ".join(candidate["skills"])
            })
        
        # 6. DISPLAY SPREADSHEET OF RANKINGS
        st.subheader("Candidate Rankings Spreadsheet")
        df = pd.DataFrame(leaderboard_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No candidates meet the specified minimum match percentage.")
