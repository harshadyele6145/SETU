import logging
from sqlalchemy import text
from backend.app.core.database import engine

logger = logging.getLogger("setu.migrations")


def run_schema_migrations():
    """
    Ensures newly added columns and tables are present across both SQLite and PostgreSQL.
    Safely executes non-destructive DDL additions if columns are missing.
    """
    is_sqlite = engine.dialect.name == "sqlite"
    timestamp_default = "'2026-10-26 00:00:00'" if is_sqlite else "CURRENT_TIMESTAMP"
    bool_default = "0" if is_sqlite else "FALSE"

    try:
        with engine.connect() as conn:
            # 1. Institutions provenance columns
            for col, col_type, default_val in [
                ("source_system", "VARCHAR(50)", "'SETU_OPERATIONAL'"),
                ("external_id", "VARCHAR(100)", "NULL"),
                ("source_record_version", "VARCHAR(50)", "NULL"),
                ("source_updated_at", "TIMESTAMP", "NULL"),
                ("synced_at", "TIMESTAMP", timestamp_default),
                ("sync_status", "VARCHAR(50)", "'SYNCED'"),
                ("is_synthetic", "BOOLEAN", bool_default),
                ("last_sync_error", "TEXT", "NULL")
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE institutions ADD COLUMN {col} {col_type} DEFAULT {default_val}"))
                    conn.commit()
                    logger.info(f"Added column {col} to institutions table.")
                except Exception:
                    # Column already exists or table not yet created
                    pass

            # 2. Applications provenance columns
            for col, col_type, default_val in [
                ("source_system", "VARCHAR(50)", "'SETU_OPERATIONAL'"),
                ("external_id", "VARCHAR(100)", "NULL"),
                ("source_record_version", "VARCHAR(50)", "NULL"),
                ("source_updated_at", "TIMESTAMP", "NULL"),
                ("synced_at", "TIMESTAMP", timestamp_default),
                ("sync_status", "VARCHAR(50)", "'SYNCED'"),
                ("is_synthetic", "BOOLEAN", bool_default),
                ("last_sync_error", "TEXT", "NULL")
            ]:
                try:
                    conn.execute(text(f"ALTER TABLE applications ADD COLUMN {col} {col_type} DEFAULT {default_val}"))
                    conn.commit()
                    logger.info(f"Added column {col} to applications table.")
                except Exception:
                    # Column already exists or table not yet created
                    pass

            logger.info("Schema migrations check completed.")
    except Exception as e:
        logger.warning(f"Schema migration warning: {e}")
