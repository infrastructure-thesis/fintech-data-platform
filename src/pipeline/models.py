from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass
class Transaction:
    """Immutable transaction record."""

    id: str
    tenant_id: str
    amount: Decimal
    region: str
    timestamp: datetime

    def validate(self) -> None:
        """Validate transaction fields."""
        if not self.id:
            raise ValueError("Transaction ID cannot be empty")
        if self.amount <= 0:
            raise ValueError("Amount must be positive")
        if self.region not in ["EU", "US", "APAC"]:
            raise ValueError(f"Unknown region: {self.region}")


@dataclass
class AuditLogEntry:
    """Immutable audit log entry."""

    timestamp: datetime
    tenant_id: str
    transaction_id: str
    amount: Decimal
    region: str
    compliance_hash: str
    audit_timestamp: datetime

    @classmethod
    def from_transaction(cls, tx: Transaction, compliance_hash: str) -> "AuditLogEntry":
        """Create audit entry from transaction."""
        return cls(
            timestamp=tx.timestamp,
            tenant_id=tx.tenant_id,
            transaction_id=tx.id,
            amount=tx.amount,
            region=tx.region,
            compliance_hash=compliance_hash,
            audit_timestamp=datetime.now(timezone.utc),
        )
