from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
from lib.search_utils import load_movies

class SemanticSearch:
  def __init__(self):
    self.model = SentenceTransformer("all-MiniLM-L6-v2")
    self.embeddings = None
    self.documents = None
    self.document_map = {}
    self.embeddings_path = Path("cache/movie_embeddings.npy")

  def build_embeddings(self, documents):
    self.documents = documents
    self.document_map = {}
    movie_strings = []
    for doc in self.documents:
      self.document_map[doc['id']] = doc
      movie_strings.append(f"{doc['title']}: {doc['description']}")
    embeddings = self.model.encode(movie_strings,convert_to_numpy=True) #calls the embedding model to convert each string to a numeric vector.
    np.save(self.embeddings_path, self.embeddings)
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
  def load_or_create_embeddings(self, documents):
    self.documents = documents
    self.document_map = {}
    for doc in self.documents:
      self.document_map[doc['id']] = doc
    if self.embeddings_path.exists():
      self.embeddings = np.load(self.embeddings_path)
      if len(self.documents) == len(self.embeddings):
        return self.embeddings
    return self.build_embeddings(documents)

  def generate_embedding(self, text):
    if not text or not text.strip():
      raise ValueError("Must have text to create an embedding")
    return self.model.encode([text])[0]

def verify_embeddings():
  ss = SemanticSearch()
  documents = load_movies()
  ss.load_or_create_embeddings(documents)

def embed_text(text):
  ss = SemanticSearch()
  embedding = ss.generate_embedding(text)

  print(f"Text: {text}")
  print(f"First 3 dimensions: {embedding[:3]}")
  print(f"Dimensions: {embedding.shape[0]}")
  
def verify_model():
  ss = SemanticSearch()
  model_class = ss.model.__class__.__name__            # e.g., "SentenceTransformer"
  model_repr = repr(ss.model)
  max_len = ss.model.max_seq_length

  print(f"Model loaded:{model_repr}")
  print(f"Max sequence length: {max_len}")
