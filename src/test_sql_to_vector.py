import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database.sql_retriever import get_products
from embeddings.vector_retriever import search_products
if __name__ == "__main__":

    # Step 1: SQL retrieves structured candidates
    candidates = get_products(
        max_price=150,
        availability="InStock",
        category="chair",
        limit=50
    )

    candidate_ids = [
        product["product_id"]
        for product in candidates
    ]

    print(f"SQL candidates: {len(candidate_ids)}")

    # Step 2: Vector ranks those candidates semantically
    results = search_products(
        "comfortable office chair",
        top_k=10,
        candidate_ids=candidate_ids
    )

    print("\nFinal SQL → Vector results:")

    for product in results:
        print(product)