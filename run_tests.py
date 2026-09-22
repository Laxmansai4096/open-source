"""Standalone Test Runner for OmniSynapse-Titan using Python's standard library."""

import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests.test_fast_cdc import test_fast_cdc_boundary_chunking
from tests.test_merkle_dag import test_merkle_dag_delta_computation
from tests.test_erp_connector import test_erp_client_financial_telemetry, test_360_degree_risk_triangulation


def main():
    # Ensure UTF-8 output on Windows consoles
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 70)
    print("[*] RUNNING OMNISYNAPSE-TITAN PHASE 1 VERIFICATION SUITE")
    print("=" * 70)

    tests = [
        ("FastCDC Legal Boundary Chunking & Table Identification", test_fast_cdc_boundary_chunking),
        ("Merkle DAG Delta Diff & Compute Cost Savings Calculation", test_merkle_dag_delta_computation),
        ("Client ERP API Telemetry & Spend Retrieval", test_erp_client_financial_telemetry),
        ("360-Degree Multi-Source Risk Triangulation (Contract vs ERP)", test_360_degree_risk_triangulation),
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
