import os
import base64
import httpx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import uvicorn

app = FastAPI(title="AFIA - Automotive Financial Intelligence Agent")
app.mount("/static", StaticFiles(directory="static"), name="static")

GEMINI_MODEL = "gemini-2.5-flash"

AGENT1_SYSTEM = """You are AFIA Extraction Agent (Agent 1).
You read OEM financial reports for ONE company at a time and extract standardized KPIs.

Respond with exactly three sections:

SECTION 1 - A markdown table with these columns:
KPI | Full Year | Quarter | Confidence

Rows must cover all 10 KPIs:
1. Company Name & Currency
2. Revenue
3. EBIT / Operating Result
4. Operating Margin (%)
5. Cash Metric
6. Net Liquidity
7. Return on Capital
8. Cost of Capital
9. EPS & Dividend per Share
10. Market Cap at 100 EUR/share

Rules:
- Use "Not Reported" where quarterly data is absent
- Use "N/A" where data does not apply
- Calculate Operating Margin yourself if not stated: EBIT divided by Revenue times 100
- For Confidence: High (found directly), Medium (calculated/inferred), Low (estimated)
- Always state the currency next to each number

SECTION 2 - Titled "## KPI Mapping Notes"
Explain any terminology substitutions. State the exact term the company used and what you mapped it to.

SECTION 3 - Titled "## Company Summary"
Write 2 to 3 sentences summarizing the company's financial position."""

AGENT2_SYSTEM = """You are AFIA Analysis Agent (Agent 2).
You receive extracted KPI data from Agent 1 for three automotive OEM companies.
Your job is to combine, compare, and produce a final executive summary.

Respond with exactly three sections:

SECTION 1 - A single combined markdown table with these exact columns:
KPI | BMW Full Year | BMW Quarter | Mercedes-Benz Full Year | Mercedes-Benz Quarter | Volkswagen Full Year | Volkswagen Quarter | Confidence

Use the actual company names from the data provided. Rows must cover:
1. Company Name & Currency
2. Revenue
3. EBIT / Operating Result
4. Operating Margin (%)
5. Cash Metric
6. Net Liquidity
7. Return on Capital
8. Cost of Capital
9. EPS & Dividend per Share
10. Market Cap at 100 EUR/share

Rules:
- Keep all original values and currencies exactly as extracted by Agent 1
- Keep the confidence ratings from Agent 1
- Use "Not Reported" where quarterly data is absent
- Use "N/A" where data does not apply

SECTION 2 - Titled "## KPI Mapping Notes"
Combine and deduplicate all mapping notes from the three Agent 1 outputs.
Organize by company name. Be specific about which company used which term.

SECTION 3 - Titled "## Executive Insights"
Write 5 to 7 bullet points comparing the three companies across:
- Revenue scale and growth
- Profitability (operating margin comparison)
- Cash generation strength
- Liquidity position
- Capital efficiency (return on capital vs cost of capital)
- Any standout risks or strengths
- Overall ranking by financial health

Be specific with numbers. Reference actual values from the table."""


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("templates/index.html") as f:
        return f.read()


@app.post("/api/extract")
async def extract(
    files: List[UploadFile] = File(...),
    prompt: str = Form(...)
):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set. Please check your .env file.")

    parts = []
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            continue
        data = await f.read()
        b64 = base64.standard_b64encode(data).decode("utf-8")
        parts.append({
            "inline_data": {
                "mime_type": "application/pdf",
                "data": b64
            }
        })

    if not parts:
        raise HTTPException(status_code=400, detail="No valid PDF files uploaded.")

    parts.append({"text": prompt})

    payload = {
        "system_instruction": {"parts": [{"text": AGENT1_SYSTEM}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"maxOutputTokens": 16000, "temperature": 0.1}
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, json=payload)
            result = response.json()
            if response.status_code != 200:
                detail = result.get("error", {}).get("message", "Gemini API error")
                raise HTTPException(status_code=500, detail=detail)
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return JSONResponse({"output": text})
    except httpx.TimeoutException:
        raise HTTPException(status_code=500, detail="Request timed out. Try uploading fewer or smaller PDFs.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def analyze(
    prompt: str = Form(...)
):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set. Please check your .env file.")

    payload = {
        "system_instruction": {"parts": [{"text": AGENT2_SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 16000, "temperature": 0.1}
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, json=payload)
            result = response.json()
            if response.status_code != 200:
                detail = result.get("error", {}).get("message", "Gemini API error")
                raise HTTPException(status_code=500, detail=detail)
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            return JSONResponse({"output": text})
    except httpx.TimeoutException:
        raise HTTPException(status_code=500, detail="Request timed out. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8001)
