import logging

import pandas as pd


logger = logging.getLogger(__name__)

CSV_PATH = "data/ikea_products_cleaned.csv"
OUTPUT_PATH = "data/ikea_products_embedding_ready.csv"


def prepare_product_text(row):
    parts = [
        f"Product: {row['product_title']}",
        f"Brand: {row['brand']}",
        f"Category: {row['breadcrumbs']}",
        f"Details: {row['cleaned_product_details']}",
    ]

    return "\n".join(
        part
        for part in parts
        if pd.notna(part.split(": ", 1)[-1])
        and str(part.split(": ", 1)[-1]).strip()
    )


def prepare_embeddings_file():
    df = pd.read_csv(CSV_PATH)

    logger.info("Products loaded: %s", len(df))
    logger.info("Columns: %s", list(df.columns))

    df["embedding_text"] = df.apply(
        prepare_product_text,
        axis=1
    )

    logger.info("Example embedding text:\n%s", df["embedding_text"].iloc[0])

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    logger.info(
        "Saved %s products to %s",
        len(df),
        OUTPUT_PATH
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prepare_embeddings_file()