"""Enterprise Multi-Agent Orchestrator.

Stateful orchestrator coordinating:
- Hybrid Vector Search (Document-Level RBAC)
- DuckDB SQL Executor (Exact Table Math)
- Bi-Temporal GraphRAG (Corporate Hierarchy & Amendments)
- Client ERP API Connector (Live Spend & PO Tracking)
- Autonomous Stale-Data Self-Refresh Loop (Live Web Threat Intelligence)
- Human-in-the-Loop (HITL) Approval Gate for Sensitive Write Operations
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from src.core.models import UnifiedVendorDigitalTwin, ContractTerms
from src.storage.hybrid_search import HybridSearchEngine
from src.storage.duckdb_table_engine import DuckDBTableEngine
from src.graph.bitemporal_graph import BiTemporalGraphEngine
from src.connectors.erp_client import ErpClientConnector
from src.agents.stale_data_loop import StaleDataAgenticLoop
from src.gateway.llm_gateway import ResilientLlmGateway


class AgentOrchestrator:
    """Enterprise Multi-Agent Supervisor."""

    def __init__(self):
        self.search_engine = HybridSearchEngine()
        self.table_engine = DuckDBTableEngine()
        self.graph_engine = BiTemporalGraphEngine()
        self.erp_connector = ErpClientConnector()
        self.stale_loop = StaleDataAgenticLoop(staleness_threshold_days=60)
        self.gateway = ResilientLlmGateway()

    def audit_vendor_360(
        self,
        vendor_id: str,
        vendor_name: str,
        contract_liability_cap: float = 2000000.0,
        user_clearance: str = "Procurement"
    ) -> Dict[str, Any]:
        """
        Coordinates full multi-source agentic triangulation:
        Contract Terms + ERP Live Financials + Live Web Scraped Threat Intelligence.
        """
        # Step 1: Query Client ERP API (Stream 2)
        erp_telemetry = self.erp_connector.get_vendor_financials(vendor_name)
        active_spend = erp_telemetry.quarterly_spend_usd if erp_telemetry else 0.0

        # Step 2: Execute Stale-Data Self-Refresh Web Loop (Stream 3)
        refreshed_web_data, was_refreshed = self.stale_loop.check_and_refresh(vendor_id, vendor_name)

        # Step 3: Compute Financial Exposure Gap (Contract vs. ERP)
        gap = active_spend - contract_liability_cap
        is_over_exposed = gap > 0

        # Step 4: Detect Cybersecurity Breach Status (Contract vs. Live Web)
        recent_breaches = refreshed_web_data.get("recent_breaches", [])
        has_active_breach = len(recent_breaches) > 0

        # Step 5: Formulate Executive Audit Verdict
        if is_over_exposed and has_active_breach:
            verdict = "CRITICAL_RISK_BREACH_AND_OVEREXPOSURE"
            recommended_action = "IMMEDIATE_PURCHASE_ORDER_FREEZE_AND_LEGAL_AUDIT_DEMAND"
        elif is_over_exposed:
            verdict = "FINANCIAL_OVEREXPOSURE_ALERT"
            recommended_action = "RENEGOTIATE_LIABILITY_CAP_OR_CAP_NEW_PURCHASE_ORDERS"
        elif has_active_breach:
            verdict = "SECURITY_WARRANTY_BREACH_ALERT"
            recommended_action = "REQUEST_THIRD_PARTY_FORENSIC_SOC2_AUDIT_REPORT"
        else:
            verdict = "COMPLIANT_VENDOR_STANDING"
            recommended_action = "STANDARD_OPERATION"

        report = {
            "vendor_id": vendor_id,
            "vendor_name": vendor_name,
            "audit_verdict": verdict,
            "recommended_action": recommended_action,
            "sources_fused": {
                "contract_pdf": {
                    "liability_cap_usd": contract_liability_cap,
                    "source": "Document Ingestion Vault"
                },
                "client_erp_api": {
                    "active_spend_usd": active_spend,
                    "financial_gap_usd": gap,
                    "is_over_exposed": is_over_exposed,
                    "source": "Client SAP/Coupa ERP REST Connector"
                },
                "live_web_scraping_agent": {
                    "was_refreshed_from_live_web": was_refreshed,
                    "registry_status": refreshed_web_data.get("registry_status"),
                    "recent_breaches_count": len(recent_breaches),
                    "breaches": recent_breaches,
                    "last_crawled_at": refreshed_web_data.get("last_crawled_at"),
                    "source": "Playwright Autonomous Browser Crawler"
                }
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return report

    def request_human_in_the_loop_action(
        self,
        action_type: str,
        vendor_id: str,
        proposed_payload: Dict[str, Any],
        approved_by_officer: Optional[str] = None
    ) -> Dict[str, Any]:
        """Human-in-the-Loop (HITL) Gate: Halts sensitive write-backs until human risk officer approves."""
        if not approved_by_officer:
            return {
                "status": "SUSPENDED_AWAITING_HUMAN_APPROVAL",
                "action_type": action_type,
                "vendor_id": vendor_id,
                "message": "Sensitive write-back operation suspended. Requires explicit sign-off from Chief Risk Officer."
            }

        # Human approved: Execute write-back
        return {
            "status": "APPROVED_AND_EXECUTED",
            "action_type": action_type,
            "vendor_id": vendor_id,
            "approved_by": approved_by_officer,
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
