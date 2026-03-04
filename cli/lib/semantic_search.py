from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
from lib.search_utils import load_movies

class SemanticSearch:
  def __init__(self):
    self.model = SentenceTransformer("all-MiniLM-L6-v2") # embedding dim: 384
    self.embeddings = None # hold numeric value
    self.documents = None # hold document input list
    self.document_map = {} # map document id to original doc for quick lookup
    self.embeddings_path = Path("cache/movie_embeddings.npy")

# convert each movie (title + description) into a numeric vector (an embedding) using Sentence Transformer
  def build_embeddings(self, documents):
    self.documents = documents
    self.document_map = {}
    movie_strings = []
    for doc in self.documents:
      self.document_map[doc['id']] = doc
      movie_strings.append(f"{doc['title']}: {doc['description']}")
    self.embeddings = self.model.encode(movie_strings,show_progress_bar=True) #calls the embedding model to convert each string to a numeric vector.
    self.embeddings_path.parent.mkdir(parents=True, exist_ok=True) # to ensure that the path exist or it will crash
    np.save(self.embeddings_path,self.embeddings)
    self.embeddings = self.embeddings
    return self.embeddings


# # embeddings --> (N,D)
# N = number of strings / documents (e.g., 3 in our mini example)

# D = embedding dimension (model dependent; e.g., 1536 or 768)
# embeddings = [
#   [0.013, -0.232, 0.98, ...],   # embedding for "The Music Man..."
#   [-0.12, 0.44, -0.02, ...],    # embedding for "The Revenant..."
#   [0.66, -0.03, 0.17, ...],     # embedding for "Mortal Kombat..."
# ]
# doc map --> matched id --> doc
# {
#   423: {"id":423, "title":"The Music Man", "description":"The movie opens with..."},
#   424: {"id":424, "title":"The Revenant",  "description":"Fur trapper Hugh Glass..."},
#   425: {"id":425, "title":"Mortal Kombat vs. DC", "description":"After Shao Kahn's..."},
#   ...
# }
# movie string 
# [
#   "The Music Man: The movie opens with...",
#   "The Revenant: Fur trapper Hugh Glass...",
#   "Mortal Kombat vs. DC: After Shao Kahn's..."
#   # ...
# ]
  def load_or_create_embeddings(self, documents): # this helps to make sure that embeddings are created only ones 
    # if the doc == embedding length , then embeddings are already there and we return it , else we ask build_embeddings
    self.documents = documents
    self.document_map = {}
    for doc in self.documents:
      self.document_map[doc['id']] = doc
    if self.embeddings_path.exists():
      self.embeddings = np.load(self.embeddings_path, allow_pickle=False)
      if len(self.documents) == len(self.embeddings):
        return self.embeddings
    return self.build_embeddings(documents)

  def generate_embedding(self, text):
    if not text or not text.strip():
      raise ValueError("Must have text to create an embedding")
    return self.model.encode([text])[0]
    # wrapping text in list [text] as encode() expects list of inputs, not a single string
    # output (1, D) --> 1= number of inputs and D= embedding dimension (1 sentence, 384 features)
    # t0 get first element we do [0]

  def search(self, query, limit):
    if self.embeddings is None: 
      raise ValueError("No embeddings loaded. Call `load_or_create_embeddings` first.")
    query_emb = self.generate_embedding(query)
    similarities = []
    for doc_emb , doc in zip(self.embeddings, self.documents):
      _similarity = cosine_similarity(query_emb, doc_emb)
      similarities.append((_similarity, doc))
    similarities.sort(key = lambda x: x[0], reverse= False)
    res = []
    for sc, doc in similarities[:limit]:
      res.append({'score':sc, 
                  'title':doc['title'],
                  'description':doc['description']}) 
    return res

def search(query, limit = 5):
  ss = SemanticSearch()
  movies = load_movies()
  ss.load_or_create_embeddings(movies)
  search_result = ss.search(query, limit)
  for idx, res in enumerate(search_result):
    print(f'{idx}.{res['title']} (score: {res['score']})')
    print(res['description'[:100]])

def embed_query_text(query): 
  ss = SemanticSearch()
  embedding = ss.generate_embedding(query)
  print(f"Query: {query}")
  print(f"First 5 dimensions: {embedding[:5]}")
  print(f"Shape: {embedding.shape}")

def verify_embeddings():
  ss = SemanticSearch()
  documents = load_movies()
  embeddings = ss.load_or_create_embeddings(documents)
  print(f"Number of docs:   {len(documents)}")
  print(f"{embeddings.shape[0]} vectors in {embeddings.shape[1]} dimensions")

def embed_text(text):
  ss = SemanticSearch()
  embedding = ss.generate_embedding(text)

  print(f"Text: {text}")
  print(f"First 3 dimensions: {embedding[:3]}")
  print(f"Dimensions: {embedding.shape[0]}")
  
def verify_model():
  ss = SemanticSearch()
  # model_class = ss.load_or_create_embeddings(documents)# e.g., "SentenceTransformer"
  # model_repr = repr(ss.model)
  # max_len = ss.model.max_seq_length

  # print(f"Model loaded:{model_repr}")
  # print(f"Max sequence length: {max_len}")
  print(f"Model loaded: {ss.model}")
  print(f"Max sequence length: {ss.model.max_seq_length}")

def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)
