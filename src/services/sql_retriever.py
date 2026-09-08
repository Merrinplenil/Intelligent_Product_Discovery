import logging

from src.config.connection import get_connection
from src.config.category_rules import CATEGORY_PATTERNS


logger = logging.getLogger(__name__)


def get_products(
    max_price=None,
    availability=None,
    category=None,
    candidate_ids=None,
    subcategory=None,
    limit=10
):

    logger.info(
        "SQL search started. category=%s, candidate_ids=%s",
        category,
        candidate_ids
    )

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            product_id,
            sku,
            product_title,
            product_price,
            breadcrumbs,
            availability
        FROM products
        WHERE 1=1
    """

    params = []

    # --------------------------------------------------
    # Candidate IDs from Vector search
    # --------------------------------------------------

    if candidate_ids:

        placeholders = ",".join(
            ["%s"] * len(candidate_ids)
        )

        query += f"""
            AND product_id IN ({placeholders})
        """

        params.extend(candidate_ids)

    
    # --------------------------------------------------
    # Category filter
    # --------------------------------------------------

    if category is not None:

        category_lower = category.lower()
        
        patterns = CATEGORY_PATTERNS.get(
            category_lower,
            [category_lower]
        )

        logger.info(
            "Category=%s, patterns=%s",
            category,
            patterns
        )

        conditions = " OR ".join(
            [
                "LOWER(breadcrumbs) LIKE %s"
                for _ in patterns
            ]
        )

        query += f"""
            AND ({conditions})
        """

        for pattern in patterns:

            params.append(
                f"%{pattern.lower()}%"
            )

    # --------------------------------------------------
    # Desk-specific filtering
    # --------------------------------------------------

    if (
        category is not None
        and category.lower() in ["desk", "desks"]
    ):

        query += """
            AND LOWER(product_title) LIKE %s
            AND LOWER(product_title) NOT LIKE %s
            AND LOWER(product_title) NOT LIKE %s
            AND LOWER(product_title) NOT LIKE %s
            AND LOWER(product_title) NOT LIKE %s
        """

        params.extend([
            "%desk%",
            "%tabletop%",
            "%screen%",
            "%support%",
            "%add-on%"
        ])

    # --------------------------------------------------
    # Office desk filtering
    # --------------------------------------------------

    if (
        category is not None
        and category.lower() == "office desk"
    ):

        query += """
            AND LOWER(product_title) LIKE %s
        """

        params.append("%desk%")

    # --------------------------------------------------
    # Living room filtering
    # Remove accessories, hardware and furniture parts
    # --------------------------------------------------

    if (
        category is not None
        and category.lower() == "living room"
    ):

        excluded_keywords = [
            "cover",
            "armrest",
            "headrest",
            "accessor",
            "accessories",
            "hardware",
            "rail",
            "end cap",
            "connection",
            "extra shelf",
            "insert",
            "cushion",
            "chair pad",
            "pad",
            "replacement",
            "spare",
            "fitting",
            "bracket"
        ]

        for keyword in excluded_keywords:

            query += """
                AND LOWER(product_title) NOT LIKE %s
            """

            params.append(
                f"%{keyword}%"
            )

    # --------------------------------------------------
    # Sofa-specific filtering
    # --------------------------------------------------

    if (
        category is not None
        and category.lower() == "sofa"
    ):

        query += """
            AND (
                LOWER(product_title) LIKE %s
                OR LOWER(product_title) LIKE %s
                OR LOWER(product_title) LIKE %s
                OR LOWER(product_title) LIKE %s
            )

            AND LOWER(product_title) NOT LIKE %s
            AND LOWER(product_title) NOT LIKE %s
            AND LOWER(product_title) NOT LIKE %s
            AND LOWER(product_title) NOT LIKE %s
            AND LOWER(product_title) NOT LIKE %s
            AND LOWER(product_title) NOT LIKE %s
        """

        params.extend([
            "%sofa%",
            "%loveseat%",
            "%section%",
            "%chaise%",

            "%cover%",
            "%cushion%",
            "%armrest%",
            "%headrest%",
            "%leg%",
            "%accessor%"
        ])

    # --------------------------------------------------
    # Subcategory filter
    # --------------------------------------------------

    if subcategory is not None:

        query += """
            AND LOWER(breadcrumbs) LIKE %s
        """

        params.append(
            f"%/{subcategory.lower()}/%"
        )

    # --------------------------------------------------
    # Price filter
    # --------------------------------------------------

    if max_price is not None:

        query += """
            AND product_price <= %s
        """

        params.append(max_price)

    # --------------------------------------------------
    # Availability filter
    # --------------------------------------------------

    if availability is not None:

        query += """
            AND availability = %s
        """

        params.append(availability)

    # --------------------------------------------------
    # Sorting + limit
    # --------------------------------------------------

    query += """
        ORDER BY product_price ASC
        LIMIT %s
    """

    params.append(limit)

    # --------------------------------------------------
    # Execute
    # --------------------------------------------------

    logger.debug(
        "Executing SQL query with parameters: %s",
        params
    )

    cursor.execute(query, params)

    products = cursor.fetchall()

    cursor.close()
    connection.close()

    logger.info(
        "SQL search completed. Products found: %d",
        len(products)
    )

    return products