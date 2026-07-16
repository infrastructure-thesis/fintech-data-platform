import hashlib
from typing import Dict


class ComplianceHasher:
    """Generates immutable compliance hashes for audit trails."""

    @staticmethod
    def compute_hash(transaction_data: Dict[str, str]) -> str:
        """Compute SHA256 hash for audit proof."""
        parts = [
            transaction_data.get("id", ""),
            transaction_data.get("tenant_id", ""),
            transaction_data.get("amount", ""),
            transaction_data.get("timestamp", ""),
        ]
        content = "|".join(parts)
        return hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def verify_hash(
        transaction_data: Dict[str, str], provided_hash: str
    ) -> bool:
        """Verify that hash matches transaction data."""
        computed_hash = ComplianceHasher.compute_hash(transaction_data)
        return computed_hash == provided_hash
