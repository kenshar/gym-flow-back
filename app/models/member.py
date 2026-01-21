"""
Member Model - Core Business Entity
====================================
Purpose: Manages gym member profiles with membership tracking.

Implemented:
  Member profile and contact information
  Membership status (active/inactive/expired/suspended)
  Membership type (basic/premium/vip) with dates
  Emergency contact fields
  Relationships to Attendance & Workouts

Logic Flow - Branches to:
  ← members.py receives: CRUD operations
  ← admin_reports.py queries: for active/inactive stats
  → attendance.py uses: member_id for check-ins
  → workouts.py uses: member_id for assignments
  → reports.py uses: member activity data

Data Chain:
  User creates/manages Members → Members check in (Attendance) 
  → Members assigned to Workouts → Data aggregated in Reports
"""

import uuid
from datetime import datetime
from app import db


class Member(db.Model):
    __tablename__ = 'members'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(20))
    membership_type = db.Column(
        db.Enum('basic', 'premium', 'vip', name='membership_type'),
        default='basic'
    )
    membership_status = db.Column(
        db.Enum('active', 'inactive', 'expired', 'suspended', name='membership_status'),
        default='active'
    )
    membership_start_date = db.Column(db.DateTime, default=datetime.utcnow)
    membership_end_date = db.Column(db.DateTime)
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relationship = db.Column(db.String(50))
    notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    attendances = db.relationship('Attendance', backref='member', lazy='dynamic')
    workouts = db.relationship('Workout', backref='member', lazy='dynamic')

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'userId': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'membershipType': self.membership_type,
            'membershipStatus': self.membership_status,
            'membershipStartDate': self.membership_start_date.isoformat() if self.membership_start_date else None,
            'membershipEndDate': self.membership_end_date.isoformat() if self.membership_end_date else None,
            'emergencyContactName': self.emergency_contact_name,
            'emergencyContactPhone': self.emergency_contact_phone,
            'emergencyContactRelationship': self.emergency_contact_relationship,
            'notes': self.notes,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Member {self.name}>'
