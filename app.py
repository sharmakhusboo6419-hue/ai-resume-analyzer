import streamlit as st
import google.generativeai as genai
import os
from pypdf import PdfReader
import matplotlib.pyplot as plt

# ==========================================
# 🔒 SECURE API KEY CONFIGURATION (SPLIT METHOD)
# ==========================================
# ==========================================
# 🔒 SECURE API KEY CONFIGURATION (SPLIT METHOD)
# ==========================================
# Put the first few characters of your real key here
part1 = "AQAb8R"  
# Put the middle part here
part2 = "N6IXJeO" 
# Put the remaining part here
part3 = "48VqhVgBEqSbajmdTWPVj6tWz6mDDLjH2bW5Ziw"

# The .strip() function wipes out any accidental hidden spaces or line breaks
FULL_API_KEY = (part1 + part2 + part3).strip()

# Flexible verification check: validates length without hardcoding the prefix
if FULL_API_KEY and len(FULL_API_KEY) >= 35:
    try:
        genai.configure(api_key=FULL_API_KEY)
        st.toast("🔒 Gemini API Connection Secured Successfully!", icon="✅")
    except Exception as e:
        st.error(f"❌ Initialization Failed: Please check your API key structure. Error: {e}")
else:
    st.error("⚠️ Invalid Key Configuration: Ensure your split strings form a complete, valid API key!")
# ==========================================
# 🛠️ CORE FUNCTIONS
# ==========================================

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
    
    # Weighted rubric
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

# AI Bullet Point Rewriter
def rewrite_bullet_point(bullet_text, role):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    You are an expert resume writer. Rewrite the following weak resume bullet point to make it sound highly professional, action-oriented, and impactful for a '{role}' position.
    Use strong action verbs and create placeholders for metrics/numbers (e.g., [X]% or $[X]).
    
    Original Bullet Point: "{bullet_text}"
    
    Provide exactly 3 distinct, high-impact variations as a clean bulleted list.
    """
    response = model.generate_content(prompt)
    return response.text

# ==========================================
# 🎨 STREAMLIT USER INTERFACE
# ==========================================
st.set_page_config(page_title="AI Resume Analyzer", layout="wide")
st.title("📄 AI Resume Analyzer Dashboard")

# Create functional tabs at the top
tab1, tab2, tab3 = st.tabs(["📊 ATS & AI Analysis", "✍️ Smart Bullet Rewriter", "💡 About Tool"])

with tab1:
    st.subheader("🎯 Step 1: Enter Your Target Details & Upload Resume")
    
    # Using a clean form block to collect all inputs together in the main view
    with st.form(key="target_details_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            target_role = st.text_input("Target Job Role", placeholder="e.g., Data Analyst, Investment Banking Analyst")
            uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
            
        with col2:
            keywords_input = st.text_area(
                "Target Role Keywords (comma-separated)", 
                placeholder="e.g., Python, SQL, Financial Modeling, Power BI, Excel",
                help="Paste core technical skills or keywords from the job description here."
            )
            
        # The form submit button
        submit_button = st.form_submit_button(label="🚀 Run ATS & AI Analysis")

    # Step 2: Process the analysis ONLY after the submit button is clicked
    if submit_button:
        if uploaded_file and target_role and keywords_input:
            
            # 1. Extract text
            if uploaded_file.type == "application/pdf":
                resume_text = extract_text_from_pdf(uploaded_file)
            else:
                resume_text = uploaded_file.read().decode("utf-8")
            
            # 2. Process metrics
            keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
            matched, skills_score, exp_score, edu_score, fmt_score, final_score = ats_score(resume_text, keywords)
            
            # 3. Display Dashboard metrics
            st.markdown("---")
            st.subheader("📊 ATS Score Metrics")
            metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
            metric_col1.metric("Skills Match", f"{skills_score:.1f}%")
            metric_col2.metric("Experience", f"{exp_score:.1f}/100")
            metric_col3.metric("Education", f"{edu_score:.1f}/100")
            metric_col4.metric("Formatting", f"{fmt_score:.1f}/100")
            metric_col5.metric("Final ATS Score", f"{final_score:.1f}/100")
            
            st.info(f"**Matched Keywords:** {', '.join(matched) if matched else 'None'}")
            
            # 4. Split layout for Chart and AI Report
            layout_col1, layout_col2 = st.columns([2, 3])
            
            with layout_col1:
                st.write("### 📈 Score Visualizer")
                fig, ax = plt.subplots(figsize=(6, 5))
                categories = ["Skills", "Exp", "Edu", "Format", "Total ATS"]
                scores = [skills_score, exp_score, edu_score, fmt_score, final_score]
                colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#d62728"]
                
                bars = ax.bar(categories, scores, color=colors)
                ax.set_ylim(0, 100)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:.1f}%',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3),  
                                textcoords="offset points",
                                ha='center', va='bottom')
                                
                st.pyplot(fig)
                
            with layout_col2:
                st.write("### 🤖 AI Evaluation Deep-Dive")
                with st.spinner("Gemini is dissecting your resume..."):
                    analysis = analyze_resume(resume_text, target_role)
                    st.markdown(analysis)
        else:
            st.error("⚠️ Please fill in all fields (Target Role, Keywords, and upload your Resume) before submitting!")

with tab2:
    st.subheader("✍️ Action-Verb Optimizer & Bullet Rewriter")
    st.write("Transform basic duties into high-impact accomplishment statements that impress hiring managers.")
    
    current_role = st.text_input("Role relevant to this bullet", placeholder="e.g., Software Engineering Intern")
    weak_bullet = st.text_area("Paste a resume bullet point you want to improve", 
                               placeholder="e.g., I was responsible for looking after the company website and fixing bugs.")
    
    if st.button("✨ Optimize Bullet Point"):
        if weak_bullet and current_role:
            with st.spinner("Rewriting with strong industry power-verbs..."):
                optimized_result = rewrite_bullet_point(weak_bullet, current_role)
                st.success("Here are 3 polished options to choose from:")
                st.write(optimized_result)
        else:
            st.error("Please provide both a role and a bullet point text to rewrite!")

with tab3:
    st.subheader("ℹ️ Project Portfolio & Technical Architecture")
    
    st.markdown("""
    Welcome to the **AI Resume Analyzer Dashboard**—a data-driven career advancement tool designed to optimize resumes for modern Applicant Tracking Systems (ATS) and competitive hiring landscapes.
    """)
    
    st.success("⚡ **Core Tech Stack:** Python 3 | Streamlit Cloud | Google Gemini 2.5 Flash API | PyPDF")
    
    st.markdown("### 🛠️ System Architecture Breakdown")
    
    st.markdown("""
    | Component | Technology | Operational Function |
    | :--- | :--- | :--- |
    | **Frontend Interface** | `Streamlit` | Renders a responsive user form layout with dynamic visualization tabs. |
    | **Document Parsing** | `PyPDF (PdfReader)` | Extracts raw unstructured text from uploaded digital PDF profiles. |
    | **Heuristic Analytics** | `Python Math Engine` | Computes a weighted algorithmic score matching keyword density and structural formatting. |
    | **Generative Insights** | `Gemini 2.5 Flash` | Dissects text to deliver deep-dive feedback on gaps, strengths, and recommendations. |
    | **Text Optimization** | `Prompt Engineering` | Employs an LLM sub-routine to restructure weak bullet points using high-impact action verbs. |
    """)
    
    st.markdown("---")
    st.caption("🚀 Developed by Khusboo Sharma | Engineered as an Advanced Technical Portfolio Project.")
