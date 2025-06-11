#!/usr/bin/env python3
"""
Script to manually add missing columns to the database
"""
import sqlite3
import os

def add_missing_columns():
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'lms.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add columns to user table
        print("Adding columns to user table...")
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN last_login DATETIME")
            print("✓ Added last_login column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ last_login column already exists")
            else:
                print(f"Error adding last_login: {e}")
        
        try:
            cursor.execute("ALTER TABLE user ADD COLUMN login_count INTEGER DEFAULT 0")
            print("✓ Added login_count column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ login_count column already exists")
            else:
                print(f"Error adding login_count: {e}")
        
        # Add columns to student_profile table
        print("Adding columns to student_profile table...")
        columns_to_add = [
            ("phone", "VARCHAR(20)"),
            ("bio", "TEXT"),
            ("student_id", "VARCHAR(50)"),
            ("parent_email", "VARCHAR(120)"),
            ("parent_phone", "VARCHAR(20)")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE student_profile ADD COLUMN {col_name} {col_type}")
                print(f"✓ Added {col_name} column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"✓ {col_name} column already exists")
                else:
                    print(f"Error adding {col_name}: {e}")
        
        # Add columns to instructor_profile table
        print("Adding columns to instructor_profile table...")
        columns_to_add = [
            ("phone", "VARCHAR(20)"),
            ("department", "VARCHAR(100)"),
            ("office_location", "VARCHAR(100)"),
            ("office_hours", "VARCHAR(100)"),
            ("specialization", "VARCHAR(200)")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE instructor_profile ADD COLUMN {col_name} {col_type}")
                print(f"✓ Added {col_name} column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"✓ {col_name} column already exists")
                else:
                    print(f"Error adding {col_name}: {e}")
        
        # Add columns to course table
        print("Adding columns to course table...")
        columns_to_add = [
            ("code", "VARCHAR(20)"),
            ("category", "VARCHAR(50)"),
            ("level", "VARCHAR(20)"),
            ("max_students", "INTEGER DEFAULT 50"),
            ("start_date", "DATE"),
            ("end_date", "DATE"),
            ("meeting_days", "VARCHAR(100)"),
            ("meeting_time", "TIME"),
            ("syllabus", "TEXT"),
            ("prerequisites", "TEXT"),
            ("learning_outcomes", "TEXT"),
            ("is_active", "BOOLEAN DEFAULT 1"),
            ("allow_enrollment", "BOOLEAN DEFAULT 1"),
            ("enable_quizzes", "BOOLEAN DEFAULT 1"),
            ("enable_assignments", "BOOLEAN DEFAULT 1")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE course ADD COLUMN {col_name} {col_type}")
                print(f"✓ Added {col_name} column")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"✓ {col_name} column already exists")
                else:
                    print(f"Error adding {col_name}: {e}")
        
        # Add columns to assignment table
        print("Adding columns to assignment table...")
        try:
            cursor.execute("ALTER TABLE assignment ADD COLUMN is_active BOOLEAN DEFAULT 1")
            print("✓ Added is_active column to assignment")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ is_active column already exists in assignment")
            else:
                print(f"Error adding is_active to assignment: {e}")
        
        # Add columns to quiz table
        print("Adding columns to quiz table...")
        try:
            cursor.execute("ALTER TABLE quiz ADD COLUMN is_active BOOLEAN DEFAULT 1")
            print("✓ Added is_active column to quiz")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("✓ is_active column already exists in quiz")
            else:
                print(f"Error adding is_active to quiz: {e}")
        
        # Create assignment_submission table if it doesn't exist
        print("Creating assignment_submission table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assignment_submission (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assignment_id INTEGER,
                student_id INTEGER,
                submitted_at DATETIME,
                file_path VARCHAR(500),
                comments TEXT,
                grade FLOAT,
                feedback TEXT,
                FOREIGN KEY (assignment_id) REFERENCES assignment (id),
                FOREIGN KEY (student_id) REFERENCES user (id)
            )
        """)
        print("✓ Created assignment_submission table")
        
        # Create material table if it doesn't exist
        print("Creating material table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS material (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                title VARCHAR(100),
                description TEXT,
                file_path VARCHAR(500),
                file_type VARCHAR(50),
                uploaded_at DATETIME,
                FOREIGN KEY (course_id) REFERENCES course (id)
            )
        """)
        print("✓ Created material table")
        
        # Commit all changes
        conn.commit()
        print("\n✅ Database updated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_missing_columns() 