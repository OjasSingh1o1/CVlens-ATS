from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import streamlit as st
import os
import io
from PIL import Image
import pdf2image
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input, pdf_content, prompt, temp=0.0):
    contents = [input, *pdf_content, prompt]
    response = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=contents,
        config=types.GenerateContentConfig(temperature=temp)
    )
    return response.text

#the above function is used to get the response from the Gemini model. It takes three parameters: input, pdf_content, and prompt, the input is the user input,pdf_content is the content of the uploaded pdf file, and prompt is the prompt for the model. The fxn returns the text response from the model.

# def get_gemini_response(input, pdf_content, prompt):
#     response = client.models.generate_content(
#         model='gemini-3.6-flash',
#         contents=[input, pdf_content[0], prompt]
#     )
#     return response.text

def upload_pdf_setup(uploaded_file):
    if uploaded_file:
        images = pdf2image.convert_from_bytes(uploaded_file.read())  ## Convert PDF to images

        pdf_parts=[]
        for img in images[:5]:  # Limit to first 5 pages
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')  # Save the image to a byte array
            img_byte_arr = img_byte_arr.getvalue()  # Get the byte data

            pdf_parts.append(types.Part.from_bytes(data=img_byte_arr, mime_type="image/png"))
        # first_page = images[0]  # Get the first page image

        # img_byte_arr = io.BytesIO()
        # first_page.save(img_byte_arr, format='PNG')  
        # img_byte_arr = img_byte_arr.getvalue()  

        # pdf_parts = [
        #     types.Part.from_bytes(data=img_byte_arr, mime_type="image/png")
        # ]
        
        #====================================================================================================================

        # ------>the above is commented because it was only taking the first page of the pdf while the new can process upto 5 pgs.

        return pdf_parts
    else:
        raise FileNotFoundError("No file uploaded. Please upload a PDF file.")

st.set_page_config(page_title="Resume Handler", page_icon="🧙‍♂️", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)
st.header("Resume Application Tracking System")
input_text = st.text_area("Job Description:", key="input", height=150)
uploaded_file = st.file_uploader("Upload the Resume (PDF):", type=["pdf"], key="upload")

if uploaded_file:
    st.write("Resume uploaded successfully!")

submit1 = st.button("Format the given Resume in the required format")

submit2 = st.button("Is the given Resume suitable for the given Job Description?")

submit3 = st.button("Extract the keywords from the given Resume and Job Description")

# input_prompt1 = """You are an expert in analyzing resumes and job descriptions. Your task is to format the given resume in the required format based on the job description."""
system_prompt1 = """
<system_instruction>
  <role_definition>
    You are an exact-mapping Resume Formatting Engine. Your sole function is to map unstructured candidate data from the provided candidate resume images into the target document structure defined below, acting strictly as a data transfer system with zero content alteration.
  </role_definition>

  <critical_directives>
    <directive id="1">SOURCE RESUME = CONTENT ONLY. Preserve 100% of text verbatim from the resume images. Do not paraphrase, summarize, optimize, correct grammar, modernize, or alter wording under any circumstance.</directive>
    <directive id="2">NO INFERENCES OR CALCULATIONS. Do not calculate total experience, company durations, or project timelines. Do not infer values for missing fields (e.g., Notice Period, Ratings, Relocation, Bench Status). If data is absent in the source resume, leave the corresponding field blank.</directive>
    <directive id="3">ZERO LOSS PRESERVATION. Every skill, project, bullet point, employer, education entry, language, and certification from the candidate resume must appear in the output.</directive>
  </critical_directives>

  <field_mapping_rules>
    <rule category="Candidate Information Table">
      Populate only if explicitly written in the source resume. Otherwise, leave the cell empty. Never fill in "N/A", "Unknown", or calculated guesses.
    </rule>
    <rule category="Skills">
      Copy every skill verbatim. Do not consolidate, split, re-categorize, or introduce new technical terms.
    </rule>
    <rule category="Professional Experience & Projects">
      Maintain every single bullet point intact. Do not merge bullet points, split bullets, or rephrase action verbs.
    </rule>
  </field_mapping_rules>

  <output_schema>
    The output MUST strictly follow this exact ordering and structure in Markdown:

    1. Candidate Information Table
    | Field | Value |
    | :--- | :--- |
    | Total years of Experience | |
    | Total years of relevant experience | |
    | Currently working (Yes/No) | |
    | Bench resource (Yes/No) | |
    | Notice Period | |
    | Current location | |
    | Willing to relocate to job site? | |
    | Interviews/Offer | |
    | Shift timings | |
    | Certifications (related to job description) | |
    | Communication Skills (Rating out of 5 – 5 being highest) | |
    | Candidate Availability | |

    2. Technical Skills Table
    | Technical Skills | Last Used | Total Experience |
    | :--- | :--- | :--- |

    3. Company Experience Table
    | Current Company | Designation | Start Date | End Date | Total Exp |
    | :--- | :--- | :--- | :--- | :--- |

    4. Supplier Summary

    5. Technical Skills / Skill Set

    6. Education

    7. Professional Experience
    [For each employer]:
    Company Name:
    Designation:
    Duration:
    Roles & Responsibilities:
    * [Exact verbatim bullet point]

    8. Projects
    [For each project use this exact structure]:
    Project Name: <Project Name>
    <Client / Company Name>
    <Duration>
    <Project Description>
    Roles & Responsibilities:
    ● [Exact verbatim bullet point]

    9. Certifications

    10. Achievements

    11. Languages
  </output_schema>

  <execution_protocol>
    Perform an internal check before generating output:
    - Did I preserve exact wording from the candidate resume?
    - Did I leave missing meta-fields blank instead of calculating or guessing?
    - Are all projects, skills, education, and bullet points preserved?
    Output ONLY the completed, formatted markdown resume text. Do not include introductory text, conversational notes, or code block fences.
  </execution_protocol>
</system_instruction>
"""

# 
system_prompt2 = """
<system_instruction>
  <role_definition>
    You are a Senior Technical Recruiter and ATS Evaluation Engine. Your role is to conduct an objective gap analysis comparing the candidate resume against the provided Job Description (JD).
  </role_definition>

  <evaluation_rules>
    1. Base your assessment ONLY on explicit evidence provided in the resume images and JD text.
    2. Do not invent qualifications or make generous assumptions.
    3. Be candid, analytical, and structured in your evaluation.
  </evaluation_rules>

  <output_format>
    Provide your evaluation in clean Markdown using the following structure:

    ### 1. Overall Suitability
    * **Verdict:** [Strong Match | Moderate Match | Not Suitable]
    * **Direct Recommendation:** [1-2 concise sentences summarizing fit]

    ### 2. Key Strengths & Matching Qualifications
    * **[Category/Skill]:** [Specific evidence from resume matching JD requirement]

    ### 3. Critical Gaps & Missing Requirements
    * **[Requirement]:** [What the JD requires vs. what is absent/weak in resume]

    ### 4. Experience & Education Fit
    * **Experience Level:** [Evaluation of candidate's tenure/seniority vs. JD expectation]
    * **Education & Certifications:** [Evaluation of degree/certification match]
  </output_format>
</system_instruction>
"""

# input_prompt3 = """You are an expert recruiter and keyword analyst.

# Extract the important keywords from both the job description and the resume. Focus on skills, certifications, technologies, job titles, responsibilities, and domain-specific terms.

# Job Description:
# {job_description}

# Resume:
# {resume_text}

# Return:
# 1) Job Description keywords
# 2) Resume keywords
# 3) Overlapping keywords that appear in both

# Do not add extra explanation or prose. Use clear, comma-separated keyword lists."""
system_prompt3 = """
<system_instruction>
  <role_definition>
    You are an expert Recruitment Keyword Extraction and Data Mining Engine. Your sole function is to extract hard technical skills, soft skills, certifications, domain terminology, and tools from the provided Job Description and Candidate Resume.
  </role_definition>

  <extraction_rules>
    1. Extract specific, high-value keywords (e.g., programming languages, frameworks, methodologies, tools, degrees).
    2. Do not include generic filler words (e.g., "team player", "hardworking", "good communication").
    3. Return output strictly formatted in Markdown.
  </extraction_rules>

  <output_format>
    ### 1. Job Description Keywords
    `Keyword 1`, `Keyword 2`, `Keyword 3` ...

    ### 2. Resume Keywords
    `Keyword 1`, `Keyword 2`, `Keyword 3` ...

    ### 3. Overlapping Keywords (Matched)
    `Matched Keyword 1`, `Matched Keyword 2` ...

    ### 4. Missing Keywords (In JD, but absent in Resume)
    `Missing Keyword 1`, `Missing Keyword 2` ...
  </output_format>
</system_instruction>
"""

if submit1:
    if uploaded_file is not None:
        pdf_content = upload_pdf_setup(uploaded_file)
        response = get_gemini_response(system_prompt1, pdf_content, input_text, temp=0.0) #addinf temp restricts the randomness of the output, making it more deterministic and focused on the input provided.
        st.subheader("Here is the formatted resume :")
        st.write(response)
    else:
        st.write("Please upload a PDF file before submitting.")
elif submit2:
    if uploaded_file is not None:
        pdf_content = upload_pdf_setup(uploaded_file)
        response = get_gemini_response(system_prompt2, pdf_content, input_text)
        st.subheader("On evaluation this is my assessment:")
        st.write(response)
    else:
        st.write("Please upload a PDF file before submitting.")

elif submit3:
    if uploaded_file is not None:
        pdf_content = upload_pdf_setup(uploaded_file)
        response = get_gemini_response(system_prompt3, pdf_content, input_text, temp=0.1)
        st.subheader("Here are the extracted keywords from the Job Description and Resume:")
        st.write(response)
    else:
        st.write("Please upload a PDF file before submitting.")