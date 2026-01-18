import os
import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from database import Base  # noqa: E402
import models  # Import models module to ensure all models are registered  # noqa: F401, E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


# Get database URL from environment
def get_url():
    """Get database URL from environment or use default."""
    # Check for staging pooler URL first (for better connectivity)
    database_url = os.getenv("STAGING_SUPABASE_POOLER_URL") or os.getenv("DATABASE_URL")

    if not database_url:
        # Default to local development database
        database_url = (
            "postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia"
        )

    # For production/staging, replace postgres:// with postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    return database_url


def process_revision_directives(context, revision, directives):
    """Validate migrations to prevent dangerous operations."""
    # Skip validation if we're creating initial schema (empty database)
    if os.getenv("SKIP_MIGRATION_VALIDATION") == "true":
        return

    # Core business tables that should never be created by autogenerate
    PROTECTED_TABLES = {
        "users",
        "students",
        "classrooms",
        # "schools",  # Removed - being created as part of organization hierarchy
        "programs",
        "lessons",
        "contents",
        "student_assignments",
        "activity_results",
        "classroom_program_mappings",
    }

    if directives and directives[0].upgrade_ops:
        for op in directives[0].upgrade_ops.ops:
            # Check for create table operations
            if hasattr(op, "table_name") and op.__class__.__name__ == "CreateTableOp":
                table_name = op.table_name
                if table_name in PROTECTED_TABLES:
                    raise ValueError(
                        f"🚨 MIGRATION VALIDATION ERROR 🚨\n"
                        f"Migration attempts to create core table '{table_name}' which should already exist.\n"
                        f"This usually indicates:\n"
                        f"1. Model changes without proper migration history\n"
                        f"2. Incorrect autogenerate detection\n"
                        f"3. Database schema drift\n\n"
                        f"Please check:\n"
                        f"- Current database state: alembic current\n"
                        f"- Migration history: alembic history\n"
                        f"- Model definitions in models.py\n\n"
                        f"Consider using: alembic revision -m 'description' (without --autogenerate)\n"
                        f"And manually write the specific changes needed."
                    )

            # Check for suspicious operations on protected tables
            if hasattr(op, "table_name") and op.table_name in PROTECTED_TABLES:
                op_type = op.__class__.__name__
                if op_type in ["DropTableOp"]:
                    raise ValueError(
                        f"🚨 DANGEROUS OPERATION DETECTED 🚨\n"
                        f"Migration attempts to drop core table '{op.table_name}'.\n"
                        f"This would destroy critical business data!\n"
                        f"If this is intentional, manually create the migration."
                    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
