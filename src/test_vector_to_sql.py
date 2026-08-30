import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from database.sql_retriever import get_products
from embeddings.vector_retriever import search_products


if __name__ == "__main__":

    # Step 1: Vector search finds semantically relevant products
    vector_results = search_products(
        "comfortable office chair",
        top_k=10
    )

    candidate_ids = [
        product["product_id"]
        for product in vector_results
    ]

    print(f"Vector candidates: {len(candidate_ids)}")
    print("Candidate IDs:", candidate_ids)

    # Step 2: SQL applies structured constraints
    # We first retrieve the candidates from SQL,
    # then keep only the products whose IDs came from vector search.
  
    # final_results = get_products(
    #     max_price=150,
    #     availability="InStock",
    #     category="chair",
    #     candidate_ids=candidate_ids,
    #     limit=100
    # )
    final_results = get_products(
        candidate_ids=candidate_ids,
        limit=100
    )
    print("\nFinal Vector → SQL results:")

    if not final_results:
        print("No Product")
    else:
        for product in final_results:
            print(product)