import argparse
import logging
import sys
import pandas as pd
from get_papers.fetcher import search_pubmed, fetch_details

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Fetch PubMed papers with non-academic authors"
    )
    parser.add_argument(
        "query", type=str, help="PubMed query (use quotes for multi-word queries)"
    )
    parser.add_argument(
        "-f", "--file", type=str, help="CSV file to save the results"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug output"
    )
    return parser.parse_args()

def main():
    args = parse_arguments()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    logging.info(f"Searching PubMed for query: {args.query}")
    
    try:
        pubmed_ids = search_pubmed(args.query)
        if not pubmed_ids:
            logging.warning("No results found.")
            sys.exit(0)

        logging.info(f"Found {len(pubmed_ids)} articles. Fetching details...")

        results = fetch_details(pubmed_ids)

        if not results:
            logging.warning("No non-academic papers found.")
            sys.exit(0)

        df = pd.DataFrame(results)

        if args.file:
            df.to_csv(args.file, index=False)
            print(f"\n✅ Results saved to: {args.file}")
        else:
            print("\n📄 Results:\n")
            print(df.to_string(index=False))

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)

