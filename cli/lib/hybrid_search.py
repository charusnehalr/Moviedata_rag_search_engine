import os

from .keyword_search import InvertedIndex
from .semantic_search import ChunkedSemanticSearch


class HybridSearch:
    def __init__(self, documents):
        self.documents = documents
        self.semantic_search = ChunkedSemanticSearch()
        self.semantic_search.load_or_create_chunk_embeddings(documents)

        self.idx = InvertedIndex()
        if not os.path.exists(self.idx.index_path):
            self.idx.build()
            self.idx.save()

    def _bm25_search(self, query, limit):
        self.idx.load()
        return self.idx.bm25_search(query, limit)

    def weighted_search(self, query, alpha=0.5, limit=5):
          bm25_results = self._bm25_search(query, limit*500)
          sem_results = self.semantic_search.search_chunks(query, limit*500)
          combined_results = combine_search_results(bm25_results, sem_results)
          return combined_results

    def rrf_search(self, query, k, limit=10):
        raise NotImplementedError("RRF hybrid search is not implemented yet.")

def hybrid_score(bm25_score, sem_score, alpha=0.5):
  return (alpha * bm25_score + (1 - alpha) * semantic_score)

def normalize_scores(scores):
  if not scores: return []

  min_score = min(scores)
  max_score = max(scores)

  if min_score == max_score: return [1.] * len(scores)

  score_range = max_score - min_score
  # “Take each score in scores, apply this formula, and put the result into a new list.”
  return [(score-min_score)/score_range for score in scores] 
      # last line does the below 
      # normalized = []
      # for score in scores:
      #     normalized.append((score - min_score) / score_range)

      # return normalized