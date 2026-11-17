"""Indic-OCR MCP tool with PDF rasterization and multi-page layout assembly."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any

from bodhan_mcp.cache import cache
from bodhan_mcp.client import bodhan_client
from bodhan_mcp.cost import calculate_ocr_cost
from bodhan_mcp.tools.media_utils import split_pdf_to_images


def run_ocr(
    file_path: str,
    table_format: str = "markdown",
) -> dict[str, Any]:
    """Extract text, tables, and layout structure from an image or PDF using Indic-OCR.
    
    Automatically detects multi-page PDFs, rasterizes each page, extracts text
    with reading order and table formatting, and joins the assembled document.
    """
    start_time = time.time()
    p = Path(file_path).resolve()
    if not p.is_file():
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "markdown": "",
            "blocks": [],
            "cost_inr": 0.0,
        }

    suffix = p.suffix.lower()
    total_cost = 0.0
    page_markdowns: list[str] = []
    all_blocks: list[dict[str, Any]] = []

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            if suffix == ".pdf":
                # Multi-page PDF: split into page images
                image_files = split_pdf_to_images(p, output_dir=tmp_path)
            elif suffix in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"):
                image_files = [p]
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file extension '{suffix}'. Expected an image (PNG, JPG) or PDF.",
                    "markdown": "",
                    "blocks": [],
                    "cost_inr": 0.0,
                }

            page_count = len(image_files)
            cache_hits = 0

            for page_idx, img_file in enumerate(image_files, start=1):
                cache_key = cache.compute_key("indic-ocr", img_file, table_format=table_format)
                cached_res = cache.get(cache_key)

                if cached_res:
                    page_md = cached_res.get("markdown", "")
                    page_blocks = cached_res.get("blocks", [])
                    cache_hits += 1
                else:
                    ocr_res = bodhan_client.ocr_image(img_file, table_format=table_format)
                    page_md = ocr_res.get("markdown", "")
                    page_blocks = ocr_res.get("blocks", [])
                    page_cost = calculate_ocr_cost(1)
                    total_cost += page_cost
                    cache.set(cache_key, {"markdown": page_md, "blocks": page_blocks, "cost_inr": page_cost})

                page_markdowns.append(f"<!-- Page {page_idx} -->\n{page_md}")
                for b in page_blocks:
                    b_copy = dict(b)
                    b_copy["page"] = page_idx
                    all_blocks.append(b_copy)

        combined_markdown = "\n\n".join(page_markdowns).strip()
        latency_sec = round(time.time() - start_time, 2)
        nominal_cost = calculate_ocr_cost(page_count)

        return {
            "success": True,
            "markdown": combined_markdown,
            "blocks": all_blocks,
            "page_count": page_count,
            "table_format": table_format,
            "cost_inr": round(total_cost, 4),
            "nominal_cost_inr": round(nominal_cost, 4),
            "is_cached": cache_hits == page_count,
            "latency_seconds": latency_sec,
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"OCR processing failed: {str(e)}",
            "markdown": "",
            "blocks": [],
            "cost_inr": 0.0,
        }
