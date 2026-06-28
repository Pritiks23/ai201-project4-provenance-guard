from flask import Flask, request, jsonify
import uuid
from datetime import datetime

from signals import llm_signal, style_signal, combined_score
from audit_log import write_log, get_log

app = Flask(__name__)


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()

    text = data.get("text")
    creator_id = data.get("creator_id")

    if not text or not creator_id:
        return jsonify({
            "error": "missing required fields: text, creator_id"
        }), 400

    content_id = str(uuid.uuid4())

    # -------------------------
    # SIGNALS
    # -------------------------
    llm_score = llm_signal(text)
    style_score = style_signal(text)
    confidence = combined_score(llm_score, style_score)

    # -------------------------
    # LABELS (3-class system)
    # -------------------------
    if confidence <= 0.35:
        label = "Likely Human-Written"
    elif confidence >= 0.65:
        label = "Likely AI-Generated"
    else:
        label = "Uncertain"

    # -------------------------
    # AUDIT LOG
    # -------------------------
    entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": datetime.utcnow().isoformat(),

        "llm_score": llm_score,
        "style_score": style_score,
        "confidence": confidence,

        "attribution": label,
        "status": "classified"
    }

    write_log(entry)

    # -------------------------
    # RESPONSE
    # -------------------------
    return jsonify({
        "content_id": content_id,
        "llm_score": llm_score,
        "style_score": style_score,
        "confidence": confidence,
        "label": label
    })


@app.route("/log", methods=["GET"])
def log():
    return jsonify({"entries": get_log()})


if __name__ == "__main__":
    app.run(debug=True)