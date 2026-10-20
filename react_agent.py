import os
from dotenv import load_dotenv


from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from db import db
from tools import TOOLS
from cost import log_cost

from models import gemini_model as model

load_dotenv()


llm = model.bind_tools(TOOLS)
tool_map = {tool.name: tool for tool in TOOLS}
msteps = 50
KEEP_RECENT = 2  # last N tool results stay in full
TRIM_TO = 200  # older results are cut to this many chars


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
- Stop as soon as a query result answers the question.
- If the data can't answer the question, say so.
"""


def run_tool(call: dict) -> str:
    tool = tool_map.get(call["name"])

    if tool is None:
        return f"Error: unknown tool {call['name']}"

    try:
        return str(tool.invoke(call["args"]))
    except Exception as e:
        return f"Error: {e}"


def trim_history(messages: list) -> None:
    # Shorten old tool results in place. Schemas stay so the model can still write SQL.
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    for m in tool_msgs[:-KEEP_RECENT]:
        if m.name != "get_schema" and len(m.content) > TRIM_TO:
            m.content = m.content[:TRIM_TO] + "\n...[old result trimmed]"


def ask(question: str, verbose: bool = False) -> str:
    messages = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]
    input_tokens = output_tokens = 0
    answer = "⚠️   Agent took too many steps. Try a more specific question."

    for step in range(1, msteps + 1):
        reply = llm.invoke(messages)  # Reason
        messages.append(reply)  # keep as-is (thought_signature)

        usage = reply.usage_metadata or {}  # tokens for this one model call
        input_tokens += usage.get("input_tokens", 0)
        output_tokens += usage.get("output_tokens", 0)

        if not reply.tool_calls:  # no tools → final answer
            answer = reply.text
            break

        for call in reply.tool_calls:  # Act
            result = run_tool(call)
            if verbose:
                print(
                    f"\n[step {step}] {call['name']}({call['args']})\n→ {result[:300]}"
                )
            messages.append(
                ToolMessage(content=result, tool_call_id=call["id"])
            )  # Observe

    cost = log_cost(question, step, input_tokens, output_tokens)
    if verbose:
        print(f"\n💰 {input_tokens} in / {output_tokens} out → ${cost:.4f}")
    return answer


if __name__ == "__main__":
    while True:
        q = input("\nAsk (or 'q'): ").strip()
        if q.lower() == "q":
            break
        print("\n" + ask(q, verbose=True))
