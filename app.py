import os
import uvicorn
import gradio as gr
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from react_agent import ask

load_dotenv()

app = FastAPI(title="Text2SQL Agent")
APP_API_KEY = os.getenv(
    "APP_API_KEY"
)  # protects your company DB from the public internet
UI_USER = os.getenv("UI_USER")  # protects /ui
UI_PASS = os.getenv("UI_PASS")


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    answer: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(body: AskRequest, x_api_key: str | None = Header(default=None)):
    # Simple auth: caller must send the secret key in the X-API-Key header
    if not APP_API_KEY or x_api_key != APP_API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")

    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="'question' is required")

    return AskResponse(question=question, answer=ask(question))


def chat(message: str, history: list) -> str:
    # Each question is answered independently; history is only for display
    return ask(message)


demo = gr.ChatInterface(
    fn=chat,
    title="Keyy t2s tool.",
    description="Ask questions about the database in plain English.",
    examples=[
        "How many cards are there?",
        "How many different portals are there in accelerated rewards?",
    ],
)

if not (UI_USER and UI_PASS):
    raise RuntimeError("Set UI_USER and UI_PASS in .env — the UI must not be public")

app = gr.mount_gradio_app(app, demo, path="/ui", auth=(UI_USER, UI_PASS))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
