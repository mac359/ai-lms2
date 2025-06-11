#!/usr/bin/env python3
"""
Script to create an admin user for the LMS system.
Run this script once to set up the admin account.
"""

import os
import sys
from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

def create_admin_user():
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = User.query.filter_by(email='admin@example.com').first()
        if existing_admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_active=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Admin user created successfully!")
        print("📧 Email: admin@example.com")
        print("🔑 Password: admin123")
        print("🌐 Login URL: http://localhost:5000/admin/login")

if __name__ == '__main__':
    create_admin_user() 