import uuid
from datetime import datetime, date
from app import db


class Attendance(db.Model):
    __tablename__ = 'attendances'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = db.Column(db.String(36), db.ForeignKey('members.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    check_in_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'memberId': self.member_id,
            'userId': self.user_id,
            'checkInTime': self.check_in_time.isoformat() if self.check_in_time else None,
            'memberName': self.member.name if self.member else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def has_checked_in_today(member_id):
        """Check if member has already checked in today."""
        today = date.today()
        existing = Attendance.query.filter(
            Attendance.member_id == member_id,
            db.func.date(Attendance.check_in_time) == today
        ).first()
        return existing is not None

    @staticmethod
    def get_member_history(member_id, limit=30):
        """Get member's attendance history."""
        return Attendance.query.filter_by(
            member_id=member_id
        ).order_by(
            Attendance.check_in_time.desc()
        ).limit(limit).all()

    @staticmethod
    def get_today_attendances():
        """Get all check-ins for today."""
        today = date.today()
        return Attendance.query.filter(
            db.func.date(Attendance.check_in_time) == today
        ).order_by(
            Attendance.check_in_time.desc()
        ).all()

    def __repr__(self):
        return f'<Attendance {self.member_id} - {self.check_in_time}>'