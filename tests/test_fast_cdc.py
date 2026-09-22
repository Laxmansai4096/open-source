"""Unit Tests for Content-Defined Chunking (FastCDC) Engine."""

import os
import pytest
from src.ingestion.fast_cdc import FastCDCEngine
from src.ingestion.doc_parser import DocumentParser


def test_fast_cdc_boundary_chunking():
    """Verifies that FastCDC accurately respects legal clause boundaries."""
    parser = DocumentParser()
    contract_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "sample_contracts", "Apex_Cloud_Master_Services_Agreement.md"
    )
    parsed_doc = parser.parse_document(contract_path)
    text = parsed_doc["text"]

    cdc_engine = FastCDCEngine()
    chunks = cdc_engine.chunk_document(text, document_id="CTR-2024-APEX-MSA")

    assert len(chunks) >= 12, "Contract should be split into at least 12 distinct legal sections"

    # Verify table detection in Section 8
    table_chunks = [c for c in chunks if c.is_table]
    assert len(table_chunks) >= 1, "Section 8 volume pricing matrix must be identified as a table"
    assert "Volume Tier" in table_chunks[0].content

    # Verify SHA-256 hashes are valid 64-character hex strings
    for chk in chunks:
        assert len(chk.sha256_hash) == 64
        assert chk.chunk_id.startswith("CTR-2024-APEX-MSA")
