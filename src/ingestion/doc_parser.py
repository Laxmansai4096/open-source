"""Document Intelligence and Layout Extraction Adapter.

Supports:
- Azure Document Intelligence (Layout Model) for live cloud extraction.
- Offline Local Fallback for continuous local development and CI/CD testing.
"""

import os
from typing import Dict, Any, List
from src.core.config import settings


class DocumentParser:
    """Enterprise Document Parser with table and layout awareness."""

    def __init__(self):
        self.run_mode = settings.run_mode

    def parse_document(self, file_path: str) -> Dict[str, Any]:
        """Parses a document file and extracts text, tables, and section metadata."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Target document not found: {file_path}")

        if self.run_mode == "azure" and settings.azure_doc_intelligence_key != "mock-doc-key":
            return self._parse_with_azure_doc_intel(file_path)
        else:
            return self._parse_with_local_fallback(file_path)

    def _parse_with_azure_doc_intel(self, file_path: str) -> Dict[str, Any]:
        """Live cloud extraction using Azure AI Document Intelligence."""
        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential

            client = DocumentIntelligenceClient(
                endpoint=settings.azure_doc_intelligence_endpoint,
                credential=AzureKeyCredential(settings.azure_doc_intelligence_key)
            )

            with open(file_path, "rb") as f:
                poller = client.begin_analyze_document(
                    "prebuilt-layout",
                    body=f,
                    content_type="application/pdf"
                )
            result = poller.result()

            extracted_text = result.content or ""
            tables: List[Dict[str, Any]] = []

            if hasattr(result, "tables") and result.tables:
                for t in result.tables:
                    tables.append({
                        "row_count": t.row_count,
                        "column_count": t.column_count,
                        "cells": [
                            {"row": c.row_index, "col": c.column_index, "content": c.content}
                            for c in t.cells
                        ]
                    })

            return {
                "source_path": file_path,
                "text": extracted_text,
                "tables": tables,
                "engine": "Azure Document Intelligence (Live)"
            }
        except Exception as e:
            # Fallback gracefully if cloud credentials fail
            return self._parse_with_local_fallback(file_path)

    def _parse_with_local_fallback(self, file_path: str) -> Dict[str, Any]:
        """Local offline layout extractor that parses plain text or markdown files."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Extract markdown tables if present
        table_blocks: List[str] = []
        lines = content.split("\n")
        in_table = False
        current_table: List[str] = []

        for line in lines:
            if "|" in line:
                in_table = True
                current_table.append(line)
            else:
                if in_table and current_table:
                    table_blocks.append("\n".join(current_table))
                    current_table = []
                in_table = False

        if current_table:
            table_blocks.append("\n".join(current_table))

        return {
            "source_path": file_path,
            "text": content,
            "tables_found_count": len(table_blocks),
            "table_blocks": table_blocks,
            "engine": "Enterprise Local Parser (Offline Fallback)"
        }
