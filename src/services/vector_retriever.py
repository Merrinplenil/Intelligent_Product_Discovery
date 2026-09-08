import logging

import chromadb
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


MODEL_NAME = "BAAI/bge-small-en-v1.5"

_model = None


def get_model():
    """
    Load the embedding model only when it is needed.
    The loaded model is reused for subsequent searches.
    """

    global _model

    if _model is None:

        logger.info(
            "Loading embedding model: %s",
            MODEL_NAME
        )

        _model = SentenceTransformer(MODEL_NAME)

    return _model


def search_products(
    query,
    top_k=10,
    candidate_ids=None,
    category=None
):

    model = get_model()

    client = chromadb.PersistentClient(
        path="data/chroma_db"
    )

    collection = client.get_collection(
        name="products"
    )

    query_embedding = model.encode(
        query
    ).tolist()

    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": top_k
    }

    # --------------------------------------------------
    # Candidate + category filter
    # --------------------------------------------------

    if candidate_ids and category:

        query_args["where"] = {
            "$and": [
                {
                    "product_id": {
                        "$in": [
                            str(pid)
                            for pid in candidate_ids
                        ]
                    }
                },
                {
                    "category": category
                }
            ]
        }

    # --------------------------------------------------
    # Candidate ID filter
    # --------------------------------------------------

    elif candidate_ids:

        query_args["where"] = {
            "product_id": {
                "$in": [
                    str(pid)
                    for pid in candidate_ids
                ]
            }
        }

    # --------------------------------------------------
    # Category filter
    # --------------------------------------------------

    elif category:

        query_args["where"] = {
            "category": category
        }

    logger.debug(
        "Candidate IDs sent to Chroma: %s",
        candidate_ids
    )

    logger.debug(
        "Category sent to Chroma: %s",
        category
    )

    logger.debug(
        "Chroma where filter: %s",
        query_args.get("where")
    )

    # --------------------------------------------------
    # Vector search
    # --------------------------------------------------

    results = collection.query(
        **query_args
    )

    ids = results["ids"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    products = []

    for product_id, metadata, distance in zip(
        ids,
        metadatas,
        distances
    ):

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

    logger.info(
        "Vector search completed. Products found: %d",
        len(products)
    )

    return products


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    results = search_products(
        "Scandinavian living room",
        top_k=10,
        category="living room"
    )

    print(results)