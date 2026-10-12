"""
Prompt Dungeon — Pytest Configuration & Test Fixtures
Canonical Reference: docs/case-spec.md v1.1.0 & docs/api-contract.md v1.1.0

Guarantees:
  - Unit tests run hermetically in offline deterministic mode.
  - No external network calls to third-party LLM providers during test execution.
  - Protects against local developer .env keys altering deterministic test assertions.
"""

import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import pytest
import gemma_provider


@pytest.fixture(autouse=True)
def isolate_unit_tests_from_llm(monkeypatch):
    """Ensures all unit tests execute against deterministic offline fallback."""
    monkeypatch.setattr(gemma_provider, "LLM_PROVIDER", "none")
    monkeypatch.setattr(gemma_provider, "LLM_API_KEY", "")
