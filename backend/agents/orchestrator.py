import json
import logging
import re
from typing import Any

from langchain_aws import ChatBedrock

logger = logging.getLogger(__name__)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from models.state import AgentState
from observability.langfuse_tracer import (
    LLAMA_3_1_70B_INPUT_COST_PER_TOKEN,
    LLAMA_3_1_70B_OUTPUT_COST_PER_TOKEN,
    create_span,
    end_span,
)

# System Prompt for the Orchestrator Agent
SYSTEM_PROMPT = """You are the central Orchestrator Agent for PropGenie, an advanced property search assistant in India.
Your objective is to understand natural language user queries, classify the user's search intent, and extract structured parameters for property search.

You must extract and classify the following fields and return a strictly valid JSON object:
1. "intent": "Buy" | "Rent" | "Ambiguous"
   - "Buy": User wants to purchase, buy, acquire, or mentions terms like "for sale", "purchase", "buying", "plot", "land".
   - "Rent": User wants to rent, lease, hire, or mentions terms like "for rent", "rental", "letting", "renting".
   - "Ambiguous": The intent is unclear or not specified (e.g., "looking for a flat in bangalore", "need a 2BHK").

2. "city": The Indian city name (e.g. Bangalore, Mumbai, Delhi, Chennai, Hyderabad, Pune, Kolkata, Ahmedabad, Jaipur, Kochi).
   - If the city is NOT explicitly mentioned but a landmark, locality, neighborhood, school, or metro station belonging to one of the major Indian cities is mentioned, you MUST infer the city:
     * Bangalore: Indiranagar, HSR Layout, Manyata Tech Park, Whitefield, Koramangala, Marathahalli, Bellandur, Electronic City, NPS Indiranagar, NPS School
     * Mumbai: Bandra, Andheri, Juhu, Worli, Powai, Colaba, Thane, Borivali
     * Delhi: Connaught Place, Dwarka, Karol Bagh, Vasant Kunj, Noida, Gurgaon, Sector 62, DLF Phase 5
     * Chennai: Adyar, Velachery, T. Nagar, Anna Nagar, OMR, ECR, Mylapore
     * Hyderabad: Gachibowli, Madhapur, Jubilee Hills, Banjara Hills, Hitech City, Kondapur
     * Pune: Kothrud, Koregaon Park, Viman Nagar, Hinjewadi, Wakad, Baner
     * Kolkata: Salt Lake, Newtown, Gariahat, Ballygunge, Howrah, Park Street
     * Ahmedabad: Satellite, Vastrapur, SG Highway, Prahlad Nagar, Bopal
     * Jaipur: Vaishali Nagar, Malviya Nagar, Mansarovar, C-Scheme
     * Kochi: Kakkanad, Edappally, Marine Drive, Vyttila
   - Normalize inferred or explicit city to a standard name (e.g., "Bengaluru" -> "Bangalore", "Delhi-NCR" -> "Delhi"). If no city is found or inferred, return null.

3. "location_anchor": The specific locality, landmark, building, society, school, or metro station mentioned (e.g. "NPS Indiranagar", "Manyata Tech Park", "HSR Layout"). Do NOT include the city name here. If none is mentioned, return null.

4. "property_type": The type of property (e.g. "apartment", "house", "villa", "independent house", "plot").
   - If user says "flat", "apartment", or "condo", return "apartment".
   - If "house", "independent house", or "villa" is mentioned, return "house" or "villa" accordingly.
   - If "plot" or "land" is mentioned, return "plot".
   - If not specified, return null.

5. "bhk": Number of bedrooms as an integer (e.g. 1, 2, 3, 4, etc.). If "1BHK" return 1, "2 BHK" return 2, "3bhk" return 3. If unspecified, return null.

6. "budget_min": Minimum budget normalized to a raw integer value in Indian Rupees (INR).
7. "budget_max": Maximum budget normalized to a raw integer value in Indian Rupees (INR).
   - VERY IMPORTANT currency normalization rules:
     * "25k" or "25 thousand" or "25000" -> 25000
     * "25k to 35k" -> budget_min = 25000, budget_max = 35000
     * "1Cr" or "1 crore" or "100 lakhs" -> 10000000 (10 million)
     * "1.5Cr" or "1.5 crore" -> 15000000
     * "1.5Cr to 2Cr" -> budget_min = 15000000, budget_max = 20000000
     * "under 35k" -> budget_min = null, budget_max = 35000
     * "above 1Cr" -> budget_min = 10000000, budget_max = null
     * If no budget is specified, return null for both budget_min and budget_max.

8. "radius_km": The search radius in kilometers as an integer if explicitly requested (e.g. "within 5 km" -> 5). If unspecified, return null.

You MUST analyze the entire conversation history. Return ONLY a JSON object matching this schema. Do not include any explanations, markdown code blocks, or extra text outside the JSON.

Example JSON output:
{
  "intent": "Rent",
  "city": "Bangalore",
  "location_anchor": "NPS Indiranagar",
  "property_type": "house",
  "bhk": 3,
  "budget_min": 25000,
  "budget_max": 35000,
  "radius_km": null
}
"""

def extract_json(text: str) -> dict[str, Any]:
    """
    Robustly extracts and parses JSON content from the LLM's raw text response.
    """
    text_clean = text.strip()

    # Try finding markdown JSON block
    match = re.search(r"```json\s*(.*?)\s*```", text_clean, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            res = json.loads(match.group(1).strip())
            if isinstance(res, dict):
                return res
        except json.JSONDecodeError:
            pass

    # Try finding any triple backticks block
    match = re.search(r"```\s*(.*?)\s*```", text_clean, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            res = json.loads(match.group(1).strip())
            if isinstance(res, dict):
                return res
        except json.JSONDecodeError:
            pass

    # Try parsing the whole text
    try:
        res = json.loads(text_clean)
        if isinstance(res, dict):
            return res
    except json.JSONDecodeError:
        pass

    # Find first '{' and last '}' and parse that segment
    start = text_clean.find("{")
    end = text_clean.rfind("}")
    if start != -1 and end != -1:
        try:
            res = json.loads(text_clean[start:end + 1])
            if isinstance(res, dict):
                return res
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse valid JSON from LLM response: {text}")

def orchestrator_node(state: AgentState) -> dict[str, Any]:
    """
    Classifies search intent and extracts entities from natural language user input using Amazon Bedrock.
    """
    import time
    print("[Orchestrator Agent] Started execution")
    start_time = time.time()

    # Get user message
    user_message = ""
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break

    trace = state.get("trace")
    span = create_span(trace, "orchestrator", user_message)

    # 2. Increment clarification round tracking
    current_round = state.get("clarification_round", 0) + 1
    updates: dict[str, Any] = {
        "clarification_round": current_round
    }

    # 3. Construct message list for Bedrock
    messages_for_llm: list[Any] = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in state.get("messages", []):
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            messages_for_llm.append(HumanMessage(content=content))
        elif role == "assistant":
            messages_for_llm.append(AIMessage(content=content))

    try:
        import os
        model_id = os.environ.get("BEDROCK_MODEL_ID", "us.meta.llama3-1-70b-instruct-v1:0")
        region_name = os.environ.get("BEDROCK_REGION", "us-east-1")
        llm = ChatBedrock(  # type: ignore[call-arg]
            model_id=model_id,
            region_name=region_name,
            model_kwargs={"temperature": 0.0}
        )

        # Invoke model
        llm_start = time.time()
        response = llm.invoke(messages_for_llm)
        llm_latency = int((time.time() - llm_start) * 1000)
        logger.info(f"[BEDROCK_CALL] Model {model_id} invoked. Latency: {llm_latency}ms")

        content = response.content if hasattr(response, "content") else response
        if isinstance(content, list):
            response_text = json.dumps(content)
        else:
            response_text = str(content)
        print(f"[Orchestrator Agent] LLM Raw Response: {response_text}")

        # Accumulate usage statistics
        updates["llm_calls"] = state.get("llm_calls", 0) + 1
        if hasattr(response, "response_metadata") and "usage" in response.response_metadata:
            usage = response.response_metadata["usage"]
            updates["total_input_tokens"] = state.get("total_input_tokens", 0) + usage.get("input_tokens", 0)
            updates["total_output_tokens"] = state.get("total_output_tokens", 0) + usage.get("output_tokens", 0)
        elif hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            updates["total_input_tokens"] = state.get("total_input_tokens", 0) + usage.get("input_tokens", 0)
            updates["total_output_tokens"] = state.get("total_output_tokens", 0) + usage.get("output_tokens", 0)

        # Extract extracted parameters from LLM response
        extracted = extract_json(response_text)

        # Update state fields with non-null values extracted
        for key in ["intent", "city", "location_anchor", "property_type", "bhk", "budget_min", "budget_max", "radius_km"]:
            val = extracted.get(key)
            if val is not None:
                updates[key] = val
            else:
                updates[key] = state.get(key)

    except Exception as e:
        print(f"[Orchestrator Agent] Error invoking Bedrock LLM: {e}")
        # In case of LLM error, keep existing values
        for key in ["intent", "city", "location_anchor", "property_type", "bhk", "budget_min", "budget_max", "radius_km"]:
            updates[key] = state.get(key)
        updates["error"] = f"Orchestrator LLM invocation failed: {str(e)}"

    # 4. Perform completeness check against required fields matrix (buy vs rent)
    pending_fields = []

    # Resolve intent value for check
    intent = updates.get("intent") or state.get("intent")

    if intent is None or str(intent).strip() == "" or str(intent).lower() == "ambiguous":
        # Intent is ambiguous or not specified
        pending_fields.append("intent")

        # If budget is missing
        if updates.get("budget_min") is None and updates.get("budget_max") is None:
            pending_fields.append("budget")

        # If BHK is missing (since it could be rental)
        if updates.get("bhk") is None:
            pending_fields.append("bhk")

        # If other fields are missing
        if updates.get("city") is None:
            pending_fields.append("city")
        if updates.get("property_type") is None:
            pending_fields.append("property_type")

    elif str(intent).lower() == "rent":
        # Rent required fields: intent, city, location_anchor, property_type, bhk, budget range
        if updates.get("city") is None:
            pending_fields.append("city")
        if updates.get("location_anchor") is None:
            pending_fields.append("location_anchor")
        if updates.get("property_type") is None:
            pending_fields.append("property_type")
        if updates.get("bhk") is None:
            pending_fields.append("bhk")
        if updates.get("budget_min") is None and updates.get("budget_max") is None:
            pending_fields.append("budget")

    elif str(intent).lower() == "buy":
        # Buy required fields: intent, city, location_anchor, property_type, budget range (BHK is NOT required)
        if updates.get("city") is None:
            pending_fields.append("city")
        if updates.get("location_anchor") is None:
            pending_fields.append("location_anchor")
        if updates.get("property_type") is None:
            pending_fields.append("property_type")
        if updates.get("budget_min") is None and updates.get("budget_max") is None:
            pending_fields.append("budget")

    updates["pending_fields"] = pending_fields
    print(f"[Orchestrator Agent] Completed. Pending fields: {pending_fields}")

    # End Langfuse span
    latency_ms = int((time.time() - start_time) * 1000)
    init_input_tokens = state.get("total_input_tokens", 0)
    init_output_tokens = state.get("total_output_tokens", 0)
    added_input_tokens = updates.get("total_input_tokens", init_input_tokens) - init_input_tokens
    added_output_tokens = updates.get("total_output_tokens", init_output_tokens) - init_output_tokens

    metrics = {
        "latency": latency_ms,
        "input_tokens": added_input_tokens,
        "output_tokens": added_output_tokens,
        "total_tokens": added_input_tokens + added_output_tokens,
        "cost": added_input_tokens * LLAMA_3_1_70B_INPUT_COST_PER_TOKEN + added_output_tokens * LLAMA_3_1_70B_OUTPUT_COST_PER_TOKEN
    }

    output_data = {
        "intent": updates.get("intent"),
        "city": updates.get("city"),
        "location_anchor": updates.get("location_anchor"),
        "property_type": updates.get("property_type"),
        "bhk": updates.get("bhk"),
        "budget_min": updates.get("budget_min"),
        "budget_max": updates.get("budget_max"),
        "radius_km": updates.get("radius_km"),
        "pending_fields": pending_fields
    }

    end_span(span, output_data, metrics)

    return updates
