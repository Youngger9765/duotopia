#!/usr/bin/env python
"""
Re-initialize staging database with new seed data
"""
import os
import sys
from sqlalchemy import text
from database import SessionLocal, engine
import models
from db_init import DatabaseInitializer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_database(db):
    """Clear all data from database"""
    logger.info("🗑️  Clearing existing data...")
    
    # Clear in correct order to avoid foreign key constraints
    db.query(models.ActivityResult).delete()
    db.query(models.StudentAssignment).delete()
    db.query(models.Lesson).delete()
    db.query(models.ClassroomCourseMapping).delete()
    db.query(models.ClassroomStudent).delete()
    db.query(models.Course).delete()
    db.query(models.Classroom).delete()
    db.query(models.Student).delete()
    db.query(models.User).delete()
    db.query(models.School).delete()
    db.commit()
    
    logger.info("✅ Database cleared")

def main():
    """Re-initialize staging database"""
    # Make sure we're in staging environment
    os.environ["ENVIRONMENT"] = "staging"
    
    logger.info("🚀 Re-initializing staging database...")
    
    db = SessionLocal()
    try:
        # Clear existing data
        clear_database(db)
        
        # Run seed data
        from seed_staging import create_staging_data
        create_staging_data(db)
        
        logger.info("✅ Staging database re-initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()