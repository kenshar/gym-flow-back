#!/usr/bin/env python
"""Initialize database tables."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db
    
    print("🔧 Initializing database...")
    
    app = create_app('development')
    
    with app.app_context():
        print("📋 Creating all tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # List tables created
        from app.models import User, Member, Attendance, Workout
        print("\n📊 Tables created:")
        print("   ✅ users")
        print("   ✅ members")
        print("   ✅ attendances")
        print("   ✅ workouts")
        
        print("\n💡 You can now:")
        print("   1. Start the backend: python run.py")
        print("   2. Register a new user via the frontend")
        print("   3. Login with your credentials")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
