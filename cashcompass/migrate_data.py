import sqlite3
import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
from datetime import datetime, date # Import date for handling Date objects

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
SQLITE_DB_PATH = 'budget.db' # Path to your existing SQLite database file
POSTGRES_DATABASE_URL = os.getenv("DATABASE_URL")

# Define the tables to migrate and their column names
# IMPORTANT: These column names now precisely match your SQLite schema and the PostgreSQL DDL.
TABLE_SCHEMAS = {
    "users": ["id", "username", "password_hash", "email", "created_at"],
    "income": ["id", "user_id", "source", "amount", "date"],
    "expenses": ["id", "user_id", "category", "amount", "date"],
    "budget": ["id", "user_id", "category", "amount", "date"],
    "savings": ["id", "user_id", "goal", "amount", "date", "target_amount"],
    "debt": [
        "id", "user_id", "debt_name", "debt_type", "original_amount",
        "current_balance", "interest_rate", "minimum_payment", "due_date",
        "start_date", "end_date", "lender", "notes"
    ],
    "read_user_alerts": ["user_id", "alert_hash", "read_at"],
}

# --- Connection Functions ---
def connect_sqlite(db_path):
    """Connects to the SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        print(f"Connected to SQLite database: {db_path}")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to SQLite: {e}")
        return None

def connect_postgres(db_url):
    """Connects to the PostgreSQL database."""
    try:
        url = urlparse(db_url)
        conn = psycopg2.connect(
            database=url.path[1:], # remove leading '/'
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        conn.autocommit = False # We'll manage transactions manually
        print(f"Connected to PostgreSQL database: {url.path[1:]}")
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None

# --- Data Migration Function ---
def migrate_data():
    """Migrates data from SQLite to PostgreSQL."""
    sqlite_conn = None
    pg_conn = None
    try:
        # 1. Connect to databases
        sqlite_conn = connect_sqlite(SQLITE_DB_PATH)
        if not sqlite_conn:
            print("Failed to connect to SQLite. Exiting.")
            return

        pg_conn = connect_postgres(POSTGRES_DATABASE_URL)
        if not pg_conn:
            print("Failed to connect to PostgreSQL. Exiting.")
            return

        pg_cur = pg_conn.cursor()

        # 2. Iterate through tables and migrate data
        for table_name, columns in TABLE_SCHEMAS.items():
            print(f"\n--- Migrating data for table: {table_name} ---")
            sqlite_cur = sqlite_conn.cursor()

            try:
                # Fetch data from SQLite
                sqlite_cur.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
                rows = sqlite_cur.fetchall()

                if not rows:
                    print(f"No data found in SQLite table '{table_name}'. Skipping.")
                    continue

                # Prepare INSERT statement for PostgreSQL
                placeholders = ', '.join(['%s'] * len(columns)) # PostgreSQL uses %s placeholders
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

                # Execute inserts into PostgreSQL
                inserted_count = 0
                for row in rows:
                    data = list(row) # Convert Row object to list

                    processed_data = []
                    for col_name, value in zip(columns, data):
                        # Convert date/datetime strings to datetime/date objects for PostgreSQL
                        if 'date' in col_name and value:
                            try:
                                # SQLite's DATETIME and TIMESTAMP often store as 'YYYY-MM-DD HH:MM:SS'
                                # SQLite's DATE often stores as 'YYYY-MM-DD'
                                # SQLite's TEXT DEFAULT CURRENT_TIMESTAMP for 'date' in income/savings can be 'YYYY-MM-DD HH:MM:SS'
                                if len(value) >= 19 and '-' in value and ':' in value: # YYYY-MM-DD HH:MM:SS
                                    processed_data.append(datetime.strptime(value, '%Y-%m-%d %H:%M:%S'))
                                elif len(value) == 10 and '-' in value: # YYYY-MM-DD
                                    processed_data.append(datetime.strptime(value, '%Y-%m-%d').date()) # Store as date object
                                else:
                                    processed_data.append(value) # Keep as is if unparsable date format
                            except (ValueError, TypeError) as e:
                                print(f"  Warning: Could not parse date value '{value}' for column '{col_name}'. Keeping as is. Error: {e}")
                                processed_data.append(value)
                        # Ensure numeric values are floats/decimals for PostgreSQL NUMERIC columns
                        elif col_name in ['amount', 'current_balance', 'original_amount',
                                          'interest_rate', 'minimum_payment', 'target_amount']:
                            try:
                                processed_data.append(float(value) if value is not None else None)
                            except (ValueError, TypeError) as e:
                                print(f"  Warning: Could not convert numeric value '{value}' for column '{col_name}' to float. Keeping as is. Error: {e}")
                                processed_data.append(value)
                        else:
                            processed_data.append(value)

                    try:
                        pg_cur.execute(insert_sql, processed_data)
                        inserted_count += 1
                    except psycopg2.IntegrityError as e:
                        # Handle duplicate key errors (e.g., for 'users' table 'id' or 'username')
                        # or other constraint violations.
                        print(f"  Warning: Skipped row due to IntegrityError (e.g., duplicate key, data type mismatch, or null violation) in {table_name}: {e}")
                        pg_conn.rollback() # Rollback the problematic statement, but continue with others
                    except Exception as e:
                        print(f"  Error inserting row into {table_name}: {e}")
                        pg_conn.rollback() # Rollback current transaction on other errors
                        raise # Re-raise to stop migration for this table if critical

                pg_conn.commit() # Commit after each table is successfully migrated
                print(f"Successfully inserted {inserted_count} rows into '{table_name}'.")

            except Exception as e:
                print(f"Error migrating table '{table_name}': {e}")
                pg_conn.rollback() # Ensure rollback if an error occurs for the whole table
                print("Transaction rolled back for current table.")
                # You might want to break here if one table's failure should stop all migration
                # For now, it will try the next table.

    except Exception as e:
        print(f"An unexpected error occurred during migration: {e}")
        if pg_conn:
            pg_conn.rollback() # Final rollback if something goes wrong overall
            print("PostgreSQL transaction rolled back.")
    finally:
        # Close connections
        if sqlite_conn:
            sqlite_conn.close()
            print("SQLite connection closed.")
        if pg_conn:
            pg_conn.close()
            print("PostgreSQL connection closed.")

if __name__ == "__main__":
    print("Starting data migration from SQLite to PostgreSQL...")
    migrate_data()
    print("\nMigration process completed.")
