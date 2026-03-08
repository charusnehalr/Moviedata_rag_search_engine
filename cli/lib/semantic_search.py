from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
from lib.search_utils import load_movies
import re
import json
from collections import defaultdict
from math import inf

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
    similarities = [] #empty list to store similarity_score and document
    for doc_emb , doc in zip(self.embeddings, self.documents):
      # here we assume self.embeddings and self.doc are of equal length. If not zip hides 
      #extra item silently - this could miss docs
      _similarity = cosine_similarity(query_emb, doc_emb)
      # assume cosine similarity returns score where larger is more similar. If it 
      # returns distance (smaller is better) then sorting ascending is better
      similarities.append((_similarity, doc))
        # If cosine similarity: higher = more similar -> use nlargest
    # top_pairs = heapq.nlargest(limit, pairs, key=lambda x: x[0])
    # above code validates limit. heapq so that don't have to sort entire list when we only need small 
    # top-k O(n log k) instead of O(n log n)
    # .get() to avoid keyError if the doc is missing in field
    similarities.sort(key = lambda x: x[0], reverse= True) # value in descending order 
    res = []
    for sc, doc in similarities[:limit]:
      res.append({'score':sc, 
                  'title':doc['title'],
                  'description':doc['description']}) 
    return res
def semantic_chunking(text, max_chunk_size = 4, overlap = 0):
  text = text.strip()
  if not text:
    return []
  sentence = re.split(r"(?<=[.!?])\s+", text)
  if ((len(sentence)==1) and sentences[0].endswith('!','.','?')):
    pass  
  # split to sentences
  chunks = []
  step_size = max_chunk_size - overlap
  sentences = [s.strip() for s in sentences if s]
  for i in range(0, len(sentence),step_size):
    # each sentences split into chunks 
    # loop such that it jumps step size (containing overlap)
    chunk_sentences = sentence[i:i+max_chunk_size]
    if len(chunk_sentences) <= overlap:
      break
    chunks.append(" ".join(chunk_sentences))
  return chunks

def chunk_text_semantic(text, chunk_size = 4, overlap = 0):
  chunks = semantic_chunking(text, chunk_size, overlap)
  print(f"Semantically chunking {len(text)} characters.")
  for i, chunk in enumerate(chunks):
    print(f"{i+1}. {chunk}")

def fixed_size_chunking(text, chunk_size=200, overlap=1):
  words = text.split() # split at whitespaces
  chunks = []
  # word[0:200]
  # word[200:400]
  step_size = chunk_size - overlap # how many new words each chunk advances
  for i in range(0, len(words), step_size):
    chunk_words = words[i:i+chunk_size]
    if len(chunk_words)<= overlap:
      break
    chunks.append(" ".join(chunk_words))
  # chunks.append(" ".join(words[i : i+chunk_size]))
  return chunks
# overlap chunk
# words[0:200]
# words[190:300] 
def chunk_text(text, chunk_size=200, overlap=1):
  chunks = fixed_size_chunking(text, chunk_size, overlap)
  print(f"Chunking {len(text)} characters")
  for i, chunk in enumerate(chunks):
    print(f" {i+1}. {chunk}")

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
    a = np.asarray(vec1).ravel()   # flatten to 1-D
    b = np.asarray(vec2).ravel()   # flatten to 1-D

    # ensure same length
    if a.size != b.size:
        raise ValueError(f"Vector size mismatch: {a.size} vs {b.size}")

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    # np.dot yields a 0-d array or scalar; .item() converts to native Python float
    return float(np.dot(a, b) / (norm_a * norm_b))
    # dot_product = np.dot(vec1, vec2)
    # norm1 = np.linalg.norm(vec1).ravel()
    # norm2 = np.linalg.norm(vec2).ravel()

    # # ensure same length
    # if norm1.size != norm2.size:
    #     raise ValueError(f"Vector size mismatch: {norm1.size} vs {norm2.size}")

    # if norm1 == 0 or norm2 == 0:
    #     return 0.0

    # return dot_product / (norm1 * norm2)

class ChunkedSemanticSearch(SemanticSearch):
    def __init__(self) -> None:
        super().__init__()
        self.chunk_embeddings = None
        self.chunk_embeddings_path = Path("cache/chunk_embeddings.npy")
        self.chunk_metadata = None
        self.chunk_metadata_path = Path("cache/chunk_metadata.json")
# This does exactly what the name says - builds chunk embeddings
    def build_chunk_embeddings(self, documents): 
      self.documents = documents
      self.document_map = {idx: doc for idx, doc in enumerate(documents)}
      all_chunks = []
      chunk_metadata = []
      
      for midx, doc in enumerate(documents):
        if doc['description'].strip() == '': #when description is not empty
          continue
        _chunks = semantic_chunking(doc['description'], max_chunk_size = 4, overlap = 1)
        start_global = len(all_chunks)  
        all_chunks += _chunks
        for cidx in range(len(_chunks)):
          chunk_metadata.append({"movie_idx": midx,
                                 "doc_id": doc['id'],
                                 "chunk_idx": cidx,
                                 "total_chunks": len(_chunks),
                                 "global_idx": start_global + cidx })
        
      self.chunk_embeddings = self.model.encode(all_chunks, show_progress_bar=True)
      self.chunk_metadata = chunk_metadata # a list
      np.save(self.chunk_embeddings_path, self.chunk_embeddings)
      with open(self.chunk_metadata_path, 'w') as f:
        json.dump({"chunks": chunk_metadata, "total_chunks": len(all_chunks)}, f, indent=2)
      return self.chunk_embeddings

    def load_or_create_chunk_embeddings(self,documents):
      self.documents = documents
      self.document_map = {idx: doc for idx, doc in enumerate(documents)}
      # if the embeddings are there then load else call build chunk
      if self.chunk_embeddings_path.exists() and self.chunk_metadata_path.exists():
        self.chunk_embeddings = np.load(self.chunk_embeddings_path, allow_pickle=False)
        with open(self.chunk_metadata_path, 'r', encoding = 'utf-8') as f:
          disk_meta = json.load(f)
          # self.chunk_metadata = json.load(f)
          self.chunk_metadata = disk_meta.get("chunks", disk_meta)
        return self.chunk_embeddings
      return self.build_chunk_embeddings(documents)

# this is to get result of cosine similarity between semantic embed query and data 
    def search_chunks(self, query, limit=10):
      query_emb = self.generate_embedding(query)
      chunk_scores = []
      movie_scores = defaultdict(lambda: -inf)
      for idx in range(len(self.chunk_embeddings)):
        chunk_embedding = self.chunk_embeddings[idx]
        # metadata = self.chunk_metadata['chunks'][idx]
        metadata = self.chunk_metadata[idx]
        midx, cidx = metadata['movie_idx'], metadata['chunk_idx']
        sim = cosine_similarity(query_emb, chunk_embedding)
        chunk_scores.append({
          'movie_idx': midx,
          'chunk_idx': cidx,
          'score': sim
        })
        movie_scores[midx] = max(movie_scores[midx],sim)
      movie_score_sorted = sorted(movie_scores.items(), key=lambda x: x[1], reverse = True) #descending 
      res = []
      for midx, score in movie_score_sorted[:limit]:
        doc = self.document_map[midx]

        res.append({
            "id": doc['id'],
            "title": doc['title'],
            "document": doc['description'][:100],
            "score": round(score, 4),
            "metadata": {}
        })
      return res

# Entry to do sematic chunked search
def search_chunked(query, limit=5):
  css = ChunkedSemanticSearch()
  movies = load_movies()
  # here ask or create embeddings required
  embeddings = css.load_or_create_chunk_embeddings(movies)
  results = css.search_chunks(query, limit)
  for i, res in enumerate(results):
    print(f"\n{i+1}. {res['title']} (score: {res['score']:.4f})")
    print(f"   {res['document']}...")

def embed_chunks():
  movies = load_movies()
  css = ChunkedSemanticSearch()
  embeddings = css.load_or_create_chunk_embeddings(movies)
  print(f"Generated {len(embeddings)} chunked embeddings")