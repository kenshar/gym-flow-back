import uuid
from datetime import datetime
from app import db


class Attendance(db.Model):
    __tablename__ = 'attendances'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = db.Column(db.String(36), db.ForeignKey('members.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    check_in_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # in minutes
    notes = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_duration(self):
        """Calculate duration when checking out."""
        if self.check_out_time and self.check_in_time:
            diff = self.check_out_time - self.check_in_time
            self.duration = int(diff.total_seconds() / 60)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'memberId': self.member_id,
            'userId': self.user_id,
            'checkInTime': self.check_in_time.isoformat() if self.check_in_time else None,
            'checkOutTime': self.check_out_time.isoformat() if self.check_out_time else None,
            'duration': self.duration,
            'notes': self.notes,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict_with_member(self):
        """Convert to dictionary including member info."""
        data = self.to_dict()
        if self.member:
            data['member'] = {
                'name': self.member.name,
                'email': self.member.email
            }
        return data

    def __repr__(self):
        return f'<Attendance {self.id}>'
