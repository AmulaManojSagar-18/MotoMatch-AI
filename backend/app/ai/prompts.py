"""Prompt text for turning natural language into structured preferences.

Kept in its own module so the wording can be tuned without touching logic.
The prompt tells the model to ONLY extract preferences -- it must not mention
or choose any motorcycle. Bike selection is the engine's job.
"""

PREFERENCE_SYSTEM_PROMPT = (
    "You are a preference extraction assistant for a motorcycle recommendation "
    "system. Your ONLY job is to read a rider's message and output their "
    "requirements as JSON. You must NOT suggest, name, or choose any motorcycle. "
    "You do not know anything about specific bikes."
)

# The model is asked to return exactly these keys. We also enable Ollama JSON
# mode, so the output should be a single valid JSON object.
PREFERENCE_INSTRUCTIONS = """\
Read the rider's message and extract their preferences.

Output ONLY a JSON object with these EXACT keys (no extra keys):

- "budget": integer in Indian Rupees, or null if not mentioned.
    Convert phrases like "2 lakh" -> 200000, "3 lakhs" -> 300000.
- "daily_commute_km": integer kilometers per day, or null if not mentioned.
- "city_usage": ALWAYS one of "low", "medium", or "high". Default to "medium".
- "touring_usage": ALWAYS one of "low", "medium", or "high" (long/highway/weekend trips). Default to "medium".
- "adventure_usage": ALWAYS one of "low", "medium", or "high" (off-road / rough terrain). Default to "low".
- "comfort_priority": ALWAYS one of "low", "medium", or "high". Default to "medium".
- "mileage_priority": ALWAYS one of "low", "medium", or "high" (fuel efficiency). Default to "medium".
- "performance_priority": ALWAYS one of "low", "medium", or "high" (power/speed/sporty). Default to "medium".

Rules:
- If the user mentions "highway" or "long trips", set touring_usage to "high".
- If the user says "city", "commuter", or "daily commute", set city_usage to "high".
- If the user says "adventure", "off-road", or "rough", set adventure_usage to "high".
- If budget or daily_commute_km is not mentioned, use null.
- If a priority is not mentioned, default to "medium" — NEVER use null.
- Do NOT add extra keys. Do not include any text outside the JSON object.
- Do NOT mention or recommend any motorcycle.

Examples:

Message: "I travel 40 km daily in the city, budget 2 lakh, mileage is important."
Output:
{{
  "budget": 200000,
  "daily_commute_km": 40,
  "city_usage": "high",
  "touring_usage": "medium",
  "adventure_usage": "low",
  "comfort_priority": "medium",
  "mileage_priority": "high",
  "performance_priority": "low"
}}

Message: "Need a comfortable bike for highway riding, budget 3 lakhs."
Output:
{{
  "budget": 300000,
  "daily_commute_km": null,
  "city_usage": "low",
  "touring_usage": "high",
  "adventure_usage": "low",
  "comfort_priority": "high",
  "mileage_priority": "medium",
  "performance_priority": "medium"
}}

Message: "Budget 1 lakh only, city commuter."
Output:
{{
  "budget": 100000,
  "daily_commute_km": null,
  "city_usage": "high",
  "touring_usage": "low",
  "adventure_usage": "low",
  "comfort_priority": "medium",
  "mileage_priority": "high",
  "performance_priority": "low"
}}

Rider message:
\"\"\"{message}\"\"\"
"""


def build_preference_prompt(message: str) -> str:
    return PREFERENCE_INSTRUCTIONS.format(message=message)
