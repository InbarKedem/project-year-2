import mysql.connector
from db import DB_CONFIG
import sys

def init_db(generate_data=True):
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
        
    # Execute Schema
    print("Creating tables...")
    statements = schema_sql.split(';')
    for statement in statements:
        if statement.strip():
            cursor.execute(statement)
            
    print("Tables created successfully.")
    conn.commit()
    conn.close()
    
    # Generate data if requested
    if generate_data:
        print("\nGenerating data (seed + faker)...")
        from generate_fake_data import generate_all_fake_data
        # Don't drop schema since we just created it
        generate_all_fake_data(drop_schema=False)
    else:
        print("Skipping data generation (schema only).")
    
    print("Database initialization complete.")

if __name__ == '__main__':
    generate_data = '--schema-only' not in sys.argv
    init_db(generate_data=generate_data)
