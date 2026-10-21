# Text2SQL Agent

Ask questions about a MySQL database in plain English. An LLM agent finds the right tables, writes a `SELECT` query, runs it, and answers in plain English (showing the SQL it used).

## How it works

```
Question → LLM ──tool call──> list_tables / get_schema / run_query
            ↑                          │
            └──────── tool result ─────┘   (loop until the LLM answers)
```

- **ReAct loop** (`react_agent.py`): Reason → Act (call a tool) → Observe (tool result) → repeat, up to 50 steps.
- **Tools** (`tools.py`):
  - `list_tables`: shows which tables the agent may query
  - `get_schema`: shows columns + 1 sample row for the tables asked for
  - `run_query`: runs one `SELECT` query
- **Guardrails**:
  - only a single `SELECT` statement is allowed
  - `LIMIT 5` is added if the query has no `LIMIT`
  - results are cut off after 2000 chars
  - the agent only sees the tables listed in `db.py`
- **Context trimming**: older tool results are shortened so the prompt doesn't grow too big (schemas are kept in full).
- **Cost tracking** (`cost.py`): counts tokens and logs the cost of each question to `data/costs.csv`.
- **Serving** (`app.py`): a FastAPI API plus a Gradio chat UI, both password-protected.

## Files

| File | Purpose |
|---|---|
| `db.py` | Connects to the database; sets the list of tables the agent may use |
| `tools.py` | The 3 agent tools + guardrails |
| `models.py` | LLM clients (Gemini, Groq) |
| `react_agent.py` | Hand-written ReAct loop (used by the app) |
| `agent.py` | Same agent built with LangChain's `create_agent` (for comparison) |
| `cost.py` | Token prices + cost logging |
| `app.py` | FastAPI `/health`, `/ask` + Gradio UI at `/ui` |
| `Dockerfile` | Container image |

## Run locally

### 1. What you need
- Python 3.11+
- A MySQL database you can reach, containing the tables listed in `db.py`. Use a **read-only** DB user.
- A Gemini API key (or a Groq key, see step 4)

### 2. Install
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure `.env`
```bash
cp .env.example .env
```
Fill in:

| Variable | Example | Purpose |
|---|---|---|
| `DB_URL` | `mysql+pymysql://user:pass@host:3306/dbname` | Database connection |
| `GEMINI_API_KEY` | `...` | Gemini API key |
| `MODEL_NAME` | `gemini-3.8-flash` | Must be a key in `PRICES` in `cost.py` |
| `APP_API_KEY` | any long random string | Required in the `X-API-Key` header for `/ask` |
| `UI_USER` / `UI_PASS` | your choice | Login for the Gradio UI |
| `GROQ_API_KEY` | `...` | Only if you use the Groq model |

### 4. (Optional) Change the tables or model
- **Tables**: edit `TABLES` in `db.py` to match your database.
- **Model**: in `react_agent.py`, switch `gemini_model` to `groq_model`, and set `MODEL_NAME` to a Groq model listed in `cost.py` (e.g. `openai/gpt-oss-120b`).

### 5. Check each part
```bash
python db.py        # prints dialect, tables, schema → DB works
python tools.py     # runs each tool once → tools work
```

### 6. Run
**Terminal (shows each step + cost):**
```bash
python react_agent.py
```

**API + UI:**
```bash
python app.py
```
- UI: http://localhost:8001/ui (log in with `UI_USER` / `UI_PASS`)
- Health: http://localhost:8001/health
- API:
  ```bash
  curl -X POST http://localhost:8001/ask \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $APP_API_KEY" \
    -d '{"question": "How many cards are there?"}'
  ```

**Docker:**
```bash
docker build -t text2sql .
docker run --env-file .env -p 8001:8001 text2sql
```
> If MySQL runs on your own machine, use `host.docker.internal` instead of `localhost` in `DB_URL`.

## Known issues
- `GROQ_API_KEY` is missing from `.env.example`.
- In `agent.py`, the loop calls `ask(q)` but never prints the result.
- Each question is answered on its own; the chat UI doesn't remember earlier questions.
