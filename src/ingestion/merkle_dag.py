"""Merkle DAG Delta Engine for Large Enterprise Documents.

Maintains a cryptographic Merkle Tree of document chunks.
When a 10,000-page document is updated with 10 changed pages, this engine:
1. Identifies the exact modified chunks via SHA-256 diffing.
2. Skips all unmodified chunks, preventing wasteful OCR and re-embedding.
3. Computes the quantifiable cost and compute reduction percentage.
"""

import hashlib
from typing import List, Dict, Tuple
from src.core.models import MerkleChunk, MerkleDiffResult


class MerkleDAGEngine:
    """Enterprise Merkle Tree and Delta Diff Calculator."""

    @staticmethod
    def compute_merkle_root(chunks: List[MerkleChunk]) -> str:
        """Computes the root SHA-256 hash representing the complete document state."""
        if not chunks:
            return hashlib.sha256(b"EMPTY_DOCUMENT").hexdigest()

        # Concatenate sorted chunk hashes to build the Merkle root
        combined_hashes = "".join([c.sha256_hash for c in sorted(chunks, key=lambda x: x.chunk_index)])
        return hashlib.sha256(combined_hashes.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_delta(
        document_id: str,
        old_chunks: List[MerkleChunk],
        new_chunks: List[MerkleChunk]
    ) -> MerkleDiffResult:
        """Diffs new chunks against previous version and returns exact delta instructions."""
        old_hash_map: Dict[str, MerkleChunk] = {c.sha256_hash: c for c in old_chunks}
        old_index_map: Dict[int, MerkleChunk] = {c.chunk_index: c for c in old_chunks}

        unmodified_chunks: List[MerkleChunk] = []
        chunks_to_reindex: List[MerkleChunk] = []
        modified_count = 0
        added_count = 0

        for new_chk in new_chunks:
            # If the exact SHA-256 hash exists in previous version, chunk is UNTOUCHED
            if new_chk.sha256_hash in old_hash_map:
                unmodified_chunks.append(new_chk)
            else:
                # Chunk is modified or newly added
                if new_chk.chunk_index in old_index_map:
                    modified_count += 1
                else:
                    added_count += 1
                chunks_to_reindex.append(new_chk)

        # Detect deleted chunks
        new_indices = {c.chunk_index for c in new_chunks}
        deleted_count = sum(1 for idx in old_index_map if idx not in new_indices)

        total_new = len(new_chunks)
        unmodified_count = len(unmodified_chunks)
        
        # Calculate cost savings percentage
        if total_new > 0:
            savings_pct = (unmodified_count / total_new) * 100.0
        else:
            savings_pct = 0.0

        return MerkleDiffResult(
            document_id=document_id,
            total_chunks_new=total_new,
            unmodified_chunks_count=unmodified_count,
            added_chunks_count=added_count,
            modified_chunks_count=modified_count,
            deleted_chunks_count=deleted_count,
            chunks_to_reindex=chunks_to_reindex,
            cost_reduction_percentage=round(savings_pct, 2)
        )
