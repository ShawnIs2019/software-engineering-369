"""Database models. User matches the abstract User class in the UML."""
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from cems import db

STUDENT = "student"
ORGANIZER = "organizer"
ADMIN = "admin"
ROLES = (STUDENT, ORGANIZER, ADMIN)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=STUDENT)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password: str) -> None:
        """Store only a salted hash, never the plain-text password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"
