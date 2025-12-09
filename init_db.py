import mysql.connector
from db import DB_CONFIG

def init_db():
    # Connect to MySQL server (without database first to create it)
    conn = mysql.connector.connect(
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host']
    )
    cursor = conn.cursor()
    
    # Read schema and seed files
    with open('sql/schema.sql', 'r') as f:
        schema_sql = f.read()
    
    with open('sql/seed.sql', 'r') as f:
        seed_sql = f.read()
        
    # Execute Schema (multi=True for multiple statements)
    # We need to split by ';' manually or use multi=True carefully. 
    # mysql-connector's execute(multi=True) returns an iterator.
    
    print("Initializing database...")
    
    # Execute Schema
    print("Initializing database...")
    
    # Split by semicolon and execute each statement
    # This is a simple split, might break if ; is inside strings, but for this schema it's fine.
    statements = schema_sql.split(';')
    for statement in statements:
        if statement.strip():
            cursor.execute(statement)
            
    print("Schema created.")
    
    # Reconnect to the specific database to ensure we are in the right context for seeding
    # although schema.sql has 'USE flytau;' it's safer to be explicit or rely on the script.
    # The schema.sql creates the DB and uses it.
    
    # Execute Seed
    print("Seeding data...")
    statements = seed_sql.split(';')
    for statement in statements:
        if statement.strip():
            cursor.execute(statement)
            
    print("Seed data inserted.")
    
    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == '__main__':
    init_db()
