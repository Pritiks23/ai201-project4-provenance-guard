import requests
import os
import re
from collections import Counter

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# -------------------------
# SIGNAL 1: LLM (Groq)
# -------------------------
def llm_signal(text: str) -> float:
    """
    Returns float in [0,1]
    0 = human-like, 1 = AI-like
    """

    prompt = f"""
You are a text classification system.

Return ONLY a single floating point number between 0 and 1.

Rules:
- 0.0 = extremely human-like writing
- 1.0 = extremely AI-like writing
- Must be decimal (e.g., 0.12, 0.57)
- No explanation
- Only output number

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
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
    )

    result = response.json()

    print("RAW GROQ RESPONSE:", result)

    if "choices" not in result:
        raise Exception(f"Groq API error: {result}")

    score_text = result["choices"][0]["message"]["content"].strip()

    try:
        return max(0.0, min(1.0, float(score_text)))
    except ValueError:
        raise Exception(f"Invalid LLM score: {score_text}")


# -------------------------
# SIGNAL 2: STYLOMETRY
# -------------------------
def style_signal(text: str) -> float:
    """
    Returns float in [0,1]
    0 = human-like variation
    1 = AI-like uniformity
    """

    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    words = re.findall(r'\w+', text.lower())

    if len(sentences) == 0 or len(words) == 0:
        return 0.5

    # sentence length variance
    lengths = [len(s.split()) for s in sentences]
    avg_len = sum(lengths) / len(lengths)
    variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)

    # vocabulary diversity
    vocab_diversity = len(set(words)) / len(words)

    # repetition
    freq = Counter(words)
    repetition = max(freq.values()) / len(words)

    score = (
        (1 / (1 + variance)) * 0.4 +
        (1 - vocab_diversity) * 0.3 +
        repetition * 0.3
    )

    return max(0.0, min(1.0, score))


# -------------------------
# FUSION SCORE
# -------------------------
def combined_score(llm_score: float, style_score: float) -> float:
    return 0.6 * llm_score + 0.4 * style_score