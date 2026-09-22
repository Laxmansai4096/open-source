"""Unit Tests for Autonomous Web Scraper, Stale Data Self-Refresh Loop & Multi-Agent Orchestrator."""

from datetime import datetime, timezone, timedelta
import pytest
from src.agents.web_scraper import AutonomousWebScraperTool
from src.agents.stale_data_loop import StaleDataAgenticLoop
from src.agents.orchestrator import AgentOrchestrator


def test_autonomous_web_scraper_intelligence():
    """Verifies that the web scraper autonomous tool extracts live CVE breach intelligence."""
    tool = AutonomousWebScraperTool()
    intel = tool.scrape_vendor_intel("Apex Cloud Systems Inc.")

    assert intel.canonical_vendor_name == "Apex Cloud Systems Inc."
    assert "Delaware" in intel.registry_status
    assert len(intel.recent_breaches) >= 1
    assert intel.recent_breaches[0].cve_id == "CVE-2026-4412"
    assert "ransomware" in intel.recent_breaches[0].summary.lower()


def test_stale_data_autonomous_refresh_loop():
    """Verifies that the agent automatically detects aged records, crawls web, and updates timestamps."""
    loop = StaleDataAgenticLoop(staleness_threshold_days=60)

    # Seed an aged record from 120 days ago (stale)
    aged_date = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    loop.seed_initial_record("VND-APEX-01", {
        "vendor_id": "VND-APEX-01",
        "last_crawled_at": aged_date,
        "registry_status": "Outdated Info"
    })

    # Execute loop -> Should trigger autonomous refresh
    refreshed_record, was_refreshed = loop.check_and_refresh("VND-APEX-01", "Apex Cloud Systems Inc.")

    assert was_refreshed is True, "Stale record must trigger web refresh"
    assert refreshed_record["freshness_score"] == 1.0
    assert "audit_trail" in refreshed_record
    assert len(refreshed_record["recent_breaches"]) >= 1

    # Immediate second call -> Should use fresh cached data without re-scraping
    cached_record, was_refreshed_second = loop.check_and_refresh("VND-APEX-01", "Apex Cloud Systems Inc.")
    assert was_refreshed_second is False, "Fresh record should not re-trigger web scraper"


def test_orchestrator_360_risk_triangulation():
    """Verifies that the multi-agent orchestrator accurately triangulates Docs + ERP + Web Scraper."""
    orchestrator = AgentOrchestrator()
    report = orchestrator.audit_vendor_360(
        vendor_id="apex_cloud",
        vendor_name="Apex Cloud Systems Inc.",
        contract_liability_cap=2000000.0  # $2.0M liability cap
    )

    assert report["vendor_id"] == "apex_cloud"
    assert report["audit_verdict"] == "CRITICAL_RISK_BREACH_AND_OVEREXPOSURE"
    assert "PURCHASE_ORDER_FREEZE" in report["recommended_action"]

    fused = report["sources_fused"]
    # 1. Contract PDF
    assert fused["contract_pdf"]["liability_cap_usd"] == 2000000.0
    # 2. Client ERP API
    assert fused["client_erp_api"]["active_spend_usd"] == 4500000.0  # $4.5M
    assert fused["client_erp_api"]["financial_gap_usd"] == 2500000.0  # $2.5M gap
    assert fused["client_erp_api"]["is_over_exposed"] is True
    # 3. Live Web Scraper
    assert fused["live_web_scraping_agent"]["recent_breaches_count"] >= 1


def test_human_in_the_loop_gate():
    """Verifies that the Human-in-the-Loop gate suspends write operations until officer approves."""
    orchestrator = AgentOrchestrator()

    # Attempt sensitive write without approval
    res_suspended = orchestrator.request_human_in_the_loop_action(
        action_type="FREEZE_VENDOR_PURCHASE_ORDERS",
        vendor_id="apex_cloud",
        proposed_payload={"freeze_amount": 4500000.0}
    )
    assert res_suspended["status"] == "SUSPENDED_AWAITING_HUMAN_APPROVAL"

    # Human approves action
    res_approved = orchestrator.request_human_in_the_loop_action(
        action_type="FREEZE_VENDOR_PURCHASE_ORDERS",
        vendor_id="apex_cloud",
        proposed_payload={"freeze_amount": 4500000.0},
        approved_by_officer="Chief_Risk_Officer_Sarah_Connor"
    )
    assert res_approved["status"] == "APPROVED_AND_EXECUTED"
    assert res_approved["approved_by"] == "Chief_Risk_Officer_Sarah_Connor"
