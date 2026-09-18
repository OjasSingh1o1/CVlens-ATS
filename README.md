# CVLens Intelligence Platform

> An AI-powered ATS (Applicant Tracking System) evaluation engine built to bridge the gap between qualified candidates and automated hiring filters.

Modern hiring pipelines rely heavily on ATS software that blindly filters out candidates due to poor resume formatting or missing keywords — regardless of actual ability. CVLens reverses this by giving candidates a precise, AI-driven workspace to format, benchmark, and optimize their resume against any job description.

---

## Features

| Module | Description |
|---|---|
| **Document Upload** | Upload a PDF resume and paste a job description once. All modules share this context. |
| **Resume Formatter** | Restructures your resume into a clean, parser-safe, ATS-optimized format — preserving all original content verbatim, no rephrasing. |
| **JD Matcher** | Rates the candidate-JD fit out of 100, with a visual score ring and a structured breakdown of strengths (pros) and gaps (cons). |
| **Keyword Analyzer** | Extracts and cross-references core technical terminology from both the JD and resume — highlights matched and missing keywords. |
| **Preview & Export** | Renders the formatted resume in a Word-document-style canvas. Editable inline, exportable as a `.doc` file. |
| **JD Auto-Generate** | Reverse-engineers a realistic Job Description from your resume using Gemini — useful for discovering roles you naturally fit. |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **AI** | Google Gemini API (`google-genai` SDK) with multi-key pool and model fallback chain |
| **PDF Processing** | `pdf2image` + Poppler (system dependency) |
| **Frontend** | Vanilla HTML/CSS/JS, Tailwind CSS (CDN), Marked.js |
| **Environment** | `python-dotenv` |

---

## Project Structure

```
cvlens_intelligence_platform/
|
+-- cvlens_app/                   # Active application (Flask SPA)
|   +-- app.py                    # Flask server, API routes, Gemini prompts
|   +-- requirements.txt          # Python dependencies
|   +-- .env.example              # Template -- copy to .env and add your API key(s)
|   +-- templates/
|   |   +-- dashboard.html        # Single-page application (all modules)
|   +-- static/
|       +-- uploads/              # Temp upload directory (gitignored)
|
+-- CVLens-main/                  # Legacy Streamlit prototype (archived reference)
|   +-- final.py                  # Original Streamlit app
|   +-- requirements.txt          # Streamlit-era dependencies
|
+-- .gitignore
+-- README.md
```

---

## Setup

### 1. Prerequisites

Install [Poppler](https://poppler.freedesktop.org/) -- required by `pdf2image` for PDF-to-image conversion. It is a **system dependency**, not a Python package.

```bash
# macOS
brew install poppler

# Verify
pdfinfo -v
```

### 2. Clone the repository

```bash
git clone https://github.com/OjasSingh1o1/CVlens-.git
cd cvlens_intelligence_platform
```

### 3. Create and activate a virtual environment

```bash
cd cvlens_app
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure your API key

`.env` is **never committed** (it is in `.gitignore`). Create it manually inside `cvlens_app/`:

```
# cvlens_app/.env

# Single key:
GOOGLE_API_KEY=your_key_here

# OR multiple keys (comma-separated, for rate-limit rotation):
GOOGLE_API_KEYS=key_one,key_two,key_three
```

Get a free key at [Google AI Studio](https://ai.google.dev/).

### 6. Run the app

```bash
python app.py
```

Opens at `http://localhost:8501`.

---

## How It Works

1. **Upload Context** -- PDF resume + Job Description are submitted once and shared across all modules.
2. **Format** -- Gemini receives the resume as page images and maps all content into a structured, ATS-safe schema with zero rephrasing.
3. **Match** -- Gemini returns a JSON payload (`rating`, `pros`, `cons`). The frontend renders this as a score ring with color-coded pros/cons cards.
4. **Keyword Analysis** -- Cross-references JD and resume terminology; surfaces missing keywords.
5. **Export** -- The formatted resume is rendered as a live-editable HTML canvas and exported as a `.doc` file via the Blob API.

### Rate Limit Handling

The backend operates a **multi-key, multi-model fallback chain**. On a `429 RESOURCE_EXHAUSTED` error, it automatically rotates to the next API key. Within each key it tries:

```
gemini-3.5-flash-lite -> gemini-3.5-flash -> gemini-3.6-flash -> gemini-3.8-flash -> gemini-flash-latest
```

---

## Notes

- Analyzes up to the **first 5 pages** of an uploaded PDF.
- All AI prompts use low `temperature` values (`0.0` to `0.1`) to ensure deterministic, source-grounded output.
- The `CVLens-main/` folder is the original Streamlit prototype, kept as an archived reference. It is **not part of the active application**.

---

## What NOT to Push to GitHub

| File / Directory | Reason |
|---|---|
| `cvlens_app/.env` | Contains live API keys -- **never commit** |
| `CVLens-main/.env` | Contains live API keys -- **never commit** |
| `venv/`, `app_venv/`, any `venv/` | Virtual environments are local-machine-specific |
| `cvlens_app/static/uploads/` | Contains user-submitted resumes (PII) |
| `.DS_Store`, `Thumbs.db` | OS junk |
| `*.pdf` (unless intentional) | User data / test files |

All of the above are covered by the root `.gitignore`.

---

## Roadmap

- [ ] Authentication / user accounts
- [ ] Persistent session history
- [ ] `.docx` resume upload support
- [ ] Deployment to a cloud platform (Railway / Render / Fly.io)
