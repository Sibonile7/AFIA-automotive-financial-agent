# AFIA — Automotive Financial Intelligence Agent

A multi-agent system that reads automotive OEM financial reports (annual and quarterly), extracts key performance indicators, maps inconsistent terminology across companies, and produces an executive summary table with cross-company analysis.

Built by **Sibonile Mthunzi** for the Magna Global AI Internship assignment (R00242813).

## What it does

AFIA processes PDF financial reports from three automotive OEMs (BMW, Mercedes-Benz, Volkswagen) and extracts 10 standardized KPIs:

- Company name
- Revenue
- EBIT / Operating Result
- Operating margin (EBIT divided by Revenue)
- Cash Metric (company preferred core cash KPI)
- Net liquidity / liquidity indicator
- Return on capital metric (each company's value based KPI)
- Cost of Capital / hurdle concept (only where disclosed)
- EPS and dividend per share
- Market cap if share value would be 100 EUR per share

The reports use different languages (German and English) and different terminology for the same financial concepts. AFIA handles this by mapping equivalent metrics and clearly documenting every substitution.

## Multi-agent architecture

The system uses two agents in a pipeline:

```
PDF reports (2 per company)
        |
        v
  Agent 1: Extraction Agent (runs 3 times, once per company)
        |
        v
  Structured KPI data x3
        |
        v
  Agent 2: Analysis Agent (runs once across all 3 companies)
        |
        v
  Final executive summary table + KPI mapping notes + insights
```

**Agent 1 (Extraction)** reads one company's annual and quarterly report. It identifies the correct financial figures, maps non-standard terminology to the requested KPI names, and assigns a confidence level (High, Medium, Low) to each data point.

**Agent 2 (Analysis)** takes the combined output from all three Agent 1 runs. It merges the data into a single comparison table, consolidates the KPI mapping notes by company, and writes 5 to 7 executive insights comparing profitability, cash generation, liquidity, and capital efficiency across all three OEMs.

## Why two agents instead of one

Automotive annual reports are large PDF documents (often 100+ pages). Processing all six reports in a single request would exceed token limits and reduce extraction accuracy. By splitting extraction and analysis into separate agents:

- Each extraction run focuses deeply on one company
- Confidence scoring is more accurate with smaller context
- The analysis agent works with clean, structured data rather than raw PDFs
- The pipeline is easier to debug when a value looks wrong

## Tech stack

- **Python 3.12** with FastAPI for the web server
- **Gemini 2.5 Flash** via Google Generative AI API for document analysis
- **Plain HTML, CSS, and JavaScript** for the frontend (no frameworks)
- PDFs are sent as base64-encoded documents directly to the API

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/Sibonile7/AFIA-automotive-financial-agent.git
cd AFIA-automotive-financial-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your API key

```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_key_here
```

Get a free key at https://aistudio.google.com/apikey

### 4. Create the static folder

```bash
mkdir static
```

### 5. Run the app

```bash
python start.py
```

Open your browser at http://localhost:8001

## How to use

1. Go to the **Extract** tab
2. Upload 2 PDFs for one company (annual report + quarterly report)
3. Click **Run Agent 1**
4. Click **Save to Agent 2 input**
5. Repeat steps 2 to 4 for the other two companies
6. Go to the **Analyze** tab
7. Click **Run Agent 2**
8. The final executive summary table appears with KPI mapping notes and cross-company insights

## Project structure

```
afia/
  app.py              # FastAPI backend with Agent 1 and Agent 2 endpoints
  start.py            # Server startup script (loads .env)
  requirements.txt    # Python dependencies
  .env.example        # Template for API key
  static/             # Static assets folder
  templates/
    index.html        # Frontend with all 4 tabs (Extract, Analyze, Architecture, Agent prompts)
```

## Confidence scoring

Every extracted data point is tagged with a confidence level:

- **High** means the value was found directly in the report
- **Medium** means the value was calculated or inferred (for example, operating margin computed from EBIT and revenue)
- **Low** means the value was estimated from partial data

This prevents decision-makers from treating uncertain figures as confirmed facts.

## KPI terminology mapping

Automotive companies use different terms for the same financial concepts. Examples from this project:

| Requested KPI | BMW uses | Mercedes-Benz uses | Volkswagen uses |
|---|---|---|---|
| Revenue | Revenues | Revenue | Umsatzerlöse (Sales Revenue) |
| EBIT | EBIT | EBIT | Operatives Ergebnis (Operating Result) |
| Cash Metric | Automotive Free Cash Flow | Free Cash Flow Industrial | Netto-Cashflow Automobile |
| Return on Capital | RoCE (Automotive) | ROCE | RoI (Automotive) |

The agent documents every substitution so the reader knows exactly which metrics are directly comparable and which are approximate equivalents.

## Author

**Sibonile Mthunzi**
M.Eng Artificial Intelligence, Technische Hochschule Deggendorf

- Portfolio: [sibonilemthunzi.com](https://sibonilemthunzi.com)
- GitHub: [github.com/Sibonile7](https://github.com/Sibonile7)
- Email: bonniemthunzi@gmail.com