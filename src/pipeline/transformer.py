from src.audit.encryption import ComplianceHasher
from src.pipeline.models import AuditLogEntry, Transaction


class SettlementTransformer:
    """Transform transactions into audit log entries."""

    @staticmethod
    def transform(transaction: Transaction) -> AuditLogEntry:
        """Convert Transaction to AuditLogEntry with compliance hash."""
        # Validate transaction
        transaction.validate()

        # Compute compliance hash
        tx_data = {
            "id": transaction.id,
            "tenant_id": transaction.tenant_id,
            "amount": str(transaction.amount),
            "timestamp": transaction.timestamp.isoformat(),
        }
        compliance_hash = ComplianceHasher.compute_hash(tx_data)

        # Create audit entry
        return AuditLogEntry.from_transaction(transaction, compliance_hash)
