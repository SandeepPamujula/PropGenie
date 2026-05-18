import json
from datetime import datetime, timezone
from typing import Any, Optional
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langfuse.decorators import observe, langfuse_context
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

@observe(name="clarification")  # type: ignore[misc]
def clarification_node(state: AgentState) -> dict[str, Any]:
    """
    Asks clarifying questions if user query is ambiguous, or applies defaults on 3-round breach.
    """
    print("[Clarification Agent] Started execution")
    
    # 1. Update trace metadata in Langfuse
    langfuse_context.update_current_trace(
        session_id=state.get("session_id"),
        user_id=state.get("ip"),
        tags=["propgenie", "clarification"]
    )
    
    # 2. Check 3-round breach logic (if clarification_round is 3 or more)
    round_count = state.get("clarification_round", 0)
    if round_count >= 3:
        print(f"[Clarification Agent] 3-round breach detected (round: {round_count}). Applying defaults.")
        updates: dict[str, Any] = {
            "proceed_with_defaults": True,
            "pending_fields": []
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
        "proceed_with_defaults": False
    }
    
    try:
        # Initialize AWS Bedrock LLM Client
        llm = ChatBedrock(  # type: ignore[call-arg]
            model_id="us.meta.llama3-1-70b-instruct-v1:0",
            region_name="us-east-1",
            model_kwargs={"temperature": 0.0}
        )
        
        # Invoke model
        response = llm.invoke(messages_for_llm)
        question = response.content if hasattr(response, "content") else response
        if isinstance(question, list):
            question_text = str(question[0])
        else:
            question_text = str(question).strip()
            
        print(f"[Clarification Agent] LLM question: {question_text}")
        
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
    
    return updates

