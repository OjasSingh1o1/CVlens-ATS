import os
import io
from flask import Flask, render_template, request, jsonify
from PIL import Image
import pdf2image
import hashlib

_ANALYSIS_CACHE = {} # In-memory cache

from google import genai
from google.genai import types
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)

app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'), 
            static_folder=os.path.join(BASE_DIR, 'static'))

def get_api_keys():
    load_dotenv(dotenv_path, override=True)
    keys = []
    # Check GOOGLE_API_KEYS (comma-separated string)
    keys_str = os.getenv("GOOGLE_API_KEYS", "")
    for k in keys_str.split(","):
        k = k.strip()
        if k and k not in keys:
            keys.append(k)
            
    # Also check standard GOOGLE_API_KEY
    single_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if single_key and single_key not in keys:
        keys.append(single_key)

    # Also check for GOOGLE_API_KEY_1, GOOGLE_API_KEY_2...
    for env_k, env_v in os.environ.items():
        if env_k.startswith("GOOGLE_API_KEY_") and env_v.strip() and env_v.strip() not in keys:
            keys.append(env_v.strip())

    return keys

def upload_pdf_setup(file_bytes):
    images = pdf2image.convert_from_bytes(file_bytes)
    pdf_parts = []
    for img in images[:5]:
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        pdf_parts.append(types.Part.from_bytes(data=img_byte_arr, mime_type="image/png"))
    return pdf_parts

def get_gemini_response(system_prompt, pdf_content, input_text, temp=0.0):
    keys = get_api_keys()
    if not keys:
        return "Error: No GOOGLE_API_KEY or GOOGLE_API_KEYS found in environment variables."
        
    contents = [input_text, *pdf_content, system_prompt]
    
    # Valid active models verified working with current API key
    MODEL_CHAIN = [
        'gemini-3.5-flash-lite',
        'gemini-3.5-flash',
        'gemini-3.6-flash',
        'gemini-3.8-flash',
        'gemini-flash-latest',
    ]

    last_err = None
    exhausted_keys = []

    for key_index, key in enumerate(keys):
        client = genai.Client(api_key=key)
        key_exhausted = False
        
        for model_name in MODEL_CHAIN:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(temperature=temp)
                )
                if response.text is None:
                    raise ValueError(f"Model '{model_name}' returned an empty or blocked response.")
                return response.text
            except Exception as err:
                last_err = err
                err_str = str(err)
                # If rate limited / quota exhausted on this key, rotate immediately to next key
                if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str or 'quota' in err_str.lower():
                    print(f"[Key Pool Rotation] Key #{key_index + 1} (...{key[-6:]}) exhausted quota (429). Rotating to next key...")
                    exhausted_keys.append(key)
                    key_exhausted = True
                    break  # Try next key in key pool
                # Otherwise (e.g. 404 or unsupported model), try next model in chain
                continue

        if not key_exhausted:
            # If all models failed for non-429 reasons on this key, keep last_err
            pass

    if len(exhausted_keys) == len(keys):
        raise RuntimeError(
            f"All {len(keys)} Gemini API Key(s) in your pool have exhausted their daily quota (429). Please add another API key to cvlens_app/.env."
        )

    raise last_err


# System Prompts from original CVLens engine
SYSTEM_PROMPT_FORMATTER = """
<system_instruction>
  <role_definition>
    You are an exact-mapping Resume Formatting Engine. Your sole function is to map unstructured candidate data from the provided candidate resume images into the target document structure defined below, acting strictly as a data transfer system with zero content alteration.
  </role_definition>

  <critical_directives>
    <directive id="1">SOURCE RESUME = CONTENT ONLY. Preserve 100% of text verbatim from the resume images. Do not paraphrase, summarize, optimize, correct grammar, modernize, or alter wording under any circumstance.</directive>
    <directive id="2">NO INFERENCES OR CALCULATIONS. Do not calculate total experience, company durations, or project timelines. Do not infer values for missing fields (e.g., Notice Period, Ratings, Relocation, Bench Status). If data is absent in the source resume, leave the corresponding field blank.</directive>
    <directive id="3">ZERO LOSS PRESERVATION. Every skill, project, bullet point, employer, education entry, language, and certification from the candidate resume must appear in the output.</directive>
  </critical_directives>

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

    8. Projects

    9. Certifications

    10. Achievements

    11. Languages
  </output_schema>
</system_instruction>
"""

SYSTEM_PROMPT_MATCHER = """
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
    You MUST output ONLY a valid JSON object. Do not include markdown code blocks (like ```json) or any other text.
    Use the following exact schema:
    {
      "rating": <integer between 0 and 100 representing the overall match score>,
      "pros": [
        "<string: reason to hire, specific knowledge they have, matching skills, etc.>",
        ...
      ],
      "cons": [
        "<string: what they lack, missing requirements, experience gaps, etc.>",
        ...
      ]
    }
  </output_format>
</system_instruction>
"""

SYSTEM_PROMPT_ANALYZER = """
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

SYSTEM_PROMPT_GENERATE_JD = """
<system_instruction>
  <role_definition>
    You are an expert Technical Recruiter and Hiring Manager. Your task is to automatically generate a realistic, tailored Job Description (JD) based on the provided candidate resume.
  </role_definition>

  <extraction_rules>
    1. Analyze the candidate's core skills, experience level, and primary domain/industry.
    2. Write a professional Job Description that this candidate would be a strong match for.
    3. Include a Job Title, Company Overview (fictional but realistic), Responsibilities, and Required Qualifications.
    4. Keep it concise, engaging, and directly aligned with the candidate's profile.
  </extraction_rules>
</system_instruction>
"""

# Web Page Routes — Single Page Application
from flask import redirect

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# Legacy routes redirect to SPA section anchors
@app.route('/analyzer')
def analyzer():
    return redirect('/#section-analyzer')

@app.route('/matcher')
def matcher():
    return redirect('/#section-matcher')

@app.route('/formatter')
def formatter():
    return redirect('/#section-formatter')

@app.route('/preview')
def preview():
    return redirect('/#section-preview')

# API Route for Gemini AI processing
@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    action = request.form.get('action', 'match')
    job_description = request.form.get('job_description', '')
    
    if 'resume' not in request.files:
        return jsonify({'error': 'No resume PDF file uploaded.'}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400
        
    file_bytes = file.read()
    
    # Check cache first
    cache_key = hashlib.md5(f"{action}_{job_description}".encode('utf-8') + file_bytes).hexdigest()
    if cache_key in _ANALYSIS_CACHE:
        return jsonify({'result': _ANALYSIS_CACHE[cache_key]})

    
    try:
        pdf_content = upload_pdf_setup(file_bytes)
    except Exception as e:
        return jsonify({'error': f"Failed to process PDF: {str(e)}"}), 500

    try:
        if action == 'format':
            response_text = get_gemini_response(SYSTEM_PROMPT_FORMATTER, pdf_content, job_description, temp=0.0)
        elif action == 'match':
            response_text = get_gemini_response(SYSTEM_PROMPT_MATCHER, pdf_content, job_description, temp=0.0)
        elif action in ['keywords', 'analyze']:
            response_text = get_gemini_response(SYSTEM_PROMPT_ANALYZER, pdf_content, job_description, temp=0.1)
        elif action == 'generate_jd':
            response_text = get_gemini_response(SYSTEM_PROMPT_GENERATE_JD, pdf_content, "", temp=0.7)
        else:
            return jsonify({'error': f'Invalid action specified: {action}'}), 400
            
        _ANALYSIS_CACHE[cache_key] = response_text
        return jsonify({'result': response_text})
    except Exception as err:
        import traceback
        tb = traceback.format_exc()
        print(f"[CVLens API Error] action={action}\n{tb}")
        return jsonify({'error': f"Gemini Analysis Error: {str(err)}"}), 500

if __name__ == '__main__':
    print("Starting CVLens Intelligence Platform on http://localhost:8501")
    app.run(host='0.0.0.0', port=8501, debug=True)
