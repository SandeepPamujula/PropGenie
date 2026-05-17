from typing import Any


# AWS Lambda entry point stub
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Handles API Gateway requests and invokes the agent graph.
    """
    return {"statusCode": 200, "body": "PropGenie Backend Stub"}
