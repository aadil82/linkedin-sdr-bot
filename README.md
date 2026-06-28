#  LinkedIn SDR Agent

**AI-powered Sales Development Representative agent** that identifies high-quality B2B leads from LinkedIn hiring signals, scores them, generates personalized outreach emails, and produces daily reports.

---

##  Features

- **Lead Scoring** — Multi-dimensional scoring (0-100) based on technology match, hiring activity, company size, industry, seniority, growth indicators, and consulting likelihood
- **Personalized Email Generation** — Context-aware outreach drafts mentioning the prospect's hiring activity and technology stack
- **Duplicate Detection** — Built-in lead history prevents contacting the same person twice within 90 days
- **Excel Reports** — Structured output with all lead details, scores, and email drafts
- **Daily Summaries** — Human-readable text reports with top technologies, industries, and locations
- **GitHub Actions** — Automated daily runs (weekdays at 08:00 AM IST)
- **Extensible** — Easy to add technologies, adjust scoring weights, or integrate a CRM

---

##  Quick Start

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository (or download the files)
cd linkedin-sdr-agent

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Edit `src/config.py` with your real company details:

```python
COMPANY_NAME = "Your Company Name"
SENDER_NAME = "Your Name"
SENDER_TITLE = "Business Development Manager"
SENDER_EMAIL = "you@yourcompany.com"
```

### Run

```bash
# Process a CSV of leads you collected from LinkedIn
python -m src.lead_engine --input data/input/leads_2026-06-27.csv --min-score 70

# View today's summary
python -m src.lead_engine --summary

# View history statistics
python -m src.lead_engine --history-stats

# Print help
python -m src.lead_engine --help
```

---

##  Project Structure

```
linkedin-sdr-agent/
├── .github/workflows/
│   └── daily-lead-generation.yml   # GitHub Actions cron (weekdays 08:00 IST)
├── src/
│   ├── __init__.py                  # Package init
│   ├── config.py                    # Company profile, tech keywords, scoring weights
│   └── lead_engine.py               # Scoring, email generation, reporting
├── templates/
│   └── leads_input_template.csv     # CSV format for LinkedIn data (see file for columns)
├── data/
│   ├── input/                       # Your daily CSV files go here
│   ├── output/                      # Generated Excel reports & summaries
│   └── history/                     # leads_history.json (auto-managed CRM)
├── docs/
│   └── WORKFLOW.md                  # Detailed daily usage guide
├── requirements.txt                 # pandas, openpyxl
├── .gitignore
├── LICENSE
└── README.md
```

---

##  Daily Workflow

###  Morning ( ~30 min)

1. **Search LinkedIn** for hiring signals and copy data into `data/input/leads_YYYY-MM-DD.csv`
2. **Run the engine**: `python -m src.lead_engine --input data/input/leads_2026-06-27.csv`
3. **Review** the generated Excel report in `data/output/`
4. **Get approval** for each email draft before sending
5. **Send** approved emails via Outlook

###  Evening ( ~10 min)

1. Review the daily summary
2. Update follow-up tasks
3. Archive inputs

See [docs/WORKFLOW.md](docs/WORKFLOW.md) for the complete guide.

---

##  Scoring System

| Dimension | Max Score | Description |
|-----------|-----------|-------------|
| Technology Match | 30 | Number of matching tech keywords |
| Hiring Activity | 20 | Hiring signal phrases detected |
| Company Size | 10 | Larger companies score higher |
| Industry Relevance | 10 | IT, finance, healthcare, etc. |
| Decision Maker Seniority | 15 | CTO > Director > Manager > Recruiter |
| Growth Indicators | 10 | Hiring frequency, funding, etc. |
| Consulting Likelihood | 5 | Industry and role alignment |

**Threshold**: Only leads scoring **≥ 70** are qualified for outreach.

---

##  Compliance

- **LinkedIn Terms of Service** — Only uses publicly available information
- **GDPR** — Lawful basis required for processing personal data
- **CAN-SPAM** — Include opt-out in every email
- **No scraping** — This tool does not scrape private data
- **Human approval** — Every email must be manually approved before sending

---

##  Extending

- **Add technologies**: Edit `TECHNOLOGY_KEYWORDS` in `src/config.py`
- **Tune scoring**: Adjust `ScoringWeights` in `src/config.py`
- **CRM integration**: Replace the stub in `process_input_csv()` with your CRM API
- **More languages**: Install additional dependencies as needed

---

##  License

MIT — see [LICENSE](LICENSE).
