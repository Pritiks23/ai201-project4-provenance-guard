# from flask import Flask, request, jsonify
# import uuid
# from datetime import datetime

# from signals import llm_signal, style_signal, combined_score
# from audit_log import write_log, get_log

# app = Flask(__name__)


# @app.route("/submit", methods=["POST"])
# def submit():
#     data = request.get_json()

#     text = data.get("text")
#     creator_id = data.get("creator_id")

#     if not text or not creator_id:
#         return jsonify({
#             "error": "missing required fields: text, creator_id"
#         }), 400

#     content_id = str(uuid.uuid4())

#     # -------------------------
#     # SIGNALS
#     # -------------------------
#     llm_score = llm_signal(text)
#     style_score = style_signal(text)
#     confidence = combined_score(llm_score, style_score)

#     # -------------------------
#     # LABELS (3-class system)
#     # -------------------------
#     if confidence <= 0.35:
#         label = "Likely Human-Written"
#     elif confidence >= 0.65:
#         label = "Likely AI-Generated"
#     else:
#         label = "Uncertain"

#     # -------------------------
#     # AUDIT LOG
#     # -------------------------
#     entry = {
#         "content_id": content_id,
#         "creator_id": creator_id,
#         "timestamp": datetime.utcnow().isoformat(),

#         "llm_score": llm_score,
#         "style_score": style_score,
#         "confidence": confidence,

#         "attribution": label,
#         "status": "classified"
#     }

#     write_log(entry)

#     # -------------------------
#     # RESPONSE
#     # -------------------------
#     return jsonify({
#         "content_id": content_id,
#         "llm_score": llm_score,
#         "style_score": style_score,
#         "confidence": confidence,
#         "label": label
#     })


# @app.route("/log", methods=["GET"])
# def log():
#     return jsonify({"entries": get_log()})


# if __name__ == "__main__":
#     app.run(debug=True)
from flask import Flask, request, jsonify
import uuid
from datetime import datetime

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from signals import llm_signal, style_signal, combined_score
from audit_log import write_log, get_log

app = Flask(__name__)

# -------------------------
# RATE LIMITER (Milestone 5)
# -------------------------
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

# -------------------------
# LABEL FUNCTION (TRANSPARENCY LAYER)
# -------------------------
def get_label(confidence: float) -> str:
    if confidence <= 0.35:
        return "Likely Human-Written"
    elif confidence >= 0.65:
        return "Likely AI-Generated"
    else:
        return "Uncertain"


# -------------------------
# SUBMISSION ENDPOINT
# -------------------------
@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
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

    label = get_label(confidence)

    # -------------------------
    # AUDIT LOG ENTRY
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

    return jsonify({
        "content_id": content_id,
        "llm_score": llm_score,
        "style_score": style_score,
        "confidence": confidence,
        "label": label
    })


# -------------------------
# APPEAL ENDPOINT (NEW)
# -------------------------
@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json()

    content_id = data.get("content_id")
    reasoning = data.get("creator_reasoning")

    if not content_id or not reasoning:
        return jsonify({
            "error": "missing required fields: content_id, creator_reasoning"
        }), 400

    # Update log entry
    logs = get_log()

    updated = False
    for entry in logs:
        if entry["content_id"] == content_id:
            entry["status"] = "under_review"
            entry["appeal_reasoning"] = reasoning
            entry["appeal_timestamp"] = datetime.utcnow().isoformat()
            updated = True

    if not updated:
        return jsonify({"error": "content_id not found"}), 404

    # rewrite log
    from audit_log import write_log
    import json

    with open("audit_log.json", "w") as f:
        json.dump(logs, f, indent=2)

    return jsonify({
        "message": "appeal received",
        "content_id": content_id,
        "status": "under_review"
    })


# -------------------------
# LOG ENDPOINT
# -------------------------
@app.route("/log", methods=["GET"])
def log():
    return jsonify({"entries": get_log()})


if __name__ == "__main__":
    app.run(debug=True)