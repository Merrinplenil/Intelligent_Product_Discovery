import logging
import re
from typing import Optional

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from src.config.settings import GROQ_API_KEY


logger = logging.getLogger(__name__)
# --------------------------------------------------
# Structured output schema
# --------------------------------------------------

class QueryPlan(BaseModel):
    intent: str = Field(
        description="The user's intent"
    )

    structured_constraints: dict = Field(
        default_factory=dict,
        description="Exact constraints such as category, max_price, availability"
    )

    semantic_constraints: list[str] = Field(
        default_factory=list,
        description="Semantic requirements such as compact, modern, Scandinavian"
    )

    execution_plan: str = Field(
        description=(
            "One of: SQL_ONLY, VECTOR_ONLY, "
            "SQL_TO_VECTOR, VECTOR_TO_SQL"
        )
    )

    limit: int = Field(
        default=10,
        description="Maximum number of products requested"
    )


# --------------------------------------------------
# Groq model
# --------------------------------------------------
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=GROQ_API_KEY
)

# --------------------------------------------------
# Prompt
# --------------------------------------------------

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a query planner for an intelligent product discovery system.

Convert the user's product search query into a structured execution plan.

You must determine:

1. Structured constraints
   - category
   - max_price
   - availability

Availability normalization:
- "available" -> "InStock"
- "in stock" -> "InStock"
- "instock" -> "InStock"

Never output boolean true/false for availability.

The intent field must be "product_search" for normal product searches.
Do not put the user's full query into the intent field.


2. Semantic constraints

Semantic constraints can include:
- style
- comfort
- mood
- suitability
- use case
- aesthetic requirements


3. Execution plan

Available execution plans:

SQL_ONLY

Use when the query contains only structured or exact constraints
and no meaningful semantic requirement.

Structured constraints include:
- category
- price
- availability

Example:

"living room furniture under $200"

-> category = "living room"
-> max_price = 200
-> execution_plan = SQL_ONLY


VECTOR_ONLY

Use when the query contains semantic or descriptive requirements
and has no important structured constraints.

Example:

"cosy furniture for a reading corner"

-> semantic_constraints = ["cosy", "reading corner"]
-> execution_plan = VECTOR_ONLY


SQL_TO_VECTOR

Use when BOTH structured constraints and semantic constraints exist,
AND the user explicitly mentions a clear product category.

First use SQL to reduce the candidate set using exact constraints
such as category, price, or availability.

Then use vector search to rank those candidates according to
semantic requirements.

Examples:

"modern sofa under $500"

-> category = "sofa"
-> max_price = 500
-> semantic_constraints = ["modern"]
-> execution_plan = SQL_TO_VECTOR


"compact desks under $250 suitable for a small home office"

-> category = "desk"
-> max_price = 250
-> semantic_constraints = [
    "compact",
    "suitable for a small home office"
]
-> execution_plan = SQL_TO_VECTOR


"comfortable chair available under $300"

-> category = "chair"
-> max_price = 300
-> availability = "InStock"
-> semantic_constraints = ["comfortable"]
-> execution_plan = SQL_TO_VECTOR


VECTOR_TO_SQL

Use when BOTH semantic and structured constraints exist,
BUT the user does NOT explicitly mention a clear product category.

The main intent is descriptive or semantic.

First use vector search to find semantically relevant products.

Then use SQL to apply exact structured constraints such as:
- max_price
- availability

Examples:

"something warm and inviting for a peaceful corner under $300"

-> max_price = 300
-> semantic_constraints = [
    "warm",
    "inviting",
    "peaceful corner"
]
-> execution_plan = VECTOR_TO_SQL


"comfortable furniture for relaxing under $400"

-> max_price = 400
-> semantic_constraints = [
    "comfortable",
    "relaxing"
]
-> execution_plan = VECTOR_TO_SQL


"stylish furniture for a cosy space under $500"

-> max_price = 500
-> semantic_constraints = [
    "stylish",
    "cosy space"
]
-> execution_plan = VECTOR_TO_SQL


DECISION PRIORITY

Follow this exact decision order:

1. If the query contains only structured constraints
   -> SQL_ONLY

2. If the query contains only semantic constraints
   -> VECTOR_ONLY

3. If BOTH structured and semantic constraints exist AND
   a clear product category is explicitly mentioned
   -> SQL_TO_VECTOR

4. If BOTH structured and semantic constraints exist BUT
   no clear product category is explicitly mentioned
   -> VECTOR_TO_SQL


Important rules:

- category is structured when clearly identifiable.
- price is structured.
- availability is structured.
- style is semantic.
- comfort is semantic.
- mood is semantic.
- suitability is semantic.
- use-case is semantic.
- aesthetic requirements are semantic.

- "cheapest", "lowest price", and "most affordable"
  require SQL ranking after semantic retrieval when
  semantic requirements exist.

- Do not invent constraints.
- Understand the complete meaning of the query.
- Return only the information represented by the user query.


For category values, use these mappings when the phrase
is clearly present:

- "office chair" -> "office chair"
- "desk chair" -> "desk chair"
- "chair" -> "chair"

- "office desk" -> "office desk"
- "office desks" -> "office desk"
- "desk" -> "desk"

- "dining table" -> "dining table"
- "table" -> "table"

- "sofa" or "sofas" -> "sofa"

- "bed" or "beds" -> "bed"

- "living room" -> "living room"


IMPORTANT:

- If "living room" appears anywhere in the query, ALWAYS set:

  structured_constraints.category = "living room"

- Do NOT treat "living room" as only a semantic constraint.

- For "Scandinavian-style living room":

  category = "living room"

  semantic_constraints = ["Scandinavian-style"]

- Because "living room" is an explicit category and
  "Scandinavian-style" is semantic:

  execution_plan = SQL_TO_VECTOR


Return a plan matching the required schema.
"""
    ),
    (
        "human",
        "{query}"
    )
])


# --------------------------------------------------
# Structured LLM
# --------------------------------------------------

structured_llm = llm.with_structured_output(QueryPlan)

planner = prompt | structured_llm

def validate_query_plan(query: str, plan: dict) -> dict:
    """
    Validate important constraints extracted from the user query.
    """

    query_lower = query.lower()

    # --------------------------------------------------
    # Validate price constraint
    # --------------------------------------------------

    price_match = re.search(
    r"(?:under|below|less than|up to|max(?:imum)?(?: price)?|within)[ ]*\$?[ ]*([0-9]+(?:\.[0-9]+)?)",
    query_lower
    )

    if price_match:
        expected_price = float(price_match.group(1))

        structured_constraints = plan.setdefault(
            "structured_constraints",
            {}
        )

        actual_price = structured_constraints.get("max_price")

        if actual_price is None:
            logger.warning(
                "Price constraint missing from planner output. "
                "Expected max_price=%s",
                expected_price
            )

            structured_constraints["max_price"] = expected_price

        else:
            try:
                actual_price = float(actual_price)

                if actual_price != expected_price:
                    logger.warning(
                        "Incorrect max_price from planner. "
                        "Expected %s, got %s",
                        expected_price,
                        actual_price
                    )

                    structured_constraints["max_price"] = expected_price

            except (TypeError, ValueError):
                logger.warning(
                    "Invalid max_price returned by planner: %s",
                    actual_price
                )

                structured_constraints["max_price"] = expected_price

    # --------------------------------------------------
    # Validate execution plan
    # --------------------------------------------------

    valid_plans = {
        "SQL_ONLY",
        "VECTOR_ONLY",
        "SQL_TO_VECTOR",
        "VECTOR_TO_SQL",
    }

    if plan.get("execution_plan") not in valid_plans:
        logger.warning(
            "Invalid execution plan returned: %s",
            plan.get("execution_plan")
        )

        plan["execution_plan"] = "VECTOR_ONLY"

    # --------------------------------------------------
    # Validate intent
    # --------------------------------------------------

    if not plan.get("intent"):
        plan["intent"] = "product_search"

    return plan

# --------------------------------------------------
# Public planner function
# --------------------------------------------------
def plan_query(query: str):
    try:
        plan = planner.invoke({
            "query": query
        })

    except Exception as exc:
        logger.error(
            "Query planner failed for '%s': %s",
            query,
            exc
        )

        fallback_plan = {
            "intent": "product_search",
            "structured_constraints": {},
            "semantic_constraints": [query],
            "execution_plan": "VECTOR_ONLY",
            "limit": 10
        }

        return validate_query_plan(
            query,
            fallback_plan
        )

    plan_dict = plan.model_dump()

    plan_dict = validate_query_plan(
        query,
        plan_dict
    )

    logger.info(
        "Query plan generated and validated successfully for: %s",
        query
    )

    return plan_dict


# --------------------------------------------------
# Test
# --------------------------------------------------

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    queries = [

        "available dining tables below $300",

        "cosy reading corner furniture",

        "compact desks under $250 suitable for a small home office",

        "Scandinavian-style living room, show the 5 cheapest",

        "office desks under $200",

        "modern comfortable office chair",

        "available sofas below $500",

        "small Scandinavian desk for a home office"
    ]

    for query in queries:

        print("\n" + "=" * 70)
        print("QUERY:")
        print(query)

        plan = plan_query(query)

        print("\nPLAN:")
        print(plan)