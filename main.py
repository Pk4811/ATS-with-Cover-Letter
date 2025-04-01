from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import PyPDF2 as pdf
from typing import Optional

# Load environment variables
load_dotenv()

# Configure Gemini AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_prompt: str) -> Optional[str]:
    """Get response from Gemini AI with error handling"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(input_prompt)
        return response.text
    except Exception as e:
        st.error(f"Error getting response from Gemini: {str(e)}")
        return None

def extract_pdf_text(uploaded_file) -> Optional[str]:
    """Extract text from PDF with error handling"""
    try:
        reader = pdf.PdfReader(uploaded_file)
        return "\n".join([page.extract_text() for page in reader.pages])
    except Exception as e:
        st.error(f"Error reading PDF file: {str(e)}")
        return None

# Streamlit UI Configuration
st.set_page_config(page_title="Gemini ATS", page_icon="📄")

# Main Application
def main():
    st.title("📄 Gemini ATS - Resume Optimizer")
    st.caption("Developed By: Pawan Kumar | Improve Your Resume ATS Score")
    
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        1. Paste the job description in the text area
        2. Upload your resume (PDF format)
        3. Click 'Analyze' to get detailed feedback
        4. Use suggestions to improve your resume
        """)
    
    # Input Section
    jd = st.text_area("📋 Paste Job Description", height=150)
    uploaded_file = st.file_uploader("📤 Upload Resume (PDF)", type="pdf")
    
    # Analysis Parameters
    with st.sidebar:
        st.header("Analysis Settings")
        strictness = st.slider("🏆 Competitiveness Level", 1, 5, 3,
                             help="Adjust based on job market competitiveness")

    if st.button("🔍 Analyze", type="primary") and uploaded_file and jd:
        with st.spinner("🔍 Analyzing resume..."):
            resume_text = extract_pdf_text(uploaded_file)
            
            if resume_text:
                input_prompt = f"""
                Act as an expert ATS scanner with 10+ years of experience in tech hiring. 
                Analyze this resume against the job description with strictness level {strictness}/5.
                
                **Required Output Format:**
                ###MATCH_SCORE###
                [percentage]%
                
                ###STRENGTHS###
                - Bullet points of resume strengths
                
                ###MISSING_KEYWORDS###
                - List of missing keywords
                
                ###IMPROVEMENTS###
                - Specific improvement suggestions
                
                ###COVER_LETTER###
                [Tailored cover letter using resume info and JD]
                
                **Resume:**
                {resume_text[:3000]}  # Limit input size
                
                **Job Description:**
                {jd[:3000]}
                """
                
                response = get_gemini_response(input_prompt)
                
                if response:
                    # Parse response sections
                    sections = {
                        "MATCH_SCORE": None,
                        "STRENGTHS": None,
                        "MISSING_KEYWORDS": None,
                        "IMPROVEMENTS": None,
                        "COVER_LETTER": None
                    }
                    
                    current_section = None
                    for line in response.split('\n'):
                        if line.startswith("###") and line.endswith("###"):
                            current_section = line.strip('#').strip()
                        elif current_section and current_section in sections:
                            if sections[current_section] is None:
                                sections[current_section] = []
                            sections[current_section].append(line)
                    
                    # Display results
                    if sections["MATCH_SCORE"]:
                        score = sections["MATCH_SCORE"][0].strip('%')
                        st.subheader(f"📊 ATS Match Score: {score}%")
                        st.progress(float(score)/100)
                    
                    with st.container():
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if sections["STRENGTHS"]:
                                st.subheader("✅ Strengths")
                                st.markdown("\n".join(sections["STRENGTHS"]))
                                
                            if sections["IMPROVEMENTS"]:
                                st.subheader("🛠️ Improvement Suggestions")
                                st.markdown("\n".join(sections["IMPROVEMENTS"]))
                        
                        with col2:
                            if sections["MISSING_KEYWORDS"]:
                                st.subheader("❌ Missing Keywords")
                                st.markdown("\n".join(sections["MISSING_KEYWORDS"]))
                    
                    if sections["COVER_LETTER"]:
                        st.subheader("✉️ Generated Cover Letter")
                        st.write("\n".join(sections["COVER_LETTER"]))
                        st.download_button("📥 Download Cover Letter", 
                                         "\n".join(sections["COVER_LETTER"]),
                                         file_name="generated_cover_letter.txt")

if __name__ == "__main__":
    main()
