import logging

from src.services.sql_retriever import get_products
from src.services.vector_retriever import search_products
from src.core.result_evaluator import evaluate_results
from src.core.query_planner import plan_query


logger = logging.getLogger(__name__)


def execute_plan(plan):

    execution_plan = plan["execution_plan"]

    structured = plan.get(
        "structured_constraints",
        {}
    )

    semantic = plan.get(
        "semantic_constraints",
        []
    )

    # ==================================================
    # SQL ONLY
    # ==================================================

    if execution_plan == "SQL_ONLY":

        return get_products(
            max_price=structured.get("max_price"),
            availability=structured.get("availability"),
            category=structured.get("category"),
            limit=plan.get("limit", 10)
        )

    # ==================================================
    # VECTOR ONLY
    # ==================================================

    elif execution_plan == "VECTOR_ONLY":

        query = " ".join(semantic)

        return search_products(
            query,
            top_k=plan.get("limit", 10)
        )

    # ==================================================
    # SQL → VECTOR
    # ==================================================

    elif execution_plan == "SQL_TO_VECTOR":

        logger.info(
            "Executing SQL_TO_VECTOR with structured constraints: %s",
            structured
        )

        # Step 1:
        # SQL applies exact / structured constraints
        sql_results = get_products(
            max_price=structured.get("max_price"),
            availability=structured.get("availability"),
            category=structured.get("category"),
            subcategory=structured.get("subcategory"),
            limit=50
        )

        logger.info(
            "SQL candidates found: %d",
            len(sql_results)
        )

        if not sql_results:
            return []

        # Extract candidate IDs
        candidate_ids = [
            product["product_id"]
            for product in sql_results
        ]

        # Build semantic query
        query = " ".join(
            [structured.get("category", "")]
            + semantic
        )

        # Step 2:
        # Vector search ranks SQL candidates
        return search_products(
            query,
            top_k=plan.get("limit", 10),
            candidate_ids=candidate_ids
        )

    # ==================================================
    # VECTOR → SQL
    # ==================================================

    elif execution_plan == "VECTOR_TO_SQL":

        # Step 1:
        # Vector finds semantically relevant products
        semantic_query = " ".join(
            [structured.get("category", "")]
            + semantic
        )

        logger.info(
            "Executing VECTOR_TO_SQL with semantic query: %s",
            semantic_query
        )

        vector_results = search_products(
            semantic_query,
            top_k=50,
            category=structured.get("category")
        )

        # Extract product IDs
        candidate_ids = [
            product["product_id"]
            for product in vector_results
        ]

        if not candidate_ids:
            return []

        # Preserve semantic distances
        distance_map = {
            product["product_id"]: product.get("distance")
            for product in vector_results
        }

        # Step 2:
        # SQL applies exact constraints
        final_results = get_products(
            candidate_ids=candidate_ids,
            max_price=structured.get("max_price"),
            availability=structured.get("availability"),
            category=structured.get("category"),
            subcategory=structured.get("subcategory"),
            limit=plan.get("limit", 10)
        )

        # Restore semantic distances
        for product in final_results:

            product["distance"] = distance_map.get(
                product["product_id"]
            )

        # Smaller distance = better semantic match
        final_results.sort(
            key=lambda product: (
                product["distance"]
                if product["distance"] is not None
                else float("inf")
            )
        )

        return final_results

    # ==================================================
    # UNKNOWN PLAN
    # ==================================================

    else:

        raise ValueError(
            f"Unknown execution plan: {execution_plan}"
        )


# ======================================================
# MAIN FUNCTION FOR UI
# ======================================================

def search(query):

    # Generate execution plan
    plan = plan_query(query)

    # Execute plan
    results = execute_plan(plan)

    # Evaluate results
    evaluation = evaluate_results(
        results,
        structured_constraints=plan.get(
            "structured_constraints",
            {}
        ),
        semantic_constraints=plan.get(
            "semantic_constraints",
            []
        )
    )

    return {
        "plan": plan,
        "results": results,
        "evaluation": evaluation
    }


# ======================================================
# TERMINAL TEST
# ======================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    query = "cosy furniture for a reading corner"

    output = search(query)

    plan = output["plan"]
    results = output["results"]
    evaluation = output["evaluation"]

    print("\n=== QUERY ===")
    print(query)

    print("\n=== GENERATED PLAN ===")
    print(plan)

    print("\n=== EVALUATION ===")
    print(evaluation)

    print("\n=== FINAL RESULTS ===")

    print(
        "Execution plan:",
        plan["execution_plan"]
    )

    print(
        "Results found:",
        len(results)
    )

    for product in results:
        print(product)