from sentence_transformers import SentenceTransformer

class SemanticSearch:
  def __init__(self, model_name: "all-MiniLM-L6-v2"):
    self.model = SentenceTransformer(model_name)

def verify_model():
  ss = SemanticSearch()
  model_repr = ss.model.model