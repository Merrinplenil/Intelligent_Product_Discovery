import pandas as pd
import chromadb


CSV_PATH = "data/ikea_products_embedding_ready.csv"
CHROMA_PATH = "data/chroma_db"

def get_category(breadcrumbs):
    breadcrumbs = str(breadcrumbs).lower()

    # ----------------------------------------
    # Living room furniture
    # ----------------------------------------
    if "sofas & sectionals" in breadcrumbs:

        # Exclude covers and accessories
        if any(word in breadcrumbs for word in [
            "covers",
            "accessories",
            "armrest",
            "headrest",
            "cushion"
        ]):
            return "other"

        return "living room"

    if "armchairs & accent chairs" in breadcrumbs:

        # Exclude covers and accessories
        if any(word in breadcrumbs for word in [
            "covers",
            "accessories",
            "cushion"
        ]):
            return "other"

        return "living room"

    # ----------------------------------------
    # Desks
    # ----------------------------------------
    if "desks & computer desks" in breadcrumbs:
        return "desk"

    # ----------------------------------------
    # Dining tables
    # ----------------------------------------
    if "dining tables" in breadcrumbs:
        return "dining table"

    # ----------------------------------------
    # Beds
    # ----------------------------------------
    if "beds" in breadcrumbs:
        return "bed"

    # ----------------------------------------
    # Chairs
    # ----------------------------------------
    if "chairs" in breadcrumbs:
        return "chair"

    return "other"


client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_collection(
    name="products"
)

df = pd.read_csv(CSV_PATH)

print("CSV products:", len(df))
print("Chroma products:", collection.count())


# Get existing Chroma IDs
existing = collection.get(
    include=["metadatas"]
)

ids = existing["ids"]
metadatas = existing["metadatas"]

print("Metadata records:", len(ids))


updated_metadatas = []

for metadata in metadatas:

    breadcrumbs = metadata.get("breadcrumbs", "")

    metadata["category"] = get_category(
        breadcrumbs
    )

    updated_metadatas.append(metadata)


# Update metadata ONLY
# Chroma has a maximum batch size
batch_size = 5000

for start in range(0, len(ids), batch_size):

    end = min(
        start + batch_size,
        len(ids)
    )

    print(
        f"Updating metadata {start} -> {end}"
    )

    collection.update(
        ids=ids[start:end],
        metadatas=updated_metadatas[start:end]
    )

print("Metadata update complete!")