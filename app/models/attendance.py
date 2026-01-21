import uuid
from datetime import datetime, date
from app import db


class Attendance(db.Model):
    """Model for tracking gym member check-ins."""
    __tablename__ = 'attendances'

    # Unique identifier for each attendance record.
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Referencing the member who checked in.
    member_id = db.Column(db.String(36), db.ForeignKey('members.id'), nullable=False)
    # Referencing the staff member who processed the check-in.
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    # Timestamp of when the member checked in.
    check_in_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # Timestamp of when this record was created.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'memberId': self.member_id,
            'userId': self.user_id,
            # Format the check-in time as ISO format string if it exists.
            'checkInTime': self.check_in_time.isoformat() if self.check_in_time else None,
            # Retrieve the member's name from the related member object.
            'memberName': self.member.name if self.member else None,
            # Format the creation time as ISO format string if it exists coz it makes sure dates are consistent and not ambiguous.
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def has_checked_in_today(member_id):
        """Check if member has already checked in today."""
        # Get today's date to compare against check-in records.
        today = date.today()
        # Query for any attendance record for this member from today.
        existing = Attendance.query.filter(
            Attendance.member_id == member_id,
            db.func.date(Attendance.check_in_time) == today
        ).first()
        # Return True if the member has already checked in today.
        return existing is not None

    @staticmethod
    def get_member_history(member_id, limit=30):
        """Get member's attendance history."""
        # Queries all attendance records for the member.
        return Attendance.query.filter_by(
            member_id=member_id
        # Makes us start with the most recent check-ins.
        ).order_by(
            Attendance.check_in_time.desc()
        # Limit results to the specified number.
        ).limit(limit).all()

    @staticmethod
    def get_today_attendances():
        """Get all check-ins for today."""
        # Get today's date to filter attendance records.
        today = date.today()
        # Queries all attendance records from today.
        return Attendance.query.filter(
            db.func.date(Attendance.check_in_time) == today
        # Sorts by most recent check-ins first.
        ).order_by(
            Attendance.check_in_time.desc()
        ).all()

    def __repr__(self):
        # Returns a string representation of the attendance record.
        return f'<Attendance {self.member_id} - {self.check_in_time}>'