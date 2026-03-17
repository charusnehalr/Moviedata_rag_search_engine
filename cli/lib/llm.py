import os, json
from dotenv import load_dotenv
from lib.search_utils import PROMPT_PATH

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY environment variable not set")

from google import genai

model = 'gemma-3-27b-it'
client = genai.Client(api_key=api_key)

def generate_content(prompt, query, **kwargs):
  prompt = prompt.replace('{query}', query)
  for key, value in kwargs.items():
      prompt = prompt.replace(f'{{{key}}}', str(value))
  response = client.models.generate_content(model=model,contents=prompt)
  if response.text is None:
      print(f"[DEBUG] Full response: {response}")
  return response.text

def augment_prompt(query,type):
    with open(PROMPT_PATH/f'{type}.md', 'r') as f:
      prompt = f.read()
    return generate_content(prompt, query)

def correct_spelling(query):
  return augment_prompt(query, 'spell')

def rewrite_query(query):
  return augment_prompt(query, 'rewrrite')

def expand_query(query):
  return augment_prompt(query, 'expand')

def llm_judge(query, formatted_results):
    with open(PROMPT_PATH/'llm_evaluation.md', 'r') as f:
      prompt = f.read()
    results = generate_content(prompt, query, formatted_results=formatted_results)
    if not results:
        raise ValueError(f"LLM returned empty response for query: '{query}'")
    results = json.loads(results.strip('```json').strip('```').strip())
    return results 


