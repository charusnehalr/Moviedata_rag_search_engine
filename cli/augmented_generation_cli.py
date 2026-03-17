import argparse
from lib.rag import query_answer, doc_summarize

def main():
    parser = argparse.ArgumentParser(description="Retrieval Augmented Generation CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    rag_parser = subparsers.add_parser("rag", help="Perform RAG (search + generate answer)")
    rag_parser.add_argument("query", type=str, help="Search query for RAG")
    
    rag_summary_parser = subparsers.add_parser("summarize", help="Perform RAG summary")
    rag_summary_parser.add_argument("query", type=str, help="Search query for RAG")
    rag_summary_parser.add_argument("--limit", type=int, default=5, help="Limit of output")
    

    args = parser.parse_args()

    match args.command:
        case "rag":
            query_answer(args.query)
        case "summarize":
            doc_summarize(args.query, args.limit)

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()