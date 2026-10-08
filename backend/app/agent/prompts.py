"""Prompts and templated replies for the conversational agent.

Two LLM-facing prompts:
- ANALYZE: understand one user turn -> TurnAnalysis (structured JSON).
- EXPLAIN / KNOWLEDGE: turn facts into natural language (grounded).

Follow-up questions and safety replies are templated (deterministic) so the
conversation stays reliable and testable; the LLM handles understanding and
explanation.
"""

from __future__ import annotations

from app.data.catalog import BIKE_CATALOG

# Comma-separated catalog so the model knows exactly what we offer.
CATALOG_NAMES = ", ".join(f"{b['brand']} {b['model']}" for b in BIKE_CATALOG)

ANALYZE_SYSTEM_PROMPT = (
    "You are the understanding module of MotoMatch, a motorcycle recommender. "
    "You read ONE user message (with prior conversation context) and output a "
    "structured JSON analysis. You do NOT choose a motorcycle and you do NOT "
    "answer questions here -- you only classify intent and extract preferences. "
    f"MotoMatch only deals with these 10 motorcycles: {CATALOG_NAMES}."
)

ANALYZE_INSTRUCTIONS = """\
Analyze the LATEST user message using the conversation context.

Return ONLY a JSON object with these keys:

- "intent": one of
    "recommend"  -> the user wants a bike / is giving requirements,
    "knowledge"  -> the user asks a factual question about a specific catalog bike,
    "chitchat"   -> greeting, thanks, or unclear.
- "out_of_catalog_request": true ONLY if the user asks for a brand/model that is
    NOT one of the 10 MotoMatch bikes (e.g. Ducati, KTM, Harley). Otherwise false.
- "requested_bike_name": the out-of-catalog bike name if any, else null.
- "knowledge_query": if intent is "knowledge", a short query describing what
    they want to know (e.g. "engine capacity of Royal Enfield Hunter 350"),
    else null.
- "preferences": an object with ONLY the values the user mentioned this turn;
    use null for anything not mentioned:
    - "budget": integer INR (e.g. "2 lakh" -> 200000, "3 lakhs" -> 300000) or null
    - "daily_commute_km": integer or null
    - "city_usage": "low" | "medium" | "high" | null
    - "touring_usage": "low" | "medium" | "high" | null   (highway / long / weekend trips)
    - "adventure_usage": "low" | "medium" | "high" | null  (off-road / rough terrain)
    - "comfort_priority": "low" | "medium" | "high" | null
    - "mileage_priority": "low" | "medium" | "high" | null
    - "performance_priority": "low" | "medium" | "high" | null

Rules:
- Only fill a preference when the user actually indicated it; otherwise null.
- "highway" / "long trips" / "weekend trips" -> touring_usage.
- Do NOT recommend or name any specific MotoMatch bike here.
- Output only the JSON object, nothing else.

Conversation so far:
{history}

Known preferences so far: {known}

Latest user message:
\"\"\"{message}\"\"\"
"""

EXPLAIN_SYSTEM_PROMPT = (
    "You are MotoMatch's explanation module. You explain, in a friendly and "
    "concise way, why a motorcycle was recommended. You may ONLY use the facts "
    "provided to you. Never invent specifications, prices, or features. Do not "
    "mention any motorcycle other than the recommended one."
)

EXPLAIN_INSTRUCTIONS = """\
Write 2-3 sentences explaining why we recommend this motorcycle to the rider.
Use ONLY the facts below. Do not invent anything.

Recommended motorcycle: {bike_name}
Suitability score (0-100): {score}
Reasons it matched (from our engine): {matching_factors}
Key facts: {facts}
Rider's stated preferences: {preferences}

Explanation:"""

KNOWLEDGE_SYSTEM_PROMPT = (
    "You are MotoMatch's bike knowledge assistant. Answer the user's question "
    "using ONLY the provided reference facts about MotoMatch catalog bikes. If "
    "the facts do not contain the answer, say you don't have that information. "
    "Never invent specifications."
)

KNOWLEDGE_INSTRUCTIONS = """\
Answer the user's question using ONLY these reference facts:

{context}

Question: {question}

Answer concisely in 1-3 sentences:"""


# --- Templated (deterministic) replies -------------------------------------

BUDGET_QUESTION = "What is your approximate budget for the motorcycle?"

USAGE_QUESTION = (
    "What type of riding will you mostly do - daily city commuting, "
    "highway or weekend touring, or off-road adventure?"
)

GREETING_REPLY = (
    "Hi! I'm MotoMatch. Tell me what you're looking for in a motorcycle - "
    "your budget and the kind of riding you do - and I'll recommend the best "
    "match from our lineup."
)

CLARIFY_REPLY = (
    "Sorry, I didn't quite catch that. Could you tell me a bit about your "
    "budget and how you plan to use the bike?"
)


def out_of_catalog_reply(requested_bike_name: str | None) -> str:
    bike = requested_bike_name or "that motorcycle"
    return (
        f"MotoMatch currently recommends only from its fixed catalog of 10 "
        f"motorcycles, so I can't recommend {bike}. If you tell me your budget "
        f"and riding needs, I'll find the best match from our lineup."
    )


def build_analyze_prompt(message: str, history: str, known: str) -> str:
    return ANALYZE_INSTRUCTIONS.format(message=message, history=history, known=known)


def build_explain_prompt(
    bike_name: str,
    score: float,
    matching_factors: list[str],
    facts: str,
    preferences: str,
) -> str:
    factors = ", ".join(matching_factors) if matching_factors else "general suitability"
    return EXPLAIN_INSTRUCTIONS.format(
        bike_name=bike_name,
        score=score,
        matching_factors=factors,
        facts=facts,
        preferences=preferences,
    )


def build_knowledge_prompt(question: str, context: str) -> str:
    return KNOWLEDGE_INSTRUCTIONS.format(question=question, context=context)
