"""Unit Tests for Enterprise Client ERP Connector (Stream 2)."""

import pytest
from src.connectors.erp_client import ErpClientConnector
from src.core.models import ContractTerms, UnifiedVendorDigitalTwin


def test_erp_client_financial_telemetry():
    """Verifies that ERP connector correctly retrieves active spend and flags exposure gap."""
    connector = ErpClientConnector()
    financials = connector.get_vendor_financials("Apex Cloud Systems")

    assert financials is not None, "Vendor financials should be found in ERP database"
    assert financials.vendor_id == "VND-APEX-9921"
    assert financials.quarterly_spend_usd == 4500000.00  # $4.5M
    assert financials.active_purchase_orders_count == 14
    assert financials.payment_terms == "Net-30"


def test_360_degree_risk_triangulation():
    """Simulates agentic fusion of Contract terms vs. ERP live financials."""
    connector = ErpClientConnector()
    erp_data = connector.get_vendor_financials("Apex Cloud")
    assert erp_data is not None

    contract_data = ContractTerms(
        contract_id="CTR-2024-APEX-MSA",
        vendor_name="Apex Cloud Systems Inc.",
        liability_cap_usd=2000000.00,  # $2.0M liability cap
        governing_law="Delaware",
        effective_date="2024-01-15",
        auto_renewal_date="2026-11-15",
        cancellation_notice_days=60
    )

    # Compute financial exposure gap
    gap = erp_data.quarterly_spend_usd - contract_data.liability_cap_usd
    is_over_exposed = gap > 0

    twin = UnifiedVendorDigitalTwin(
        canonical_id="urn:enterprise:vendor:apex_cloud",
        vendor_name="Apex Cloud Systems Inc.",
        contract=contract_data,
        erp=erp_data,
        financial_exposure_gap_usd=gap,
        is_over_exposed=is_over_exposed,
        audit_verdict="CRITICAL_EXPOSURE_ALERT" if is_over_exposed else "COMPLIANT"
    )

    # Assert that spend ($4.5M) exceeds liability cap ($2.0M) by $2.5M
    assert twin.is_over_exposed is True
    assert twin.financial_exposure_gap_usd == 2500000.00
    assert twin.audit_verdict == "CRITICAL_EXPOSURE_ALERT"
