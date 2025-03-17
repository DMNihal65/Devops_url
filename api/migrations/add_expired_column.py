import os
import psycopg2

# Get database URL from environment variable or use a default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/urlshortener")

def run_migration():
    """Add expired column to urls table."""
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='urls' AND column_name='expired';
        """)
        
        if cursor.fetchone() is None:
            # Add the expired column
            cursor.execute("""
                ALTER TABLE urls 
                ADD COLUMN expired BOOLEAN DEFAULT FALSE;
            """)
            print("Added 'expired' column to urls table")
        else:
            print("Column 'expired' already exists")
            
        # Close connection
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Error running migration: {e}")
        return False

if __name__ == "__main__":
    run_migration() 