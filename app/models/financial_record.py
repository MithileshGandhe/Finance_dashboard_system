import enum
from datetime import datetime, timezone
from app.extensions import db


class RecordTypeEnum(str, enum.Enum):
    income = "income"
    expense = "expense"


class FinancialRecord(db.Model):
    """
    Represents a single financial transaction/entry.

    Fields mirror typical bookkeeping: amount, type (income/expense),
    category, date of the transaction, and optional notes.
    Soft-delete is supported via `is_deleted` / `deleted_at`.
    """

    __tablename__ = "financial_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Core financial fields
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    record_type = db.Column(db.Enum(RecordTypeEnum), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    record_date = db.Column(db.Date, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    # Audit / ownership
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Soft delete
    is_deleted = db.Column(db.Boolean, nullable=False, default=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    #  Soft delete
    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)

    #  Serialisation
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": float(self.amount),
            "record_type": self.record_type.value,
            "category": self.category,
            "record_date": self.record_date.isoformat(),
            "description": self.description,
            "created_by_id": self.created_by_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<FinancialRecord id={self.id} type={self.record_type.value} amount={self.amount}>"
