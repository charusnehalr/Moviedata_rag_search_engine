from lib.llm import answer_question, rag_summary, cited_summary
from lib.hybrid_search import HybridSearch
from lib.search_utils import load_movies

def query_answer(query):
   movies = load_movies()
   hs = HybridSearch(movies)
   rrf_results = hs.rrf_search(query, k= 60, limit=5)
   print("Search Results")
   for res in rrf_results:
    print(f"- {res['title']}")
   rag_results = answer_question(query, rrf_results)
   print("RAG Response:")
   print(rag_results)

def doc_summarize(query, limit=5):
   movies = load_movies()
   hs = HybridSearch(movies)
   rrf_results = hs.rrf_search(query, k= 60, limit=5)
   print("Search Results")
   for res in rrf_results:
    print(f"- {res['title']}")
   rag_summary_results = rag_summary(query, rrf_results)
   print("LLM Summary:")
   print(rag_summary_results)

def cited_summarize(query, limit=5):
   movies = load_movies()
   hs = HybridSearch(movies)
   rrf_results = hs.rrf_search(query, k= 60, limit=5)
   print("Search Results")
   for res in rrf_results:
    print(f"- {res['title']}")
   rag_summary_results = cited_summary(query, rrf_results)
   print("LLM Answer (cited):")
   print(rag_summary_results)

