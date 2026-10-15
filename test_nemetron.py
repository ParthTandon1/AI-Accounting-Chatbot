import os
# import json
# import re
# from openai import OpenAI
#
# # --- Load system prompt ---
# with open('system_prompt.txt', 'r') as f:
#     system_prompt_template = f.read()
#
# # --- Load value lookup ---
# with open('value_lookup.json', 'r') as f:
#     value_map = json.load(f)
#
# # --- Candidate match function ---
# def get_candidate_matches(question, value_map):
#     question_lower = question.lower()
#     matches = {}
#     for key, candidates in value_map.items():
#         if len(key) < 3:
#             continue
#         pattern = r'\b' + re.escape(key) + r'\b'
#         if re.search(pattern, question_lower):
#             matches[key] = candidates
#     return matches
#
# # --- Assemble full prompt for a given question ---
# def build_prompt(question):
#     matches = get_candidate_matches(question, value_map)
#     matches_json = json.dumps(matches, indent=2)
#     system_prompt = system_prompt_template.replace(
#         "{candidate_matches_json}", matches_json
#     )
#     return system_prompt
#
# # --- Call Nemotron ---
# def ask_nemotron(question):
#     system_prompt = build_prompt(question)
#
#     client = OpenAI(
#         base_url="https://integrate.api.nvidia.com/v1",
#         api_key="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"  # replace with your actual key
#     )
#
#     completion = client.chat.completions.create(
#         model="nvidia/nemotron-3-ultra-550b-a55b",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user",   "content": question}
#         ],
#         temperature=0.2,
#         top_p=0.95,
#         max_tokens=1000,
#         extra_body={
#             "chat_template_kwargs": {"enable_thinking": True},
#             "reasoning_budget": 4096
#         },
#         stream=False
#     )
#
#     reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
#     sql = completion.choices[0].message.content.strip()
#     return reasoning, sql
#
#
# # --- Test with 3 real questions ---
# questions = [
#     "What is the total indirect expense for Padup Ventures?",
#     "Which are the top 5 customers by total debit amount?",
#     "What is the total GST liability across all branches?"
# ]
#
# for q in questions:
#     print(f"\n{'='*60}")
#     print(f"QUESTION: {q}")
#     reasoning, sql = ask_nemotron(q)
#     if reasoning:
#         print(f"\nREASONING:\n{reasoning}")
#     print(f"\nGENERATED SQL:\n{sql}")

import os
import json
import re
import time
from openai import OpenAI

# --- Load system prompt ---
with open('system_prompt.txt', 'r') as f:
    system_prompt_template = f.read()

# --- Load value lookup ---
with open('value_lookup.json', 'r') as f:
    value_map = json.load(f)

# --- Candidate match function ---
def get_candidate_matches(question, value_map):
    question_lower = question.lower()
    matches = {}
    for key, candidates in value_map.items():
        if len(key) < 3:
            continue
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, question_lower):
            matches[key] = candidates
    return matches

# --- Assemble full prompt for a given question ---
def build_prompt(question):
    matches = get_candidate_matches(question, value_map)
    matches_json = json.dumps(matches, indent=2)
    system_prompt = system_prompt_template.replace(
        "{candidate_matches_json}", matches_json
    )
    return system_prompt

# --- Call Nemotron with retry ---
def ask_nemotron(question, retries=3, wait=5):
    system_prompt = build_prompt(question)

    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="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"
    )

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
            reasoning = getattr(
                completion.choices[0].message, "reasoning_content", None
            )
            sql = completion.choices[0].message.content.strip()
            return reasoning, sql

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                return None, f"ERROR: {e}"

# --- Test with 3 real questions ---
questions = [
    "What is the total indirect expense for Padup Ventures?",
    "Which are the top 5 customers by total debit amount?",
    "What is the total GST liability across all branches?"
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"QUESTION: {q}")
    reasoning, sql = ask_nemotron(q)
    if reasoning:
        print(f"\nREASONING:\n{reasoning}")
    print(f"\nGENERATED SQL:\n{sql}")