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

Note: These reports may be written in German. Extract all data regardless of language and present all output in English. Use the original German term in parentheses when noting terminology mappings.

Read the uploaded financial reports for this company. There is one full year report and one quarterly report.

Using only the data in these reports, extract the following for both the full year and the most recent quarter:

1. Company name
2. Revenue
3. EBIT / Operating Result
4. Operating margin (EBIT margin / Return on Sales) calculated as EBIT divided by Revenue
5. Cash Metric: use the company's preferred core cash KPI
6. Net liquidity / liquidity indicator
7. Return on capital metric: use the company's own value based KPI
8. Cost of Capital / hurdle concept: only extract if explicitly disclosed, otherwise write "Not Reported"
9. EPS and dividend per share: if not shown in the report write "N/A"
10. Market cap if share value would be 100 EUR per share: calculate as total shares outstanding times 100. If not available write "N/A"

If the exact metric name is not found, use the closest equivalent and clearly state what was substituted and why.

If data is not available in the quarterly report but exists in the full year report, write "Not Reported" for the quarterly value.

Assign confidence to each value: High (found directly), Medium (calculated), Low (estimated).

Output a markdown table with columns: KPI | Full Year | Quarter | Confidence
Then a KPI Mapping Notes section explaining every terminology substitution.
Then a short company summary."""

AGENT2_SYSTEM = """You are AFIA Analysis Agent (Agent 2). You receive extracted KPI data from Agent 1 for three automotive OEM companies: BMW, Mercedes-Benz, and Volkswagen.

Your task is to produce a final executive summary suitable for senior decision-makers.

SECTION 1: Combined table
Create a single markdown table with these columns:
KPI | BMW Full Year | BMW Quarter | Mercedes-Benz Full Year | Mercedes-Benz Quarter | Volkswagen Full Year | Volkswagen Quarter | Confidence

Rows must include:
1. Company name
2. Revenue
3. EBIT / Operating Result
4. Operating margin (EBIT margin / Return on Sales) as EBIT divided by Revenue
5. Cash Metric (company preferred core cash KPI)
6. Net liquidity / liquidity indicator
7. Return on capital metric (each company's value based KPI)
8. Cost of Capital / hurdle concept (only where disclosed, otherwise Not Reported)
9. EPS and dividend per share (N/A if not disclosed)
10. Market cap if share value would be 100 EUR per share (N/A if not available)

Rules for the table:
Rules for the table:
Copy each value exactly as Agent 1 extracted it. Do not swap a return on capital figure for Value Added or a profit margin. If Agent 1 gives RoCE, RONA, or RoI, keep it.
Keep the confidence ratings from Agent 1.
Use "Not Reported" where quarterly data is absent.
Use "N/A" where data does not apply to a company.
Show all money values in millions of euros as plain numbers (for example 133,453), except market cap which is in billions (for example 61.6 billion). Convert German Mio. and Mrd. into the same English units.

SECTION 2: KPI Mapping Notes
Write a short text summary organized by company explaining which data output has been replaced by a similar KPI and why. Include the original term used by the company in parentheses. This section must make it clear to a reader which metrics are directly comparable across companies and which are approximate equivalents.

SECTION 3: Executive Insights
Write 5 to 7 specific observations comparing the three companies across:
Revenue scale
Profitability and operating margin trends
Cash generation strength
Liquidity position
Capital efficiency (return on capital versus cost of capital where available)
Any standout risks or strengths

Use actual numbers from the table. Do not use vague language. Each insight should help a decision-maker understand how these companies compare financially."""


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