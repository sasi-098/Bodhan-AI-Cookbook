"""Cost tracking and rate card calculations for Bodhan Indic models."""

from __future__ import annotations

import threading
from typing import Any

from pydantic import BaseModel

# Bodhan official rates in INR
RATE_TRANSCRIBE_PER_MINUTE = 0.10       # ₹0.10 per input audio minute
RATE_TRANSLATE_PER_10K_TOKENS = 0.20    # ₹0.20 per 10,000 output tokens
RATE_SPEAK_PER_10K_CHARS = 6.00         # ₹6.00 per 10,000 input characters
RATE_OCR_PER_IMAGE = 0.20               # ₹0.20 per image / page


def calculate_transcribe_cost(duration_seconds: float) -> float:
    """Calculate transcription cost based on audio duration in seconds."""
    minutes = max(0.0, duration_seconds) / 60.0
    return round(minutes * RATE_TRANSCRIBE_PER_MINUTE, 6)


def calculate_translate_cost(output_tokens: int) -> float:
    """Calculate translation cost based on output token count."""
    return round((max(0, output_tokens) / 10_000.0) * RATE_TRANSLATE_PER_10K_TOKENS, 6)


def calculate_speak_cost(char_count: int) -> float:
    """Calculate speech synthesis cost based on input character count."""
    return round((max(0, char_count) / 10_000.0) * RATE_SPEAK_PER_10K_CHARS, 6)


def calculate_ocr_cost(image_count: int = 1) -> float:
    """Calculate OCR cost based on number of processed images/pages."""
    return round(max(0, image_count) * RATE_OCR_PER_IMAGE, 6)


class CostItem(BaseModel):
    model: str
    operation: str
    metric: str
    quantity: float
    cost_inr: float
    timestamp: float


class CostTracker:
    """Thread-safe cost and usage tracker enforcing budget constraints."""

    def __init__(self, max_cost_inr: float = 20.0):
        self.max_cost_inr = max_cost_inr
        self._total_cost_inr: float = 0.0
        self._items: list[CostItem] = []
        self._lock = threading.Lock()

    @property
    def total_cost_inr(self) -> float:
        with self._lock:
            return round(self._total_cost_inr, 4)

    def record_cost(self, model: str, operation: str, metric: str, quantity: float, cost_inr: float, timestamp: float) -> None:
        with self._lock:
            self._total_cost_inr += cost_inr
            self._items.append(
                CostItem(
                    model=model,
                    operation=operation,
                    metric=metric,
                    quantity=quantity,
                    cost_inr=round(cost_inr, 6),
                    timestamp=timestamp,
                )
            )

    def is_budget_exceeded(self) -> bool:
        with self._lock:
            return self._total_cost_inr >= self.max_cost_inr

    def get_summary(self) -> dict[str, Any]:
        with self._lock:
            by_model: dict[str, float] = {}
            for item in self._items:
                by_model[item.model] = round(by_model.get(item.model, 0.0) + item.cost_inr, 4)
            return {
                "total_cost_inr": round(self._total_cost_inr, 4),
                "budget_max_inr": self.max_cost_inr,
                "budget_exceeded": self._total_cost_inr >= self.max_cost_inr,
                "calls_count": len(self._items),
                "cost_by_model": by_model,
            }

    def reset(self) -> None:
        with self._lock:
            self._total_cost_inr = 0.0
            self._items.clear()
