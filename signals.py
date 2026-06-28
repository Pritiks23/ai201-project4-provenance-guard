import requests
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def llm_signal(text: str) -> float:
    """
    Returns a float in [0,1]:
    0 = human-like
    1 = AI-like
    """

    prompt = f"""
You are a text classification system.

Return ONLY a single floating point number between 0 and 1.

Guidelines:
- 0.0 = extremely human-like writing
- 1.0 = extremely AI-like writing
- Use decimals (e.g., 0.12, 0.57, 0.89)
- Do NOT return integers
- Do NOT return explanations
- Output ONLY the number

Text:
{text}
"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
    )

    result = response.json()

    # Debug print (safe for Milestone 3)
    print("RAW GROQ RESPONSE:", result)

    # Error handling
    if "choices" not in result:
        raise Exception(f"Groq API error: {result}")

    score_text = result["choices"][0]["message"]["content"].strip()

    # Convert safely to float
    try:
        score = float(score_text)
    except ValueError:
        raise Exception(f"Invalid score returned by model: {score_text}")

    # Clamp to valid range (safety layer)
    return max(0.0, min(1.0, score))