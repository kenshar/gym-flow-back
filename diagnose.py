#!/usr/bin/env python
"""Quick diagnostic script to test backend connectivity."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db
    from app.models import User
    
    print("✅ Imports successful")
    
    app = create_app('development')
    
    with app.app_context():
        print("✅ App context created")
        
        # Check database
        try:
            result = db.session.execute("SELECT 1")
            print("✅ Database connection OK")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            
        # Check if users table exists
        try:
            user_count = db.session.query(User).count()
            print(f"✅ Users table OK - {user_count} users found")
        except Exception as e:
            print(f"❌ Users table error: {e}")
            
        # List all users
        try:
            users = db.session.query(User).all()
            print(f"\n📋 Registered users:")
            for user in users:
                print(f"   - {user.email} (role: {user.role})")
            if not users:
                print("   (none - you need to register first)")
        except Exception as e:
            print(f"❌ Error listing users: {e}")
            
except Exception as e:
    print(f"❌ Startup failed: {e}")
    import traceback
    traceback.print_exc()
