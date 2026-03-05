#!/usr/bin/env python3

import argparse
from lib.semantic_search import (
  verify_model, 
  embed_text, 
  verify_embeddings,
  embed_query_text,
  search, 
  chunk_text,
  chunk_text_semantic
)
def main():
    parser = argparse.ArgumentParser(description="Semantic Search CLI")
    # subparsers = parser.add_subparsers(dest="command", help="Available commands")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    verify_parser = subparsers.add_parser("verify", help="Verify model loading")

    embed_subparser = subparsers.add_parser("embed_text", help="Encode text with embedding model")
    embed_subparser.add_argument("text", type=str, help="Text to be encoded")

    verify_embeddings_subparser = subparsers.add_parser("verify_embeddings", help="verify if the document embedding works")

    queryemb_subparser = subparsers.add_parser("embedquery", help="Encode query with model")
    queryemb_subparser.add_argument("query", type=str, help="Query to be encoded")

    search_subparser = subparsers.add_parser("search", help="Search using semantic search")
    search_subparser.add_argument("query", type=str, help="Query to search")
    search_subparser.add_argument("--limit", type=int, help="Top number of results limit")

    chunk_subparser = subparsers.add_parser("chunk", help="Chunk the given text")
    chunk_subparser.add_argument("text", type=str, help="Input text to chuck")
    chunk_subparser.add_argument("--chunk-size", type=int,default=200, help="Optional chunk size")
    chunk_subparser.add_argument("--overlap", type=int, help="Optional overlap size")

    semantic_chunk_subparser = subparsers.add_parser("semantic_chunking", help="Chunk the given text")
    semantic_chunk_subparser.add_argument("text", type=str, help="Input text to chuck")
    semantic_chunk_subparser.add_argument("--chunk-size", type=int,default=4, help="Optional chunk size")
    semantic_chunk_subparser.add_argument("--overlap", type=int, default=0, help="Optional overlap size")

    args = parser.parse_args()
    match args.command:
        case "verify":
          verify_model()
        case "embed_text":
          embed_text(args.text)
        case "verify_embeddings":
          verify_embeddings()
        case "embedquery":
          embed_query_text(args.query)
        case "search":
          search(args.query, args.limit)
        case "chunk":
          chunk_text(args.text, args.chunk_size, args.overlap)
        case "semantic_chunking":
          chunk_text_semantic(args.text, args.chunk_size, args.overlap)
        case _:
            parser.print_help()
            return 1
    return 0
if __name__ == "__main__":
    main()