import os
from dotenv import load_dotenv
from lib.search_utils import PROMPT_PATH
import time

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY environment variable not set")

from google import genai

model = 'gemma-3-27b-it'
client = genai.Client(api_key=api_key)

def individual_rerank(query, documents):
  with open(PROMPT_PATH/ 'individual_rerank.md') as f:
    prompt = f.read()
  results =[]
  for doc in documents:
    _prompt = prompt.format(
                query = query, 
                title = doc['title'],
                description = doc['description'])
    response = client.models.generate_content(model=model,contents=_prompt)
    clean_response_text = (response.text or "").strip()
    try:
      clean_response_text = int(clean_response_text)
    except:
      print(f"Failed to case {response.text} to int for {doc['title']}")
      clean_response_text = 0
    results.append({**doc, 'rerank_response':clean_response_text})
    time.sleep(3)
    # print((response.text, results))
  
  results = sorted(results, key=lambda x: x['rerank_response'], reverse=True)
  return results