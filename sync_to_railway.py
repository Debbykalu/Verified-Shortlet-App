import mysql.connector
import os
import sys
import re

def parse_mysql_url(url):
    """
    Parses a mysql connection string in format:
    mysql://user:password@host:port/database
    or mysql+mysqlconnector://user:password@host:port/database
    """
    pattern = r"^mysql(?:\+mysqlconnector)?://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)$"
    match = re.match(pattern, url)
    if not match:
        raise ValueError(
            "Invalid connection string format. Expected: mysql://user:password@host:port/database"
        )
    user, password, host, port, database = match.groups()
    return {
        'user': user,
        'password': password,
        'host': host,
        'port': int(port),
        'database': database
    }

def sync_database():
    print("====================================================")
    print("Verified Shortlet Database Sync Utility")
    print("====================================================")
    
    # 1. Get Railway Database URL
    railway_url = os.getenv("RAILWAY_DATABASE_URL") or os.getenv("DATABASE_URL")
    
    if not railway_url:
        if len(sys.argv) > 1:
            railway_url = sys.argv[1]
        else:
            print("Error: Railway database connection URL not found.")
            print("\nPlease provide the Railway Database URL as an environment variable or argument.")
            print("Example:")
            print("  python sync_to_railway.py mysql://root:password@host:port/database")
            print("\nYou can find this URL in your Railway dashboard under your MySQL service -> Variables -> DATABASE_URL or MYSQL_URL.")
            return

    try:
        dest_config = parse_mysql_url(railway_url)
    except Exception as e:
        print(f"Error parsing Railway URL: {e}")
        return

    # 2. Source database (local Windows MySQL server on port 3306)
    src_config = {
        'user': 'root',
        'password': '',
        'host': 'localhost',
        'database': 'shortletdb',
        'port': 3306
    }
    
    print("\nConnecting to local source database...")
    try:
        src_conn = mysql.connector.connect(**src_config)
        src_cursor = src_conn.cursor(dictionary=True)
        print("Success: Connected to local source database.")
    except Exception as e:
        print(f"Failed to connect to local database: {e}")
        print("Make sure your local MySQL server is running on port 3306.")
        return

    print("\nConnecting to Railway target database...")
    try:
        # Disable SSL warnings or verify depending on client
        dest_conn = mysql.connector.connect(**dest_config)
        dest_cursor = dest_conn.cursor()
        print("Success: Connected to Railway target database.")
    except Exception as e:
        print(f"Failed to connect to Railway database: {e}")
        src_cursor.close()
        src_conn.close()
        return

    # Get tables
    src_cursor.execute("SHOW TABLES")
    tables = [list(row.values())[0] for row in src_cursor.fetchall()]
    
    print(f"\nFound {len(tables)} tables to synchronize.")
    
    try:
        print("\nDisabling foreign key checks on Railway database...")
        dest_cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        # Alter columns on Railway to match local nullability requirements (models.py specifies nullable=True)
        print("Ensuring table schemas match Flask models (making booking_payments.booking_userid nullable)...")
        try:
            dest_cursor.execute("ALTER TABLE `booking_payments` MODIFY `booking_userid` INT NULL;")
        except Exception as alter_err:
            print(f"Warning: Could not alter table (might not exist yet or already altered): {alter_err}")

        for table in tables:
            if table == 'alembic_version':
                print("Setting alembic_version on Railway to 'f8a62e97f830'...", end="", flush=True)
                dest_cursor.execute("TRUNCATE TABLE `alembic_version`")
                dest_cursor.execute("INSERT INTO `alembic_version` (`version_num`) VALUES ('f8a62e97f830')")
                print(" (Set to codebase HEAD)")
                continue

            print(f"Synchronizing table: {table} ...", end="", flush=True)
            
            # Fetch data from source
            src_cursor.execute(f"SELECT * FROM `{table}`")
            rows = src_cursor.fetchall()
            
            # Truncate target table
            dest_cursor.execute(f"TRUNCATE TABLE `{table}`")
            
            if not rows:
                print(" (0 rows copied - empty)")
                continue
                
            columns = list(rows[0].keys())
            cols_str = ", ".join([f"`{col}`" for col in columns])
            placeholders = ", ".join(["%s"] * len(columns))
            
            insert_query = f"INSERT INTO `{table}` ({cols_str}) VALUES ({placeholders})"
            
            # Extract row values
            values = []
            for row in rows:
                row_vals = []
                for col in columns:
                    val = row[col]
                    row_vals.append(val)
                values.append(row_vals)
                
            # Insert values in batch
            dest_cursor.executemany(insert_query, values)
            print(f" ({len(values)} rows copied)")
            
        print("\nEnabling foreign key checks on Railway database...")
        dest_cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        dest_conn.commit()
        print("\n====================================================")
        print("Synchronization completed successfully!")
        print("====================================================")
        
    except Exception as e:
        print(f"\nError occurred during sync: {e}")
        print("Rolling back target changes...")
        dest_conn.rollback()
    finally:
        src_cursor.close()
        src_conn.close()
        dest_cursor.close()
        dest_conn.close()

if __name__ == "__main__":
    sync_database()
