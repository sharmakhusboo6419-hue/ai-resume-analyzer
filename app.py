import streamlit as st
import google.generativeai as genai
import os
from pypdf import PdfReader
import matplotlib.pyplot as plt

# Hardcode your API key right here inside the Python file:
# This tells your code to look into a secure vault instead of reading raw text
part1 = "AIzaSy"
part2 = "PASTE_THE_MIDDLE_PART_OF_YOUR_KEY_HERE"
part3 = "PASTE_THE_REST_OF_YOUR_KEY_HERE"

API_KEY = st.secrets.get("AQAb8RN6IXJeO48VqhVgBEqSbajmdTWPVj6tWz6mDDLjH2bW5Ziw")

# 2. If it's not there, check inside a [secrets] table section
if not API_KEY and "secrets" in st.secrets:
    API_KEY = st.secrets["secrets"].get("API_KEY")

# 3. If it's still not there, look for a lowercase version just in case
if not API_KEY:
    API_KEY = st.secrets.get("AQAb8RN6IXJeO48VqhVgBEqSbajmdTWPVj6tWz6mDDLjH2bW5Ziw")

# Now check if we found it anywhere
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("🔑 Streamlit cannot find 'API_KEY' inside your Secrets settings tab. Please check your dashboard settings!")

# Extract text from PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Keyword match %
def keyword_match(resume_text, keywords):
    resume_text_lower = resume_text.lower()
    matched = [kw for kw in keywords if kw.lower() in resume_text_lower]
    score = (len(matched) / len(keywords)) * 100 if keywords else 0
    return matched, score

# Weighted ATS scoring rubric
def ats_score(resume_text, keywords):
    matched, keyword_score = keyword_match(resume_text, keywords)
    
    # Heuristic scoring
    skills_score = keyword_score                                     # % of keywords matched
    experience_score = min(100, len(resume_text.split())/15)  # proxy: resume length
    education_score = 80 if "mba" in resume_text.lower() or "bachelor" in resume_text.lower() else 50
    formatting_score = 90 if "-" in resume_text or "•" in resume_text else 70
    
    # Weighted rubric (adjust weights as needed)
    final_score = (skills_score * 0.4 +
                   experience_score * 0.3 +
                   education_score * 0.2 +
                   formatting_score * 0.1)
    
    return matched, skills_score, experience_score, education_score, formatting_score, final_score

# AI analysis using Gemini
def analyze_resume(resume_text, target_role):
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Analyze this resume for the role of {target_role}. 
    Provide feedback on strengths, gaps, and recommendations.
    
    Resume Text:
    {resume_text}
    
    Provide output in this structure:
    1. Overall Summary
    2. Skills & Competencies
    3. Experience Evaluation
    4. Education & Certifications
    5. ATS & Keyword Optimization
    6. Formatting & Presentation
    7. Final Recommendations
    """
    response = model.generate_content(prompt)
    return response.text
# Streamlit UI
st.title("📄 AI Resume Analyzer Dashboard")

uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
target_role = st.text_input("Target Role (e.g., Investment Banking Analyst)")
keywords_input = st.text_area("Enter target role keywords (comma-separated)", 
                              "DCF, WACC, Valuation, Financial Modeling, Bloomberg, Excel, SQL")

if uploaded_file and target_role:
    if uploaded_file.type == "application/pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    else:
        resume_text = uploaded_file.read().decode("utf-8")
    
    keywords = [kw.strip() for kw in keywords_input.split(",")]
    matched, skills_score, exp_score, edu_score, fmt_score, final_score = ats_score(resume_text, keywords)
    
    # Dashboard metrics
    st.subheader("📊 ATS Dashboard")
    st.metric("Skills Match", f"{skills_score:.1f}%")
    st.metric("Experience Score", f"{exp_score:.1f}/100")
    st.metric("Education Score", f"{edu_score:.1f}/100")
    st.metric("Formatting Score", f"{fmt_score:.1f}/100")
    st.metric("Final ATS Score", f"{final_score:.1f}/100")
    st.write("Matched Keywords:", ", ".join(matched))
    
    # Chart visualization
    fig, ax = plt.subplots()
    categories = ["Skills", "Experience", "Education", "Formatting", "Final ATS"]
    scores = [skills_score, exp_score, edu_score, fmt_score, final_score]
    ax.bar(categories, scores, color=["blue", "orange", "green", "purple", "red"])
    ax.set_ylim(0, 100)
    st.pyplot(fig)
    
    # AI Analysis
    st.subheader("🤖 AI Resume Analysis")
    analysis = analyze_resume(resume_text, target_role)
    st.write(analysis)
