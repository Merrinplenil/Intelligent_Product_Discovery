import json
import pandas as pd
from bs4 import BeautifulSoup
DATA_PATH = "data/ikea_sample_file.json"


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("JSON type:", type(data))

    if isinstance(data, dict):
        print("Dictionary keys:", data.keys())

    return data
def clean_product_details(html):
    if not html or not isinstance(html, str):
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # Extract text from all HTML elements
    text = soup.get_text(" ", strip=True)

    return text

def main():
    data = load_data()

    # Convert JSON to DataFrame
    if isinstance(data, list):
        df = pd.DataFrame(data)
    elif isinstance(data, dict):
        # Adjust this if the products are stored under a specific key
        df = pd.DataFrame(data)

    print("\nShape:", df.shape)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nData types:")
    print(df.dtypes)

    print("\nMissing values:")
    print(df.isna().sum())

    print("\nDuplicate rows:", df.duplicated().sum())
    df = df.drop_duplicates()

    print("Rows after removing exact duplicates:", len(df))
    print("Remaining duplicate SKUs:", df["sku"].duplicated().sum())
    print("Unique SKUs:", df["sku"].nunique())
    for column in ["average_rating", "reviews_count"]:
        blank_count = df[column].astype(str).str.strip().eq("").sum()
    print(f"{column} - blank values:", blank_count)
    print(
    "average_rating - blank values:",
    df["average_rating"].astype(str).str.strip().eq("").sum()
    )
    non_numeric = pd.to_numeric(df[column], errors="coerce").isna() & df[column].notna()
    print(f"{column} - non-numeric values:", non_numeric.sum())

    print(f"{column} - examples of non-numeric values:")
    print(df.loc[non_numeric, column].value_counts().head(10))

    df["product_price"] = pd.to_numeric(df["product_price"], errors="coerce")
    df[ "average_rating"] = pd.to_numeric(df["average_rating"], errors="coerce")
    df["reviews_count"] = pd.to_numeric(df["reviews_count"], errors="coerce")
    print(df[["product_price", "average_rating", "reviews_count"]].dtypes)
    print(df[["product_price", "average_rating", "reviews_count"]].isna().sum())

    print("\nRaw product details sample:")
    print(df["raw_product_details"].iloc[0])
    df["cleaned_product_details"] = df["raw_product_details"].apply(
    clean_product_details
                        )
    df["embedding_text"] = (
    "Product: " + df["product_title"].fillna("") +
    ". Brand: " + df["brand"].fillna("") +
    ". Category: " + df["breadcrumbs"].fillna("") +
    ". Description: " + df["cleaned_product_details"].fillna("")
    )
    print("\nCleaned product details sample:")
    print(df["cleaned_product_details"].iloc[0])

    # OUTPUT_PATH = "data/ikea_products_cleaned.csv"
    OUTPUT_PATH = "data/ikea_products_embedding_ready.csv"
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"\nCleaned dataset saved to: {OUTPUT_PATH}")
    print(f"Final shape: {df.shape}")
if __name__ == "__main__":
    main()