import streamlit as st
import spacy
import pandas as pd
from pdfminer.high_level import extract_text as extract_pdf_text
import docx2txt
import re
from collections import Counter
from fpdf import FPDF
import base64
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="ResuMate AI | Your Career Partner", page_icon="🚀", layout="wide")

# Load NLP Model
@st.cache_resource
def load_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except:
        import os
        os.system("python -m spacy download en_core_web_sm")
        return spacy.load("en_core_web_sm")

nlp = load_nlp()

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Hero Section */
    .hero {
        padding: 3rem 1rem;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    .hero h1 {
        font-size: 3.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(#8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    /* Cards */
    .st-emotion-cache-1r6slb0 {
        background-color: #1e293b !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }
    
    .score-card {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
        padding: 2.5rem;
        border-radius: 24px;
        border: 1px solid rgba(139, 92, 246, 0.3);
        text-align: center;
        margin: 1rem 0;
    }
    
    .score-value {
        font-size: 5rem;
        font-weight: 900;
        color: #f8fafc;
        margin: 0;
        line-height: 1;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    
    /* Inputs */
    .stTextArea textarea {
        background-color: #0f172a !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
    }
    
    /* Sidebar */
    .sidebar-content {
        background-color: #1e293b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- UTILS ---
def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith('.pdf'):
        try:
            return extract_pdf_text(uploaded_file)
        except:
            return "Error extracting PDF text"
    elif uploaded_file.name.endswith('.docx'):
        try:
            return docx2txt.process(uploaded_file)
        except:
            return "Error extracting DOCX text"
    return ""

def get_keywords(text):
    """
    Extracts key technical and soft skills from a text using SpaCy NLP.
    Returns a dictionary of skills grouped by category.
    """
    # Grouped skills for better analysis
    SKILLS_CATEGORIES = {
        "Languages": {"python", "javascript", "java", "c++", "sql", "typescript", "rust", "go", "html", "css"},
        "Frameworks": {"react", "node.js", "angular", "vue", "django", "flask", "pytorch", "tensorflow", "spring", "express"},
        "Tools & Cloud": {"docker", "kubernetes", "aws", "azure", "git", "linux", "terraform", "jenkins", "nosql", "mongodb", "postgresql", "rest api", "graphql", "devops", "cicd", "blockchain", "cybersecurity"},
        "Data & AI": {"machine learning", "data science", "pandas", "numpy", "scikit-learn", "tableau", "power bi"},
        "Soft Skills": {"agile", "scrum", "project management", "ui/ux", "figma", "communication", "leadership", "problem solving", "teamwork", "analytical", "critical thinking", "time management"}
    }
    
    # Process text
    text_lower = text.lower()
    doc = nlp(text_lower)
    
    results = {cat: [] for cat in SKILLS_CATEGORIES}
    found_any = set()

    # 1. POS Tagging Method: Extract nouns and proper nouns
    for token in doc:
        if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
            clean_text = token.text.strip().lower()
            if len(clean_text) > 2:
                # Check which category it belongs to
                for cat, skills in SKILLS_CATEGORIES.items():
                    if clean_text in skills and clean_text not in found_any:
                        results[cat].append(clean_text)
                        found_any.add(clean_text)
    
    # 2. Phrase Matching Method (for multi-word or exact matches)
    for cat, skills in SKILLS_CATEGORIES.items():
        for skill in skills:
            if skill not in found_any:
                if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                    results[cat].append(skill)
                    found_any.add(skill)
            
    return results

class PDF(FPDF):
    def header(self):
        pass
    def footer(self):
        pass

def generate_resume_pdf(data, accent_color, layout_style="Modern"):
    pdf = PDF()
    pdf.add_page()
    
    # Convert hex to RGB
    h = accent_color.lstrip('#')
    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    # Header
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(15, 23, 42)
    
    align = 'C' if layout_style == "Modern" else 'L'
    
    pdf.cell(0, 15, data['name'].upper(), ln=True, align=align)
    
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(100, 116, 139)
    contact_info = f"{data['email']} | {data['phone']} | {data['location']}"
    pdf.cell(0, 5, contact_info, ln=True, align=align)
    if data['linkedin']:
        pdf.cell(0, 5, data['linkedin'], ln=True, align=align)
    
    pdf.ln(10)
    
    # Sections
    def add_section(title, content):
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(rgb[0], rgb[1], rgb[2]) 
        pdf.cell(0, 10, title.upper(), ln=True)
        pdf.set_draw_color(226, 232, 240)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + (190 if layout_style == "Modern" else 80), pdf.get_y())
        pdf.ln(2)
        
        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(30, 41, 59)
        pdf.multi_cell(0, 6, content)
        pdf.ln(5)

    if data['summary']:
        add_section("Professional Summary", data['summary'])
    
    if data['education']:
        add_section("Education", data['education'])
        
    if data['experience']:
        add_section("Experience", data['experience'])
        
    if data['skills']:
        add_section("Skills", data['skills'])
        
    if data['projects']:
        add_section("Projects", data['projects'])

    return pdf.output(dest='S')

# --- SIDEBAR NAV ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135691.png", width=100)
    st.title("ResuMate AI")
    st.markdown("---")
    page = st.radio("Navigation", ["Home", "Analyzer", "Resume Builder", "Interview Prep"])
    st.markdown("---")
    st.info("Built for students to land their dream jobs 🚀")

# --- PAGES ---
if page == "Home":
    st.markdown("""
        <div class="hero">
            <h1>Elevate Your Career with AI</h1>
            <p style="font-size: 1.2rem; color: #94a3b8;">
                Optimized Resumes. Smart Analysis. Perfect Matches.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📊 ATS Scoring")
        st.write("Find out how well your resume matches the job description and beat the bots.")
        
    with col2:
        st.markdown("### 🛠️ Builder")
        st.write("Create a professional, ATS-friendly resume from scratch in minutes.")
        
    with col3:
        st.markdown("### 💡 AI Insights")
        st.write("Get suggestions for missing keywords and better phrasing for your experience.")

    st.markdown("---")
    
    st.markdown("## 💡 Career Growth Tips for Students")
    tip_col1, tip_col2 = st.columns(2)
    
    with tip_col1:
        with st.expander("📝 Resume Writing 101", expanded=True):
            st.write("""
            - **Quantify your impact:** Instead of 'Built project', use 'Built project that served 100+ users'.
            - **Tailor for ATS:** Use technical keywords from the job description naturally.
            - **Keep it clean:** Use a professional single-column layout for better readability.
            """)
            
    with tip_col2:
        with st.expander("🎯 Interview Preparation", expanded=True):
            st.write("""
            - **STAR Method:** Explain situations, tasks, actions, and results clearly.
            - **Research the company:** Know their core products and recent news.
            - **Ask great questions:** Shows you are curious and proactive.
            """)

    st.markdown("---")
    st.markdown("### 🚀 How to start?")
    st.info("""
    1. **Analyze:** Go to the **Analyzer** tab to check your current resume's match score against a job.
    2. **Refine:** Use the missing keywords suggested by our AI to improve your content.
    3. **Build:** Use the **Resume Builder** to generate a fresh, clean, ATS-optimized PDF resume.
    """)

elif page == "Analyzer":
    st.title("Resume Matcher & Optimizer 📊")
    st.write("Upload your resume and paste the job description to see your match score.")
    
    if st.button("📝 Load Sample Job & Resume"):
        st.session_state['jd_sample'] = "Seeking a Full-Stack Python Developer with experience in Django, React, and AWS. Must be familiar with Docker and SQL."
        st.session_state['resume_trigger'] = True
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("#### 1. Target Job Description")
        jd_text = st.text_area("Paste the text here...", height=250, 
                             value=st.session_state.get('jd_sample', ""),
                             placeholder="e.g. Seeking a Python Developer with experience in Django...")
        
    with col_b:
        st.markdown("#### 2. Your Resume")
        uploaded_file = st.file_uploader("Upload PDF or DOCX", type=['pdf', 'docx'])
        if st.session_state.get('resume_trigger'):
            st.info("Sample Job loaded! Since file uploads are secure, please upload any PDF/DOCX to see the matching logic in action.")
        
    if st.button("Calculate Match Score"):
        if jd_text and uploaded_file:
            with st.spinner("Processing documents..."):
                resume_text = extract_text_from_file(uploaded_file)
                
                if "Error" in resume_text:
                    st.error(resume_text)
                else:
                    jd_results = get_keywords(jd_text)
                    resume_results = get_keywords(resume_text)
                    
                    found_dict = {}
                    missing_dict = {}
                    
                    all_jd_keywords = []
                    all_res_keywords = []
                    
                    for cat in jd_results:
                        f = set(jd_results[cat]).intersection(set(resume_results[cat]))
                        m = set(jd_results[cat]).difference(set(resume_results[cat]))
                        
                        if f: found_dict[cat] = sorted(list(f))
                        if m: missing_dict[cat] = sorted(list(m))
                        
                        all_jd_keywords.extend(jd_results[cat])
                        all_res_keywords.extend(resume_results[cat])
                    
                    total_jd = len(all_jd_keywords)
                    total_found = len(set(all_jd_keywords).intersection(set(all_res_keywords)))
                    
                    score = round((total_found / total_jd) * 100) if total_jd > 0 else 0
                    
                    st.markdown(f"""
                        <div class="score-card">
                            <p style="margin: 0; color: #94a3b8; font-weight: 600;">MATCH SCORE</p>
                            <h1 class="score-value">{score}%</h1>
                            <p style="margin-top: 0.5rem; color: #8b5cf6;">{"Great match!" if score > 70 else "Needs some improvement" if score > 40 else "Low match - try adding more keywords"}</p>
                        </div>
                    """, unsafe_allow_html=True)

                    # --- VISUALIZATION ---
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = score,
                        title = {'text': "Matching Accuracy"},
                        gauge = {
                            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                            'bar': {'color': "#8b5cf6"},
                            'bgcolor': "rgba(0,0,0,0)",
                            'borderwidth': 2,
                            'bordercolor': "gray",
                            'steps': [
                                {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.1)'},
                                {'range': [40, 70], 'color': 'rgba(234, 179, 8, 0.1)'},
                                {'range': [70, 100], 'color': 'rgba(34, 197, 94, 0.1)'}
                            ],
                        }
                    ))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Inter"}, height=300)
                    st.plotly_chart(fig, use_container_width=True)

                    # --- SKILLS GAP CHART ---
                    gap_data = pd.DataFrame({
                        "Category": ["Matched", "Missing"],
                        "Count": [total_found, total_jd - total_found],
                        "Color": ["#22c55e", "#ef4444"]
                    })
                    
                    fig_gap = go.Figure(go.Bar(
                        x=gap_data["Category"],
                        y=gap_data["Count"],
                        marker_color=gap_data["Color"],
                        text=gap_data["Count"],
                        textposition='auto',
                    ))
                    fig_gap.update_layout(
                        title="Quick Skills Gap Analysis",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font={'color': "white"},
                        height=300,
                        yaxis=dict(showgrid=False)
                    )
                    st.plotly_chart(fig_gap, use_container_width=True)

                    st.markdown("### 📊 Detailed Skill Breakdown")
                    res_c1, res_c2 = st.columns(2)
                    
                    with res_c1:
                        st.success(f"✅ **Matched Keywords**")
                        for cat, ks in found_dict.items():
                            st.markdown(f"**{cat}:** " + ", ".join([f"`{k}`" for k in ks]))
                        
                    with res_c2:
                        st.warning(f"⚠ **Missing Keywords**")
                        for cat, ks in missing_dict.items():
                            st.markdown(f"**{cat}:** " + ", ".join([f"`{k}`" for k in ks]))
                        
                    st.markdown("### 💡 AI Suggestions")
                    missing_flat = [item for sublist in missing_dict.values() for item in sublist]
                    if missing_flat:
                        st.info(f"**Action Plan:** Try to incorporate concepts like **{', '.join(missing_flat[:3])}** into your experience bullets.")
                        st.write("Focus on categories where you have the most gaps to improve your ATS ranking.")
                    else:
                        st.info("Your resume matches all identified technical keywords in the JD! Focus on quantifying your achievements.")
        else:
            st.error("Please provide both documents.")

elif page == "Resume Builder":
    st.title("Professional Resume Builder 🛠️")
    st.write("Fill in your details to generate a clean, ATS-optimized PDF resume.")
    
    if st.button("✨ Load Sample Profile"):
        st.session_state['sample_profile'] = {
            'name': 'Alex Johnson',
            'email': 'alex.j@example.com',
            'phone': '+1 555-0123',
            'location': 'San Francisco, CA',
            'linkedin': 'linkedin.com/in/alexj',
            'summary': 'Passionate CS student specializing in Python and AI. Seeking summer internships.',
            'education': 'B.S. in Computer Science - Tech University (2021-2025)',
            'experience': 'Software Engineering Intern - DevCorp\n- Built a dashboard using Streamlit and Pandas.',
            'skills': 'Python, SQL, React, Git, Docker, Agile',
            'projects': 'ResuMate AI: An NLP tool for resume optimization.'
        }

    with st.form("resume_form"):
        st.markdown("#### 🎨 Theme & Layout")
        col_t1, col_t2 = st.columns(2)
        resume_color = col_t1.color_picker("Accent Color", "#6366f1")
        resume_layout = col_t2.selectbox("Select Layout", ["Modern", "Classic"], help="Modern is centered, Classic is left-aligned.")
        
        st.markdown("---")
        st.markdown("#### 👤 1. Personal Information")
        
        # Load sample data if exists
        s = st.session_state.get('sample_profile', {})
        
        c1, c2 = st.columns(2)
        name = c1.text_input("Full Name", value=s.get('name', ""), placeholder="e.g. Alex Johnson")
        email = c2.text_input("Email Address", value=s.get('email', ""), placeholder="alex@example.com")
        phone = c1.text_input("Phone Number", value=s.get('phone', ""), placeholder="+1 234 567 890")
        location = c2.text_input("Location", value=s.get('location', ""), placeholder="City, State/Country")
        linkedin = st.text_input("LinkedIn/GitHub Profile URL", value=s.get('linkedin', ""), placeholder="linkedin.com/in/alexj")
        
        st.markdown("---")
        st.markdown("#### 📝 2. Professional Summary")
        summary = st.text_area("A 2-3 sentence overview", height=100, value=s.get('summary', ""))
        
        st.markdown("---")
        st.markdown("#### 🎓 3. Education")
        education = st.text_area("Degrees and schools", height=100, value=s.get('education', ""))
        
        st.markdown("---")
        st.markdown("#### 💼 4. Work Experience")
        experience = st.text_area("Roles and achievements", height=150, value=s.get('experience', ""))
        
        st.markdown("---")
        st.markdown("#### 🛠️ 5. Key Skills")
        skills = st.text_area("Languages and tools", height=100, value=s.get('skills', ""))
        
        st.markdown("---")
        st.markdown("#### 🚀 6. Significant Projects")
        projects = st.text_area("Projects", height=100, value=s.get('projects', ""))
        
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Preview & Generate PDF Resume")
        
        if submitted:
            if not name or not email:
                st.error("Name and Email are required.")
            else:
                resume_data = {
                    'name': name, 'email': email, 'phone': phone,
                    'location': location, 'linkedin': linkedin,
                    'summary': summary, 'education': education,
                    'experience': experience, 'skills': skills,
                    'projects': projects
                }
                
                pdf_bytes = generate_resume_pdf(resume_data, resume_color, resume_layout)
                
                st.success("✅ Your professional resume is ready!")
                st.download_button(
                    label="Download Resume PDF",
                    data=pdf_bytes,
                    file_name=f"{name.replace(' ', '_')}_Resume.pdf",
                    mime="application/pdf"
                )

elif page == "Interview Prep":
    st.title("Interview Preparation Assistant 🤖")
    st.write("Get tailored interview questions based on the job description you're targeting.")
    
    jd_input = st.text_area("Paste Job Description here...", height=200, 
                          value=st.session_state.get('jd_sample', ""),
                          placeholder="Paste the job you're preparing for...")
    
    if st.button("Generate Interview Questions"):
        if jd_input:
            with st.spinner("Analyzing JD and generating questions..."):
                categorized_keywords = get_keywords(jd_input)
                # Flatten the keywords for display
                flat_keywords = [item for sublist in categorized_keywords.values() for item in sublist]
                
                st.markdown("### 🎯 Technical Questions (Based on JD)")
                if flat_keywords:
                    for i, kw in enumerate(flat_keywords[:8]):
                        st.info(f"**Q{i+1}:** Can you describe a project where you used **{kw.upper()}** and what challenges you faced?")
                else:
                    st.warning("No specific technical keywords found. Try pasting a more detailed JD.")
                
                st.markdown("---")
                st.markdown("### 🤝 Behavioral Questions (The Essentials)")
                behavioral_qs = [
                    "Tell me about a time you worked in a team and faced a conflict. How did you resolve it?",
                    "Describe a situation where you had to learn a new technology quickly. What was your process?",
                    "What is your greatest technical achievement so far, and why?",
                    "Where do you see yourself in 3 years in terms of technical growth?"
                ]
                for i, q in enumerate(behavioral_qs):
                    st.success(f"**BQ{i+1}:** {q}")
                    
                st.markdown("---")
                st.markdown("### 💡 Interview Tips")
                st.info("""
                - **The STAR Method:** For behavioral questions, always use Situation, Task, Action, and Result.
                - **Be Quantifiable:** Whenever possible, use numbers (e.g., 'Reduced load time by 20%').
                - **Ask Questions:** Always prepare 2-3 questions for the interviewer (e.g., 'What does a typical day look like for the engineering team?').
                """)
        else:
            st.error("Please paste a Job Description first.")
