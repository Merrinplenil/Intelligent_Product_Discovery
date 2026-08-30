import pandas as pd

from connection import get_connection


CSV_PATH = "data/ikea_products_cleaned.csv"


def load_products():
    df = pd.read_csv(CSV_PATH)

    # Convert Pandas NaN values to None so MySQL stores them as NULL
    df = df.where(pd.notna(df), None)

    connection = get_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO products (
            product_title,
            product_url,
            sku,
            mpn,
            currency,
            product_price,
            product_condition,
            availability,
            seller,
            seller_url,
            brand,
            raw_product_details,
            cleaned_product_details,
            breadcrumbs,
            country,
            language,
            average_rating,
            reviews_count
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    records = [
        tuple(row)
        for row in df[
            [
                "product_title",
                "product_url",
                "sku",
                "mpn",
                "currency",
                "product_price",
                "product_condition",
                "availability",
                "seller",
                "seller_url",
                "brand",
                "raw_product_details",
                "cleaned_product_details",
                "breadcrumbs",
                "country",
                "language",
                "average_rating",
                "reviews_count",
            ]
        ].to_numpy()
    ]

    batch_size = 500
    total_inserted = 0

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]

        cursor.executemany(query, batch)
        connection.commit()

        total_inserted += len(batch)

        print(f"Inserted {total_inserted} / {len(records)} products")

    cursor.close()
    connection.close()


if __name__ == "__main__":
    load_products()