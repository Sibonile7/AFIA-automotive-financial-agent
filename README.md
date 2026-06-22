# AFIA, Automotive Financial Intelligence Agent

A two agent system that reads automotive OEM financial reports, extracts key financial numbers, maps the different terms each company uses, and produces one executive summary table with cross company analysis.

Built by **Sibonile Mthunzi** 
## What it does

AFIA reads the PDF financial reports of three automotive OEMs (BMW, Mercedes-Benz, Volkswagen) and pulls out 10 standard KPIs:

- Company name
- Revenue
- EBIT / Operating Result
- Operating margin (EBIT divided by Revenue)
- Cash metric (each company's preferred core cash KPI)
- Net liquidity / liquidity indicator
- Return on capital (each company's own value based KPI)
- Cost of capital / hurdle concept (only where disclosed)
- EPS and dividend per share
- Market cap if the share price were 100 EUR

The reports are written in two languages (German and English) and each company uses different words for the same number. AFIA handles this by mapping the equivalent terms and writing down every swap it makes.

## How it works: two agents

The system uses two agents in a pipeline:

```
PDF reports (2 per company)
        |
        v
  Agent 1: the reader (runs 3 times, once per company)
        |
        v
  Clean KPI data x3
        |
        v
  Agent 2: the analyst (runs once across all 3 companies)
        |
        v
  Final summary table + mapping notes + insights
```

**Agent 1 (the reader)** reads one company's annual and quarterly report. It finds the right numbers, maps the company's wording to the requested KPI names, and gives each value a confidence level (High, Medium, or Low).

**Agent 2 (the analyst)** takes the output from all three Agent 1 runs. It builds one comparison table, combines the mapping notes by company, and writes 5 to 7 insights comparing profitability, cash, liquidity, and capital efficiency across the three companies.

## Why two agents instead of one

The annual reports are large, often 400+ pages each. Sending all six reports in one request would go past the limits and lower accuracy. Splitting the work into two agents helps in a few ways:

- Each extraction run focuses on one company, so it reads more carefully
- Confidence scoring is more reliable with a smaller amount of text at a time
- The analyst agent works with clean, structured data instead of raw PDFs
- When a number looks wrong, it is easy to see which step produced it

I used the free Gemini API because I did not have a Copilot or paid subscription. The free tier has a smaller limit on how much text it can read at once, and that limit is exactly why one big prompt would not work. So the constraint pushed me toward a cleaner design.

## Checking the work by hand

AI can make mistakes, so I checked every value against the source reports myself. The agent was right most of the time, but I found a few cases where it was inconsistent and corrected them.

The main one was BMW return on capital. Unlike Mercedes (one clear RONA figure) and Volkswagen (one clear RoI figure), BMW does not publish a single headline return on capital at group level. So the agent picked a different number on each run: Value Added, then Group Return on Equity, then Not Reported. I tried fixing it through the prompt, but the value stayed unstable. In the end I stopped trusting the prompt for that one cell and verified it against the report. The BMW annual report states the RoCE for the Automotive segment is 9.0%, so I used that and corrected it by hand.

This is the real lesson from the project: an AI agent gets you most of the way, but a human check on the source is what makes the output trustworthy.

## Tech stack

- **Python 3.12** with FastAPI for the web server
- **Gemini 2.5 Flash** through the Google Generative AI API for reading the documents
- **Plain HTML, CSS, and JavaScript** for the frontend, no frameworks
- PDFs are sent as base64 encoded documents straight to the API

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
2. Upload 2 PDFs for one company (annual report and quarterly report)
3. Click **Run Agent 1**
4. Click **Save to Agent 2 input**
5. Repeat steps 2 to 4 for the other two companies
6. Go to the **Analyze** tab
7. Click **Run Agent 2**
8. The final summary table appears with mapping notes and cross company insights

## Project structure

```
afia/
  app.py              # FastAPI backend with Agent 1 and Agent 2 endpoints
  start.py            # Server startup script (loads .env)
  requirements.txt    # Python dependencies
  .env.example        # Template for the API key
  static/             # Static assets folder
  templates/
    index.html        # Frontend with all 4 tabs (Extract, Analyze, Architecture, Agent prompts)
```

## Confidence scoring

Every value is tagged with a confidence level:

- **High** means the value was found directly in the report
- **Medium** means the value was calculated, for example operating margin worked out from EBIT and revenue
- **Low** means the value was estimated from partial data

This keeps a reader from treating an uncertain figure as a confirmed fact.

## Terminology mapping

Each company uses different words for the same idea. Examples from this project:

| Requested KPI | BMW uses | Mercedes-Benz uses | Volkswagen uses |
|---|---|---|---|
| Revenue | Revenues | Revenue | Umsatzerlöse |
| EBIT | EBIT | EBIT | Operatives Ergebnis |
| Cash metric | Free cash flow (Automotive) | Free cash flow of the industrial business | Netto-Cashflow (Automobile) |
| Return on capital | RoCE (Automotive) | RONA (Return on net assets) | RoI (Automobile) |
| Cost of capital | WACC | Cost of capital rate (Group) | Mindestverzinsungsanspruch |

The agent writes down every swap so the reader knows which numbers are directly comparable and which are close equivalents.

## Author

**Sibonile Mthunzi**
M.Eng Artificial Intelligence, Technische Hochschule Deggendorf

- Portfolio: [sibonilemthunzi.com](https://sibonilemthunzi.com)
- GitHub: [github.com/Sibonile7](https://github.com/Sibonile7)
- Email: bonniemthunzi@gmail.com
