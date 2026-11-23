# SQL & Database Analytics Agent

A natural-language SQL analytics agent built with Google Gemini, LangGraph, SQLAlchemy, SQLGlot and NeMo Guardrails.

The application allows users to ask questions about structured business data in plain English. It converts those questions into SQL queries, validates them before execution, and uses a self-correction workflow to recover from database errors. Results are presented through a Streamlit dashboard with interactive Plotly visualizations.

## Features

- **Natural-language to SQL:** Converts business questions into SQL using Google Gemini.
- **Database schema inspection:** Uses SQLAlchemy reflection to inspect database tables and columns.
- **LangGraph workflow:** Coordinates schema inspection, SQL generation, execution and reflection.
- **Self-correction:** Uses database error messages to regenerate incorrect SQL, with a maximum of three retries.
- **SQL AST validation:** Uses SQLGlot to allow only a single read-only SELECT statement.
- **Input guardrails:** Uses deterministic input screening and NeMo Guardrails to block suspicious requests before they reach the LLM.
- **Interactive dashboard:** Displays generated SQL, execution telemetry, correction history and query results.
- **Automatic visualizations:** Uses Plotly to generate suitable line, bar or pie charts from structured numeric results.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| LLM | Google Gemini |
| Agent orchestration | LangGraph |
| Database | SQLite |
| Database toolkit | SQLAlchemy |
| SQL AST validation | SQLGlot |
| Input security | NeMo Guardrails |
| Dashboard | Streamlit |
| Visualizations | Plotly |
| Testing | Pytest |

## Project Structure

```text
sql-analytics-agent/
├── app/
│   ├── agent/
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   ├── prompts.py
│   │   ├── sql_generator.py
│   │   └── state.py
│   ├── database/
│   │   ├── connection.py
│   │   ├── schema.py
│   │   └── seed.py
│   ├── llm/
│   │   └── gemini_client.py
│   ├── security/
│   │   ├── guardrails.py
│   │   └── sql_validator.py
│   └── ui/
│       └── dashboard.py
├── configs/
│   └── guardrails/
│       ├── actions.py
│       ├── config.yml
│       └── rails/
│           └── input.co
├── data/
├── docs/
├── tests/
├── app.py
├── requirements.txt
├── .env.example
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.11
- A Google Gemini API key
- Git

### 1. Clone the repository

```powershell
git clone https://github.com/Akshatkr09/sql-analytics-agent.git
cd sql-analytics-agent
```

### 2. Create a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file:

```powershell
Copy-Item .env.example .env
```

Add your Gemini API key and configuration:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_selected_gemini_model
DATABASE_URL=sqlite:///./data/analytics.db
MAX_RETRIES=3
```

Keep your `.env` file private. Never commit API credentials to GitHub.

### 5. Create and seed the sample database

```powershell
python -m app.database.seed
```

This creates the SQLite database and populates it with sample data across four tables:

- `customers`
- `products`
- `orders`
- `order_items`

The seed operation is designed to be repeatable without duplicating existing sample records.

## Running the Application

Start the Streamlit dashboard:

```powershell
streamlit run app.py
```

Open the local URL displayed in your terminal, usually:

```text
http://localhost:8501
```

Enter a question in natural language and select **Run analysis**.

Example questions:

- Show orders sorted by date.
- What is the total revenue by order status?
- List the top 5 customers by total spending.
- Show monthly sales trends.

The dashboard displays the execution status, generated SQL, execution time, rows returned, correction retries, logs, result table and an automatic visualization when the result data supports one.

## System Architecture

The agent follows a LangGraph workflow:

1. **Inspect schema:** Reads the database structure using SQLAlchemy.
2. **Generate SQL:** Sends the user question and schema context to Gemini.
3. **Validate SQL:** Parses the generated statement using SQLGlot.
4. **Execute query:** Runs the validated read-only query against SQLite.
5. **Reflect on errors:** If execution fails, the error is passed back to the SQL generator as correction context.
6. **Retry or finish:** The workflow repeats the correction process until successful or the retry limit is reached.

The graph tracks the user query, generated SQL, database result, error message and retry count in its state.

## Security and Guardrails

The application uses multiple security checkpoints:

### Input validation

Raw user input is screened before the workflow reaches schema inspection or Gemini.

Deterministic checks identify suspicious patterns such as:

- Destructive SQL instructions.
- SQL comment and statement-expansion patterns.
- Common tautology-based injection patterns.
- Script tags.

### NeMo Guardrails

The project uses a configured NeMo input rail with a local Python action through a Colang 1.0 flow.

The integration uses NeMo's check-only API and does not invoke a second LLM. If NeMo cannot verify a request, the application blocks it rather than silently proceeding.

The execution state exposes `guardrail_nemo_checked` to indicate whether the NeMo check-only pass ran.

### SQL AST validation

SQLGlot parses generated SQL before database execution.

The validator permits exactly one read-only SELECT query and rejects:

- INSERT
- UPDATE
- DELETE
- DROP
- ALTER
- CREATE
- Multiple SQL statements
- SELECT INTO
- Invalid SQL

These checks help protect the database from destructive generated queries.

## Testing

Run the complete automated test suite from the project root:

```powershell
python -m pytest -v
```

The suite covers:

- LangGraph routing and workflow behavior.
- Database creation, seeding and schema formatting.
- Gemini SQL generation logic.
- SQL self-correction and retry limits.
- SQL AST validation.
- Deterministic input guardrails.
- NeMo Guardrails integration.
- Dashboard result formatting and chart selection.

The M7 verification run completed with **38 passing tests**.

## Manual Verification

### Test 1: SQL self-correction

Start the application:

```powershell
streamlit run app.py
```

Submit:

```text
Show orders sorted by date.
```

Verify that the agent returns the order records. If the generated query initially references an invalid column such as `created_at`, the reflection workflow should use the database error to regenerate the query with the correct column, `order_date`.

### Test 2: SQL injection and destructive command blocking

Submit:

```text
DROP TABLE orders; --
```

Verify that the request is blocked with a security warning and that the database remains intact.

The `orders` table should still exist after the blocked request.

### Test 3: Automated tests

```powershell
python -m pytest -v
```

All tests should pass.

## Environment and Data Safety

The repository includes `.env.example` as a configuration template.

The following local files and directories should not be committed:

- `.env`
- `.venv/`
- `data/analytics.db`

The sample database can be recreated using the database seed script.

## Development Milestones

| Milestone | Implementation |
|---|---|
| M1 | Project scaffold and dependencies |
| M2 | Database setup and schema reflection |
| M3 | Gemini integration and SQL generation |
| M4 | LangGraph workflow |
| M5 | Self-correction and retry mechanism |
| M6 | SQL AST validation and NeMo Guardrails |
| M7 | Streamlit dashboard and Plotly visualizations |

## Repository

GitHub: https://github.com/Akshatkr09/sql-analytics-agent

## Author

Akshat Kumar
