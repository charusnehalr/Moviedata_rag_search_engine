import os
import logging

from .keyword_search import InvertedIndex
from .semantic_search import ChunkedSemanticSearch
from lib.search_utils import load_movies
from lib.llm import augment_prompt
from lib.rerank import individual_rerank, batch_rerank, cross_encoder_rerank

logger = logging.getLogger(__name__)

def weighted_search(query, alpha=0.5, limit=5):
  movies = load_movies()
  hs = HybridSearch(movies)
  results = hs.weighted_search(query, alpha, limit)
  for idx, r in enumerate(results[:limit]):
    print(f"{idx+1} {r['title']}")
    print(f"Hybrid Score: {r['hybrid_score']}")
    print(f"BM25: {r['bm25_score']}, Semantic: {r['sem_score']}")
    print(r['description'][:100])

def rrf_search(query, k=60, limit=5, enhance=None, rerank_method = None):
  logger.debug("=" * 60)
  logger.debug(f"[STAGE 1] Original query: '{query}'")

  movies = load_movies()
  hs = HybridSearch(movies)

  if enhance:
    new_query = augment_prompt(query, enhance)
    print(f"Enhanced query ({'enhance'}): '{query}' -> '{new_query}'\n")
    logger.debug(f"[STAGE 2] Query after enhancement ({enhance}): '{new_query}'")
    query = new_query
  else:
    logger.debug(f"[STAGE 2] No query enhancement applied")

  rrf_limit = limit * 5 if rerank_method else limit
  results = hs.rrf_search(query, k, rrf_limit)

  logger.debug(f"[STAGE 3] RRF search returned {len(results)} results")
  for i, r in enumerate(results[:5]):
    logger.debug(f"  [{i+1}] '{r['title']}' | rrf={r['rrf_score']:.4f} | bm25_rank={r['bm25_rank']} | sem_rank={r['sem_rank']}")

  match rerank_method:
    case "individual":
      results = individual_rerank(query, results)
      print(f"Reranking top {limit} results using individual method...")
    case "batch":
      results = batch_rerank(query, results)
      print(f"Reranking top {limit} results using batch method...")
    case "cross_encoder":
      results = cross_encoder_rerank(query, results)
      print(f"Reranking top {limit} results using cross_encoder method...")
    case _:
      pass

  if rerank_method:
    logger.debug(f"[STAGE 4] Results after re-ranking ({rerank_method}), showing top {min(limit, len(results))}")
    for i, r in enumerate(results[:limit]):
      score_info = f"rrf={r['rrf_score']:.4f}"
      if rerank_method == "cross_encoder":
        score_info += f" | cross_encoder={r.get('cross_encoder_score', 'N/A'):.4f}"
      elif rerank_method in ("individual", "batch"):
        score_info += f" | rerank_score={r.get('rerank_score') or r.get('rerank_response', 'N/A')}"
      logger.debug(f"  [{i+1}] '{r['title']}' | {score_info}")
  else:
    logger.debug(f"[STAGE 4] No re-ranking applied")

  logger.debug("=" * 60)

  for idx, r in enumerate(results[:limit]):
    print(f"{idx+1} {r['title']}")
    print(f"RRF Score: {r['rrf_score']}")
    if rerank_method == "cross_encoder":
      print(f"Cross Encoder Score: {r['cross_encoder_score']}")
    print(f"BM25 Rank: {r['bm25_rank']}, Semantic Rank: {r['sem_rank']}")
    print(r['description'][:100])

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
          combined_results = combine_search_results(bm25_results, sem_results, alpha)
          return combined_results

    def rrf_search(self, query, k, limit=10):
        bm25_results = self._bm25_search(query, limit*500)
        logger.debug(f"  [BM25] Retrieved {len(bm25_results)} results | top: {[r['title'] for r in bm25_results[:3]]}")

        sem_results = self.semantic_search.search_chunks(query, limit*500)
        logger.debug(f"  [Semantic] Retrieved {len(sem_results)} results | top: {[r['title'] for r in sem_results[:3]]}")

        combined_results = rrf_combine_search_results(bm25_results, sem_results, k)
        logger.debug(f"  [RRF Combined] {len(combined_results)} docs fused, returning top {limit}")
        return combined_results[:10]

def hybrid_score(bm25_score, sem_score, alpha=0.5):
  return (alpha * bm25_score + (1 - alpha) * sem_score)

def normalize_search_results(results):
  scores = [r['score'] for r in results]
  norm_scores = normalize_scores(scores)
  for idx, result in enumerate(results):
    result['normalized_score'] = norm_scores[idx]
  return results

def rrf_score(rank, k):
  return 1/(rank + k)

def rrf_final_score(r1, r2,k):
  if r1 and r2:
    return rrf_score(r1, k) + rrf_score(r2, k)
  return 0.

def rrf_combine_search_results(bm25_results, sem_results, k):
  scores = {}

  for rank, result in enumerate(bm25_results, start=1):
    doc_id = result['id']
    scores[doc_id] = {
      'doc_id': doc_id,
      'bm25_rank': rank,
      'bm25_score':rrf_score(rank, k),
      'sem_rank': None,
      'sem_score': None,
      'title': result['title'],
      'description': result['document']
    }

  for rank, result in enumerate(sem_results, start=1):
    doc_id = result['id']
    if doc_id not in scores:
      scores[doc_id] = {
        'doc_id': doc_id,
        'bm25_rank': None,
        'bm25_score':None,
        'sem_rank': None,
        'sem_score': None,
        'title': result['title'],
        'description': result['document']
      }
    scores[doc_id]['sem_rank'] = rank
    scores[doc_id]['sem_score'] = rrf_score(rank,k)
  
  for doc_id in scores.keys():
    scores[doc_id]['rrf_score'] = rrf_final_score(
      scores[doc_id]['bm25_rank'],
      scores[doc_id]['sem_rank'], k
    )
  results = sorted(list(scores.values()), key=lambda x: x['rrf_score'], reverse=True )
  return results

      
def combine_search_results(bm25_results, sem_result, alpha):
  bm25_norm = normalize_search_results(bm25_results)
  sem_norm = normalize_search_results(sem_results)

  combined_norm = {}
  for norm in bm25_norm:
    doc_id = norm['id']
    combined_norm[doc_id] = {
      'doc_id': doc_id,
      'bm25_score': norm['normalized_score'],
      'sem_score': 0.,
      'title': norm['title'],
      'description': norm['document']
    }
  for norm in sem_norm:
    doc_id = norm['id']
    if doc_id not in combined_norm:
      combined_norm[doc_id] = {
      'doc_id': doc_id,
      'bm25_score': 0.,
      'sem_score': 0.,
      'title': norm['title'],
      'description': norm['document']
      }
    combined_norm[doc_id]['sem_score'] = norm['normalized_score']

  for k,v in combined_norm.items():
    combined_norm[k]['hybrid_score'] = hybrid_score(v['bm25_score'], v['sem_score'], alpha)

  results = sorted(list(combined_norm.values()), key=lambda x: x['hybrid_score'], reverse=True )
  return results

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