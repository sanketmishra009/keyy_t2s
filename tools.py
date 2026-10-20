import re
from langchain_core.tools import tool
from db import db

MAX_RESULT_CHARS = 2000


@tool
def list_tables() -> str:
    "List all tables the agent can query."
    return ", ".join(db.get_usable_table_names())


@tool
def get_schema(tables: str) -> str:
    """Get columns and sample rows for tables. Input: comma-separated table names, e.g. 'orders, customers'."""
    names = [t.strip() for t in tables.split(",")]
    return db.get_table_info_no_throw(names)


@tool
def run_query(query: str) -> str:
    """Run a single MySQL SELECT query and return the rows. Always call get_schema first."""
    q = query.strip().rstrip(";")

    # Guardrail 1: only one SELECT statement
    if not re.match(r"(?is)^select\b", q) or ";" in q:
        return "Error: only a single SELECT query is allowed."

    # Guardrail 2: cap the number of rows returned
    if not re.search(r"(?i)\blimit\s+\d+", q):
        q += " LIMIT 5"

    result = db.run_no_throw(q)

    # Guardrail 3: cap the size of the result
    if len(result) > MAX_RESULT_CHARS:
        result = (
            result[:MAX_RESULT_CHARS]
            + "\n...[truncated: aggregate or select fewer columns]"
        )
    return result


TOOLS = [list_tables, get_schema, run_query]


if __name__ == "__main__":
    print(list_tables.invoke({}))
    print(get_schema.invoke({"tables": db.get_usable_table_names()[0]}))
    print(run_query.invoke({"query": "SELECT 1"}))
