"""Unit tests for cost calculations and budget tracking."""

from bodhan_mcp.cost import (
    CostTracker,
    calculate_ocr_cost,
    calculate_speak_cost,
    calculate_transcribe_cost,
    calculate_translate_cost,
)


def test_transcribe_cost():
    # 60 seconds (1 minute) = ₹0.10
    assert calculate_transcribe_cost(60.0) == 0.10
    # 30 seconds = ₹0.05
    assert calculate_transcribe_cost(30.0) == 0.05
    # 0 seconds = ₹0.0
    assert calculate_transcribe_cost(0.0) == 0.0


def test_translate_cost():
    # 10,000 output tokens = ₹0.20
    assert calculate_translate_cost(10000) == 0.20
    # 5,000 output tokens = ₹0.10
    assert calculate_translate_cost(5000) == 0.10
    # 0 tokens = ₹0.0
    assert calculate_translate_cost(0) == 0.0


def test_speak_cost():
    # 10,000 characters = ₹6.00
    assert calculate_speak_cost(10000) == 6.00
    # 1,000 characters = ₹0.60
    assert calculate_speak_cost(1000) == 0.60
    # 0 characters = ₹0.0
    assert calculate_speak_cost(0) == 0.0


def test_ocr_cost():
    # 1 image = ₹0.20
    assert calculate_ocr_cost(1) == 0.20
    # 5 images = ₹1.00
    assert calculate_ocr_cost(5) == 1.00
    # 0 images = ₹0.0
    assert calculate_ocr_cost(0) == 0.0


def test_cost_tracker_budget():
    tracker = CostTracker(max_cost_inr=1.0)
    assert not tracker.is_budget_exceeded()

    # Record ₹0.50
    tracker.record_cost("indic-ocr", "ocr_page", "pages", 2, 0.40, 100.0)
    assert not tracker.is_budget_exceeded()
    assert tracker.total_cost_inr == 0.40

    # Record ₹0.70 (total ₹1.10 -> exceeds ₹1.0)
    tracker.record_cost("indic-speak", "synthesize", "chars", 1200, 0.72, 101.0)
    assert tracker.is_budget_exceeded()
    assert tracker.total_cost_inr == 1.12

    summary = tracker.get_summary()
    assert summary["budget_exceeded"] is True
    assert summary["calls_count"] == 2
    assert "indic-ocr" in summary["cost_by_model"]
    assert "indic-speak" in summary["cost_by_model"]
