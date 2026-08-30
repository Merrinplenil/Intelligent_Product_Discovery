import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from database.connection import get_connection


MODEL_NAME = "BAAI/bge-small-en-v1.5"
CSV_PATH = "data/ikea_products_embedding_ready.csv"
CHROMA_PATH = "data/chroma_db"


if __name__ == "__main__":

    # --------------------------------------------------
    # 1. Load embedding model
    # --------------------------------------------------
    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    print("Embedding model loaded successfully!")


    # --------------------------------------------------
    # 2. Load embedding-ready CSV
    # --------------------------------------------------
    print("Loading embedding-ready CSV...")

    df = pd.read_csv(CSV_PATH)

    print(f"Products loaded: {len(df)}")
    print(f"Columns: {list(df.columns)}")


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


    df["product_id"] = df["sku"].map(product_id_map)


    print(
        "Products with product_id:",
        df["product_id"].notna().sum()
    )

    print(
        "Products without product_id:",
        df["product_id"].isna().sum()
    )


    # Stop if some products could not be mapped
    if df["product_id"].isna().any():
        print("ERROR: Some products do not have a product_id.")
        print(
            df[df["product_id"].isna()][
                ["sku", "product_title"]
            ].head(20)
        )

        raise ValueError(
            "Product ID mapping failed. Fix SKU mapping before generating embeddings."
        )


    # --------------------------------------------------
    # 4. Generate embeddings
    # --------------------------------------------------
    print("Generating embeddings...")

    embeddings = model.encode(
        df["embedding_text"].tolist(),
        batch_size=32,
        show_progress_bar=True
    )

    print("Embeddings generated!")
    print("Number of embeddings:", len(embeddings))
    print("Embedding dimensions:", len(embeddings[0]))


    # --------------------------------------------------
    # 5. Connect to ChromaDB
    # --------------------------------------------------
    print("Connecting to ChromaDB...")

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_or_create_collection(
        name="products"
    )

    print("ChromaDB collection ready!")


    # --------------------------------------------------
    # 6. Insert embeddings + metadata
    # --------------------------------------------------
    batch_size = 500

    for start in range(0, len(df), batch_size):

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
                    "product_id": str(row["product_id"]),
                    "sku": str(row["sku"]),
                    "product_title": str(row["product_title"]),
                    "brand": str(row["brand"]),
                    "breadcrumbs": str(row["breadcrumbs"]),
                    "product_price": float(row["product_price"]),
                    "availability": str(row["availability"])
                }
                for _, row in batch_df.iterrows()
            ]
        )

        print(
            f"Inserted {end}/{len(df)} products"
        )


    # --------------------------------------------------
    # 7. Verify ChromaDB
    # --------------------------------------------------
    print("All products inserted into ChromaDB!")

    print(
        "ChromaDB count:",
        collection.count()
    )
