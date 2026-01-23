import uuid
from datetime import datetime
from app import db


class MemberRequest(db.Model):
    __tablename__ = 'member_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    plan = db.Column(
        db.Enum('basic', 'premium', 'vip', name='plan_type'),
        nullable=False
    )
    status = db.Column(
        db.Enum('pending', 'approved', 'rejected', name='request_status'),
        default='pending'
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'plan': self.plan,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'approved_by': self.approved_by,
        }
