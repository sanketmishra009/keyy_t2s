import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.errors import GraphRecursionError
from db import db
from tools import TOOLS

load_dotenv()

model = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

SYSTEM_PROMPT = f"""You are a {db.dialect} expert who answers questions using the company database.

Steps:
1. Call list_tables to see the available tables.
2. Call get_schema for the relevant tables. Never guess column names.
3. Write ONE SELECT query and run it with run_query.
4. If the query errors, read the error, fix the SQL, and try again.
5. Answer in plain English, and show the SQL you used.

Rules:
- Only SELECT. Never modify data.
- Select only the columns you need, not SELECT *.
- If the data can't answer the question, say so.
"""

agent = create_agent(model, tools=TOOLS, system_prompt=SYSTEM_PROMPT)


def ask(question: str) -> str:
    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"recursion_limit": 50},
        )
        return result["messages"][-1].text  # final AI message, text only
    except GraphRecursionError:
        return "⚠️  Agent took too many steps. Try a more specific question."


if __name__ == "__main__":
    while True:
        q = input("\nAsk (or 'q'): ").strip()
        if q.lower() == "q":
            break
        ask(q)


# sample query: how many portls are there in accelerated rewards ?
