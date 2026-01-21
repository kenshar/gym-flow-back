#!/usr/bin/env python
"""Seed database with initial data."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.member import Member

def seed_database():
    """Create initial admin user and sample data."""

    env = os.getenv('FLASK_ENV', 'production')
    app = create_app(env)

    with app.app_context():
        # Create tables if they don't exist
        db.create_all()

        # Check if admin already exists
        admin = User.query.filter_by(email='admin@example.com').first()

        if not admin:
            print("Creating admin user...")
            admin = User(
                name='Admin User',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('password123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin@example.com / password123")
        else:
            print("Admin user already exists")

        # Create a sample member if none exist
        member_count = Member.query.count()
        if member_count == 0:
            print("Creating sample member...")
            member = Member(
                name='John Doe',
                email='john@example.com',
                phone='555-0100',
                membership_type='basic',
                membership_status='active'
            )
            db.session.add(member)
            db.session.commit()
            print("Sample member created")
        else:
            print(f"Members already exist: {member_count}")

        print("Database seeding complete!")

if __name__ == '__main__':
    seed_database()
