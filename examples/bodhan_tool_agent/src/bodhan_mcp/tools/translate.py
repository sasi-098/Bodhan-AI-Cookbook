"""Indic-Translate MCP tool with language validation, pivot support, and cost tracking."""

from __future__ import annotations

import time
from typing import Any

from bodhan_mcp.cache import cache
from bodhan_mcp.client import bodhan_client
from bodhan_mcp.cost import calculate_translate_cost

# Supported Bodhan Indic-Translate languages from API rules
SUPPORTED_LANGUAGES = {
    "as", "bn", "brx", "doi", "en", "gu", "hi", "kn", "kok", "ks", "ks-Deva",
    "mai", "ml", "mni", "mni-Beng", "mr", "ne", "or", "pa", "sa", "sat", "sd",
    "sd-Arab", "ta", "te", "ur",
}


def run_translate(
    text: str,
    target_lang: str,
    source_lang: str | None = None,
) -> dict[str, Any]:
    """Translate text using Bodhan Indic-Translate.
    
    Supports 25 Indic languages and English. Handles Indic-to-Indic translations
    via English pivot when required.
    """
    start_time = time.time()
    if not text or not text.strip():
        return {
            "success": True,
            "translation": "",
            "source_lang": source_lang or "auto",
            "target_lang": target_lang,
            "tokens_count": 0,
            "cost_inr": 0.0,
            "latency_seconds": 0.0,
        }

    # Normalize target language code
    norm_target = target_lang.strip().lower()
    if norm_target not in SUPPORTED_LANGUAGES:
        return {
            "success": False,
            "error": (
                f"Unsupported target language '{target_lang}'. "
                f"Bodhan Indic-Translate only supports Indic languages and English "
                f"({', '.join(sorted(SUPPORTED_LANGUAGES))})."
            ),
            "translation": "",
            "cost_inr": 0.0,
        }

    norm_source = source_lang.strip().lower() if source_lang else None

    try:
        # Check if Indic-to-Indic pivot through English is needed
        is_indic_source = norm_source and norm_source != "en" and norm_source in SUPPORTED_LANGUAGES
        is_indic_target = norm_target != "en"

        if is_indic_source and is_indic_target and norm_source != norm_target:
            # Step 1: Source Indic -> English
            key_step1 = cache.compute_key("indic-translate", text, source=norm_source, target="en")
            cached_step1 = cache.get(key_step1)
            if cached_step1:
                en_text = cached_step1["translation"]
                cost1 = 0.0
            else:
                en_text = bodhan_client.translate_text(text, target_lang="en", source_lang=norm_source)
                tokens1 = max(1, len(en_text) // 4)
                cost1 = calculate_translate_cost(tokens1)
                cache.set(key_step1, {"translation": en_text, "cost_inr": cost1})

            # Step 2: English -> Target Indic
            key_step2 = cache.compute_key("indic-translate", en_text, source="en", target=norm_target)
            cached_step2 = cache.get(key_step2)
            if cached_step2:
                final_translation = cached_step2["translation"]
                cost2 = 0.0
            else:
                final_translation = bodhan_client.translate_text(en_text, target_lang=norm_target, source_lang="en")
                tokens2 = max(1, len(final_translation) // 4)
                cost2 = calculate_translate_cost(tokens2)
                cache.set(key_step2, {"translation": final_translation, "cost_inr": cost2})

            total_cost = cost1 + cost2
            total_tokens = max(1, (len(en_text) + len(final_translation)) // 4)
            pivoted = True
        else:
            # Direct translation
            cache_key = cache.compute_key("indic-translate", text, source=norm_source, target=norm_target)
            cached_res = cache.get(cache_key)
            if cached_res:
                final_translation = cached_res["translation"]
                total_cost = 0.0
                total_tokens = max(1, len(final_translation) // 4)
            else:
                final_translation = bodhan_client.translate_text(text, target_lang=norm_target, source_lang=norm_source)
                total_tokens = max(1, len(final_translation) // 4)
                total_cost = calculate_translate_cost(total_tokens)
                cache.set(cache_key, {"translation": final_translation, "cost_inr": total_cost})
            pivoted = False

        latency_sec = round(time.time() - start_time, 2)
        return {
            "success": True,
            "translation": final_translation,
            "source_lang": norm_source or "auto",
            "target_lang": norm_target,
            "tokens_count": total_tokens,
            "pivoted_via_english": pivoted,
            "cost_inr": round(total_cost, 4),
            "latency_seconds": latency_sec,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Translation failed: {str(e)}",
            "translation": "",
            "cost_inr": 0.0,
        }
