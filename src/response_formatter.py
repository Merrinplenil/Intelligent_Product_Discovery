def format_response(response: dict) -> str:

    status = response.get("status")
    products = response.get("products", [])
    relaxations = response.get("relaxations", [])

    lines = []

    # -------------------------
    # No results
    # -------------------------
    if status == "NO_MATCH":

        lines.append(
            "Sorry, no products were found matching your requirements."
        )

        return "\n".join(lines)

    # -------------------------
    # Match quality
    # -------------------------
    if status == "STRONG_MATCH":

        lines.append(
            "Great news! I found products that closely match your requirements."
        )

    elif status == "PARTIAL_MATCH":

        lines.append(
            "I found some products that partially match your requirements."
        )

    elif status == "WEAK_MATCH":

        lines.append(
            "No exact match was found for your original requirements."
        )

    # -------------------------
    # Explain relaxations
    # -------------------------
    if relaxations:

        lines.append("")
        lines.append(
            "To find alternatives, the following constraints were relaxed:"
        )

        for relaxation in relaxations:
            lines.append(f"- {relaxation}")

    # -------------------------
    # Products
    # -------------------------
    if products:

        lines.append("")
        lines.append("Recommended products:")

        for index, product in enumerate(products, start=1):

            title = product.get(
                "product_title",
                "Unknown product"
            )

            price = product.get(
                "product_price",
                "N/A"
            )

            brand = product.get(
                "brand",
                ""
            )

            availability = product.get(
                "availability",
                ""
            )

            lines.append(
                f"\n{index}. {title}"
            )

            if brand:
                lines.append(
                    f"   Brand: {brand}"
                )

            lines.append(
                f"   Price: ${price}"
            )

            if availability:
                lines.append(
                    f"   Availability: {availability}"
                )

    return "\n".join(lines)