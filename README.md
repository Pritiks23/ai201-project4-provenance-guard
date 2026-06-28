# AI Provenance Guard — README

## Overview
This project implements a lightweight provenance detection system that classifies submitted text as likely AI-generated or human-written. It combines two independent detection signals (LLM-based semantic classification and stylometric analysis), fuses them into a single confidence score, and maps that score into a transparency label. The system also supports audit logging, rate limiting, and an appeals workflow for post-classification review.

---

## Architecture Summary

The system is structured as a Flask API with three core modules:

- `app.py` → API layer (`/submit`, `/log`, `/appeal`)
- `signals.py` → detection logic (LLM + stylometry + fusion)
- `audit_log.py` → persistent JSON-based audit trail

Each submission flows through:

1. Input validation (`text`, `creator_id`)
2. Signal extraction:
   - `llm_signal(text)` → semantic AI-likelihood score
   - `style_signal(text)` → stylistic uniformity score
3. Fusion:
   - `confidence = 0.6 * llm_score + 0.4 * style_score`
4. Label assignment (3-tier system)
5. Audit logging

---

## Detection Signals (Design Rationale)

### 1. LLM-Based Signal (`llm_signal`)
This signal uses a Groq-hosted LLM to estimate how "AI-like" a text is based on semantic structure, fluency, and phrasing regularity.

**Why this signal:**
- LLMs capture higher-level linguistic patterns (coherence, repetition, formality)
- These are difficult to model with handcrafted heuristics
- Provides semantic sensitivity that stylometry cannot capture

**Weakness:**
- Can misclassify highly formal human writing as AI-generated
- Sensitive to prompt phrasing and model bias

---

### 2. Stylometric Signal (`style_signal`)
This signal measures statistical properties of writing:
- sentence length variance
- lexical diversity
- repetition frequency

**Why this signal:**
- Captures low-level writing behavior independent of meaning
- Useful counterbalance to LLM semantic bias
- Cheap and deterministic

**Weakness:**
- Fails on short texts
- Cannot detect semantic AI patterns alone

---

## Confidence Scoring Approach

The final score is a weighted fusion:

```python
confidence = 0.6 * llm_score + 0.4 * style_score

Why this weighting:
- LLM signal is more expressive but less stable → higher weight  
- Stylometry stabilizes edge cases and reduces variance  

Future deployment improvement:
In a production system, this would be replaced with:
- calibrated logistic regression or isotonic regression  
- per-domain tuning (academic vs informal text)  
- confidence uncertainty estimation (not just point scoring)  

# Confidence Scoring — Empirical Results

## High-confidence human-written example
Text: "ok so i finally tried that new ramen place downtown..."
- llm_score: 0.17  
- style_score: 0.0632  
- confidence: 0.1273  
- label: Likely Human-Written  

## Lower-confidence borderline example
Text: "The relationship between monetary policy and asset price inflation..."
- llm_score: 0.42  
- style_score: 0.0756  
- confidence: 0.2822  
- label: Likely Human-Written  

## AI-like / uncertain example
Text: "Artificial intelligence represents a transformative paradigm shift..."
- llm_score: 0.67  
- style_score: 0.0689  
- confidence: 0.4296  
- label: Uncertain  

---

These results demonstrate that the scoring function produces meaningful variation across writing styles rather than collapsing to a single constant value.

# Transparency Label System (3 Variants)

The system maps confidence into three interpretable categories:

## 1. High-confidence human
Condition: confidence <= 0.35  
Label:  
Likely Human-Written  

## 2. Uncertain range
Condition: 0.35 < confidence < 0.65  
Label:  
Uncertain  

## 3. High-confidence AI
Condition: confidence >= 0.65  
Label:  
Likely AI-Generated  

---

# Rate Limiting Design

Rate limiting is implemented using Flask-Limiter:

```python
@limiter.limit("10 per minute;100 per day")

# Appeals Workflow

The system supports post-classification appeals via:

Endpoint:
POST /appeal

Intended behavior:
Accept content_id + creator_reasoning  
Mark submission as "under_review"  
Append appeal data to audit log entry  

Current limitation observed:
Appeal requests fail when content_id is not found or request format mismatches stored entries. This indicates a dependency on strict ID consistency between /submit and /appeal.

# Audit Log Design

The audit log (`audit_log.json`) records structured events:

## Each entry includes:
- content_id  
- creator_id  
- timestamp  
- llm_score  
- style_score  
- confidence  
- attribution label  
- status (classified / under_review)  

## Why structured logging matters:
- Enables reproducibility of classification decisions  
- Supports appeals workflow  
- Enables downstream analytics or bias auditing  

---

# Known Limitations

## 1. Misclassification of formal human writing
Highly structured academic or policy-style writing is often flagged as AI-like due to:
- low lexical diversity  
- uniform sentence structure  
- high semantic coherence  

This directly stems from the stylometric signal design, which equates uniformity with AI-likeness.

---

## 2. Short text instability
Very short inputs produce unstable style scores because variance and lexical diversity are not statistically meaningful at low token counts.

---

# Spec Reflection

## How the spec helped:
The requirement for two independent signals forced a modular architecture where semantic and statistical signals are explicitly separated. This made it easier to debug scoring behavior by isolating failure modes.

## Where implementation diverged:
The spec implied a more formal appeal lifecycle (including reclassification), but the implementation only logs appeals and marks status as "under_review" without re-scoring. This was simplified to keep the system deterministic and within scope.

# AI Usage Disclosure API error debugging (Flask + curl)

Prompted AI: diagnosis of `dquote>` shell error in curl requests and JSON escaping issues  

AI output: recommended switching to double-quoted JSON payload with escaped internal quotes  

What was changed: manually rewrote curl commands using proper JSON escaping and verified against local server responses


Rate Limiting
# Rate Limiting Test

```bash
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text":"test","creator_id":"ratelimit"}'
done

200
200
200
200
200
200
200
200
200
200
429
429