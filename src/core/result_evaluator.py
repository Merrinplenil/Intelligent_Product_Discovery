import logging


logger = logging.getLogger(__name__)


def evaluate_results(
    results,
    structured_constraints=None,
    semantic_constraints=None
):
    """
    Evaluate retrieved products.

    Returns:
        status: VALID / WEAK / EMPTY
        confidence: 0.0 - 1.0
        results: validated results
        reason: explanation
    """

    structured_constraints = structured_constraints or {}
    semantic_constraints = semantic_constraints or []

    # --------------------------------
    # 1. Empty result check
    # --------------------------------

    if not results:
        logger.info("No products were retrieved.")

        return {
            "status": "EMPTY",
            "confidence": 0.0,
            "result_count": 0,
            "results": [],
            "reason": "No products were retrieved."
        }

    # --------------------------------
    # 2. Check hard constraints
    # --------------------------------

    valid_results = []

    max_price = structured_constraints.get("max_price")
    availability = structured_constraints.get("availability")

    for product in results:

        # Price constraint
        if max_price is not None:

            product_price = product.get("product_price")

            if product_price is None:
                logger.warning(
                    "Product %s has no price value.",
                    product.get("product_id", "unknown")
                )
                continue

            try:
                if float(product_price) > float(max_price):
                    continue
            except (TypeError, ValueError):
                logger.warning(
                    "Invalid price value for product %s: %s",
                    product.get("product_id", "unknown"),
                    product_price
                )
                continue

        # Availability constraint
        if availability is not None:

            product_availability = product.get("availability")

            if product_availability != availability:
                continue

        valid_results.append(product)

    # --------------------------------
    # 3. Check if all results failed
    # --------------------------------

    if not valid_results:

        logger.info(
            "All retrieved products failed the hard constraints."
        )

        return {
            "status": "EMPTY",
            "confidence": 0.0,
            "result_count": 0,
            "results": [],
            "reason": (
                "Retrieved products do not satisfy "
                "the hard constraints."
            )
        }

    # --------------------------------
    # 4. Calculate semantic distance
    # --------------------------------

    distances = []

    for product in valid_results:

        distance = product.get("distance")

        if distance is not None:

            try:
                distances.append(float(distance))

            except (TypeError, ValueError):

                logger.warning(
                    "Invalid distance value for product %s: %s",
                    product.get("product_id", "unknown"),
                    distance
                )

    average_distance = None

    if distances:
        average_distance = sum(distances) / len(distances)

    top_distances = sorted(distances)[:5]

    top5_average_distance = None

    if top_distances:
        top5_average_distance = (
            sum(top_distances) / len(top_distances)
        )

    # --------------------------------
    # 5. Result count
    # --------------------------------

    result_count = len(valid_results)

    # --------------------------------
    # 6. Basic confidence
    # --------------------------------

    if result_count >= 5:

        confidence = 1.0
        status = "VALID"

    elif result_count >= 2:

        confidence = 0.7
        status = "VALID"

    else:

        confidence = 0.4
        status = "WEAK"

    # --------------------------------
    # 7. Semantic quality
    # --------------------------------

    if semantic_constraints and top5_average_distance is not None:

        if top5_average_distance <= 0.60:

            semantic_confidence = 1.0

        elif top5_average_distance <= 0.70:

            semantic_confidence = 0.8

        elif top5_average_distance <= 0.80:

            semantic_confidence = 0.6

        else:

            semantic_confidence = 0.3

        confidence = confidence * semantic_confidence

        if confidence < 0.5:
            status = "WEAK"

        reason = (
            f"Hard constraints satisfied. "
            f"Top-5 semantic average distance: "
            f"{top5_average_distance:.3f}."
        )

        if top5_average_distance > 0.80:

            reason += " Semantic relevance is weak."

        elif top5_average_distance > 0.70:

            reason += " Semantic relevance is moderate."

        else:

            reason += " Semantic relevance is good."

    else:

        reason = (
            "Retrieved products satisfy the available "
            "hard constraints."
        )

    # --------------------------------
    # 8. Final evaluation
    # --------------------------------

    evaluation = {
        "status": status,
        "confidence": confidence,
        "result_count": result_count,
        "average_distance": average_distance,
        "top5_average_distance": top5_average_distance,
        "results": valid_results,
        "reason": reason
    }

    logger.info(
        "Evaluation completed: status=%s, confidence=%.2f, results=%d",
        status,
        confidence,
        result_count
    )

    return evaluation


# ======================================================
# TEST
# ======================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    test_results = [
        {
            "product_id": 1,
            "product_title": "Test Desk",
            "product_price": 100,
            "availability": "InStock"
        },
        {
            "product_id": 2,
            "product_title": "Another Desk",
            "product_price": 150,
            "availability": "InStock"
        }
    ]

    constraints = {
        "max_price": 200,
        "availability": "InStock"
    }

    evaluation = evaluate_results(
        test_results,
        structured_constraints=constraints
    )

    print("Evaluation:")
    print(evaluation)