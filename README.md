# eBV Benefits Eligibility Demo

This repository demonstrates an MCP-style eligibility demo for healthcare benefits. The app converts free-form natural language requests into a structured payload, checks required fields, and only calls the backend when the request is complete.

## What this demo shows

- A simple natural language interface for eligibility requests.
- An MCP layer that extracts structured request fields from text.
- Validation of required fields before calling backend services.
- A mock eligibility backend when no remote API is configured.
- Both a FastAPI demo page and a Streamlit application for interactive use.

## Repository contents

- `app.py` — FastAPI web app with a lightweight browser UI for test requests.
- `streamlit_app.py` — Streamlit UI to showcase the MCP demo with payload and response debugging.
- `mcp.py` — MCP implementation that parses, merges, validates, and controls eligibility request execution.
- `benefits_client.py` — Backend client for real or mock eligibility checks.
- `requirements.txt` — Python dependencies required to run the demo.
- `.env.example` — Template for configuration variables.

## How it works

### 1. Free-form input

The demo accepts a free-form request containing provider, patient, and drug information. Example:

```text
Check eligibility for NPI 1234567890, patient Jane Doe DOB 1984-07-10 female member ID MBR12345, drug NDC 12345-6789.
```

### 2. NLP parsing

The core MCP layer in `mcp.py` tries to parse the input into a structured payload.

- If `OPENAI_API_KEY` is available and `langchain` is installed, it uses `ChatOpenAI` to extract JSON fields.
- If the LLM path is unavailable, it falls back to regex extraction.

### 3. Payload merging

The parsed values are merged with any existing payload state. This supports incremental input and progressive fulfillment of missing data.

### 4. Validation

The MCP validates that all required fields are present:

- `npi`
- `patient.first_name`
- `patient.last_name`
- `patient.dob`
- `patient.gender`
- `patient.member_id`
- `drug.ndc`

If any value is missing, the app returns a `missing_fields` response and does not call the backend.

### 5. Backend call

Once the payload is complete, the app calls `BenefitsClient.check_eligibility()`.

- If `BENEFITS_API_URL` is configured, the demo sends a POST request to the remote API.
- If no URL is configured, the demo uses `_local_mock()` to return deterministic mock eligibility results.

### 6. Response

The result contains:

- `status`: `missing_fields` or `success`
- `message`: a short explanation of the state
- `missing_fields`: required fields still missing, if any
- `payload`: the aggregated structured payload
- `api_result`: backend or mock response when the check is executed

## Required fields enforced by the MCP

The MCP will not execute an eligibility check until these fields are present:

- `npi`
- `patient.first_name`
- `patient.last_name`
- `patient.dob`
- `patient.gender`
- `patient.member_id`
- `drug.ndc`

## Setup

1. Install the dependencies:

```bash
python3 -m pip install -r requirements.txt
```

2. Copy the environment template:

```bash
cp .env.example .env
```

3. Configure environment variables in `.env` as needed.

## Configuration

Supported environment variables:

- `BENEFITS_API_URL` — remote eligibility backend endpoint.
- `BENEFITS_API_TIMEOUT` — timeout in seconds for backend calls (default: `15`).
- `OPENAI_API_KEY` — OpenAI API key for optional LLM-based parsing.
- `OPENAI_MODEL` — OpenAI model to use when parsing (default: `gpt-3.5-turbo`).

## Running the demo

### FastAPI demo

```bash
uvicorn app:app --reload --port 8000
```

Then open `http://localhost:8000`.

### Streamlit demo

```bash
streamlit run streamlit_app.py
```

Then open `http://localhost:8501`.

## Example prompts

Use these example prompts in either the FastAPI or Streamlit UI.

- `Check eligibility for NPI 1234567890, patient Jane Doe DOB 1984-07-10 female member ID MBR12345, drug NDC 12345-6789.`
- `Verify coverage for NPI 1234567890 for John Smith born 1975-05-01, member number ABC987, medication NDC 55555-4444.`
- `Check eligibility for NPI 1234567890, patient Sarah Smith DOB 1975-10-21 female member ID MBR00002, drug NDC PA-0000.`
- `Check eligibility for NPI 1234567890, patient Peter Lee DOB 1990-06-15 male member ID MBR00003, drug NDC STEP-1234.`

## Expected behavior

### Partial request example

Input:

```text
Check eligibility for NPI 1234567890 for patient Jane Doe DOB 1984-07-10 female.
```

Expected output:

- `status`: `missing_fields`
- `missing_fields`: `['patient.member_id', 'drug.ndc']`
- `payload`: parsed provider and patient fields

### Full request example: no restrictions

Input:

```text
Check eligibility for NPI 1234567890, patient John Doe born 1980-01-01 male member ID MBR00001, drug NDC 12345-6789.
```

Expected output:

- `status`: `success`
- `api_result.response.coverage`: `covered_no_restrictions`
- `api_result.response.message`: `The drug appears covered without restrictions.`

### Full request example: prior authorization required

Input:

```text
Check eligibility for NPI 1234567890, patient Sarah Smith DOB 1975-10-21 female member ID MBR00002, drug NDC PA-0000.
```

Expected output:

- `api_result.response.coverage`: `covered_pa_required`
- `api_result.response.message`: `This drug requires prior authorization.`

### Full request example: step therapy required

Input:

```text
Check eligibility for NPI 1234567890, patient Peter Lee DOB 1990-06-15 male member ID MBR00003, drug NDC STEP-1234.
```

Expected output:

- `api_result.response.coverage`: `covered_step_therapy`
- `api_result.response.message`: `Step therapy is required before coverage is approved.`

## Implementation details

### `mcp.py`

- `BenefitMCP.parse_nlp_payload()` — Converts free-form text into structured JSON using an LLM or regex fallback.
- `BenefitMCP.merge_payloads()` — Merges incoming payload data with prior state.
- `BenefitMCP.validate_payload()` — Checks for required fields.
- `BenefitMCP.handle_text_input()` — Controls parsing, merging, validation, and backend execution.

### `benefits_client.py`

- `check_eligibility()` — Calls the configured remote API or returns mock results.
- `_local_mock()` — Generates demo coverage decisions based on NDC or drug name content.

### `app.py`

- Serves a browser-based UI for sending natural language requests.
- Displays the MCP response and current payload state.

### `streamlit_app.py`

- Provides a richer interactive experience with Streamlit.
- Displays the aggregated payload, missing fields, and backend/mock responses.
- Includes sample buttons and reset functionality.

## Troubleshooting

- If `streamlit` is not installed, install it with:

```bash
python3 -m pip install streamlit
```

- If the app returns `missing_fields`, add the missing fields into the request text.
- If `OPENAI_API_KEY` is set and parsing fails, the demo will still fall back to regex extraction.
- If you want real backend behavior, set `BENEFITS_API_URL`; otherwise the demo uses mock responses.

## Notes

This project is a demo and is intended to illustrate MCP-style control flow and validation logic rather than production-ready natural language extraction or benefits processing.
