import os, time, json
from dotenv import load_dotenv
from lib.search_utils import PROMPT_PATH
from sentence_transformers import CrossEncoder

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
    # response is a number -> 67
    response = client.models.generate_content(model=model,contents=_prompt)
    # response cleaned -> 67/n --> 67
    clean_response_text = (response.text or "").strip()
    try:
      clean_response_text = int(clean_response_text)
    except:
      print(f"Failed to case {response.text} to int for {doc['title']}")
      clean_response_text = 0
    results.append({**doc, 'rerank_response':clean_response_text})
      # {
      #  "title":"Gravity",
      #  "description":"Astronaut stranded...",
      #  "rerank_response":92
      # }
    time.sleep(3)
    # Avoid API rate limit
    # print((response.text, results))
  
  results = sorted(results, key=lambda x: x['rerank_response'], reverse=True)
  # higher score = higher rank
  return results

def batch_rerank(query, documents):
    with open(PROMPT_PATH/ 'batch_rerank.md') as f:
      prompt = f.read()
    _mtemp = ''' <movie id:{idx}=>{title}:\n{desc}:\n</movie>\n'''
    #This defines how each movie appears inside the prompt
    doc_list_str = ''
    for idx,doc in enumerate(documents):
      doc_list_str += _mtemp.format(idx=idx,title=doc['title'], desc=doc['description'])
    # Loop through all the movies 
    # append the movie format
    # <movie id:0=>Interstellar:
    # A team travels through a wormhole...
    # </movie>

    # <movie id:1=>Gravity:
    # Two astronauts struggle to survive...
    # </movie>

    # <movie id:2=>The Martian:
    # An astronaut is stranded on Mars...
    # </movie>
    _prompt = prompt.format(
          query = query, 
          doc_list_str=doc_list_str,
          num_docs = len(documents))

    # insert this into main prompt
    response = client.models.generate_content(model=model,contents=_prompt)
    # calling LLM once
    response_parsed = json.loads(response.text.strip('```json').strip('```json').strip())

    # print(response_parsed) --> [7, 1, 9, 3, 5, 0, 8, 2, 6, 4]
    # This response says "movie in ID 7 is the best match, ID 1 is second best, ID 9 thrid best"

    # removing code blocking formatting
    results=[]
    for idx, doc in enumerate(documents):
      if idx < len(response_parsed):
        score = response_parsed.index(idx)
      # where a movie's ID appears in the ranked list 
      # LLM returns: [7, 2, 0, 1, 9, 3, 8, 6, 4, 5]
      # meaning: "ID 7 is best, ID 2 is second, ID 0 is third..."'
      # code :   ID 0 → appears at position 2 → rerank_score = 2
      # Sort ascending: ID 7 (score 0), ID 2 (score 1), ID 0 (score 2)...

      else:
        print(f"Missing score for doc {idx}: {doc['title']}, defaulting to 0")
        score = 0
      results.append({**doc, 'rerank_score':score})
    # Append the ranking
    #     {
    #  "title":"Gravity",
    #  "description":"Astronaut stranded...",
    #  "rerank_score":92
    # }
    results = sorted(results, key=lambda x: x['rerank_score'], reverse=False)
    return results
    
def cross_encoder_rerank(query, documents):
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-TinyBERT-L2-v2")
    pairs = []
    for doc in documents:
        pairs.append([query, f"{doc.get('title', '')} - {doc.get('document', '')}"])
    # `predict` returns a list of numbers, one for each pair
    scores = cross_encoder.predict(pairs)
    results = []
    for idx, doc in enumerate(documents):
        results.append({**doc, 'cross_encoder_score': scores[idx]})
    results = sorted(results, key=lambda x: x['cross_encoder_score'], reverse=True)
    return results