"""
Seed data for Duotopia - Modular structure
建立完整的 Demo 資料：教師、學生、班級、課程、作業
覆蓋所有作業系統情境（教師端和學生端）

Refactored into modular stages for better maintainability.
"""

from .seed_main import create_demo_data, seed_template_programs, reset_database

__all__ = ["create_demo_data", "seed_template_programs", "reset_database"]
