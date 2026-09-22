"""Standalone Test Runner for OmniSynapse-Titan using Python's standard library."""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests.test_fast_cdc import test_fast_cdc_boundary_chunking
from tests.test_merkle_dag import test_merkle_dag_delta_computation
from tests.test_erp_connector import test_erp_client_financial_telemetry, test_360_degree_risk_triangulation
from tests.test_llm_gateway import (
    test_gateway_primary_execution,
    test_gateway_semantic_caching,
    test_gateway_automatic_fallback_on_429,
    test_circuit_breaker_tripping_and_recovery,
    test_rate_limiter_exceeded
)
from tests.test_storage_and_graph import (
    test_hybrid_search_and_rbac_filtering,
    test_duckdb_text_to_sql_exact_math,
    test_bitemporal_graph_amendment_resolution,
    test_corporate_hierarchy_traversal
)


def main():
    # Ensure UTF-8 output on Windows consoles
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 70)
    print("[*] RUNNING OMNISYNAPSE-TITAN PHASE 1, 2 & 3 VERIFICATION SUITE")
    print("=" * 70)

    tests = [
        # Phase 1
        ("Phase 1: FastCDC Legal Boundary Chunking & Table Identification", test_fast_cdc_boundary_chunking),
        ("Phase 1: Merkle DAG Delta Diff & Compute Cost Savings", test_merkle_dag_delta_computation),
        ("Phase 1: Client ERP API Telemetry & Spend Retrieval", test_erp_client_financial_telemetry),
        ("Phase 1: 360-Degree Multi-Source Risk Triangulation (Contract vs ERP)", test_360_degree_risk_triangulation),
        # Phase 2
        ("Phase 2: LLM Gateway Primary Provider Generation", test_gateway_primary_execution),
        ("Phase 2: High-Speed Semantic Query Caching (<25ms, $0.00 cost)", test_gateway_semantic_caching),
        ("Phase 2: Zero-Downtime Automatic Fallback to Open-Source (Llama-3.3)", test_gateway_automatic_fallback_on_429),
        ("Phase 2: Circuit Breaker State Transitions (CLOSED -> OPEN -> HALF_OPEN)", test_circuit_breaker_tripping_and_recovery),
        ("Phase 2: Token-Bucket Rate Limiter Quota Enforcement", test_rate_limiter_exceeded),
        # Phase 3
        ("Phase 3: Hybrid Search Document-Level RBAC Security Filtering", test_hybrid_search_and_rbac_filtering),
        ("Phase 3: In-Memory DuckDB Text-to-SQL for 100% Exact Math", test_duckdb_text_to_sql_exact_math),
        ("Phase 3: Bi-Temporal GraphRAG Amendment Resolution ([SUPERSEDES])", test_bitemporal_graph_amendment_resolution),
        ("Phase 3: Multi-Hop Corporate Hierarchy & Subsidiary Traversal", test_corporate_hierarchy_traversal),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name} - Error: {e}")
            failed += 1

    print("=" * 70)
    print(f"RESULT: {passed} PASSED, {failed} FAILED")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
