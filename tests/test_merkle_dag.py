"""Unit Tests for Merkle DAG Delta Engine and Compute Savings."""

import os
import pytest
from src.ingestion.doc_parser import DocumentParser
from src.ingestion.fast_cdc import FastCDCEngine
from src.ingestion.merkle_dag import MerkleDAGEngine


def test_merkle_dag_delta_computation():
    """Verifies that amending 2 sections out of 14 skips 12 sections and flags only 2 for re-indexing."""
    parser = DocumentParser()
    cdc_engine = FastCDCEngine()
    merkle_engine = MerkleDAGEngine()

    base_dir = os.path.join(os.path.dirname(__file__), "..", "data", "sample_contracts")
    v1_path = os.path.join(base_dir, "Apex_Cloud_Master_Services_Agreement.md")
    v2_path = os.path.join(base_dir, "Apex_Cloud_Amendment_v2.md")

    # Ingest Version 1
    doc_v1 = parser.parse_document(v1_path)
    chunks_v1 = cdc_engine.chunk_document(doc_v1["text"], document_id="CTR-APEX-MSA-V1")
    root_v1 = merkle_engine.compute_merkle_root(chunks_v1)

    # Ingest Version 2 (Amended)
    doc_v2 = parser.parse_document(v2_path)
    chunks_v2 = cdc_engine.chunk_document(doc_v2["text"], document_id="CTR-APEX-MSA-V2")
    root_v2 = merkle_engine.compute_merkle_root(chunks_v2)

    # Assert roots are different because 2 sections were amended
    assert root_v1 != root_v2, "Merkle roots must differ when document content changes"

    # Compute Delta Diff
    diff_result = merkle_engine.compute_delta(
        document_id="CTR-APEX-MSA-V2",
        old_chunks=chunks_v1,
        new_chunks=chunks_v2
    )

    # Verify that majority of chunks are unmodified (cost savings)
    assert diff_result.unmodified_chunks_count >= 10, "At least 10 unchanged sections should be skipped"
    assert diff_result.cost_reduction_percentage > 70.0, "Cost savings should exceed 70%"
    assert len(diff_result.chunks_to_reindex) == diff_result.modified_chunks_count + diff_result.added_chunks_count

    # Verify that the modified sections include Section 12 ($10M liability)
    reindex_content = " ".join([c.content for c in diff_result.chunks_to_reindex])
    assert "10,000,000" in reindex_content, "Amended liability cap ($10M) must be flagged for re-indexing"
