"""Cost tracking, pre-call atomic budget reservations, and rate card calculations."""

from __future__ import annotations

import threading
import uuid
from typing import Any

from pydantic import BaseModel

# Bodhan official rates in INR
RATE_TRANSCRIBE_PER_MINUTE = 0.10       # ₹0.10 per input audio minute
RATE_TRANSLATE_PER_10K_TOKENS = 0.20    # ₹0.20 per 10,000 output tokens
RATE_SPEAK_PER_10K_CHARS = 6.00         # ₹6.00 per 10,000 input characters
RATE_OCR_PER_IMAGE = 0.20               # ₹0.20 per image / page


class BudgetExceededError(Exception):
    """Raised when pre-call budget reservation or execution exceeds max allowed INR budget."""
    pass


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


def estimate_tool_cost(tool_name: str, arguments: dict[str, Any]) -> float:
    """Provide a conservative upper-bound cost estimate before dispatching a paid tool call."""
    if tool_name == "bodhan_ocr":
        return 0.40  # Conservative estimate for 1-2 pages
    elif tool_name == "bodhan_transcribe":
        return 0.10  # 1 minute audio conservative estimate
    elif tool_name == "bodhan_translate":
        text = str(arguments.get("text", ""))
        tokens = max(10, len(text) // 3)
        return calculate_translate_cost(tokens)
    elif tool_name == "bodhan_speak":
        text = str(arguments.get("text", ""))
        return calculate_speak_cost(len(text))
    return 0.0


class CostItem(BaseModel):
    model: str
    operation: str
    metric: str
    quantity: float
    cost_inr: float
    timestamp: float


class CostTracker:
    """Thread-safe cost and usage tracker with pre-call atomic budget reservations."""

    def __init__(self, max_cost_inr: float = 20.0):
        self.max_cost_inr = max_cost_inr
        self._total_cost_inr: float = 0.0
        self._reserved_cost_inr: float = 0.0
        self._active_reservations: dict[str, float] = {}
        self._items: list[CostItem] = []
        self._lock = threading.Lock()

    @property
    def total_cost_inr(self) -> float:
        with self._lock:
            return round(self._total_cost_inr, 4)

    @property
    def reserved_cost_inr(self) -> float:
        with self._lock:
            return round(self._reserved_cost_inr, 4)

    def reserve(self, estimated_amount_inr: float) -> str:
        """Atomically reserve funds before calling a paid model API.
        
        Raises BudgetExceededError if (spent + reserved + estimated) > max_cost_inr.
        """
        with self._lock:
            if self._total_cost_inr + self._reserved_cost_inr + estimated_amount_inr > self.max_cost_inr:
                available = max(0.0, self.max_cost_inr - (self._total_cost_inr + self._reserved_cost_inr))
                raise BudgetExceededError(
                    f"Pre-call budget protection: Cannot reserve ₹{estimated_amount_inr:.4f} INR. "
                    f"Available budget is ₹{available:.4f} INR (Max: ₹{self.max_cost_inr:.2f})."
                )

            token = str(uuid.uuid4())
            self._active_reservations[token] = estimated_amount_inr
            self._reserved_cost_inr += estimated_amount_inr
            return token

    def settle(
        self,
        token: str,
        actual_cost_inr: float,
        model: str,
        operation: str,
        metric: str,
        quantity: float,
        timestamp: float,
    ) -> None:
        """Release reservation and commit actual cost incurred."""
        with self._lock:
            reserved_amount = self._active_reservations.pop(token, 0.0)
            self._reserved_cost_inr = max(0.0, self._reserved_cost_inr - reserved_amount)

            self._total_cost_inr += actual_cost_inr
            self._items.append(
                CostItem(
                    model=model,
                    operation=operation,
                    metric=metric,
                    quantity=quantity,
                    cost_inr=round(actual_cost_inr, 6),
                    timestamp=timestamp,
                )
            )

    def release(self, token: str) -> None:
        """Release reservation on tool failure or abort."""
        with self._lock:
            reserved_amount = self._active_reservations.pop(token, 0.0)
            self._reserved_cost_inr = max(0.0, self._reserved_cost_inr - reserved_amount)

    def record_cost(self, model: str, operation: str, metric: str, quantity: float, cost_inr: float, timestamp: float) -> None:
        """Directly record cost without reservation token."""
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
            return (self._total_cost_inr + self._reserved_cost_inr) >= self.max_cost_inr

    def get_summary(self) -> dict[str, Any]:
        with self._lock:
            by_model: dict[str, float] = {}
            for item in self._items:
                by_model[item.model] = round(by_model.get(item.model, 0.0) + item.cost_inr, 4)
            return {
                "total_cost_inr": round(self._total_cost_inr, 4),
                "reserved_cost_inr": round(self._reserved_cost_inr, 4),
                "budget_max_inr": self.max_cost_inr,
                "budget_exceeded": self._total_cost_inr >= self.max_cost_inr,
                "calls_count": len(self._items),
                "cost_by_model": by_model,
            }

    def reset(self) -> None:
        with self._lock:
            self._total_cost_inr = 0.0
            self._reserved_cost_inr = 0.0
            self._active_reservations.clear()
            self._items.clear()
