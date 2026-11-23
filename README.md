# SQL & Database Analytics Agent

M1 starter scaffold for the SQL & Database Analytics Agent with Self-Correction & Guardrails.

## Requirements
- Python 3.11
- Gemini API key (needed in a later milestone)

## Windows PowerShell setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Keep `.env` local. Never commit API credentials.

## Current milestone
M1 establishes the project structure and dependencies. Database, Gemini, LangGraph, guardrails, dashboard, and tests will be implemented in later milestones.
