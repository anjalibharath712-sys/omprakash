import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from mcp import BenefitMCP

app = FastAPI(title="eBV Benefits Eligibility Demo")

mcp = BenefitMCP()

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>eBV Benefits Check Demo</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f7fb; color: #1f2937; }
    header { background: #2563eb; color: #fff; padding: 24px; text-align: center; }
    main { padding: 24px; max-width: 960px; margin: auto; }
    textarea { width: 100%; min-height: 140px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; font-size: 1rem; }
    button { background: #2563eb; border: none; color: #fff; padding: 12px 18px; font-size: 1rem; border-radius: 8px; cursor: pointer; }
    button.secondary { background: #475569; margin-left: 8px; }
    pre { background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px; overflow-x: auto; }
    .sample-buttons button { margin-bottom: 8px; }
    .notice { margin: 16px 0; padding: 16px; border-radius: 8px; background: #eff6ff; color: #1e3a8a; }
  </style>
</head>
<body>
  <header>
    <h1>eBV Benefits Eligibility Demo</h1>
    <p>Enter a natural language request and the MCP layer will validate required fields before calling the backend.</p>
  </header>
  <main>
    <div class="notice">
      <strong>Required fields:</strong> NPI, patient first/last name, DOB, gender, member ID, and drug NDC.
      If any of these are missing, the backend is not called.
    </div>
    <label for="userText"><strong>Request text</strong></label>
    <textarea id="userText" placeholder="Example: Check benefits for NPI 1234567890 for patient Jane Doe DOB 1984-07-10 female member ID MBR12345 and drug NDC 0000000000."></textarea>
    <div style="margin: 16px 0;">
      <button id="submitButton">Run eligibility check</button>
      <button class="secondary" id="clearButton" type="button">Clear</button>
    </div>
    <div class="sample-buttons">
      <button type="button" onclick="useExample('Check eligibility for NPI 1234567890, patient John Doe born 1980-01-01 male member ID MBR00001, drug NDC 12345-6789.')">covered_no_restrictions sample</button>
      <button type="button" onclick="useExample('Check eligibility for NPI 1234567890, patient Sarah Smith DOB 1975-10-21 female member ID MBR00002, drug NDC PA-0000.')">covered_pa_required sample</button>
      <button type="button" onclick="useExample('Check eligibility for NPI 1234567890, patient Peter Lee DOB 1990-06-15 male member ID MBR00003, drug NDC STEP-1234.')">covered_step_therapy sample</button>
    </div>
    <div style="margin-top: 24px;">
      <h2>Payload and result</h2>
      <pre id="resultArea">Waiting for user input...</pre>
    </div>
  </main>
  <script>
    const resultArea = document.getElementById('resultArea');
    const userText = document.getElementById('userText');
    let currentPayload = {};

    document.getElementById('submitButton').addEventListener('click', async () => {
      await sendRequest();
    });

    document.getElementById('clearButton').addEventListener('click', () => {
      userText.value = '';
      currentPayload = {};
      resultArea.textContent = 'Waiting for user input...';
    });

    async function sendRequest() {
      const text = userText.value.trim();
      if (!text) {
        resultArea.textContent = 'Please enter a natural language request first.';
        return;
      }

      resultArea.textContent = 'Processing...';
      try {
        const response = await fetch('/api/check-benefits', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text, current_payload: currentPayload }),
        });
        const payload = await response.json();
        if (payload.payload) {
          currentPayload = payload.payload;
        }
        resultArea.textContent = JSON.stringify(payload, null, 2);
      } catch (error) {
        resultArea.textContent = 'Error: ' + error.message;
      }
    }

    function useExample(text) {
      userText.value = text;
      sendRequest();
    }
  </script>
</body>
</html>"""


class RequestPayload(BaseModel):
    text: str
    current_payload: Optional[Dict[str, Any]] = None


@app.get("/", response_class=HTMLResponse)
async def homepage() -> HTMLResponse:
    return HTML_PAGE


@app.post("/api/check-benefits")
async def check_benefits(payload: RequestPayload) -> JSONResponse:
    result = mcp.handle_text_input(payload.text, payload.current_payload or {})
    return JSONResponse(result)
