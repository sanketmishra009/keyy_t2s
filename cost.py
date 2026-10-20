import csv
import os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")

# USD per 1M tokens (input, output), standard tier. Output includes thinking tokens.
# Gemini 3.x Flash prices double from Jan 1, 2027: update then.
PRICES = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.6-flash": (0.75, 3.75),
    "gemini-3.1-flash-lite": (0.25, 1.50),
    "openai/gpt-oss-120b": (0.15, 0.60),
    "openai/gpt-oss-20b": (0.075, 0.30),
}

if MODEL_NAME not in PRICES:
    raise RuntimeError(
        f"No price for model '{MODEL_NAME}'. Add it to PRICES in cost.py"
    )

PRICE_IN, PRICE_OUT = PRICES[MODEL_NAME]

COST_FILE = Path(__file__).resolve().parent / "data" / "costs.csv"


def compute_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * PRICE_IN + output_tokens * PRICE_OUT) / 1_000_000


def log_cost(question: str, steps: int, input_tokens: int, output_tokens: int) -> float:
    cost = compute_cost(input_tokens, output_tokens)
    COST_FILE.parent.mkdir(parents=True, exist_ok=True)
    new_file = not COST_FILE.exists()
    with open(COST_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(
                [
                    "timestamp",
                    "model",
                    "question",
                    "steps",
                    "input_tokens",
                    "output_tokens",
                    "cost_usd",
                ]
            )
        writer.writerow(
            [
                datetime.now().isoformat(timespec="seconds"),
                MODEL_NAME,
                question,
                steps,
                input_tokens,
                output_tokens,
                f"{cost:.6f}",
            ]
        )
    return cost
