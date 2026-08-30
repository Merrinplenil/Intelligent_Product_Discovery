from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from query_planner import plan_query
from execution_engine import execute_plan
from result_evaluator import evaluate_results
from response_formatter import format_response

class ProductSearchState(TypedDict, total=False):

    query: str

    plan: dict
    results: list
    evaluation: dict

    retry_count: int

    original_constraints: dict

    final_response: dict

def planner_node(state: ProductSearchState):

    plan = plan_query(state["query"])

    # Deep-ish copy so the original is never modified
    original_plan = {
        **plan,
        "structured_constraints": {
            **plan.get("structured_constraints", {})
        },
        "semantic_constraints": list(
            plan.get("semantic_constraints", [])
        )
    }

    return {
        "plan": plan,
        "original_plan": original_plan,
        "relaxations": []
    }

def planner_node(state: ProductSearchState):

    plan = plan_query(state["query"])

    update = {
        "plan": plan
    }

    # Save the original user constraints only once
    if not state.get("original_constraints"):

        update["original_constraints"] = {
            "structured": {
                **plan.get(
                    "structured_constraints",
                    {}
                )
            },
            "semantic": list(
                plan.get(
                    "semantic_constraints",
                    []
                )
            )
        }

    return update

def executor_node(state: ProductSearchState):

    results = execute_plan(state["plan"])

    return {
        "results": results
    }


def evaluator_node(state: ProductSearchState):

    evaluation = evaluate_results(
        state["results"],
        structured_constraints=state["plan"].get(
            "structured_constraints", {}
        ),
        semantic_constraints=state["plan"].get(
            "semantic_constraints", []
        )
    )

    return {
        "evaluation": evaluation
    }

def retry_node(state: ProductSearchState):
    relaxations = list(state.get("relaxations", []))
    print("\n=== RETRY NODE ===")

    retry_count = state.get("retry_count", 0) + 1

    print("Retry count:", retry_count)

    # Copy the plan safely
    plan = {
        **state["plan"],
        "structured_constraints": {
            **state["plan"].get("structured_constraints", {})
        },
        "semantic_constraints": list(
            state["plan"].get("semantic_constraints", [])
        )
    }

    constraints = plan["structured_constraints"]
    semantic_constraints = plan["semantic_constraints"]

    # -----------------------------------
    # Retry strategy
    # -----------------------------------

    if retry_count == 1:

        # Relax price
        if "max_price" in constraints:

            old_price = constraints["max_price"]
            new_price = old_price * 2

            print(
                f"Relaxing max price: "
                f"${old_price} → ${new_price}"
            )

            constraints["max_price"] = new_price

            relaxations.append(
                 f"max_price: ${old_price} → ${new_price}"
            )

    elif retry_count == 2:

        # Relax price again
        if "max_price" in constraints:

            old_price = constraints["max_price"]
            new_price = old_price * 2

            print(
                f"Relaxing max price: "
                f"${old_price} → ${new_price}"
            )

            constraints["max_price"] = new_price

    elif retry_count == 3:

        # Remove strongest semantic constraint
        if semantic_constraints:

           
            removed_constraint = semantic_constraints.pop(0)

            print(
                "Relaxing semantic constraint:",
                removed_constraint
            )

            relaxations.append(
                f"removed semantic constraint: {removed_constraint}"
            )

    elif retry_count == 4:

        # Remove another semantic constraint
        if semantic_constraints:

            removed_constraint = semantic_constraints.pop(0)

            print(
                "Relaxing semantic constraint:",
                removed_constraint
            )

    # Execute with relaxed plan
    results = execute_plan(plan)

    return {
        "plan": plan,
        "results": results,
        "retry_count": retry_count
    }
def route_after_evaluation(state: ProductSearchState):

    confidence = state["evaluation"].get("confidence", 0)
    retry_count = state.get("retry_count", 0)

    print("\n=== ROUTING ===")
    print("Confidence:", confidence)
    print("Retry count:", retry_count)

    if confidence >= 0.7:
        print("Route: END")
        return "end"

    if retry_count >= 4:
        print("Maximum retries reached")
        print("Route: END")
        return "end"

    print("Route: RETRY")
    return "retry"
def response_node(state: ProductSearchState):

    evaluation = state["evaluation"]
    results = state["results"]

    confidence = evaluation.get("confidence", 0)
    result_count = evaluation.get("result_count", 0)

    # Determine final status
    if result_count == 0:
        status = "NO_MATCH"
    elif confidence >= 0.9:
        status = "STRONG_MATCH"
    elif confidence >= 0.6:
        status = "GOOD_MATCH"
    else:
        status = "WEAK_MATCH"

    original_constraints = state.get(
        "original_constraints",
        {
            "structured": {},
            "semantic": []
        }
    )

    final_constraints = {
        "structured": state["plan"].get(
            "structured_constraints", {}
        ),
        "semantic": state["plan"].get(
            "semantic_constraints", []
        )
    }

    relaxations = []

    original_max_price = (
        original_constraints["structured"].get("max_price")
    )

    final_max_price = (
        final_constraints["structured"].get("max_price")
    )

    if (
        original_max_price is not None
        and final_max_price is not None
        and final_max_price > original_max_price
    ):
        relaxations.append(
            f"Maximum price relaxed from "
            f"${original_max_price} to ${final_max_price}"
        )

    original_semantic = original_constraints.get(
        "semantic", []
    )

    final_semantic = final_constraints.get(
        "semantic", []
    )

    for constraint in original_semantic:

        if constraint not in final_semantic:
            relaxations.append(
                f"Semantic preference relaxed: {constraint}"
            )

    response = {
        "status": status,
        "confidence": confidence,
        "result_count": result_count,
        "original_constraints": original_constraints,
        "final_constraints": final_constraints,
        "relaxations": relaxations,
        "products": results
    }

    print("\n=== FINAL RESPONSE ===")
    print(response)

    return {
        "final_response": response
    }

    
# ---------------------------------------
# Build graph
# ---------------------------------------
graph_builder = StateGraph(ProductSearchState)

graph_builder.add_node("planner", planner_node)
graph_builder.add_node("executor", executor_node)
graph_builder.add_node("evaluator", evaluator_node)
graph_builder.add_node("retry", retry_node)
graph_builder.add_node("response", response_node)


# START → Planner
graph_builder.add_edge(START, "planner")

# Planner → Executor
graph_builder.add_edge("planner", "executor")

# Executor → Evaluator
graph_builder.add_edge("executor", "evaluator")


# Evaluator → Response OR Retry
graph_builder.add_conditional_edges(
    "evaluator",
    route_after_evaluation,
    {
        "end": "response",
        "retry": "retry"
    }
)


# Retry → Evaluator
graph_builder.add_edge("retry", "evaluator")


# Response → END
graph_builder.add_edge("response", END)


graph = graph_builder.compile()


# ---------------------------------------
# Run graph
# ---------------------------------------
if __name__ == "__main__":

    query = "ultra luxury Scandinavian living room sofa under $50"

    result = graph.invoke({
        "query": query,
        "retry_count": 0
    })

    print("\n=== PLAN ===")
    print(result["plan"])

    print("\n=== RESULTS ===")
    for product in result["results"]:
        print(product)

    print("\n=== EVALUATION ===")
    print(result["evaluation"])
    print("\n=== FINAL RESPONSE ===")
    print(result["final_response"])

    