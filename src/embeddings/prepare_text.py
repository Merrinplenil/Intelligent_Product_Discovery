import pandas as pd

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


if __name__ == "__main__":
    df = pd.read_csv(CSV_PATH)

    print("Products loaded:", len(df))
    print("Columns:", list(df.columns))

    df["embedding_text"] = df.apply(
        prepare_product_text,
        axis=1
    )

    print("\nExample embedding text:")
    print(df["embedding_text"].iloc[0])

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(f"\nSaved {len(df)} products to {OUTPUT_PATH}")