# Resume Application Tracking System (ATS)

A Streamlit web app that uses Google's Gemini AI to analyze resumes against job descriptions — built to help candidates understand how their resume stacks up before they hit submit.

## What it does

Upload a resume (PDF, up to 5 pages) and paste in a job description. The app converts each page into an image and sends them to Gemini alongside the job description, then gives you back one of three structured analyses:

- **Format the Resume** — remaps the resume's content into a standardized recruiter-facing structure (candidate info table, skills table, experience, projects, etc.), preserving all original wording exactly — no rephrasing, no invented data.
- **Suitability Check** — an objective gap analysis: overall verdict (strong / moderate / not suitable), matching qualifications, and critical gaps, based only on what's explicitly present in the resume and JD.
- **Keyword Extraction** — pulls hard technical/domain keywords from both documents and shows JD keywords, resume keywords, overlapping (matched) keywords, and missing keywords.

All three use tightly constrained system prompts and low temperature settings to keep output deterministic and grounded in the actual source documents rather than the model's own assumptions.

## Tech Stack

- **Frontend/App**: [Streamlit](https://streamlit.io/)
- **AI Model**: Google Gemini API via the [`google-genai`](https://github.com/googleapis/python-genai) SDK
- **PDF Processing**: `pdf2image` + [Poppler](https://poppler.freedesktop.org/) (system dependency)
- **Image Handling**: Pillow (PIL)
- **Environment Config**: `python-dotenv`

## Setup

### 1. Clone the repo
```bash
git clone <your-repo-url>
cd "Resume ATS"
```

### 2. Install Poppler (system dependency — required for PDF-to-image conversion)
Poppler is not a Python package, so it isn't in `requirements.txt` and won't install via pip. On macOS:
```bash
brew install poppler
```
Verify it's on PATH:
```bash
pdfinfo -v
```

### 3. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 5. Set up your API key
`.env` is intentionally excluded from the repo (via `.gitignore`) so API keys never get committed. Create it manually in the project root:
```
GOOGLE_API_KEY=your_api_key_here
```
Get a free key at [Google AI Studio](https://ai.google.dev/).

### 6. Run the app
```bash
streamlit run app.py
```
Opens automatically at `http://localhost:8501`.

## Usage

1. Paste the job description into the text area
2. Upload your resume as a PDF
3. Click one of the three action buttons
4. Read the Gemini-generated analysis below

## Notes

- Analyzes up to the **first 5 pages** of the uploaded PDF.
- The Gemini API free tier has rate limits (a handful of requests per minute per model). If you hit a `429 ResourceExhausted` error, wait ~30 seconds and retry.
- Uses Google's current [`google-genai`](https://github.com/googleapis/python-genai) SDK. This project has been fully migrated off the deprecated `google-generativeai` package — that dependency has been removed.
- Prompts use low `temperature` values (0.0–0.1) intentionally, to favor deterministic, source-grounded output over creative variation.

## Rebuilding from scratch

If you delete your local copy and re-clone later, the setup steps above (2–6) need to be repeated in full — the venv, Poppler install, and `.env` file are all local-machine-specific and do not travel with the Git repo.

## Roadmap / Future Improvements

- [ ] Support Word (.docx) resume uploads, not just PDF
- [ ] Add a downloadable formatted resume output
- [ ] Deploy to Streamlit Community Cloud
