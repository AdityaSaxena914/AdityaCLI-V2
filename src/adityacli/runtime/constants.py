from __future__ import annotations

# ============================================================================
# Context Budget
# ============================================================================

SYSTEM_PROMPT_RESERVE = 2_000

CONVERSATION_HISTORY_RESERVE = 8_000

MODEL_RESPONSE_RESERVE = 12_000

MIN_CONTEXT_BUDGET = 4_096

CHARACTERS_PER_TOKEN = 4


# ============================================================================
# Intent Router
# ============================================================================

INTENT_CONFIDENCE = 1.00

SEMANTIC_CONFIDENCE = 0.80

REASONING_CONFIDENCE = 0.90

AMBIGUOUS_CONFIDENCE = 0.00