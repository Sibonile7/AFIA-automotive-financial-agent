# AFIA — Automotive Financial Intelligence Agent

Built by Sibonile Mthunzi for the Magna Global AI Internship assignment.

## Setup (takes about 2 minutes)

### 1. Install dependencies

Open your terminal, go into this folder, and run:

```
pip install -r requirements.txt
```

### 2. Add your API key

Copy the example env file:

```
cp .env.example .env
```

Open `.env` and replace `your_api_key_here` with your actual Anthropic API key.
You can get one at https://console.anthropic.com

### 3. Start the app

```
python start.py
```

Then open your browser and go to:

```
http://localhost:8000
```

## How to use it

1. Upload up to 6 PDF files (annual and quarterly reports for up to 3 OEM companies)
2. The agent instructions are already filled in. You can edit them if you want.
3. Click Run agent
4. The app extracts KPIs, maps terminology across companies, scores confidence, and produces an executive summary table
5. Use the Copy button to copy the full output for your submission

## What the agent produces

- A structured table with full year and quarterly data for all 3 companies
- A KPI Mapping Notes section explaining any terminology substitutions
- An Executive Insights section with 4 to 5 comparative bullet points
- A Confidence column showing High, Medium, or Low for each data point

## Agent architecture

PDF reports → Document reading → KPI extraction → KPI mapping → Validation → Executive summary

## Built with

- Python 3.12
- FastAPI for the web server
- Anthropic Claude claude-opus-4-5 for document analysis
- Plain HTML and JavaScript for the frontend
