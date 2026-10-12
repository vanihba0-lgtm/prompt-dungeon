"""
Prompt Dungeon — Gemma Live Provider Adapter (Step 3)
Canonical Reference: docs/case-spec.md v1.1.0 & docs/api-contract.md v1.1.0

Features:
  - Generates in-character suspect dialogue using Gemma LLM via hosted inference APIs.
  - Supports standard provider interfaces (Groq, Together, OpenRouter, HuggingFace, Google AI Studio).
  - Strict security: Server-side only; API key never exposed in public models, logs, or error responses.
  - Safe timeouts & graceful deterministic fallback on any error, timeout, or missing key.
  - Invariant protection: Gemma output is treated as untrusted text. Model cannot unlock evidence,
    validate contradictions, change guilt flags, or reveal canonical solutions.
"""

import os
from typing import Optional, Tuple
import httpx

from models import ModelDialogueStatus, SuspectId
from case_data import SUSPECT_DOSSIERS


# Environment Configuration (Backend only)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none").lower()
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "gemma-2-9b-it")
LLM_API_BASE_URL = os.getenv("LLM_API_BASE_URL", "")
try:
    LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "5.0"))
except ValueError:
    LLM_TIMEOUT_SECONDS = 5.0


def _build_suspect_system_prompt(suspect_id: SuspectId) -> str:
    """Builds the bounded in-character persona prompt from canonical dossiers."""
    dossier = SUSPECT_DOSSIERS[suspect_id]
    boundaries_text = "\n- ".join(dossier.strict_knowledge_boundaries)
    truthful_text = "\n- ".join(dossier.truthful_statements)
    false_text = "\n- ".join(dossier.false_statements)

    return (
        f"You are roleplaying as {dossier.full_name}, {dossier.role} at the Blackwood Museum of Antiquities.\n"
        f"The year is 2026. Tonight at 9:17 PM, during the preview gala 'The Last Exhibition', the Obsidian Sun relic was stolen.\n"
        f"A detective is currently interrogating you.\n\n"
        f"YOUR PERSONALITY & DEMEANOR:\n{dossier.personality_demeanor}\n\n"
        f"YOUR STRICT KNOWLEDGE BOUNDARIES (You know NOTHING outside these boundaries):\n- {boundaries_text}\n\n"
        f"YOUR KNOWN TRUTHS:\n- {truthful_text}\n\n"
        f"YOUR LIES / DEFLECTIONS (Defend these when questioned about your whereabouts/secrets):\n- {false_text}\n\n"
        f"CRITICAL INVARIANTS:\n"
        f"1. Stay strictly in character as {dossier.full_name}.\n"
        f"2. Keep your answers concise, conversational, and direct (1-3 sentences maximum).\n"
        f"3. Never confess to stealing the artifact.\n"
        f"4. Never mention game mechanics, points, evidence codes like E-01, or that you are an AI."
    )


def generate_gemma_dialogue(
    suspect_id: SuspectId,
    question: str,
) -> Tuple[Optional[str], ModelDialogueStatus, Optional[str]]:
    """
    Attempts to generate live in-character dialogue using Gemma instruction model.

    Returns:
        (reply_text_or_None, model_status, fallback_reason)
    """
    if LLM_PROVIDER in ("none", "") or not LLM_API_KEY:
        return None, ModelDialogueStatus.FALLBACK, "MODEL_UNAVAILABLE"

    system_prompt = _build_suspect_system_prompt(suspect_id)

    # Resolve base URL according to provider adapter
    if LLM_API_BASE_URL:
        base_url = LLM_API_BASE_URL.rstrip("/")
    elif LLM_PROVIDER == "openrouter":
        base_url = "https://openrouter.ai/api/v1"
    elif LLM_PROVIDER == "together":
        base_url = "https://api.together.xyz/v1"
    else:
        base_url = "https://api.groq.com/openai/v1"

    endpoint = f"{base_url}/chat/completions"

    payload = {
        "model": LLM_MODEL_ID,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "temperature": 0.7,
        "max_tokens": 150,
    }

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "Prompt Dungeon",
    }

    try:
        with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
            response = client.post(endpoint, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    reply = choices[0]["message"].get("content", "").strip()
                    if reply:
                        return reply, ModelDialogueStatus.SUCCESS, None
            return None, ModelDialogueStatus.FALLBACK, f"HTTP_{response.status_code}"
    except httpx.TimeoutException:
        return None, ModelDialogueStatus.FALLBACK, "MODEL_TIMEOUT"
    except Exception as e:
        return None, ModelDialogueStatus.FALLBACK, "MODEL_ERROR"
