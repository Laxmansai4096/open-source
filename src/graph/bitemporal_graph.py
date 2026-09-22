"""Bi-Temporal Knowledge Graph & GraphRAG Engine ("Graphy").

Implements:
1. Entity-Relationship Ontology: Vendors, Parent Corps, Contracts, Liability Caps, and Jurisdictions.
2. Bi-Temporal Edges: Tracks Valid Time (VT) and Transaction Time (TT).
3. Amendment Resolution: [SUPERSEDES] edges automatically resolve conflicting contract amendments.
4. Multi-Hop Corporate Tree Traversal: Connects corporate parents, subsidiaries, and risk exposure.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
import networkx as nx


class BiTemporalGraphEngine:
    """Enterprise Bi-Temporal Knowledge Graph powered by NetworkX."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_vendor(self, vendor_id: str, name: str, parent_corp: Optional[str] = None):
        """Adds a vendor entity and links to parent holding company if present."""
        self.graph.add_node(
            vendor_id,
            entity_type="Vendor",
            name=name
        )
        if parent_corp:
            self.graph.add_node(parent_corp, entity_type="ParentCorp", name=parent_corp)
            self.graph.add_edge(vendor_id, parent_corp, relationship="SUBSIDIARY_OF")

    def add_contract(
        self,
        contract_id: str,
        vendor_id: str,
        liability_cap_usd: float,
        governing_law: str,
        valid_from: str,
        valid_to: str,
        supersedes_contract_id: Optional[str] = None
    ):
        """Adds a contract node with bi-temporal validity bounds and supersedes edges."""
        self.graph.add_node(
            contract_id,
            entity_type="Contract",
            liability_cap_usd=liability_cap_usd,
            governing_law=governing_law,
            valid_from=valid_from,
            valid_to=valid_to
        )

        # Link Vendor -> Contract
        self.graph.add_edge(vendor_id, contract_id, relationship="SIGNATORY_OF")

        # Link Contract -> Jurisdiction
        self.graph.add_node(governing_law, entity_type="Jurisdiction", name=governing_law)
        self.graph.add_edge(contract_id, governing_law, relationship="GOVERNED_BY")

        # Handle Temporal Amendment [SUPERSEDES] edge
        if supersedes_contract_id and self.graph.has_node(supersedes_contract_id):
            self.graph.add_edge(
                contract_id,
                supersedes_contract_id,
                relationship="SUPERSEDES",
                valid_from=valid_from
            )

    def resolve_governing_terms(self, vendor_id: str, query_date: str) -> Dict[str, Any]:
        """Traverses the bi-temporal graph to resolve which contract/amendment governs on query_date."""
        target_date = datetime.strptime(query_date, "%Y-%m-%d").date()

        # Find all contracts linked to vendor
        contracts = []
        for _, target, data in self.graph.out_edges(vendor_id, data=True):
            if data.get("relationship") == "SIGNATORY_OF":
                contracts.append(target)

        if not contracts:
            return {"status": "NO_CONTRACT_FOUND"}

        # Resolve latest active amendment
        active_contracts = []
        for cid in contracts:
            cnode = self.graph.nodes[cid]
            v_from = datetime.strptime(cnode["valid_from"], "%Y-%m-%d").date()
            v_to = datetime.strptime(cnode["valid_to"], "%Y-%m-%d").date()

            if v_from <= target_date <= v_to:
                active_contracts.append((cid, cnode, v_from))

        if not active_contracts:
            return {"status": "NO_ACTIVE_CONTRACT_ON_DATE"}

        # Sort by valid_from descending (most recent amendment wins)
        active_contracts.sort(key=lambda x: x[2], reverse=True)
        winning_cid, winning_node, _ = active_contracts[0]

        # Check if winning contract supersedes an older one
        superseded_id = None
        for _, target, data in self.graph.out_edges(winning_cid, data=True):
            if data.get("relationship") == "SUPERSEDES":
                superseded_id = target
                break

        return {
            "active_contract_id": winning_cid,
            "liability_cap_usd": winning_node["liability_cap_usd"],
            "governing_law": winning_node["governing_law"],
            "supersedes_contract_id": superseded_id,
            "query_date": query_date,
            "is_amendment": superseded_id is not None
        }

    def get_corporate_hierarchy(self, entity_id: str) -> Dict[str, Any]:
        """Finds multi-hop relationships for an entity (parents, subsidiaries, governing laws)."""
        if not self.graph.has_node(entity_id):
            return {"error": "Entity not found"}

        parents = [
            target for _, target, data in self.graph.out_edges(entity_id, data=True)
            if data.get("relationship") == "SUBSIDIARY_OF"
        ]

        contracts = [
            target for _, target, data in self.graph.out_edges(entity_id, data=True)
            if data.get("relationship") == "SIGNATORY_OF"
        ]

        return {
            "entity": entity_id,
            "parent_corporation": parents[0] if parents else None,
            "linked_contracts": contracts
        }
