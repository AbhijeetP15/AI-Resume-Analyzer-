import streamlit as st
import PyPDF2
import io
import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")

load_dotenv()

st.set_page_config(page_title="ProEdge", page_icon="✨", layout="centered")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ---------------------- Helper functions (used by Tab 1) ----------------------
def extract_text_from_pdf(file_like):
    reader = PyPDF2.PdfReader(file_like)
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    elif uploaded_file.type == "text/plain":
        return uploaded_file.read().decode("utf-8", errors="ignore")
    else:
        return ""

# ------------------------------ ProEdge Logo ------------------------------
LOGO_SVG = f"""
<div style="display:flex; align-items:center; gap:16px; justify-content:center; margin: 30px 0 10px;">
  <svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ProEdge logo">
    <defs>
      <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#FF9800"/>
        <stop offset="50%" stop-color="#FFB74D"/>
        <stop offset="100%" stop-color="#FFC107"/>
      </linearGradient>
      <filter id="soft" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur in="SourceGraphic" stdDeviation="0.6"/>
      </filter>
    </defs>
    <rect x="4" y="4" width="56" height="56" rx="14" fill="url(#grad)" opacity="0.18" />
    <path d="M20 44 L20 20 L36 20 C41 20 45 24 45 29 C45 34 41 38 36 38 L20 38 M36 44 L48 44" stroke="url(#grad)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" filter="url(#soft)"/>
  </svg>
  <div style="line-height:1;">
    <div style="font-size:36px; font-weight:900; letter-spacing:0.5px; background: linear-gradient(90deg, #FF9800, #FFB74D, #FFC107); -webkit-background-clip:text; background-clip:text; color:transparent;">ProEdge</div>
    <div style="font-size:14px; opacity:0.75; margin-top:4px;">AI Resume Analyzer & LinkedIn Photo Rater</div>
  </div>
</div>
<hr style="opacity:0.15; margin: 8px 0 18px;"/>
"""

st.markdown(LOGO_SVG, unsafe_allow_html=True)

# =============================== Top-level tabs ===============================
tab_resume, tab_photo = st.tabs(["AI Resume Analyzer", "LinkedIn Photo Rating"])

# --------------------------------- TAB 1 -------------------------------------
with tab_resume:
    st.markdown("Upload your resume in PDF or TXT and get insights powered by OpenAI.")

    uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"], key="resume_upload")
    job_role = st.text_input("enter the job role you are applying for", placeholder="e.g. Software Engineer, Data Scientist")
    job_description = st.text_area("Enter the job description", placeholder="Paste the job description here...")
    analyze_button = st.button("Analyze Resume")

    if analyze_button and uploaded_file:
        try:
            file_content = extract_text_from_file(uploaded_file)
            if not file_content.strip():
                st.error("file does not have any content")
                st.stop()

            prompt = f"""You are an AI assistant that analyzes resumes and provide honest feedback on how well they match a given job role.
Focus on the following aspects:
1. Content clarity and impact
2. skills presentation and relevance to the provided job role and job description
3. Overall structure and formatting
4. Any missing elements that could enhance the resume
5. Experiece description based on the job role and description
6. Specific improvement for {job_role if job_role else 'general job applications'}

Resume content:
{file_content}

Provide your analysis in a clear, structured format with specific recommendations for improvement."""

            if not client:
                st.error("OpenAI API key missing.")
            else:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional resume analyzer with years of experience providing feedback on resumes."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                )

                st.markdown("### Analysis Result")
                st.markdown(response.choices[0].message.content)

        except Exception as e:
            st.error(f"An error occurred while processing the file: {e}")

# --------------------------------- TAB 2 -------------------------------------
with tab_photo:
    st.markdown("Upload a headshot you might use on LinkedIn. The model will rate professionalism and suggest improvements.")
    photo = st.file_uploader("Upload profile photo (JPG/PNG/WebP)", type=["jpg", "jpeg", "png", "webp"], key="photo")
    rate_btn = st.button("Rate Photo")

    if rate_btn and photo:
        try:
            mime = photo.type or "image/jpeg"
            data64 = base64.b64encode(photo.read()).decode("utf-8")
            prompt_photo = (
                "You are a career coach evaluating a LinkedIn profile photo. "
                "Score professionalism on a 1–10 scale and give actionable tips. "
                "Consider: lighting, background, framing, attire, facial expression, distractions, and overall first impression. "
                "Keep feedback concise with bullets and end with a one-line summary and the numeric score."
            )

            if not client:
                st.error("OpenAI API key missing.")
            else:
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Be direct, constructive, and kind."},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_photo},
                                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data64}"}},
                            ],
                        },
                    ],
                    temperature=0.4,
                    max_tokens=600,
                )

                st.image(f"data:{mime};base64,{data64}", caption="Uploaded photo", use_column_width=True)
                st.markdown("### Photo Feedback")
                st.markdown(resp.choices[0].message.content)
        except Exception as e:
            st.error(f"Error rating photo: {e}")
