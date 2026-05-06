# eBV Benefits Eligibility Demo

This repository includes a simple MCP-style Python app that validates NLP-driven eligibility requests before calling a backend benefits API.

## What is included

- `app.py` - FastAPI web app with a small browser UI for testing requests.
- `mcp.py` - MCP layer that extracts structured payloads, validates mandatory fields, and prevents backend calls until the payload is complete.
- `benefits_client.py` - Backend client that calls a real API when `BENEFITS_API_URL` is configured, or returns a local mock response otherwise.
- `requirements.txt` - Python dependencies.
- `.env.example` - Environment variable template.

## Required fields enforced by the MCP

- `npi`
- `patient.first_name`
- `patient.last_name`
- `patient.dob`
- `patient.gender`
- `patient.member_id`
- `drug.ndc`

## Setup

1. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Copy the environment example:

```bash
cp .env.example .env
```

3. Optionally set `BENEFITS_API_URL` to your Postman mock API endpoint and `OPENAI_API_KEY` if you want LangChain NLP parsing.

## Run the demo

```bash
uvicorn app:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

## Streamlit demo

A Streamlit UI is also available for the MCP demo:

```bash
streamlit run streamlit_app.py
```

This app lets you enter a free-form eligibility request, shows the parsed MCP payload, lists missing required fields, and displays the backend/mock eligibility response.

## Example prompts to test

- `Check eligibility for NPI 1234567890, patient Jane Doe DOB 1984-07-10 female member ID MBR12345, drug NDC 12345-6789.`
- `Verify coverage for NPI 1234567890 for John Smith born 1975-05-01, member number ABC987, medication NDC 55555-4444.`

If any required field is missing, the app will respond with a list of missing fields and will not call the backend.

## Notes

- If `BENEFITS_API_URL` is empty, the app uses a local mock response with sample scenarios.
- If `OPENAI_API_KEY` is set, the MCP will attempt to use `langchain` and `ChatOpenAI` to extract structured fields from free-form text.
