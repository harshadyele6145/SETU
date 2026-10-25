"""
SETU — Document Text Extraction & Compliance Discrepancy Analyzer.
Performs local text extraction on uploaded regulatory PDFs, detects dates and reference IDs,
calculates discrepancy indicators against registered metadata, and enforces mandatory human review.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.app.core.config import settings


class DocumentExtractionService:
    @staticmethod
    def _extract_text_from_pdf_stream(pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Local pure-Python PDF text stream extractor.
        Parses unencrypted text objects and font streams without requiring heavyweight external runtimes.
        """
        pages = []
        if not pdf_path.exists():
            return [{"page": 1, "text": "", "ocr_required": True, "error": "File not found on disk"}]

        try:
            with open(pdf_path, "rb") as f:
                content = f.read()

            # Find PDF page markers or stream objects
            # Standard PDF text blocks are enclosed in BT ... ET blocks
            text_blocks = re.findall(b"BT(.*?)ET", content, re.DOTALL)
            
            if text_blocks:
                full_page_text = []
                for block in text_blocks:
                    # Extract literal string tokens within parentheses (...)
                    raw_strings = re.findall(b"\((.*?)\)", block)
                    decoded = [s.decode("latin1", errors="ignore") for s in raw_strings if len(s) > 1]
                    if decoded:
                        full_page_text.append(" ".join(decoded))
                
                extracted_str = "\n".join(full_page_text).strip()
                if extracted_str:
                    pages.append({
                        "page": 1,
                        "text": extracted_str,
                        "ocr_required": False
                    })

            # If no BT...ET blocks found, check raw printable ASCII text strings
            if not pages:
                printable_ascii = re.findall(rb"[A-Za-z0-9\s,.:/\-]{5,}", content)
                if printable_ascii:
                    preview_text = " ".join([p.decode("latin1", errors="ignore") for p in printable_ascii[:40]])
                    pages.append({
                        "page": 1,
                        "text": preview_text,
                        "ocr_required": False
                    })
                else:
                    pages.append({
                        "page": 1,
                        "text": "[Scanned Image PDF: Text layer not embedded. OCR fallback required for full optical character extraction.]",
                        "ocr_required": True
                    })

        except Exception as e:
            pages.append({
                "page": 1,
                "text": "",
                "ocr_required": True,
                "error": f"Extraction failure: {str(e)}"
            })

        return pages

    @classmethod
    def analyze_document(
        cls,
        file_path: str,
        registered_title: str,
        registered_category: str,
        registered_expiry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyzes an uploaded document for regulatory keywords, validity dates,
        and discrepancies against registered application records.
        """
        full_path = Path(settings.STORAGE_DIR) / file_path
        if not full_path.exists():
            # Check relative to repo root
            alt_path = Path(file_path)
            if alt_path.exists():
                full_path = alt_path

        pages = cls._extract_text_from_pdf_stream(full_path)
        combined_text = " ".join([p.get("text", "") for p in pages])
        ocr_required = any(p.get("ocr_required") for p in pages)

        # 1. Date Detection (DD-MM-YYYY, YYYY-MM-DD, DD/MM/YYYY)
        date_patterns = [
            r"\b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b",
            r"\b(\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b"
        ]
        detected_dates = []
        for pat in date_patterns:
            matches = re.findall(pat, combined_text)
            for m in matches:
                if m not in detected_dates:
                    detected_dates.append(m)

        # 2. Reference / Deed ID Detection
        ref_patterns = [
            r"\b([A-Z]{2,4}[-/]\d{4,8}[-/]\w{1,6})\b",
            r"\b(REG[-/]\d{4,10})\b",
            r"\b(NOC[-/]\w{3,10})\b"
        ]
        detected_refs = []
        for pat in ref_patterns:
            matches = re.findall(pat, combined_text)
            for m in matches:
                if m not in detected_refs:
                    detected_refs.append(m)

        # 3. Confidence Calculation
        if ocr_required:
            confidence = 35.0
            confidence_level = "LOW_OCR_FALLBACK_RECOMMENDED"
        elif detected_dates or detected_refs:
            confidence = 88.5
            confidence_level = "HIGH_CONFIDENCE_STRUCTURED"
        else:
            confidence = 65.0
            confidence_level = "MODERATE_UNSTRUCTURED_TEXT"

        # 4. Discrepancy Assessment
        discrepancies = []
        if registered_expiry and detected_dates:
            # Check if registered expiry matches any detected date
            matched = any(registered_expiry in d or d in registered_expiry for d in detected_dates)
            if not matched:
                discrepancies.append({
                    "field": "expiry_date",
                    "registered_value": registered_expiry,
                    "extracted_values": detected_dates,
                    "explanation": f"Document text contains dates ({', '.join(detected_dates[:3])}) differing from registered expiry ({registered_expiry}). Human verification recommended."
                })

        return {
            "document_name": full_path.name,
            "category": registered_category,
            "title": registered_title,
            "extraction_status": "COMPLETED",
            "ocr_required": ocr_required,
            "confidence_score": confidence,
            "confidence_level": confidence_level,
            "pages_analyzed": len(pages),
            "source_references": [
                {"page": p.get("page", 1), "text_snippet": p.get("text", "")[:160]} for p in pages
            ],
            "detected_dates": detected_dates[:5],
            "detected_references": detected_refs[:5],
            "discrepancies": discrepancies,
            "human_verification_mandated": True,
            "statutory_notice": "In accordance with Invariant INV-01, extracted metadata is purely diagnostic. All regulatory decisions require human desk officer verification."
        }


extraction_service = DocumentExtractionService()
