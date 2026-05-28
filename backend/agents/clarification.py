import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from observability.langfuse_tracer import (
    create_span,
    end_span,
    LLAMA_3_1_70B_INPUT_COST_PER_TOKEN,
    LLAMA_3_1_70B_OUTPUT_COST_PER_TOKEN
)
from models.state import AgentState

# System Prompt for the Clarification Agent
CLARIFICATION_SYSTEM_PROMPT = """You are the Clarification Agent for PropGenie, an advanced AI property search assistant in India.
Your task is to generate EXACTLY ONE friendly, conversational, and highly contextual clarifying question to ask the user.
Do not ask multiple questions or a multi-part question. Ask only one question at a time.

You must look at:
- Already resolved fields: {resolved_fields}
- Missing fields: {missing_fields}
- Conversation history to maintain natural flow.

You must prioritize asking about the missing fields in this strict order:
1. intent: Ask if they want to Buy or Rent (e.g., "Are you looking to buy or rent a property?")
2. city or location_anchor: Ask for the city or specific locality/landmark (e.g., "Which city or locality are you interested in?")
3. property_type: Ask what type of property they are looking for (e.g., "Are you looking for an apartment, villa, independent house, or plot?")
4. bhk: Ask for the number of bedrooms/BHK (only if intent is Rent, buy searches do not require BHK)
5. budget: Ask for their budget range (e.g., "What is your budget range for this property?")
6. radius_km: Ask how far from the location anchor they'd like to search (e.g., "Within what radius from the landmark should we search?")

Tone and Formatting Guidelines:
- Keep the question concise, welcoming, and conversational.
- Incorporate already-known details to sound human (e.g., if you know they want to Rent in Bangalore, say: "Since you're looking to rent in Bangalore, what type of property are you interested in, like an apartment or villa?").
- Do NOT ask about furnishing level, floor preference, or amenities, as they are out of scope for V1.
- Output ONLY the natural language question to ask the user. Do not wrap the output in JSON, markdown code blocks, or any other formatting. Just output the question text.
"""

def clarification_node(state: AgentState) -> dict[str, Any]:
    """
    Asks clarifying questions if user query is ambiguous, or applies defaults on 3-round breach.
    """
    import time
    print("[Clarification Agent] Started execution")
    start_time = time.time()
    
    trace = state.get("trace")
    span = create_span(trace, "clarification", state.get("pending_fields", []))
    
    # 2. Check 3-round breach logic (if clarification_round is 3 or more)
    round_count = state.get("clarification_round", 0)
    session_id = state.get("session_id") or ""
    logger.info(f"[CLARIFICATION_ROUND] Clarification round {round_count} for session {session_id}")
    
    if round_count >= 3:
        print(f"[Clarification Agent] 3-round breach detected (round: {round_count}). Applying defaults.")
        updates: dict[str, Any] = {
            "proceed_with_defaults": True,
            "pending_fields": [],
            "search_completed": False
        }
        
        # Apply defaults
        # Budget defaults: budget_min = 0, budget_max = None
        if "budget" in state.get("pending_fields", []) or (state.get("budget_min") is None and state.get("budget_max") is None):
            updates["budget_min"] = 0
            updates["budget_max"] = None
            
        # Radius default: 4 km
        if state.get("radius_km") is None:
            updates["radius_km"] = 4
            
        # BHK default: omit from query (so keep it None/null)
        if "bhk" in state.get("pending_fields", []) or state.get("bhk") is None:
            updates["bhk"] = None
            
        # Add response note explaining defaults were applied
        note = "I've proceeded with your search using default options (unlimited budget and a 4 km search radius) since we've reached the limit of clarification questions."
        
        messages = list(state.get("messages", []))
        messages.append({
            "role": "assistant",
            "content": note,
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })
        updates["messages"] = messages
        
        # End Langfuse span
        latency_ms = int((time.time() - start_time) * 1000)
        metrics = {
            "latency": latency_ms,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0
        }
        end_span(span, note, metrics)
        
        return updates

    # 3. Normal clarification question generation
    resolved = {
        k: state.get(k)
        for k in ["intent", "city", "location_anchor", "property_type", "bhk", "budget_min", "budget_max", "radius_km"]
        if state.get(k) is not None
    }
    resolved_str = json.dumps(resolved)
    missing_str = ", ".join(state.get("pending_fields", []))
    
    prompt = CLARIFICATION_SYSTEM_PROMPT.format(
        resolved_fields=resolved_str,
        missing_fields=missing_str
    )
    
    messages_for_llm: list[Any] = [SystemMessage(content=prompt)]
    for msg in state.get("messages", []):
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            messages_for_llm.append(HumanMessage(content=content))
        elif role == "assistant":
            messages_for_llm.append(AIMessage(content=content))
            
    updates = {
        "proceed_with_defaults": False,
        "search_completed": False
    }
    
    try:
        import os
        model_id = os.environ.get("BEDROCK_MODEL_ID", "us.meta.llama3-1-70b-instruct-v1:0")
        region_name = os.environ.get("AWS_REGION", "us-east-1")
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
        
        question = response.content if hasattr(response, "content") else response
        if isinstance(question, list):
            question_text = str(question[0])
        else:
            question_text = str(question).strip()
            
        print(f"[Clarification Agent] LLM question: {question_text}")
        
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
        
    except Exception as e:
        print(f"[Clarification Agent] Error invoking Bedrock LLM: {e}")
        question_text = "Could you please provide more details for your property search, such as city, budget, and BHK?"
        updates["error"] = f"Clarification LLM invocation failed: {str(e)}"
        
    # Append assistant question to messages
    messages = list(state.get("messages", []))
    messages.append({
        "role": "assistant",
        "content": question_text,
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    })
    updates["messages"] = messages
    
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
    
    end_span(span, question_text, metrics)
    
    return updates

