#!/usr/bin/env python
"""
Database initialization and seed data management
"""
import os
import sys
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging
from database import SessionLocal, engine
import models
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseInitializer:
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.db = SessionLocal()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
    
    def run_migrations(self):
        """Run pending database migrations"""
        try:
            logger.info("Running database migrations...")
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("✅ Migrations completed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
    
    def is_database_initialized(self) -> bool:
        """Check if database has been initialized with basic data"""
        try:
            # Check if we have any users
            user_count = self.db.query(models.User).count()
            student_count = self.db.query(models.Student).count()
            
            logger.info(f"Current database state: {user_count} users, {student_count} students")
            
            # If we have users or students, consider it initialized
            return user_count > 0 or student_count > 0
        except Exception as e:
            logger.warning(f"Error checking database state: {e}")
            # If tables don't exist, they'll be created by migrations
            return False
    
    def seed_system_data(self):
        """Seed essential system data for all environments"""
        logger.info("Seeding system data...")
        
        try:
            # Add any system-wide configuration or default data here
            # For example: default roles, system settings, etc.
            
            # Check if we need to create a system admin
            admin = self.db.query(models.User).filter_by(email="admin@duotopia.com").first()
            if not admin:
                from auth import get_password_hash
                admin = models.User(
                    id=str(models.uuid.uuid4()),
                    email="admin@duotopia.com",
                    full_name="System Administrator",
                    hashed_password=get_password_hash("DuotopiaAdmin2024"),
                    role=models.UserRole.ADMIN,
                    is_active=True
                )
                self.db.add(admin)
                self.db.commit()
                logger.info("✅ Created system administrator account")
                
        except Exception as e:
            logger.error(f"Error seeding system data: {e}")
            self.db.rollback()
            raise
    
    def seed_test_data(self):
        """Seed test data for staging/development environments"""
        if self.environment == "production":
            logger.warning("⚠️  Skipping test data seeding in production environment")
            return
            
        logger.info(f"Seeding test data for {self.environment} environment...")
        
        try:
            if self.environment == "staging":
                # Use minimal staging data
                from seed_staging import create_staging_data
                create_staging_data(self.db)
            else:
                # Use full test data for development
                from seed import create_test_data
                create_test_data(self.db)
            
            logger.info("✅ Test data seeded successfully")
        except Exception as e:
            logger.error(f"Error seeding test data: {e}")
            self.db.rollback()
            raise
    
    def initialize(self):
        """Main initialization flow"""
        logger.info(f"🚀 Starting database initialization for {self.environment} environment...")
        
        try:
            # Step 1: Run migrations
            self.run_migrations()
            
            # Step 2: Check if database is already initialized
            if self.is_database_initialized():
                logger.info("ℹ️  Database already initialized, skipping seed data")
                return
            
            # Step 3: Seed system data (all environments)
            self.seed_system_data()
            
            # Step 4: Seed test data (non-production only)
            if self.environment in ["development", "staging"]:
                self.seed_test_data()
            
            logger.info("✅ Database initialization completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

def main():
    """Run database initialization"""
    with DatabaseInitializer() as initializer:
        initializer.initialize()

if __name__ == "__main__":
    main()