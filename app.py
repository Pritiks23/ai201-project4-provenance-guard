# from flask import Flask, request, jsonify
# import uuid
# from datetime import datetime

# from signals import llm_signal
# from audit_log import write_log, get_log

# app = Flask(__name__)


# @app.route("/submit", methods=["POST"])
# def submit():
#     data = request.get_json()

#     # Validate input
#     text = data.get("text")
#     creator_id = data.get("creator_id")

#     if not text or not creator_id:
#         return jsonify({
#             "error": "missing required fields: text, creator_id"
#         }), 400

#     # Generate content ID
#     content_id = str(uuid.uuid4())

#     # Signal 1 (LLM)
#     llm_score = llm_signal(text)

#     # Placeholder for Milestone 4
#     confidence = llm_score

#     # Label mapping
#     if confidence <= 0.35:
#         label = "Human"
#     elif confidence >= 0.65:
#         label = "AI"
#     else:
#         label = "Uncertain"

#     # Audit log entry
#     entry = {
#         "content_id": content_id,
#         "creator_id": creator_id,
#         "timestamp": datetime.utcnow().isoformat(),
#         "llm_score": llm_score,
#         "confidence": confidence,
#         "attribution": label,
#         "status": "classified"
#     }

#     write_log(entry)

#     # Response
#     return jsonify({
#         "content_id": content_id,
#         "llm_score": llm_score,
#         "confidence": confidence,
#         "label": label
#     })


# @app.route("/log", methods=["GET"])
# def log():
#     return jsonify({"entries": get_log()})


# if __name__ == "__main__":
#     app.run(debug=True)
# signals.py
import os
import requests

def llm_signal(text: str) -> float:
    """
    Returns a score in [0,1]
    0 = human-like
    1 = AI-like
    """

    # -----------------------------
    # SAFE FALLBACK (works without API)
    # -----------------------------
    if not os.getenv("GROQ_API_KEY"):
        # simple heuristic baseline so system runs
        return min(1.0, len(text.split()) / 200)

    # -----------------------------
    # GROQ LLM VERSION (optional upgrade)
    # -----------------------------
    api_key = os.getenv("GROQ_API_KEY")

    prompt = f"""
    Analyze the text and return ONLY a number between 0 and 1.
    0 = human-like writing
    1 = AI-like writing

    Text:
    {text}
    """

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0
        }
    )

    try:
        content = response.json()["choices"][0]["message"]["content"]
        return float(content.strip())
    except Exception:
        # fallback if parsing fails
        return 0.5