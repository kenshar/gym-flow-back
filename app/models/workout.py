import uuid
from datetime import datetime
from app import db


class Workout(db.Model):
    __tablename__ = 'workouts'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    member_id = db.Column(db.String(36), db.ForeignKey('members.id'))
    type = db.Column(
        db.Enum(
            'Strength Training', 'Cardio', 'HIIT', 'Yoga',
            'Pilates', 'Swimming', 'CrossFit', 'Other',
            name='workout_type'
        ),
        nullable=False
    )
    name = db.Column(db.String(100))
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    calories = db.Column(db.Integer)
    intensity = db.Column(
        db.Enum('low', 'medium', 'high', name='workout_intensity'),
        default='medium'
    )
    exercises = db.Column(db.JSON, default=[])
    notes = db.Column(db.String(500))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'userId': self.user_id,
            'memberId': self.member_id,
            'member': self.member.to_dict() if getattr(self, 'member', None) else None,
            'type': self.type,
            'name': self.name,
            'duration': self.duration,
            'calories': self.calories,
            'intensity': self.intensity,
            'exercises': self.exercises,
            'notes': self.notes,
            'date': self.date.isoformat() if self.date else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Workout {self.name}>'
