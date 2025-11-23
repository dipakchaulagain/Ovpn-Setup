import sqlite3
import os

DB_PATH = 'instance/firewall.db'

def migrate_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. It will be created when the app runs.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if forward_mode exists in user table
        cursor.execute("PRAGMA table_info(user)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'forward_mode' not in columns:
            print("Adding forward_mode column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN forward_mode VARCHAR(10) DEFAULT 'ROUTE'")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column forward_mode already exists.")

        # Check if forward_type exists in rule table
        cursor.execute("PRAGMA table_info(rule)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'forward_type' in columns:
            print("Removing forward_type column from rule table...")
            try:
                cursor.execute("ALTER TABLE rule DROP COLUMN forward_type")
                conn.commit()
                print("Column removed successfully.")
            except sqlite3.OperationalError:
                print("SQLite version might be too old for DROP COLUMN. Recreating table...")
                # Fallback: Recreate table
                cursor.execute("CREATE TABLE rule_new (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, destination_ip VARCHAR(45) NOT NULL, destination_port INTEGER, protocol VARCHAR(10) NOT NULL, action VARCHAR(10) NOT NULL, created_at DATETIME, FOREIGN KEY(user_id) REFERENCES user(id))")
                cursor.execute("INSERT INTO rule_new (id, user_id, destination_ip, destination_port, protocol, action, created_at) SELECT id, user_id, destination_ip, destination_port, protocol, action, created_at FROM rule")
                cursor.execute("DROP TABLE rule")
                cursor.execute("ALTER TABLE rule_new RENAME TO rule")
                conn.commit()
                print("Table recreated successfully.")
        else:
            print("Column forward_type already removed.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_db()
