import json
from pathlib import Path
from typing import Any

BM25_K1 = 1.5
BM25_B = 0.75
SCORE_PRECISION = 3
DEFAULT_SEARCH_LIMIT = 5

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[2]
DATA_PATH = PROJECT_ROOT/"data"/"movies.json"
STOPWORDS_PATH = PROJECT_ROOT/"data"/"stopwords.txt"
CACHE_PATH = PROJECT_ROOT/"cache"
PROMPT_PATH = PROJECT_ROOT/"cli"/"lib"/"prompts"

# __file__ --> path of this file
# Path --> converts path into Path object --> .parent etc
# .resolve() --> converts to absolute path
#  parents[2] --> jumps to level up

def load_movies() -> list[dict]:
    with open(DATA_PATH, "r") as f:
      data = json.load(f)
    return data['movies']

def load_stopwords():
  with open(STOPWORDS_PATH, "r") as f:
    return {line.strip() for line in f}
  # line.strip() removes \n

def format_search_result(
    doc_id: str, title: str, document: str, score: float, **metadata: Any
) -> dict[str, Any]:
    """Create standardized search result

    Args:
        doc_id: Document ID
        title: Document title
        document: Display text (usually short description)
        score: Relevance/similarity score
        **metadata: Additional metadata to include

    Returns:
        Dictionary representation of search result
    """
    return {
        "id": doc_id,
        "title": title,
        "document": document,
        "score": round(score, SCORE_PRECISION),
        "metadata": metadata if metadata else {},
    }
