from lib.search_utils import (
  load_movies, 
  load_stopwords, 
  CACHE_PATH, 
  format_search_result,
  DEFAULT_SEARCH_LIMIT,
  BM25_K1, 
  BM25_B)
import string
from nltk.stem import PorterStemmer
from collections import defaultdict, Counter
import pickle
import os
import math

stemmer = PorterStemmer()

class InvertedIndex:
    def __init__(self):
      self.index = defaultdict(set)
      self.docmap = {} # map document ID: document
      self.index_path = CACHE_PATH/ 'index.pkl'
      self.docmap_path = CACHE_PATH/ 'docmap.pkl'
      self.term_frequencies = defaultdict(Counter)
      self.term_frequencies_path = CACHE_PATH/ 'term_frequencies.pkl'
      self.doc_lengths = {}
      self.doc_lengths_path = CACHE_PATH/"doc_lengths.pkl"

    def __add_document(self, doc_id, text):
      tokens = tokenize_text(text)
      # set coz we only care whether the word appears in doc - not how many times
      for token in set(tokens):
        self.index[token].add(doc_id)
      self.term_frequencies[doc_id].update(tokens)
      self.doc_lengths[doc_id] = len(tokens)

    def __get_avg_doc_length(self):
      lengths = list(self.doc_lengths.values())
      if len(lengths) == 0:
        return 0.0
      ttl = 0
      for l in lengths:
        ttl += l
      return ttl/len(lengths)

    def get_documents(self, term):
      return sorted(list(self.index[term]))

    def get_tf(self, doc_id, term):
      token = tokenize_text(term)
      if len(token) != 1:
        raise ValueError("Can only have 1 tokens")
      token = token[0]
      return self.term_frequencies[doc_id][token]

    def get_idf(self, term):
      token = tokenize_text(term)
      if len(token) != 1:
        raise ValueError("Can only have 1 tokens")
      token = token[0]
      doc_count = len(self.docmap)
      term_doc_count = len(self.index[token])
      return math.log((doc_count + 1) / (term_doc_count + 1))
    
    def get_bm25_idf(self, term):
      token = tokenize_text(term)
      if len(token) != 1:
        raise ValueError("term should tokenize to only 1 token")
      token = token[0]
      doc_count = len(self.docmap)
      term_doc_count = len(self.index[token])
      return math.log((doc_count - term_doc_count + 0.5) / (term_doc_count + 0.5)+1)

    def get_tfidf(self, doc_id, term):
      tf = self.get_tf(doc_id,term)
      idf = self.get_idf(term)
      tfidf = tf * idf
      return tfidf

    def get_bm25_tf(self, doc_id, term, k1=BM25_K1, b1=BM25_B):
      tf = self.get_tf(doc_id, term)
      doc_length = self.doc_lengths[doc_id]
      avg_doc_length = self.__get_avg_doc_length()
      if avg_doc_length > 0:
        length_norm = length_norm = 1 - b1 + b1 * (doc_length / avg_doc_length)
      else: 
        length_norm = 1
      bm25_tf = (tf * (k1 + 1)) / (tf + k1* length_norm)
      return bm25_tf
    
    def bm25(self, doc_id, term):
      bm25_tf = self.get_bm25_tf(doc_id,term)
      bm_25idf = self.get_bm25_idf(term)
      bm25_tfidf = bm25_tf * bm_25idf
      return  bm25_tfidf
    
    def bm25_search(self, query, limit):
      query_tokens = tokenize_text(query)
      scores = {}
      for doc_id in self.docmap:
          score = 0.0
          for token in query_tokens:
              score += self.bm25(doc_id, token)
          scores[doc_id] = score

      sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

      results = []
      for doc_id, score in sorted_docs[:limit]:
            doc = self.docmap[doc_id]
            formatted_result = format_search_result(
                doc_id=doc["id"],
                title=doc["title"],
                document=doc["description"],
                score=score,
            )
            results.append(formatted_result)

      return results


    def build(self):
      movies = load_movies()
      for movie in movies:
        doc_id = movie['id']
        text = f"{movie['title']} {movie['description']}"
        self.__add_document(doc_id, text)
        self.docmap[doc_id] = movie

    def save(self):
      os.makedirs(CACHE_PATH, exist_ok = True)
      with open(self.index_path, 'wb') as f:
        pickle.dump(self.index, f)
      with open(self.docmap_path, 'wb') as f:
        pickle.dump(self.docmap, f)
      with open(self.term_frequencies_path, 'wb') as f:
        pickle.dump(self.term_frequencies, f)
      with open(self.doc_lengths_path, 'wb') as f:
        pickle.dump(self.doc_lengths, f)
    
    def load(self):
      with open(self.index_path, 'rb') as f:
        self.index = pickle.load(f)
      with open(self.docmap_path, 'rb') as f:
        self.docmap = pickle.load(f)
      with open(self.term_frequencies_path, 'rb') as f:
        self.term_frequencies = pickle.load(f)
      with open(self.doc_lengths_path, 'rb') as f:
        self.doc_lengths = pickle.load(f)
def bm25search_command(query, limit = DEFAULT_SEARCH_LIMIT):
    idx = InvertedIndex()
    idx.load()
    return idx.bm25_search(query, limit)

def tfidf_command(doc_id,term):
  idx = InvertedIndex()
  idx.load()
  # doc_id = int(doc_id)
  tf_idf = idx.get_tfidf(doc_id, term)
  print(f"TF-IDF score of '{term}' in document '{doc_id}': {tf_idf:.2f}")
  return tf_idf

def bm25_tf_command(doc_id,term,k1=BM25_K1, b1=BM25_B):
  idx = InvertedIndex()
  idx.load()
  bm25tf = idx.get_bm25_tf(doc_id, term, k1,b1)
  print(f"BM25 TF score of '{term}' in document '{doc_id}': {bm25tf:.2f}")
  return bm25tf

def bm25_idf_command(term):
  idx = InvertedIndex()
  idx.load()
  bm25idf = idx.get_bm25_idf(term)
  print(f"BM25 IDF score of '{term}': {bm25idf:.2f}")
  return bm25idf

def idf_command(term):
    idx = InvertedIndex()
    idx.load()
    idf = idx.get_idf(term)
    print(f"Inverse document frequency of '{term}': {idf:.2f}")
    return idf

def tf_command(doc_id, term):
  idx = InvertedIndex()
  idx.load()
  tf= idx.get_tf(doc_id, term)
  print(f"Term frequency of '{term}' in document '{doc_id}': {tf}")
  return tf

def build_command():
  idx = InvertedIndex()
  idx.build()
  idx.save()
 
def clean_text(text):
  text = text.lower()
  text = text.translate(str.maketrans("", "", string.punctuation))
  # maketrans(from, to, delete)
  return text
def tokenize_text(text):
  text = clean_text(text)
  stopwords = load_stopwords()
  res = []
  def _filter(tok):
    if tok and tok not in stopwords:
      return True
    return False

  for tok in text.split():
    if _filter(tok):
      tok = stemmer.stem(tok)
      res.append(tok)
      
  return res
  # tokens = [tok for tok in text.split() if tok]
  # "Take each token from text.split(), and keep it if it’s not empty."
  # if tok removes empty strings (extra safety)

def has_matching_token(query_tokens, movie_tokens):
  for query_tok in query_tokens:
    for movie_tok in movie_tokens:
      if query_tok in movie_tok:
        return True
  return False
# This checks if any word from the query appears inside any movie token.
def search_command(query, n_results=5):
  movies = load_movies()
  idx = InvertedIndex()
  idx.load()
  seen,res = set(), []
  query_tokens = tokenize_text(query)
  # iterate over each token in the query
  for qt in query_tokens:
    # use the inverted index to get any matching documents for each token
    matching_doc_ids = idx.get_documents(qt)
    for matching_doc_id in matching_doc_ids:
      if matching_doc_id in seen:
        continue
      seen.add(matching_doc_id)
      matching_doc = idx.docmap[matching_doc_id]
      res.append(matching_doc)
      # once you have 5 results, stop searching adn just return them
      if len(res) >= n_results:
        return res
  return res


  for movie in movies:
    movie_tokens = tokenize_text(movie['title'])
    if has_matching_token(query_tokens, movie_tokens):
      res.append(movie)
    if len(res) == n_results:
      break
  return res

  # res = [movie for movie in movies if query in movie["title"]]][:n_results]
