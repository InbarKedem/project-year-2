import mysql.connector
from db import DB_CONFIG

def init_db():
    print("Connecting to database...")
    # Connect DIRECTLY to the database (no more creating it via code)
    conn = mysql.connector.connect(
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host'],
        database=DB_CONFIG['database'] 
    )
    cursor = conn.cursor()
    
    # Read schema
    print("Reading schema...")
    with open('sql/schema.sql', 'r') as f:
        schema_sql = f.read()

    # Read seed
    print("Reading seed data...")
    with open('sql/seed.sql', 'r') as f:
        seed_sql = f.read()
        
    # Execute Schema
    print("Creating tables...")
    statements = schema_sql.split(';')
    for statement in statements:
        if statement.strip():
            cursor.execute(statement)
            
    print("Tables created successfully.")
    
    # Execute Seed
    print("Inserting seed data...")
    statements = seed_sql.split(';')
    for statement in statements:
        if statement.strip():
            try:
                cursor.execute(statement)
            except mysql.connector.errors.IntegrityError:
                # Ignore errors if data already exists (optional safety)
                pass
            
    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == '__main__':
    init_db()
