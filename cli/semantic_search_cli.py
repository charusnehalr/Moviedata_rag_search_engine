#!/usr/bin/env python3

import argparse
from lib.semantic_search import verify_model, embed_text, verify_embeddings
def main():
    parser = argparse.ArgumentParser(description="Semantic Search CLI")
    # subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    verify_parser = subparsers.add_parser("verify", help="Verify model loading")

    embed_subparser = subparsers.add_parser("embed_text", help="Encode text with embedding model")
    embed_subparser.add_argument("text", type=str, help="Text to be encoded")

    verify_embeddings_subparser = subparsers.add_parser("verify_embeddings", help="verify if the document embedding works")

    args = parser.parse_args()
    match args.command:
        case "verify":
          verify_model()
        case "embed_text":
          embed_text(args.text)
        case "verify_embeddings":
          verify_embeddings()
        case _:
            parser.print_help()
            return 1
    return 0
if __name__ == "__main__":
    main()