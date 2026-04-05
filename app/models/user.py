import enum
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class RoleEnum(str, enum.Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class User(db.Model):
    """
    Represents a system user with role-based access control.

    Roles:
        - viewer: Read-only access to records and dashboard basics.
        - analyst: Read access + dashboard insights and trends.
        - admin: Full CRUD access to records and user management.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.viewer)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)  # soft delete

    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Relationship: records created by this user
    records = db.relationship(
        "FinancialRecord", backref="creator", lazy="dynamic", foreign_keys="FinancialRecord.created_by_id"
    )

    #  Password helpers
    def set_password(self, plain_password: str) -> None:
        """Hash and store the password."""
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        """Verify a plain-text password against the stored hash."""
        return check_password_hash(self.password_hash, plain_password)

    #  Role helpers
    def is_admin(self) -> bool:
        return self.role == RoleEnum.admin

    def is_analyst(self) -> bool:
        return self.role in (RoleEnum.analyst, RoleEnum.admin)

    def is_viewer(self) -> bool:
        return True  # all roles can view

    #  Soft delete
    def soft_delete(self) -> None:
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = datetime.now(timezone.utc)

    #  Serialisation
    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_sensitive:
            data["is_deleted"] = self.is_deleted
            data["deleted_at"] = self.deleted_at.isoformat() if self.deleted_at else None
        return data

    def __repr__(self) -> str:
        return f"<User {self.username!r} role={self.role.value}>"
