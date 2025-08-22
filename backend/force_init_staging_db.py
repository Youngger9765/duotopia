#!/usr/bin/env python
"""
Force initialize staging database with test data
"""
import os
import sys

# Set environment to staging
os.environ["ENVIRONMENT"] = "staging"
os.environ["DATABASE_URL"] = "postgresql://duotopia_user:DuotopiaStaging2024@35.221.172.134:5432/duotopia"

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from seed_staging import create_staging_data
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_init_staging():
    """Force initialize staging database with test data"""
    db = SessionLocal()
    
    try:
        # Check current state
        user_count = db.query(models.User).count()
        student_count = db.query(models.Student).count()
        
        logger.info(f"Current database state: {user_count} users, {student_count} students")
        
        if user_count == 0 and student_count == 0:
            logger.info("Database is empty, creating staging data...")
            create_staging_data(db)
            
            # Verify data was created
            user_count = db.query(models.User).count()
            student_count = db.query(models.Student).count()
            school_count = db.query(models.School).count()
            classroom_count = db.query(models.Classroom).count()
            course_count = db.query(models.Course).count()
            lesson_count = db.query(models.Lesson).count()
            
            logger.info(f"\n✅ Staging data created successfully!")
            logger.info(f"  - {user_count} users")
            logger.info(f"  - {student_count} students")
            logger.info(f"  - {school_count} schools")
            logger.info(f"  - {classroom_count} classrooms")
            logger.info(f"  - {course_count} courses")
            logger.info(f"  - {lesson_count} lessons")
            
            # List test accounts
            logger.info("\n📋 Test Accounts:")
            logger.info("  Admin: admin@duotopia.com / DuotopiaAdmin2024")
            logger.info("  Teacher: demo@duotopia.com / DemoTeacher2024")
            logger.info("  Students: student1-5@demo.duotopia.com / 20100101")
            
        else:
            logger.info("Database already has data, skipping initialization")
            
            # List existing users
            users = db.query(models.User).all()
            logger.info(f"\nExisting users:")
            for user in users:
                logger.info(f"  - {user.email} ({user.role})")
                
            # List existing students
            students = db.query(models.Student).limit(5).all()
            logger.info(f"\nExisting students (first 5):")
            for student in students:
                logger.info(f"  - {student.email}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    force_init_staging()