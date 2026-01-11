"""
Seed data for Duotopia - Backward Compatibility Layer

This file maintains backward compatibility for any code that imports from seed_data.py.
The actual implementation has been refactored into the seed_data/ module for better maintainability.

To use:
    from seed_data import create_demo_data, seed_template_programs, reset_database

Or:
    import seed_data
    seed_data.create_demo_data(db)
"""

# Import all public functions from the refactored module
from seed_data import create_demo_data, seed_template_programs, reset_database

__all__ = ["create_demo_data", "seed_template_programs", "reset_database"]


if __name__ == "__main__":
    # When run directly, execute reset_database
    reset_database()
