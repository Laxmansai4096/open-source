"""Unit Tests for Hybrid Search RBAC, DuckDB Text-to-SQL, and Bi-Temporal GraphRAG."""

import os
import pytest
from src.storage.hybrid_search import HybridSearchEngine
from src.storage.duckdb_table_engine import DuckDBTableEngine
from src.graph.bitemporal_graph import BiTemporalGraphEngine
from src.core.models import MerkleChunk
from src.ingestion.doc_parser import DocumentParser


def test_hybrid_search_and_rbac_filtering():
    """Verifies that Hybrid Search strictly enforces Role-Based Access Control (RBAC)."""
    search_engine = HybridSearchEngine()

    # Create test chunks with different clearance tiers
    chunk_general = MerkleChunk(
        chunk_id="chk_gen_01",
        chunk_index=0,
        content="General Operational Scope: Cloud hosting services and uptime monitoring.",
        sha256_hash="hash_gen_01",
        byte_start=0,
        byte_end=50,
        section_title="Scope"
    )
    chunk_executive = MerkleChunk(
        chunk_id="chk_exec_01",
        chunk_index=1,
        content="Confidential Executive Retention Bonus: Special M&A carveout clause totaling $5M.",
        sha256_hash="hash_exec_01",
        byte_start=51,
        byte_end=120,
        section_title="Executive Retention"
    )

    search_engine.index_chunks([chunk_general], document_id="DOC-1", department_clearance="General")
    search_engine.index_chunks([chunk_executive], document_id="DOC-2", department_clearance="Executive")

    # 1. Query as Junior Procurement Analyst (clearance='Procurement')
    results_junior = search_engine.search("retention bonus cloud hosting", user_clearance="Procurement")
    junior_contents = " ".join([r["content"] for r in results_junior])

    # Assert junior CAN see General, but CANNOT see Executive
    assert "General Operational Scope" in junior_contents
    assert "Confidential Executive Retention" not in junior_contents, "RBAC LEAK: Junior accessed Executive data!"

    # 2. Query as Chief Legal Officer (clearance='Executive')
    results_exec = search_engine.search("retention bonus cloud hosting", user_clearance="Executive")
    exec_contents = " ".join([r["content"] for r in results_exec])

    # Assert executive CAN see both
    assert "General Operational Scope" in exec_contents
    assert "Confidential Executive Retention" in exec_contents, "Executive should have full access"


def test_duckdb_text_to_sql_exact_math():
    """Verifies that DuckDB converts markdown tables to SQL and executes 100% exact math."""
    parser = DocumentParser()
    contract_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "sample_contracts", "Apex_Cloud_Master_Services_Agreement.md"
    )
    parsed = parser.parse_document(contract_path)
    
    # Extract Section 8 table
    table_engine = DuckDBTableEngine()
    table_markdown = parsed["table_blocks"][0]
    table_engine.ingest_markdown_table(table_markdown, table_name="volume_pricing_matrix")

    # Execute Analytical SQL Query for 750,000 units (Tier 3)
    query = """
    SELECT volume_tier, unit_price_usd, guaranteed_sla 
    FROM volume_pricing_matrix 
    WHERE min_units <= 750000 AND max_units >= 750000;
    """
    rows = table_engine.query(query)

    assert len(rows) == 1, "Exactly one pricing tier should match 750,000 units"
    assert rows[0]["volume_tier"] == "Tier 3"
    assert rows[0]["unit_price_usd"] == 0.095  # Exact $0.095/unit, zero hallucination!
    assert rows[0]["guaranteed_sla"] == "99.99%"


def test_bitemporal_graph_amendment_resolution():
    """Verifies that Bi-Temporal Graph automatically resolves latest governing amendment."""
    graph_engine = BiTemporalGraphEngine()

    vendor_id = "VND-APEX-01"
    graph_engine.add_vendor(vendor_id, "Apex Cloud Systems Inc.", parent_corp="Apex Global Holdings Corp")

    # Original Contract v1 ($2.0M liability, effective 2024 to 2026)
    graph_engine.add_contract(
        contract_id="CTR-2024-APEX-MSA",
        vendor_id=vendor_id,
        liability_cap_usd=2000000.0,
        governing_law="Delaware",
        valid_from="2024-01-15",
        valid_to="2026-11-15"
    )

    # Amendment v2 ($10.0M liability, superseding v1 as of September 2026)
    graph_engine.add_contract(
        contract_id="CTR-2026-APEX-AMENDMENT-V2",
        vendor_id=vendor_id,
        liability_cap_usd=10000000.0,
        governing_law="Delaware",
        valid_from="2026-09-01",
        valid_to="2028-11-15",
        supersedes_contract_id="CTR-2024-APEX-MSA"
    )

    # Query 1: What was liability cap on June 1, 2024? -> $2.0M
    terms_2024 = graph_engine.resolve_governing_terms(vendor_id, query_date="2024-06-01")
    assert terms_2024["active_contract_id"] == "CTR-2024-APEX-MSA"
    assert terms_2024["liability_cap_usd"] == 2000000.0
    assert terms_2024["is_amendment"] is False

    # Query 2: What is liability cap on September 15, 2026? -> $10.0M (Amended)
    terms_2026 = graph_engine.resolve_governing_terms(vendor_id, query_date="2026-09-15")
    assert terms_2026["active_contract_id"] == "CTR-2026-APEX-AMENDMENT-V2"
    assert terms_2026["liability_cap_usd"] == 10000000.0
    assert terms_2026["is_amendment"] is True
    assert terms_2026["supersedes_contract_id"] == "CTR-2024-APEX-MSA"


def test_corporate_hierarchy_traversal():
    """Verifies that Knowledge Graph accurately traces parent-subsidiary relationships."""
    graph_engine = BiTemporalGraphEngine()
    graph_engine.add_vendor("VND-APEX-01", "Apex Cloud Systems Inc.", parent_corp="Apex Global Holdings Corp")

    hierarchy = graph_engine.get_corporate_hierarchy("VND-APEX-01")
    assert hierarchy["parent_corporation"] == "Apex Global Holdings Corp"
