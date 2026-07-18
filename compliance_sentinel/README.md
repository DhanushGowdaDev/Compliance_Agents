# ⚖️ Compliance Sentinel v2.0 (DPA Edition)

**A highly specialized, audit-ready contract risk-scoring swarm.**  
Analyzes SaaS Vendor Data Processing Agreements (DPAs) against GDPR, CCPA/CPRA, and commercial best practices. Powered by NVIDIA NIM or Local Ollama LLMs.

---

## 🌟 Key Features

- **Multi-Agent Swarm**: Clauses are evaluated in parallel by a `legal_agent`, `data_privacy_agent`, and `commercial_agent`.
- **Heuristic Benchmarker**: Fast, offline evaluation against market standards before invoking LLMs.
- **Redline Generator**: Automatically suggests compliant, commercial redlines for any clauses flagged as High or Medium risk.
- **Mediator Agent**: Intelligently proposes 1-2 compromise options when a Vendor clause conflicts with a Buyer's desired redline.
- **Audit Logger**: Full SQLite-backed persistence for the entire lifecycle (rating → redline → compromise → human override).
- **Premium Dashboard**: A responsive, dark-mode GUI with a 2D interactive risk map, detail panels, and human-in-the-loop override capabilities.
- **Local LLM Support**: Seamlessly switch between cloud (NVIDIA NIM) and local execution (Ollama).

---

## 📂 Project Structure

```
compliance_sentinel/
├── run.py                        # Pipeline entry point
├── server.py                     # FastAPI server for the dashboard API
├── swarm.py                      # Core swarm orchestration logic
├── fetch_cuad.py                 # Downloads sample contracts from the CUAD dataset
├── .env.example                  # Environment configuration template
│
├── dashboard/                    # Frontend GUI
│   ├── index.html                # Premium dark-mode UI
│   └── app.js                    # Plotly chart & interaction logic
│
├── orchestrator/
│   └── tools/
│       ├── aggregator.py         # Merges multi-agent ratings into 2D risk maps
│       ├── audit_logger.py       # SQLite tracking
│       ├── clause_benchmarker.py # Offline heuristic engine
│       ├── clause_splitter.py    # Regex-based clause tokenizer
│       ├── pdf_extractor.py      # PDF text extraction (pdfplumber)
│       └── redline_generator.py  # Fixes flagged clauses
│
├── legal_agent/                  # R1–R6: indemnification, liability, termination
├── data_privacy_agent/           # R1–R7: GDPR/CCPA, sub-processors, breach notice
├── commercial_agent/             # R1–R6: payment, SLA, pricing, damages
└── mediator_agent/               # Generates compromise proposals
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
pip install fastapi uvicorn pdfplumber openai python-dotenv datasets
```

### 2. Configure Environment

Copy the template and configure your API:

```bash
cp .env.example .env
```

**For NVIDIA NIM:**
```env
NIM_API_KEY=nvapi-...
NIM_BASE_URL=https://integrate.api.nvidia.com/v1/
DEFAULT_MODEL=meta/llama-3.3-70b-instruct
```

**For Local Ollama (e.g., qwen3, mistral):**
```env
NIM_API_KEY=ollama
NIM_BASE_URL=http://localhost:11434/v1/
DEFAULT_MODEL=qwen3:latest
```

### 3. Run the Swarm

You can run the pipeline on your own contract, or fetch sample commercial contracts from the Hugging Face CUAD dataset:

```bash
# Fetch CUAD samples
python fetch_cuad.py

# Process a contract
python run.py examples/cuad_contract_1.txt
```

### 4. View the Dashboard

Start the FastAPI server:

```bash
python server.py
```
Open **http://localhost:8765** in your browser to view the interactive 2D risk map, review redlines, and accept/reject agent findings via the Audit Trail.

---

## 🤖 Agent Ruleset Summary

### ⚖️ Legal Agent
- **R1**: Indemnification (Requires cap/scope)
- **R2**: Limitation of Liability (Must be mutual)
- **R3**: Termination (Requires cure period)
- **R4**: Governing Law (Must be explicit)
- **R5**: Force Majeure
- **R6**: Assignment

### 🔒 Data Privacy Agent
- **R1**: Cross-border transfers (SCCs)
- **R2**: Breach notification (72-hour notice)
- **R3**: Retention/deletion
- **R4**: CCPA Service Provider designation
- **R5**: CCPA No-Sale certification
- **R6**: Subprocessors (30-day notice)
- **R7**: Security measures

### 💼 Commercial Agent
- **R1**: Payment terms
- **R2**: Late payment penalties
- **R3**: SLA metrics
- **R4**: Price change / Escalation caps
- **R5**: Auto-renewal opt-outs
- **R6**: Liquidated damages proportionality
