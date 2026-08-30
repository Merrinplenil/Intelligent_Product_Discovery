from execution_engine import execute_plan
from query_planner import plan_query
from result_evaluator import evaluate_results


test_queries = [
    "living room furniture under $200",
    "cosy furniture for a reading corner",
    "compact desks under $250 suitable for a small home office",
    "Scandinavian-style living room"
]


for query in test_queries:

    print("\n" + "=" * 60)
    print("QUERY:")
    print(query)

    # Step 1: Generate plan
    plan = plan_query(query)

    print("\nGENERATED PLAN:")
    print(plan)

    # Step 2: Execute plan
    results = execute_plan(plan)

    # Step 3: Evaluate results
    evaluation = evaluate_results(
        results,
        structured_constraints=plan.get(
            "structured_constraints", {}
        ),
        semantic_constraints=plan.get(
            "semantic_constraints", []
        )
    )

    print("\nEVALUATION:")
    print(evaluation)

    print("\nFINAL RESULTS:")
    print("Execution plan:", plan["execution_plan"])
    print("Results found:", len(results))

    for product in results:
        print(
            product["product_title"],
            "-",
            product["product_price"]
        )