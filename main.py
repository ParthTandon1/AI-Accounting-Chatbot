import os
import json
import re
import time
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from pathlib import Path

# ============================================================
# STARTUP — load files once when the server starts,
# not on every request (expensive to re-read files repeatedly)
# Files are loaded relative to this script so running from a
# different CWD won't raise FileNotFoundError.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

with open(BASE_DIR / 'system_prompt.txt', 'r', encoding='utf-8') as f:
    SYSTEM_PROMPT_TEMPLATE = f.read()

with open(BASE_DIR / 'value_lookup.json', 'r', encoding='utf-8') as f:
    VALUE_MAP = json.load(f)

NVIDIA_API_KEY = "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"  # replace with your actual key
DB_PATH = "accounting.db"

app = FastAPI()

# CORS — allows your HTML frontend (running on a different port
# or opened directly as a file) to call this backend.
# Without this, browsers block cross-origin requests entirely.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# REQUEST MODEL
# Defines what JSON shape this endpoint expects to receive.
# {"question": "What is the total GST liability?"} is all it needs.
# ============================================================

class QuestionRequest(BaseModel):
    question: str

# ============================================================
# HELPER FUNCTIONS
# These are the exact functions you already built and tested.
# ============================================================

def get_candidate_matches(question):
    question_lower = question.lower()
    matches = {}
    for key, candidates in VALUE_MAP.items():
        if len(key) < 3:
            continue
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, question_lower):
            matches[key] = candidates
    return matches

def build_system_prompt(question):
    matches = get_candidate_matches(question)
    matches_json = json.dumps(matches, indent=2)
    return SYSTEM_PROMPT_TEMPLATE.replace(
        "{candidate_matches_json}", matches_json
    )

def generate_sql(question, retries=3, wait=5):
    """Stage 3: call Nemotron to convert question -> SQL."""
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="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"
    )
    system_prompt = build_system_prompt(question)

    for attempt in range(retries):
        try:
            completion = client.chat.completions.create(
                model="nvidia/nemotron-3-ultra-550b-a55b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": question}
                ],
                temperature=0.2,
                top_p=0.95,
                max_tokens=1000,
                extra_body={
                    "chat_template_kwargs": {"enable_thinking": True},
                    "reasoning_budget": 4096
                },
                stream=False
            )
            sql = completion.choices[0].message.content.strip()
            return sql
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "403" in error_str:
                raise HTTPException(
                    status_code=500,
                    detail=f"Nemotron auth failed: {e}"
                )
            if attempt < retries - 1:
                time.sleep(wait)
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Nemotron unavailable after {retries} attempts: {e}"
                )

def is_safe_sql(sql):
    """
    Stage 4 safety check.
    Only allow SELECT statements.
    Reject anything that could modify or destroy data.
    """
    sql_upper = sql.strip().upper()
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP",
                 "ALTER", "CREATE", "TRUNCATE", "REPLACE"]
    if not sql_upper.startswith("SELECT"):
        return False
    for word in forbidden:
        if word in sql_upper:
            return False
    return True

def run_sql(sql):
    """Stage 5: execute the SQL against accounting.db."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        # Convert to list of dicts — clean JSON-serializable format
        results = [dict(zip(columns, row)) for row in rows]
        return results
    except sqlite3.Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"SQL execution error: {e}. Generated SQL was: {sql}"
        )
    finally:
        conn.close()

def generate_answer(question, sql, results):
    """
    Stage 6: call Nemotron again to convert
    raw SQL results into a natural language answer.
    """
    print("=== Stage 6 starting ===")  # add this line
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="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"
    )

    results_text = json.dumps(results, indent=2)

    phrasing_prompt = f"""You are a helpful accounting assistant.
A user asked: "{question}"

The following SQL query was run against the database:
{sql}

The results were:
{results_text}

Write a clear, concise answer to the user's question based on these results.
Use Indian number formatting where appropriate (lakhs, crores).
If the result is negative for an expense or income account, explain what that likely means.
Do not mention SQL or databases in your answer.
Keep the answer to 2-3 sentences maximum."""

    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[
                {"role": "user", "content": phrasing_prompt}
            ],
            temperature=0.3,
            max_tokens=600,
            extra_body={
                "chat_template_kwargs": {"enable_thinking": True},
                "reasoning_budget": 1024
            },
            stream=False
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Stage 6 phrasing error: {e}")
        return f"Results: {results_text}"

# ============================================================
# THE ENDPOINT
# POST /ask  — receives a question, returns an answer
# ============================================================

@app.post("/ask")
def ask(request: QuestionRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # Stage 3: question -> SQL
    sql = generate_sql(question)

    # Stage 4: safety check
    if not is_safe_sql(sql):
        raise HTTPException(
            status_code=400,
            detail=f"Generated SQL failed safety check: {sql}"
        )

    # Stage 5: run SQL against database
    results = run_sql(sql)

    # Stage 6: results -> natural language
    answer = generate_answer(question, sql, results)

    # Return everything — useful for debugging, can strip later
    return {
        "question": question,
        "sql": sql,
        "results": results,
        "answer": answer
    }

# ============================================================
# HEALTH CHECK
# GET /health — lets you confirm the server is running
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok"}