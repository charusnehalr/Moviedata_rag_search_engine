import argparse
from lib.hybrid_search import normalize_scores

def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    norm_parser = subparsers.add_parser(name="normalize", help="Command to normalize given scores")
    norm_parser.add_argument("scores",type=float,nargs='+' , help="List of scores to normalize")
    # nargs+ means The user can type many scores, not just one

    weighted_parser = subparsers.add_parser(name="weighted-search", help="Command to do weighted search")
    weighted_parser.add_argument("query",type=str, help="User Query for the search")
    weighted_parser.add_argument("--alpha",type=float , help="Constant to dynamically control weighting between two scores")
    weighted_parser.add_argument("--limit",type=int, help="Limit of the answer")

    args = parser.parse_args()

    match args.command:
        case "weighted_search":
          pass    
        case "normalize":
          norm_scores = normalize_scores(args.scores)
          for norm_score in norm_scores:
            print(f"* {norm_score:.4f}")
        case _:
            parser.print_help()


if __name__ == "__main__":
    main()