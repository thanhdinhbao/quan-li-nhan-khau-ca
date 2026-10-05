import sqlite3
from database.db_manager import DatabaseManager
from utils.logger import log_info, log_error

class MigrationManager:
    @staticmethod
    def run_migrations():
        """Ensures all tables and schema updates are applied."""
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            # Create migrations tracking table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

            # Define migrations
            migrations = [
                (1, "Initial Schema Setup", MigrationManager._v1_init)
            ]

            for ver, desc, func in migrations:
                cursor.execute("SELECT version FROM schema_migrations WHERE version = ?", (ver,))
                if not cursor.fetchone():
                    log_info(f"Applying schema migration v{ver}: {desc}")
                    func(conn)
                    cursor.execute("INSERT INTO schema_migrations (version, description) VALUES (?, ?)", (ver, desc))
                    conn.commit()
        except Exception as e:
            conn.rollback()
            log_error(f"Migration error: {e}", exc_info=True)
            raise e
        finally:
            conn.close()

    @staticmethod
    def _v1_init(conn):
        # DatabaseManager constructor already executes schema.sql
        pass
