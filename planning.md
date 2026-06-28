# 1. Detection Signals
First need to do->
pip3 install flask flask-limiter requests python-dotenv
<img width="1693" height="929" alt="image" src="https://github.com/user-attachments/assets/a1ea5176-4727-4dd4-8606-51cfafa045fc" />


## Signal 1: LLM-Based Classification (Groq Llama 3.3)

### What it measures
- Semantic + stylistic likelihood of AI vs human authorship  
- Coherence, fluency, repetitiveness, and structural regularity  

### Output
- `llm_score ∈ [0, 1]`  
  - 0 → strongly human-like  
  - 1 → strongly AI-like  

### Blind spots
- May misclassify highly polished human writing as AI-like  
- Can be bypassed by prompt-engineered or heavily paraphrased AI text  

---

## Signal 2: Stylometric Heuristics (Python-based)

### What it measures
- Sentence length variance  
- Vocabulary diversity (type-token ratio)  
- Punctuation density  
- Repetition patterns  

### Output
- `style_score ∈ [0, 1]`  
  - 0 → human-like variability  
  - 1 → AI-like uniformity  

### Blind spots
- Formal human writing may appear “AI-like”  
- Short texts are statistically unstable  
- Cannot capture semantic intent  

---

## Signal Combination Strategy

### Final score
- `final_score = 0.6 * llm_score + 0.4 * style_score`

### Reasoning
- LLM signal captures semantic meaning → higher weight  
- Stylometry provides structural grounding → secondary but stabilizing signal  

## 2. Uncertainty Representation

### What does a score of 0.6 mean?

A score of 0.6 means:

> “Slight leaning toward AI-generated text, but not reliable enough for enforcement.”

We explicitly treat all results as probabilistic, not deterministic.

---

### Confidence Calibration

We map raw score into user-facing categories:

| Range | Label |
|------|------|
| 0.00 – 0.35 | Likely Human |
| 0.35 – 0.65 | Uncertain |
| 0.65 – 1.00 | Likely AI |

---

### Design Principle

We intentionally widen the uncertainty band.

- False positives (flagging human writing as AI) are considered worse than false negatives  
- Therefore, we require stronger evidence before making a “high-confidence AI” claim  

---

## 3. Transparency Label Design

### High-Confidence AI (≥ 0.65)
**AI-Generated Content Likely**

Our system detected strong signals that this content was generated using AI tools.

**Confidence:** {confidence * 100:.0f}%

This result is automated and may be incorrect. You may submit an appeal for review.

---

### High-Confidence Human (≤ 0.35)
**Human-Written Content Likely**

Our system detected strong signals that this content was written by a human author.

**Confidence:** {confidence * 100:.0f}%

This result is probabilistic and not definitive.

---

### Uncertain (0.35 – 0.65)
**Attribution Uncertain**

Our system found mixed signals and cannot reliably classify this content.

**Confidence:** {confidence * 100:.0f}%

No label is enforced. Creators may provide additional context via appeal.

## 4. Appeals Workflow

Who can submit an appeal?  
Any authenticated creator or content author  

Required input:
```json
{
  "content_id": "...",
  "reason": "Explanation of why classification is incorrect",
  "optional_context": "e.g., drafting notes, edit history"
}
```

System behavior on appeal:
Retrieve original classification record  
Update content status:

status = "under_review"  

Append appeal record to audit log  
Store:
content_id  
original classification  
confidence score  
creator reason  
timestamp  

What a reviewer sees:
Original text  
LLM score + stylometric score  
Final confidence score  
System-generated label  
Creator appeal explanation  
Current status: under_review  

No automatic reclassification is required.

---

## 5. Anticipated Edge Cases

## Edge Case 1: Highly Repetitive Poetry

Example:

“I am here I am here I am here…”

Issue:

Stylometric signal detects extreme repetition → high AI score  
But this is valid human poetic style  

Failure mode:

False positive AI classification  

---

## Edge Case 2: Highly Formal Academic Writing

Example:

Dense research abstract with uniform sentence structure  

Issue:

Low variance in sentence length  
High lexical density resembles LLM output  

Failure mode:

Human writing misclassified as AI  

---

## Edge Case 3: Short Text Inputs (< 2 sentences)

Issue:

Stylometric metrics become unreliable  

Failure mode:

Overconfident classification from insufficient data  

---

## Edge Case 4: AI text heavily edited by humans

Issue:

Mixed signal contamination  

Failure mode:

System may classify as “uncertain” despite AI origin (acceptable but expected limitation)

# 6. Architecture

## Submission Flow

Client  
  → POST /submit (raw text)  
    → Rate Limiter (Flask-Limiter)  
      → Signal 1: LLM (Groq)  
        → llm_score (0–1)  
      → Signal 2: Stylometry (Python)  
        → style_score (0–1)  
      → Confidence Scoring Engine  
        → final_score (0–1)  
      → Transparency Label Generator  
        → human-readable label text  
      → Audit Logger (SQLite/JSON)  
        → stores full decision trace  
      → API Response (classification + confidence + label)  

---

## Appeal Flow

Client  
  → POST /appeal (content_id, reason)  
    → Appeals Handler  
      → Validate content_id  
      → Update status = under_review  
      → Append to Audit Log  
      → Store appeal metadata  
      → API Response (confirmation)

## Narrative Summary 

The system processes submitted text through two independent detection signals: an LLM-based semantic classifier and a stylometric heuristic analyzer. Their outputs are combined into a calibrated confidence score, which is mapped to a transparency label shown to the user. Appeals allow creators to challenge decisions, updating system state and preserving full audit traceability.

# 7. AI Tool Plan

## M3 — Submission Endpoint + First Signal

Spec sections provided to AI:

Detection Signals (LLM signal only)  
Architecture diagram  
API surface (POST /submit)  

Task for AI tool:

Flask app skeleton  
/submit endpoint  
Groq LLM classification function  

Verification:

Test /submit with:  
clearly AI-like text  
clearly human-like text  
Confirm LLM score varies meaningfully  

---

## M4 — Second Signal + Confidence Scoring

Spec sections provided:

Detection Signals (both signals)  
Uncertainty Representation  
Architecture diagram  

Task:

Implement stylometric function  
Implement scoring fusion logic  
Return calibrated confidence  

Verification:

Compare outputs across:  
repetitive AI text  
varied human writing  

Ensure non-binary distribution (no clustering at 0.5 or 1.0)  

---

## M5 — Production Layer (Labels + Appeals)

Spec sections provided:

Transparency Label Design  
Appeals Workflow  
Architecture diagram  

Task:

Implement label generator  
Implement /appeal endpoint  
Implement audit log updates  

Verification:

All 3 label states reachable:  
AI  
Human  
Uncertain  

Submit appeal → verify:  
status = under_review  
audit log updated  
