"""Enterprise Domain Models and Pydantic Schemas.

Defines the multi-source data structures:
- Document Contracts & Merkle Chunks
- Client ERP Financials & Telemetry
- Live Web Scraped Threat Intelligence
- Unified 360-Degree Vendor Risk Entity
"""

from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# 1. Content-Defined Chunking & Merkle DAG Models
# ------------------------------------------------------------------------------
class MerkleChunk(BaseModel):
    """A cryptographic content-defined chunk of a document."""
    chunk_id: str
    chunk_index: int
    content: str
    sha256_hash: str
    byte_start: int
    byte_end: int
    section_title: Optional[str] = None
    page_number: Optional[int] = 1
    is_table: bool = False


class MerkleDiffResult(BaseModel):
    """Result of diffing an updated document's Merkle tree against an existing index."""
    document_id: str
    total_chunks_new: int
    unmodified_chunks_count: int
    added_chunks_count: int
    modified_chunks_count: int
    deleted_chunks_count: int
    chunks_to_reindex: List[MerkleChunk]
    cost_reduction_percentage: float = Field(
        description="Percentage of embedding/OCR computation saved via delta diffing"
    )


# ------------------------------------------------------------------------------
# 2. Multi-Source Ingestion Schemas
# ------------------------------------------------------------------------------
class ContractTerms(BaseModel):
    """Stream 1: Data extracted from legal PDF contracts."""
    contract_id: str
    vendor_name: str
    liability_cap_usd: float
    governing_law: str
    effective_date: str
    auto_renewal_date: Optional[str] = None
    cancellation_notice_days: int = 30
    warranties: List[str] = Field(default_factory=list)
    confidentiality_tier: str = "Confidential"
    department_clearance: str = "Procurement"


class ErpSpendTelemetry(BaseModel):
    """Stream 2: Data fetched from Client ERP API (SAP / Coupa)."""
    vendor_id: str
    canonical_vendor_name: str
    quarterly_spend_usd: float
    active_purchase_orders_count: int
    total_committed_po_value_usd: float
    payment_terms: str
    credit_rating: str
    last_sync_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WebThreatIncident(BaseModel):
    """Security breach or CVE incident scraped from live web."""
    cve_id: Optional[str] = None
    severity: str
    reported_date: str
    summary: str
    source_url: str


class WebThreatIntelligence(BaseModel):
    """Stream 3: Real-time data scraped by autonomous browser agent."""
    canonical_vendor_name: str
    registry_status: str = "Active"
    headquarters: str
    recent_breaches: List[WebThreatIncident] = Field(default_factory=list)
    has_active_regulatory_inquiry: bool = False
    last_crawled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    freshness_score: float = 1.0


# ------------------------------------------------------------------------------
# 3. Unified 360-Degree Vendor Risk Entity (The Digital Twin)
# ------------------------------------------------------------------------------
class UnifiedVendorDigitalTwin(BaseModel):
    """The canonical fused entity combining Docs + ERP API + Live Web."""
    canonical_id: str
    vendor_name: str
    contract: Optional[ContractTerms] = None
    erp: Optional[ErpSpendTelemetry] = None
    web: Optional[WebThreatIntelligence] = None
    
    # Computed 360-degree risk metrics
    financial_exposure_gap_usd: float = 0.0  # (ERP Active Spend - Contract Liability Cap)
    is_over_exposed: bool = False
    has_active_breach_in_breach_of_contract: bool = False
    audit_verdict: str = "PENDING"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
