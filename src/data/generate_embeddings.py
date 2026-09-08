import logging

import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer

from src.config.connection import get_connection


logger = logging.getLogger(__name__)


MODEL_NAME = "BAAI/bge-small-en-v1.5"
CSV_PATH = "data/ikea_products_embedding_ready.csv"
CHROMA_PATH = "data/chroma_db"


def generate_embeddings():

    # --------------------------------------------------
    # 1. Load embedding model
    # --------------------------------------------------

    logger.info("Loading embedding model: %s", MODEL_NAME)

    model = SentenceTransformer(MODEL_NAME)

    logger.info(
        "Embedding model loaded successfully."
    )

    # --------------------------------------------------
    # 2. Load embedding-ready CSV
    # --------------------------------------------------

    logger.info(
        "Loading embedding-ready CSV: %s",
        CSV_PATH
    )

    df = pd.read_csv(CSV_PATH)

    logger.info(
        "Products loaded: %d",
        len(df)
    )

    logger.debug(
        "Columns: %s",
        list(df.columns)
    )

    # --------------------------------------------------
    # 3. Get product_id from MySQL using SKU
    # --------------------------------------------------

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT product_id, sku
        FROM products
    """)

    products = cursor.fetchall()

    cursor.close()
    connection.close()

    product_id_map = {
        row["sku"]: row["product_id"]
        for row in products
    }

    df["product_id"] = df["sku"].map(
        product_id_map
    )

    logger.info(
        "Products with product_id: %d",
        df["product_id"].notna().sum()
    )

    logger.info(
        "Products without product_id: %d",
        df["product_id"].isna().sum()
    )

    # Stop if some products could not be mapped
    if df["product_id"].isna().any():

        logger.error(
            "Some products do not have a product_id."
        )

        logger.error(
            "Products missing product_id:\n%s",
            df[df["product_id"].isna()][
                ["sku", "product_title"]
            ].head(20)
        )

        raise ValueError(
            "Product ID mapping failed. "
            "Fix SKU mapping before generating embeddings."
        )

    # --------------------------------------------------
    # 4. Generate embeddings
    # --------------------------------------------------

    logger.info("Generating embeddings...")

    embeddings = model.encode(
        df["embedding_text"].tolist(),
        batch_size=32,
        show_progress_bar=True
    )

    logger.info(
        "Embeddings generated successfully."
    )

    logger.info(
        "Number of embeddings: %d",
        len(embeddings)
    )

    logger.info(
        "Embedding dimensions: %d",
        len(embeddings[0])
    )

    # --------------------------------------------------
    # 5. Connect to ChromaDB
    # --------------------------------------------------

    logger.info(
        "Connecting to ChromaDB..."
    )

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_or_create_collection(
        name="products"
    )

    logger.info(
        "ChromaDB collection ready."
    )

    # --------------------------------------------------
    # 6. Insert embeddings + metadata
    # --------------------------------------------------

    batch_size = 500

    for start in range(
        0,
        len(df),
        batch_size
    ):

        end = min(
            start + batch_size,
            len(df)
        )

        batch_df = df.iloc[start:end]

        collection.add(

            # Chroma ID
            ids=batch_df[
                "product_id"
            ].astype(str).tolist(),

            # Vector embeddings
            embeddings=embeddings[
                start:end
            ].tolist(),

            # Original embedding text
            documents=batch_df[
                "embedding_text"
            ].tolist(),

            # Metadata
            metadatas=[
                {
                    "product_id": str(
                        row["product_id"]
                    ),
                    "sku": str(row["sku"]),
                    "product_title": str(
                        row["product_title"]
                    ),
                    "brand": str(row["brand"]),
                    "breadcrumbs": str(
                        row["breadcrumbs"]
                    ),
                    "product_price": float(
                        row["product_price"]
                    ),
                    "availability": str(
                        row["availability"]
                    )
                }
                for _, row in batch_df.iterrows()
            ]
        )

        logger.info(
            "Inserted %d/%d products into ChromaDB.",
            end,
            len(df)
        )

    # --------------------------------------------------
    # 7. Verify ChromaDB
    # --------------------------------------------------

    logger.info(
        "All products inserted into ChromaDB."
    )

    logger.info(
        "ChromaDB count: %d",
        collection.count()
    )


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    generate_embeddings()