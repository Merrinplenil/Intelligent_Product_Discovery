import chromadb
from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"
model = SentenceTransformer(MODEL_NAME)
def search_products(
    query,
    top_k=10,
    candidate_ids=None,
    category=None
):
    

    client = chromadb.PersistentClient(path="data/chroma_db")

    collection = client.get_collection(
        name="products"
    )

    query_embedding = model.encode(query).tolist()
    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": top_k
    }

    # if candidate_ids:
    #     query_args["where"] = {
    #         "product_id": {
    #             "$in": [str(pid) for pid in candidate_ids]
    #         }
    #     }
    if candidate_ids and category:
        query_args["where"] = {
            "$and": [
                {
                    "product_id": {
                        "$in": [str(pid) for pid in candidate_ids]
                    }
                },
                {
                    "category": category
                }
            ]
        }

    elif candidate_ids:
        query_args["where"] = {
            "product_id": {
                "$in": [str(pid) for pid in candidate_ids]
            }
        }

    elif category:
        query_args["where"] = {
            "category": category
        }
    print("Candidate IDs sent to Chroma:", candidate_ids)
    print("Category sent to Chroma:", category)
    print("Where filter:", query_args.get("where"))
    
    results = collection.query(**query_args)

    ids = results["ids"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    products = []

    for product_id, metadata, distance in zip(ids, metadatas, distances):
        products.append({
            "product_id": int(product_id),
            "sku": metadata["sku"],
            "product_title": metadata["product_title"],
            "brand": metadata["brand"],
            "product_price": metadata["product_price"],
            "availability": metadata["availability"],
            "breadcrumbs": metadata["breadcrumbs"],
            "distance": distance
        })

    return products


if __name__ == "__main__":
   
    results = search_products(
        "Scandinavian living room",
        top_k=10,
        category="living room"
    )
    print(results)