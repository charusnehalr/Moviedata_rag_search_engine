import os
from dotenv import load_dotenv
from lib.search_utils import PROMPT_PATH

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY environment variable not set")

from google import genai

model = 'gemma-3-27b-it'
client = genai.Client(api_key=api_key)

def generate_content(prompt, query):
  prompt = prompt.format(query=query)
  response = client.models.generate_content(model=model,contents=prompt)
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


