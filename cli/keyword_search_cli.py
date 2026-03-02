#!/usr/bin/env python3

import argparse
from lib.keyword_search import (
    search_command, 
    build_command, 
    tf_command, 
    idf_command, 
    tfidf_command, 
    bm25_idf_command, 
    bm25_tf_command,
    bm25search_command,
    BM25_K1,
    BM25_B)

def main() -> None:
    parser = argparse.ArgumentParser(description="Keyword Search CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    build_parser = subparsers.add_parser("build", help="Build cache")

    search_parser = subparsers.add_parser("search", help="Search movies using BM25")
    search_parser.add_argument("query", type=str, help="Search query")
    
    tf_parser = subparsers.add_parser("tf", help="Calculate term frequency")
    tf_parser.add_argument("doc_id", type=int, help="Document ID for to check")
    tf_parser.add_argument("term", type=str, help="Search term to find counts for")

    idf_parser = subparsers.add_parser("idf", help="Calculate inverse document frequency")
    idf_parser.add_argument("term", type=str, help="Term to get IDF for")

    tf_idf_parser = subparsers.add_parser("tfidf", help="Calculate term frequency - inverted document frequency")
    tf_idf_parser.add_argument("doc_id", type=int, help="Document ID for to check")
    tf_idf_parser.add_argument("term", type=str, help="Search term to find counts for")

    bm25_idf_parser = subparsers.add_parser("bm25idf", help="Get BM25 IDF score for a given term")
    bm25_idf_parser.add_argument("term", type=str, help="Term to get BM25 IDF score for")

    bm25_tf_parser = subparsers.add_parser(
  "bm25tf", help="Get BM25 TF score for a given document ID and term")
    bm25_tf_parser.add_argument("doc_id", type=int, help="Document ID")
    bm25_tf_parser.add_argument("term", type=str, help="Term to get BM25 TF score for")
    bm25_tf_parser.add_argument("k1", type=float, nargs='?', default=BM25_K1, help="Tunable BM25 K1 parameter")
    bm25_tf_parser.add_argument("b1", type=float, nargs='?', default=BM25_B, help="Tunable BM25_B B1 parameter")

    bm25search_parser = subparsers.add_parser("bm25search", help="Search movies using full BM25 scoring")
    bm25search_parser.add_argument("query", type=str, help="Search query")
    args = parser.parse_args()

    match args.command:
        case "search":
            # print the search query here
            print(f"Searching for: {args.query}")
            results = search_command(args.query, 5)
            # Print numbered list of results
            for i, movie in enumerate(results, start=1):
                print(f"{i}. {movie['title']}")
        case "build":
            build_command()
        case "tf":
            tf_command(args.doc_id, args.term)
        case "idf":
            idf_command(args.term)
        case "bm25idf":
            bm25_idf_command(args.term)
        case "tfidf":
            tfidf_command(args.doc_id, args.term)
        case "bm25tf":
            bm25_tf_command(args.doc_id, args.term, args.k1, args.b1)
        case "bm25search":
            print("Searching for:", args.query)
            results = bm25search_command(args.query)
            for i, res in enumerate(results, 1):
                print(f"{i}. ({res['id']}) {res['title']} - Score: {res['score']:.2f}")
        case _:
            parser.print_help()

if __name__ == "__main__":
    main()