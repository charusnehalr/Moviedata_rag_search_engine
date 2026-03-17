import argparse
import logging
from lib.hybrid_search import normalize_scores, weighted_search, rrf_search

def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid Search CLI")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging for the search pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    norm_parser = subparsers.add_parser(name="normalize", help="Command to normalize given scores")
    norm_parser.add_argument("scores",type=float,nargs='+' , help="List of scores to normalize")
    # nargs+ means The user can type many scores, not just one

    weighted_parser = subparsers.add_parser(name="weighted_search", help="Command to do weighted search")
    weighted_parser.add_argument("query",type=str, help="User Query for the search")
    weighted_parser.add_argument("--alpha",type=float , default = 0.5, help="Constant to dynamically control weighting between two scores")
    weighted_parser.add_argument("--limit",type=int, default = 5, help="Limit of the answer")

    rrf_parser = subparsers.add_parser(name="rrf_search", help="Command to do rrf search")
    rrf_parser.add_argument("query",type=str, help="User Query for the search")
    rrf_parser.add_argument("--k",type=int , default = 60, help="Constant to dynamically control weighting between two scores")
    rrf_parser.add_argument("--limit",type=int, default = 5, help="Limit of the answer")
    rrf_parser.add_argument("--enhance",type=str, choices=["spell", "rewrite", "expand"], help="To enhance query using LLM")
    rrf_parser.add_argument("--rerank_method",type=str, choices=["individual", "batch", "cross_encoder"], help="Rerank method")


    args = parser.parse_args()

    if args.debug:
        # Only show DEBUG logs from our pipeline, not noisy third-party libraries
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
        pipeline_logger = logging.getLogger("lib.hybrid_search")
        pipeline_logger.setLevel(logging.DEBUG)
        pipeline_logger.addHandler(handler)
        pipeline_logger.propagate = False  # Prevent duplicate output to root logger
# Example to run debug : uv run cli/hybrid_search_cli.py --debug rrf_search "dinosaur" --limit 5

    match args.command:
        case "rrf_search":
          rrf_search(args.query, args.k, args.limit, args.enhance, args.rerank_method)
        case "weighted_search":
          weighted_search(args.query, args.alpha, args.limit)
        case "normalize":
          norm_scores = normalize_scores(args.scores)
          for norm_score in norm_scores:
            print(f"* {norm_score:.4f}")
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()