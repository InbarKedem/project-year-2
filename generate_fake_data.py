"""
Generate fake data for FLYTAU database using Faker library.
Merges seed data with improved naming and extends with faker-generated data.
"""
import mysql.connector
from faker import Faker
from faker.providers import BaseProvider
from datetime import datetime, timedelta
import random
import sys
from db import DB_CONFIG

# Business rules constants
BIG_PLANE_PILOTS = 3
BIG_PLANE_ATTENDANTS = 6
SMALL_PLANE_PILOTS = 2
SMALL_PLANE_ATTENDANTS = 3
SHORT_FLIGHT_MAX_HOURS = 6
LONG_FLIGHT_MIN_HOURS = 6

# Initialize faker with English locale only
fake_en = Faker('en_US')

def get_db_connection():
    """Get database connection."""
    return mysql.connector.connect(**DB_CONFIG)

def execute_insert(cursor, query, values):
    """Execute INSERT IGNORE query."""
    try:
        cursor.execute(query, values)
    except mysql.connector.errors.IntegrityError:
        pass  # Ignore duplicates

def insert_seed_airports(cursor):
    """Insert seed airports with improved naming."""
    print("Inserting seed airports...")
    airports = [
        (1, 'Ben Gurion (TLV)'),
        (2, 'John F. Kennedy (JFK)'),
        (3, 'Heathrow (LHR)'),
        (4, 'Charles de Gaulle (CDG)')
    ]
    query = "INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (%s, %s)"
    for airport in airports:
        execute_insert(cursor, query, airport)

def insert_seed_routes(cursor):
    """Insert seed flight routes."""
    print("Inserting seed routes...")
    routes = [
        (1, 2, 660),  # TLV -> JFK (11h)
        (2, 1, 660),  # JFK -> TLV
        (1, 3, 300),  # TLV -> LHR (5h)
        (3, 1, 300),  # LHR -> TLV
        (1, 4, 270),  # TLV -> CDG (4.5h)
        (4, 1, 270)   # CDG -> TLV
    ]
    query = "INSERT IGNORE INTO Flight_Route (source_airport_id, dest_airport_id, flight_duration) VALUES (%s, %s, %s)"
    for route in routes:
        execute_insert(cursor, query, route)

def insert_seed_aircraft(cursor):
    """Insert seed aircraft."""
    print("Inserting seed aircraft...")
    aircraft = [
        (1, 'Boeing', '2020-01-01', True),   # Large
        (2, 'Airbus', '2021-05-15', True),   # Large
        (3, 'Dassault', '2022-03-10', False), # Small
        (4, 'Boeing', '2019-11-20', False),   # Small
        (5, 'Airbus', '2023-02-28', False),  # Small
        (6, 'Dassault', '2024-07-01', True)   # Large
    ]
    query = "INSERT IGNORE INTO Aircraft (aircraft_id, manufacturer, purchase_date, is_large) VALUES (%s, %s, %s, %s)"
    for ac in aircraft:
        execute_insert(cursor, query, ac)

def insert_seed_aircraft_classes(cursor):
    """Insert seed aircraft classes."""
    print("Inserting seed aircraft classes...")
    classes = [
        (1, True, 2, 2),   # Plane 1 Business
        (1, False, 5, 4),  # Plane 1 Economy
        (2, True, 2, 2),   # Plane 2 Business
        (2, False, 5, 4),  # Plane 2 Economy
        (3, False, 5, 4),  # Plane 3 Economy (Small)
        (4, False, 5, 4),  # Plane 4 Economy (Small)
        (5, False, 5, 4),  # Plane 5 Economy (Small)
        (6, True, 2, 2),   # Plane 6 Business
        (6, False, 5, 4)   # Plane 6 Economy
    ]
    query = "INSERT IGNORE INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns) VALUES (%s, %s, %s, %s)"
    for cls in classes:
        execute_insert(cursor, query, cls)

def insert_seed_seats(cursor):
    """Insert seed seats for all aircraft classes."""
    print("Inserting seed seats...")
    query = "INSERT IGNORE INTO Seat (aircraft_id, is_business, `row_number`, `column_number`) VALUES (%s, %s, %s, %s)"
    
    # Generate seats for each aircraft class
    for aircraft_id in [1, 2, 3, 4, 5, 6]:
        # Check if aircraft is large
        cursor.execute("SELECT is_large FROM Aircraft WHERE aircraft_id = %s", (aircraft_id,))
        result = cursor.fetchone()
        if result and result[0]:
            # Large plane: Business and Economy
            # Business seats
            for row in range(1, 3):
                for col in range(1, 3):
                    execute_insert(cursor, query, (aircraft_id, True, row, col))
            # Economy seats
            for row in range(1, 6):
                for col in range(1, 5):
                    execute_insert(cursor, query, (aircraft_id, False, row, col))
        else:
            # Small plane: Economy only
            for row in range(1, 6):
                for col in range(1, 5):
                    execute_insert(cursor, query, (aircraft_id, False, row, col))

def insert_seed_employees(cursor):
    """Insert seed employees with improved names."""
    print("Inserting seed employees with improved names...")
    
    # Managers with fixed English names
    managers = [
        ('111111111', 'John', None, 'Smith', 'Tel Aviv', 'Main Street', 10, '0501234567', '2020-01-01'),
        ('222222222', 'Sarah', 'Elizabeth', 'Johnson', 'Haifa', 'Park Avenue', 20, '0502345678', '2021-02-01')
    ]
    
    # Pilots with realistic names
    pilots = []
    pilot_names = [
        ('John', 'Michael', 'Smith'), ('David', 'Robert', 'Jones'), ('James', 'William', 'Brown'),
        ('Richard', 'Thomas', 'Davis'), ('Charles', 'Joseph', 'Miller'), ('Christopher', 'Daniel', 'Wilson'),
        ('Matthew', 'Mark', 'Moore'), ('Anthony', 'Donald', 'Taylor'), ('Steven', 'Paul', 'Anderson'),
        ('Andrew', 'Joshua', 'Thomas')
    ]
    for i, (first, middle, last) in enumerate(pilot_names, 1):
        pilot_id = f'30000000{i}' if i < 10 else '300000010'
        pilots.append((
            pilot_id, first, middle, last, 'Tel Aviv', fake_en.street_name(),
            i, f'050{3000000 + i}', '2022-01-01'
        ))
    
    # Attendants with realistic names
    attendants = []
    attendant_names = [
        ('Sarah', 'Emily', 'Johnson'), ('Jessica', 'Amanda', 'Williams'), ('Jennifer', 'Lisa', 'Brown'),
        ('Michelle', 'Ashley', 'Davis'), ('Melissa', 'Nicole', 'Miller'), ('Amy', 'Angela', 'Wilson'),
        ('Rebecca', 'Stephanie', 'Moore'), ('Laura', 'Kimberly', 'Taylor'), ('Elizabeth', 'Megan', 'Anderson'),
        ('Lauren', 'Rachel', 'Thomas')
    ]
    for i, (first, middle, last) in enumerate(attendant_names, 1):
        attendant_id = f'40000000{i}' if i < 10 else '400000010'
        attendants.append((
            attendant_id, first, middle, last, 'Tel Aviv', fake_en.street_name(),
            i, f'050{4000000 + i}', '2023-01-01'
        ))
    
    query = "INSERT IGNORE INTO Employee (id_number, first_name, middle_name, last_name, city, street, house_number, phone, start_work_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    
    for emp in managers + pilots + attendants:
        execute_insert(cursor, query, emp)
    
    # Verify all pilots were inserted (300000001-300000010)
    cursor.execute("SELECT id_number FROM Employee WHERE (id_number LIKE '30000000%' OR id_number = '300000010') ORDER BY id_number")
    inserted_pilots = [row[0] for row in cursor.fetchall()]
    if len(inserted_pilots) < 10:
        print(f"WARNING: Only {len(inserted_pilots)} pilots inserted. Expected 10. IDs: {inserted_pilots}")
        # Try to insert missing pilot
        if '300000010' not in inserted_pilots:
            pilot_10 = pilots[9]  # 10th pilot (index 9)
            execute_insert(cursor, query, pilot_10)

def insert_seed_flight_crew(cursor):
    """Insert seed flight crew assignments."""
    print("Inserting seed flight crew...")
    
    # Pilots: first 4 trained for long flights, rest not
    pilots_crew = []
    for i in range(1, 11):
        pilot_id = f'30000000{i}' if i < 10 else '300000010'
        trained = i <= 4
        pilots_crew.append((pilot_id, trained, True))
    
    # Attendants: first 6 trained for long flights, rest not
    attendants_crew = []
    for i in range(1, 11):
        attendant_id = f'40000000{i}' if i < 10 else '400000010'
        trained = i <= 6
        attendants_crew.append((attendant_id, trained, False))
    
    query = "INSERT IGNORE INTO Flight_Crew (id_number, trained_for_long_flights, is_pilot) VALUES (%s, %s, %s)"
    for crew in pilots_crew + attendants_crew:
        execute_insert(cursor, query, crew)
    
    # Verify all pilots were inserted into Flight_Crew (300000001-300000010)
    cursor.execute("SELECT id_number FROM Flight_Crew WHERE (id_number LIKE '30000000%' OR id_number = '300000010') AND is_pilot = TRUE ORDER BY id_number")
    inserted_crew_pilots = [row[0] for row in cursor.fetchall()]
    if len(inserted_crew_pilots) < 10:
        print(f"WARNING: Only {len(inserted_crew_pilots)} pilots in Flight_Crew. Expected 10. IDs: {inserted_crew_pilots}")
        # Try to insert missing pilots
        for pilot_id, trained, is_pilot in pilots_crew:
            if pilot_id not in inserted_crew_pilots:
                execute_insert(cursor, query, (pilot_id, trained, is_pilot))

def insert_seed_managers(cursor):
    """Insert seed managers with improved passwords."""
    print("Inserting seed managers...")
    managers = [
        ('111111111', 'Admin@2024'),
        ('222222222', 'Manager#2024')
    ]
    query = "INSERT IGNORE INTO Manager (id_number, password) VALUES (%s, %s)"
    for mgr in managers:
        execute_insert(cursor, query, mgr)

def insert_seed_users(cursor):
    """Insert seed users with improved names."""
    print("Inserting seed users with improved names...")
    users = [
        ('reg1@test.com', fake_en.first_name(), None, fake_en.last_name()),
        ('reg2@test.com', fake_en.first_name(), fake_en.first_name(), fake_en.last_name()),
        ('guest1@test.com', fake_en.first_name(), None, fake_en.last_name()),
        ('guest2@test.com', fake_en.first_name(), fake_en.first_name(), fake_en.last_name())
    ]
    query = "INSERT IGNORE INTO User (email, first_name, middle_name, last_name) VALUES (%s, %s, %s, %s)"
    for user in users:
        execute_insert(cursor, query, user)

def insert_seed_phones(cursor):
    """Insert seed phone numbers."""
    print("Inserting seed phone numbers...")
    phones = [
        ('reg1@test.com', f'050{fake_en.random_int(1000000, 9999999)}'),
        ('reg1@test.com', f'050{fake_en.random_int(1000000, 9999999)}'),
        ('reg1@test.com', f'050{fake_en.random_int(1000000, 9999999)}'),
        ('reg2@test.com', f'050{fake_en.random_int(1000000, 9999999)}'),
        ('reg2@test.com', f'050{fake_en.random_int(1000000, 9999999)}'),
        ('guest1@test.com', f'050{fake_en.random_int(1000000, 9999999)}'),
        ('guest2@test.com', f'050{fake_en.random_int(1000000, 9999999)}')
    ]
    query = "INSERT IGNORE INTO Phone (email, phone_number) VALUES (%s, %s)"
    for phone in phones:
        execute_insert(cursor, query, phone)

def insert_seed_registered_customers(cursor):
    """Insert seed registered customers with improved data."""
    print("Inserting seed registered customers...")
    customers = [
        ('reg1@test.com', f'A{fake_en.random_int(1000000, 9999999)}', '1990-01-01', '2025-01-01', 'Customer@2024'),
        ('reg2@test.com', f'B{fake_en.random_int(1000000, 9999999)}', '1995-05-05', '2025-02-01', 'User#2024')
    ]
    query = "INSERT IGNORE INTO Registered_Customer (email, passport_number, birth_date, registration_date, password) VALUES (%s, %s, %s, %s, %s)"
    for cust in customers:
        execute_insert(cursor, query, cust)

def insert_seed_flights(cursor):
    """Insert seed flights."""
    print("Inserting seed flights...")
    flights = [
        (1, 2, '2026-01-01 08:00:00', 1, 'Active', 800, 1500),  # TLV->JFK (Long), Big
        (1, 3, '2026-01-02 10:00:00', 3, 'Active', 400, 900),   # TLV->LHR (Short), Small
        (2, 1, '2026-01-03 12:00:00', 2, 'Active', 850, 1600),  # JFK->TLV (Long), Big
        (3, 1, '2026-01-04 14:00:00', 4, 'Active', 450, 950)    # LHR->TLV (Short), Small
    ]
    query = "INSERT IGNORE INTO Flight (source_airport_id, dest_airport_id, departure_time, aircraft_id, flight_status, economy_price, business_price) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    for flight in flights:
        execute_insert(cursor, query, flight)

def insert_seed_crew_assignments(cursor):
    """Insert seed crew assignments for first flight (Big plane: 3 pilots + 6 attendants)."""
    print("Inserting seed crew assignments...")
    # Flight 1: TLV->JFK (Big plane)
    assignments = [
        ('300000001', 1, 2, '2026-01-01 08:00:00'),  # Pilots
        ('300000002', 1, 2, '2026-01-01 08:00:00'),
        ('300000003', 1, 2, '2026-01-01 08:00:00'),
        ('400000001', 1, 2, '2026-01-01 08:00:00'),  # Attendants
        ('400000002', 1, 2, '2026-01-01 08:00:00'),
        ('400000003', 1, 2, '2026-01-01 08:00:00'),
        ('400000004', 1, 2, '2026-01-01 08:00:00'),
        ('400000005', 1, 2, '2026-01-01 08:00:00'),
        ('400000006', 1, 2, '2026-01-01 08:00:00')
    ]
    query = "INSERT IGNORE INTO Employee_Flight_Assignment (employee_id, source_airport_id, dest_airport_id, departure_time) VALUES (%s, %s, %s, %s)"
    for assignment in assignments:
        execute_insert(cursor, query, assignment)

def insert_seed_orders(cursor):
    """Insert seed orders."""
    print("Inserting seed orders...")
    orders = [
        (1, '2025-12-01 10:00:00', 1500, 'Active', 'reg1@test.com', 1, 2, '2026-01-01 08:00:00'),
        (2, '2025-12-02 11:00:00', 500, 'Active', 'reg2@test.com', 1, 3, '2026-01-02 10:00:00'),
        (3, '2025-12-03 12:00:00', 800, 'Active', 'guest1@test.com', 1, 2, '2026-01-01 08:00:00'),
        (4, '2025-12-04 13:00:00', 1600, 'Active', 'guest2@test.com', 2, 1, '2026-01-03 12:00:00')
    ]
    query = "INSERT IGNORE INTO Order_Table (order_code, order_date, total_payment, order_status, customer_email, source_airport_id, dest_airport_id, departure_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    for order in orders:
        execute_insert(cursor, query, order)

def insert_seed_order_seats(cursor):
    """Insert seed order seats."""
    print("Inserting seed order seats...")
    order_seats = [
        (1, 1, True, 1, 1),   # Order 1, Business
        (2, 3, False, 1, 1),  # Order 2, Economy
        (3, 1, False, 1, 1),  # Order 3, Economy
        (4, 2, True, 1, 1)    # Order 4, Business
    ]
    query = "INSERT IGNORE INTO Order_Seats (order_code, aircraft_id, is_business, `row_number`, `column_number`) VALUES (%s, %s, %s, %s, %s)"
    for seat in order_seats:
        execute_insert(cursor, query, seat)

def generate_faker_airports(cursor, min_count=20):
    """Generate additional airports using well-known airports."""
    print(f"Generating {min_count} airports with faker...")
    cursor.execute("SELECT COUNT(*) FROM Airport")
    current_count = cursor.fetchone()[0]
    needed = max(0, min_count - current_count)
    
    if needed == 0:
        print(f"Already have {current_count} airports, skipping...")
        return
    
    # Well-known international airports
    well_known_airports = [
        'Dubai International (DXB)', 'Singapore Changi (SIN)', 'Tokyo Haneda (HND)',
        'Frankfurt (FRA)', 'Amsterdam Schiphol (AMS)', 'Madrid Barajas (MAD)',
        'Rome Fiumicino (FCO)', 'Barcelona El Prat (BCN)', 'Munich (MUC)',
        'Vienna (VIE)', 'Zurich (ZRH)', 'Brussels (BRU)', 'Copenhagen (CPH)',
        'Stockholm Arlanda (ARN)', 'Oslo Gardermoen (OSL)', 'Helsinki (HEL)',
        'Dublin (DUB)', 'Manchester (MAN)', 'Birmingham (BHX)', 'Glasgow (GLA)',
        'Edinburgh (EDI)', 'Barcelona (BCN)', 'Milan Malpensa (MXP)', 'Venice Marco Polo (VCE)',
        'Athens (ATH)', 'Istanbul (IST)', 'Cairo (CAI)', 'Dubai (DXB)', 'Doha (DOH)',
        'Abu Dhabi (AUH)', 'Bangkok Suvarnabhumi (BKK)', 'Hong Kong (HKG)', 'Seoul Incheon (ICN)',
        'Sydney (SYD)', 'Melbourne (MEL)', 'Toronto Pearson (YYZ)', 'Vancouver (YVR)',
        'Montreal (YUL)', 'Mexico City (MEX)', 'São Paulo Guarulhos (GRU)', 'Buenos Aires (EZE)',
        'Johannesburg (JNB)', 'Cape Town (CPT)', 'Nairobi (NBO)', 'Lagos (LOS)'
    ]
    
    airports = []
    for i in range(needed):
        airport_id = current_count + i + 1
        if i < len(well_known_airports):
            airport_name = well_known_airports[i]
        else:
            # If we need more, use faker but with better formatting
            city = fake_en.city()
            code = ''.join([c for c in city.upper() if c.isalpha()])[:3]
            airport_name = f"{city} ({code})"
        airports.append((airport_id, airport_name))
    
    query = "INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (%s, %s)"
    for airport in airports:
        execute_insert(cursor, query, airport)
    print(f"Generated {len(airports)} additional airports")

def generate_faker_routes(cursor, min_count=20):
    """Generate additional routes between airports."""
    print(f"Generating {min_count} routes with faker...")
    cursor.execute("SELECT COUNT(*) FROM Flight_Route")
    current_count = cursor.fetchone()[0]
    needed = max(0, min_count - current_count)
    
    if needed == 0:
        print(f"Already have {current_count} routes, skipping...")
        return
    
    # Get all airports
    cursor.execute("SELECT airport_id FROM Airport")
    airport_ids = [row[0] for row in cursor.fetchall()]
    
    if len(airport_ids) < 2:
        print("Not enough airports to generate routes")
        return
    
    routes = set()
    # Get existing routes
    cursor.execute("SELECT source_airport_id, dest_airport_id FROM Flight_Route")
    existing = set((row[0], row[1]) for row in cursor.fetchall())
    
    # Generate all possible routes first
    all_possible_routes = []
    for source in airport_ids:
        for dest in airport_ids:
            if source != dest:
                all_possible_routes.append((source, dest))
    
    # Remove existing routes
    available_routes = [r for r in all_possible_routes if r not in existing]
    
    # Randomly select needed routes
    if len(available_routes) < needed:
        # If not enough unique routes, we'll generate some duplicates (which INSERT IGNORE will handle)
        needed = len(available_routes)
    
    selected_routes = random.sample(available_routes, min(needed, len(available_routes)))
    
    for source, dest in selected_routes:
        # Generate duration: 180-720 minutes (3-12 hours)
        duration = random.randint(180, 720)
        routes.add((source, dest, duration))
    
    query = "INSERT IGNORE INTO Flight_Route (source_airport_id, dest_airport_id, flight_duration) VALUES (%s, %s, %s)"
    inserted_count = 0
    for route in routes:
        try:
            cursor.execute(query, route)
            inserted_count += 1
        except mysql.connector.errors.IntegrityError:
            pass  # Duplicate route, skip
    
    # If we still don't have enough, try to add more
    cursor.execute("SELECT COUNT(*) FROM Flight_Route")
    final_count = cursor.fetchone()[0]
    if final_count < min_count:
        # Try to add more routes, even if they might be duplicates
        additional_needed = min_count - final_count
        attempts = 0
        max_attempts = 1000
        while final_count < min_count and attempts < max_attempts:
            source = random.choice(airport_ids)
            dest = random.choice(airport_ids)
            if source != dest:
                duration = random.randint(180, 720)
                try:
                    cursor.execute(query, (source, dest, duration))
                    final_count += 1
                except mysql.connector.errors.IntegrityError:
                    pass
            attempts += 1
    
    print(f"Generated routes. Total routes now: {final_count}")

def generate_faker_aircraft(cursor, min_count=20):
    """Generate additional aircraft."""
    print(f"Generating {min_count} aircraft with faker...")
    cursor.execute("SELECT MAX(aircraft_id) FROM Aircraft")
    max_id = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM Aircraft")
    current_count = cursor.fetchone()[0]
    needed = max(0, min_count - current_count)
    
    if needed == 0:
        print(f"Already have {current_count} aircraft, skipping...")
        return
    
    manufacturers = ['Boeing', 'Airbus', 'Dassault', 'Embraer', 'Bombardier']
    aircraft = []
    for i in range(needed):
        aircraft_id = max_id + i + 1
        manufacturer = random.choice(manufacturers)
        purchase_date = fake_en.date_between(start_date='-10y', end_date='today')
        is_large = random.choice([True, False])  # Mix of large and small
        aircraft.append((aircraft_id, manufacturer, purchase_date, is_large))
    
    query = "INSERT IGNORE INTO Aircraft (aircraft_id, manufacturer, purchase_date, is_large) VALUES (%s, %s, %s, %s)"
    for ac in aircraft:
        execute_insert(cursor, query, ac)
    print(f"Generated {len(aircraft)} additional aircraft")

def generate_faker_aircraft_classes(cursor):
    """Generate aircraft classes for all aircraft."""
    print("Generating aircraft classes for all aircraft...")
    cursor.execute("SELECT aircraft_id, is_large FROM Aircraft")
    aircraft_list = cursor.fetchall()
    
    query = "INSERT IGNORE INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns) VALUES (%s, %s, %s, %s)"
    
    for aircraft_id, is_large in aircraft_list:
        # Check if classes already exist
        cursor.execute("SELECT COUNT(*) FROM Aircraft_Class WHERE aircraft_id = %s", (aircraft_id,))
        if cursor.fetchone()[0] > 0:
            continue
        
        if is_large:
            # Big plane: Business and Economy
            business_rows = random.randint(2, 4)
            business_cols = random.randint(2, 4)
            economy_rows = random.randint(8, 15)
            economy_cols = random.randint(4, 6)
            execute_insert(cursor, query, (aircraft_id, True, business_rows, business_cols))
            execute_insert(cursor, query, (aircraft_id, False, economy_rows, economy_cols))
        else:
            # Small plane: Economy only
            economy_rows = random.randint(5, 10)
            economy_cols = random.randint(4, 6)
            execute_insert(cursor, query, (aircraft_id, False, economy_rows, economy_cols))
    print("Generated aircraft classes for all aircraft")

def generate_faker_seats(cursor):
    """Generate seats for all aircraft classes."""
    print("Generating seats for all aircraft classes...")
    cursor.execute("SELECT aircraft_id, is_business, num_rows, num_columns FROM Aircraft_Class")
    classes = cursor.fetchall()
    
    query = "INSERT IGNORE INTO Seat (aircraft_id, is_business, `row_number`, `column_number`) VALUES (%s, %s, %s, %s)"
    
    for aircraft_id, is_business, num_rows, num_columns in classes:
        # Check if seats already exist
        cursor.execute("SELECT COUNT(*) FROM Seat WHERE aircraft_id = %s AND is_business = %s", (aircraft_id, is_business))
        if cursor.fetchone()[0] > 0:
            continue
        
        for row in range(1, num_rows + 1):
            for col in range(1, num_columns + 1):
                execute_insert(cursor, query, (aircraft_id, is_business, row, col))
    print("Generated seats for all aircraft classes")

def generate_faker_employees(cursor, min_count=20):
    """Generate additional employees with well-known names."""
    print(f"Generating {min_count} employees with faker...")
    cursor.execute("SELECT COUNT(*) FROM Employee")
    current_count = cursor.fetchone()[0]
    needed = max(0, min_count - current_count)
    
    if needed == 0:
        print(f"Already have {current_count} employees, skipping...")
        return
    
    # Get max ID
    cursor.execute("SELECT MAX(CAST(id_number AS UNSIGNED)) FROM Employee WHERE id_number REGEXP '^[0-9]+$'")
    max_id = cursor.fetchone()[0] or 0
    
    # Well-known first names
    well_known_first_names = [
        'Michael', 'David', 'James', 'Robert', 'John', 'William', 'Richard', 'Joseph',
        'Thomas', 'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald',
        'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth', 'Kevin', 'Brian', 'George',
        'Sarah', 'Emily', 'Jessica', 'Jennifer', 'Michelle', 'Melissa', 'Amy',
        'Rebecca', 'Laura', 'Elizabeth', 'Lauren', 'Nicole', 'Ashley', 'Amanda',
        'Lisa', 'Stephanie', 'Kimberly', 'Megan', 'Rachel', 'Angela', 'Emma'
    ]
    
    # Well-known last names
    well_known_last_names = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas',
        'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris',
        'Clark', 'Lewis', 'Robinson', 'Walker', 'Young', 'King', 'Wright', 'Scott',
        'Green', 'Adams', 'Baker', 'Nelson', 'Hill', 'Campbell', 'Mitchell', 'Roberts'
    ]
    
    employees = []
    cities = ['Tel Aviv', 'Haifa', 'Jerusalem', 'Beer Sheva', 'Netanya', 'Eilat']
    for i in range(needed):
        emp_id = str(max_id + i + 1).zfill(9)
        first_name = random.choice(well_known_first_names)
        middle_name = random.choice(well_known_first_names) if random.random() > 0.5 else None
        last_name = random.choice(well_known_last_names)
        city = random.choice(cities)
        street = fake_en.street_name()
        house_number = random.randint(1, 200)
        phone = f'050{fake_en.random_int(1000000, 9999999)}'
        start_date = fake_en.date_between(start_date='-5y', end_date='today')
        employees.append((emp_id, first_name, middle_name, last_name, city, street, house_number, phone, start_date))
    
    query = "INSERT IGNORE INTO Employee (id_number, first_name, middle_name, last_name, city, street, house_number, phone, start_work_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    for emp in employees:
        execute_insert(cursor, query, emp)
    print(f"Generated {len(employees)} additional employees")

def generate_faker_flight_crew(cursor):
    """Generate flight crew from employees (excluding managers)."""
    print("Generating flight crew...")
    
    # Count how many flights we'll have to ensure enough crew
    cursor.execute("SELECT COUNT(*) FROM Flight")
    flight_count = cursor.fetchone()[0]
    
    # Estimate crew needs:
    # - Each flight needs 2-3 pilots and 3-6 attendants
    # - With 50 flights, we need good coverage
    # - Minimum: 20 pilots (15 trained for long flights) and 30 attendants (20 trained for long flights)
    min_pilots = 20
    min_trained_pilots = 15  # For long flights
    min_attendants = 30
    min_trained_attendants = 20  # For long flights
    
    cursor.execute("SELECT COUNT(*) FROM Flight_Crew WHERE is_pilot = 1")
    current_pilots = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Flight_Crew WHERE is_pilot = 1 AND trained_for_long_flights = 1")
    current_trained_pilots = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Flight_Crew WHERE is_pilot = 0")
    current_attendants = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM Flight_Crew WHERE is_pilot = 0 AND trained_for_long_flights = 1")
    current_trained_attendants = cursor.fetchone()[0]
    
    pilots_needed = max(0, min_pilots - current_pilots)
    trained_pilots_needed = max(0, min_trained_pilots - current_trained_pilots)
    attendants_needed = max(0, min_attendants - current_attendants)
    trained_attendants_needed = max(0, min_trained_attendants - current_trained_attendants)
    
    if pilots_needed == 0 and attendants_needed == 0:
        print(f"Already have {current_pilots} pilots ({current_trained_pilots} trained) and {current_attendants} attendants ({current_trained_attendants} trained), skipping...")
        return
    
    # Get all employees who are not managers and not already in flight crew
    cursor.execute("""
        SELECT e.id_number FROM Employee e
        LEFT JOIN Manager m ON e.id_number = m.id_number
        LEFT JOIN Flight_Crew fc ON e.id_number = fc.id_number
        WHERE m.id_number IS NULL AND fc.id_number IS NULL
    """)
    available_employees = [row[0] for row in cursor.fetchall()]
    
    total_needed = pilots_needed + attendants_needed
    if len(available_employees) < total_needed:
        # Generate more employees if needed
        cursor.execute("SELECT COUNT(*) FROM Employee")
        current_emp_count = cursor.fetchone()[0]
        generate_faker_employees(cursor, min_count=current_emp_count + total_needed)
        cursor.execute("""
            SELECT e.id_number FROM Employee e
            LEFT JOIN Manager m ON e.id_number = m.id_number
            LEFT JOIN Flight_Crew fc ON e.id_number = fc.id_number
            WHERE m.id_number IS NULL AND fc.id_number IS NULL
        """)
        available_employees = [row[0] for row in cursor.fetchall()]
        if len(available_employees) < total_needed:
            print(f"Warning: Not enough employees to create crew. Have {len(available_employees)}, need {total_needed}")
            # Use what we have
            total_needed = len(available_employees)
    
    pilots = []
    attendants = []
    trained_pilots_added = 0
    trained_attendants_added = 0
    
    for i, emp_id in enumerate(available_employees[:total_needed]):
        if i < pilots_needed:
            # Ensure we have enough trained pilots
            if trained_pilots_added < trained_pilots_needed:
                trained = True
                trained_pilots_added += 1
            else:
                # 50% chance for remaining pilots
                trained = random.random() < 0.5
            pilots.append((emp_id, trained, True))
        else:
            # Ensure we have enough trained attendants
            if trained_attendants_added < trained_attendants_needed:
                trained = True
                trained_attendants_added += 1
            else:
                # 50% chance for remaining attendants
                trained = random.random() < 0.5
            attendants.append((emp_id, trained, False))
    
    query = "INSERT IGNORE INTO Flight_Crew (id_number, trained_for_long_flights, is_pilot) VALUES (%s, %s, %s)"
    for crew in pilots + attendants:
        execute_insert(cursor, query, crew)
    print(f"Generated {len(pilots)} pilots ({trained_pilots_added} trained) and {len(attendants)} attendants ({trained_attendants_added} trained)")

def generate_faker_users(cursor, min_count=20):
    """Generate additional users with well-known names."""
    print(f"Generating {min_count} users with faker...")
    cursor.execute("SELECT COUNT(*) FROM User")
    current_count = cursor.fetchone()[0]
    needed = max(0, min_count - current_count)
    
    if needed == 0:
        print(f"Already have {current_count} users, skipping...")
        return
    
    # Well-known first names
    well_known_first_names = [
        'Michael', 'David', 'James', 'Robert', 'John', 'William', 'Richard', 'Joseph',
        'Thomas', 'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald',
        'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth', 'Kevin', 'Brian', 'George',
        'Sarah', 'Emily', 'Jessica', 'Jennifer', 'Michelle', 'Melissa', 'Amy',
        'Rebecca', 'Laura', 'Elizabeth', 'Lauren', 'Nicole', 'Ashley', 'Amanda',
        'Lisa', 'Stephanie', 'Kimberly', 'Megan', 'Rachel', 'Angela', 'Emma'
    ]
    
    # Well-known last names
    well_known_last_names = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas',
        'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris',
        'Clark', 'Lewis', 'Robinson', 'Walker', 'Young', 'King', 'Wright', 'Scott',
        'Green', 'Adams', 'Baker', 'Nelson', 'Hill', 'Campbell', 'Mitchell', 'Roberts'
    ]
    
    users = []
    for i in range(needed):
        email = fake_en.email()
        first_name = random.choice(well_known_first_names)
        middle_name = random.choice(well_known_first_names) if random.random() > 0.5 else None
        last_name = random.choice(well_known_last_names)
        users.append((email, first_name, middle_name, last_name))
    
    query = "INSERT IGNORE INTO User (email, first_name, middle_name, last_name) VALUES (%s, %s, %s, %s)"
    for user in users:
        execute_insert(cursor, query, user)
    print(f"Generated {len(users)} additional users")

def generate_faker_phones(cursor):
    """Generate phone numbers for users."""
    print("Generating phone numbers...")
    cursor.execute("SELECT email FROM User")
    users = [row[0] for row in cursor.fetchall()]
    
    query = "INSERT IGNORE INTO Phone (email, phone_number) VALUES (%s, %s)"
    phones_generated = 0
    for email in users:
        # Each user gets 1-3 phone numbers
        num_phones = random.randint(1, 3)
        for _ in range(num_phones):
            phone = f'050{fake_en.random_int(1000000, 9999999)}'
            execute_insert(cursor, query, (email, phone))
            phones_generated += 1
    print(f"Generated {phones_generated} phone numbers")

def generate_faker_registered_customers(cursor):
    """Generate registered customers from users."""
    print("Generating registered customers...")
    cursor.execute("""
        SELECT u.email FROM User u
        LEFT JOIN Registered_Customer rc ON u.email = rc.email
        WHERE rc.email IS NULL
    """)
    available_users = [row[0] for row in cursor.fetchall()]
    
    # Register 60% of users
    num_to_register = int(len(available_users) * 0.6)
    users_to_register = random.sample(available_users, min(num_to_register, len(available_users)))
    
    query = "INSERT IGNORE INTO Registered_Customer (email, passport_number, birth_date, registration_date, password) VALUES (%s, %s, %s, %s, %s)"
    for email in users_to_register:
        passport = f'{random.choice(["A", "B", "C"])}{fake_en.random_int(1000000, 9999999)}'
        birth_date = fake_en.date_of_birth(minimum_age=18, maximum_age=80)
        registration_date = fake_en.date_between(start_date=birth_date, end_date='today')
        password = fake_en.password(length=10, special_chars=True, digits=True, upper_case=True, lower_case=True)
        execute_insert(cursor, query, (email, passport, birth_date, registration_date, password))
    print(f"Generated {len(users_to_register)} registered customers")

def generate_faker_flights(cursor, min_count=50):
    """Generate flights from today to next year, following business rules."""
    print(f"Generating {min_count} flights with faker...")
    cursor.execute("SELECT COUNT(*) FROM Flight")
    current_count = cursor.fetchone()[0]
    needed = max(0, min_count - current_count)
    
    if needed == 0:
        print(f"Already have {current_count} flights, skipping...")
        return
    
    # Get routes and their durations
    cursor.execute("SELECT source_airport_id, dest_airport_id, flight_duration FROM Flight_Route")
    routes = cursor.fetchall()
    
    # Get aircraft with their sizes
    cursor.execute("SELECT aircraft_id, is_large FROM Aircraft")
    aircraft_list = cursor.fetchall()
    big_aircraft = [ac[0] for ac in aircraft_list if ac[1]]
    small_aircraft = [ac[0] for ac in aircraft_list if not ac[1]]
    
    # Get aircraft classes to determine prices
    cursor.execute("SELECT DISTINCT aircraft_id FROM Aircraft_Class WHERE is_business = TRUE")
    aircraft_with_business = set(row[0] for row in cursor.fetchall())
    
    flights = []
    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)
    past_date = start_date - timedelta(days=180)  # For completed flights
    
    # Generate flights with realistic statuses
    # 60% Active, 25% Completed (past), 10% Canceled, 5% Fully Booked (will be set after orders)
    status_distribution = ['Active'] * 60 + ['Completed'] * 25 + ['Canceled'] * 10 + ['Active'] * 5  # Last 5% will become Fully Booked
    
    for i in range(needed):
        route = random.choice(routes)
        source_id, dest_id, duration = route
        
        # Business rule: Long flights (6+ hours) only use Big planes
        is_long = duration >= (LONG_FLIGHT_MIN_HOURS * 60)
        if is_long:
            aircraft_id = random.choice(big_aircraft)
        else:
            # Short flights can use both
            aircraft_id = random.choice(big_aircraft + small_aircraft)
        
        # Determine status first to set appropriate departure time
        status_choice = random.choice(status_distribution)
        
        # Generate departure time based on status
        if status_choice == 'Completed':
            # Completed flights should be in the past
            departure_time = fake_en.date_time_between(start_date=past_date, end_date=start_date - timedelta(hours=1))
            status = 'Completed'
        elif status_choice == 'Canceled':
            # Canceled flights can be past or future, but mostly future
            if random.random() < 0.3:  # 30% past canceled
                departure_time = fake_en.date_time_between(start_date=past_date, end_date=start_date - timedelta(hours=1))
            else:  # 70% future canceled
                departure_time = fake_en.date_time_between(start_date=start_date, end_date=end_date)
            status = 'Canceled'
        else:
            # Active flights (some will become Fully Booked later)
            departure_time = fake_en.date_time_between(start_date=start_date, end_date=end_date)
            status = 'Active'
        
        # Generate prices (integers only)
        base_price = random.randint(300, 1200)
        economy_price = base_price
        if aircraft_id in aircraft_with_business:
            business_price = int(base_price * random.uniform(1.8, 2.5))
        else:
            business_price = None
        
        flights.append((source_id, dest_id, departure_time, aircraft_id, status, economy_price, business_price))
    
    query = "INSERT IGNORE INTO Flight (source_airport_id, dest_airport_id, departure_time, aircraft_id, flight_status, economy_price, business_price) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    for flight in flights:
        execute_insert(cursor, query, flight)
    print(f"Generated {len(flights)} additional flights")

def generate_faker_crew_assignments(cursor):
    """Generate crew assignments for flights, following business rules."""
    print("Generating crew assignments...")
    # Get all flights
    cursor.execute("""
        SELECT f.source_airport_id, f.dest_airport_id, f.departure_time, f.aircraft_id, a.is_large,
               fr.flight_duration
        FROM Flight f
        JOIN Aircraft a ON f.aircraft_id = a.aircraft_id
        JOIN Flight_Route fr ON f.source_airport_id = fr.source_airport_id 
            AND f.dest_airport_id = fr.dest_airport_id
        LEFT JOIN Employee_Flight_Assignment efa ON f.source_airport_id = efa.source_airport_id
            AND f.dest_airport_id = efa.dest_airport_id
            AND f.departure_time = efa.departure_time
        WHERE efa.employee_id IS NULL
    """)
    flights = cursor.fetchall()
    
    # Get available crew
    cursor.execute("SELECT id_number, trained_for_long_flights, is_pilot FROM Flight_Crew")
    crew_list = cursor.fetchall()
    pilots = [c for c in crew_list if c[2]]
    attendants = [c for c in crew_list if not c[2]]
    
    query = "INSERT IGNORE INTO Employee_Flight_Assignment (employee_id, source_airport_id, dest_airport_id, departure_time) VALUES (%s, %s, %s, %s)"
    assignments_made = 0
    
    flights_without_crew = []
    
    for source_id, dest_id, departure_time, aircraft_id, is_large, duration in flights:
        is_long = duration >= (LONG_FLIGHT_MIN_HOURS * 60)
        
        # Determine crew requirements
        if is_large:
            num_pilots = BIG_PLANE_PILOTS
            num_attendants = BIG_PLANE_ATTENDANTS
        else:
            num_pilots = SMALL_PLANE_PILOTS
            num_attendants = SMALL_PLANE_ATTENDANTS
        
        # Select pilots (must be trained for long flights if it's a long flight)
        available_pilots = [p for p in pilots if not is_long or p[1]]  # Trained if long flight
        
        if len(available_pilots) < num_pilots:
            # Not enough pilots - try to assign what we have, or skip this flight
            if len(available_pilots) == 0:
                flights_without_crew.append((source_id, dest_id, departure_time, "No available pilots"))
                continue
            # Use all available pilots if we don't have enough
            selected_pilots = available_pilots
        else:
            selected_pilots = random.sample(available_pilots, num_pilots)
        
        # Select attendants (must be trained for long flights if it's a long flight)
        available_attendants = [a for a in attendants if not is_long or a[1]]  # Trained if long flight
        
        if len(available_attendants) < num_attendants:
            # Not enough attendants - try to assign what we have, or skip this flight
            if len(available_attendants) == 0:
                flights_without_crew.append((source_id, dest_id, departure_time, "No available attendants"))
                continue
            # Use all available attendants if we don't have enough
            selected_attendants = available_attendants
        else:
            selected_attendants = random.sample(available_attendants, num_attendants)
        
        # Assign crew
        for pilot in selected_pilots:
            execute_insert(cursor, query, (pilot[0], source_id, dest_id, departure_time))
            assignments_made += 1
        for attendant in selected_attendants:
            execute_insert(cursor, query, (attendant[0], source_id, dest_id, departure_time))
            assignments_made += 1
    
    if flights_without_crew:
        print(f"Warning: {len(flights_without_crew)} flights could not be assigned crew")
        # Try to assign crew again with relaxed requirements (allow untrained for long flights if needed)
        for source_id, dest_id, departure_time, reason in flights_without_crew:
            cursor.execute("""
                SELECT a.is_large, fr.flight_duration
                FROM Flight f
                JOIN Aircraft a ON f.aircraft_id = a.aircraft_id
                JOIN Flight_Route fr ON f.source_airport_id = fr.source_airport_id 
                    AND f.dest_airport_id = fr.dest_airport_id
                WHERE f.source_airport_id = %s AND f.dest_airport_id = %s AND f.departure_time = %s
            """, (source_id, dest_id, departure_time))
            result = cursor.fetchone()
            if result:
                is_large, duration = result
                is_long = duration >= (LONG_FLIGHT_MIN_HOURS * 60)
                
                if is_large:
                    num_pilots = BIG_PLANE_PILOTS
                    num_attendants = BIG_PLANE_ATTENDANTS
                else:
                    num_pilots = SMALL_PLANE_PILOTS
                    num_attendants = SMALL_PLANE_ATTENDANTS
                
                # Try with all pilots/attendants (relax training requirement if needed)
                all_pilots = pilots if not is_long else [p for p in pilots if p[1]] or pilots
                all_attendants = attendants if not is_long else [a for a in attendants if a[1]] or attendants
                
                if len(all_pilots) >= num_pilots and len(all_attendants) >= num_attendants:
                    selected_pilots = random.sample(all_pilots, num_pilots)
                    selected_attendants = random.sample(all_attendants, num_attendants)
                    
                    for pilot in selected_pilots:
                        execute_insert(cursor, query, (pilot[0], source_id, dest_id, departure_time))
                        assignments_made += 1
                    for attendant in selected_attendants:
                        execute_insert(cursor, query, (attendant[0], source_id, dest_id, departure_time))
                        assignments_made += 1
    
    print(f"Generated {assignments_made} crew assignments")

def generate_faker_orders(cursor, min_count=20):
    """Generate orders (excluding managers)."""
    print(f"Generating {min_count} orders with faker...")
    cursor.execute("SELECT COUNT(*) FROM Order_Table")
    current_count = cursor.fetchone()[0]
    needed = max(0, min_count - current_count)
    
    if needed == 0:
        print(f"Already have {current_count} orders, skipping...")
        return
    
    # Get users who are NOT managers
    cursor.execute("""
        SELECT u.email FROM User u
        LEFT JOIN Registered_Customer rc ON u.email = rc.email
        LEFT JOIN Employee e ON u.email = CAST(e.id_number AS CHAR)
        LEFT JOIN Manager m ON e.id_number = m.id_number
        WHERE m.id_number IS NULL
    """)
    available_users = [row[0] for row in cursor.fetchall()]
    
    # Get available flights (only Active flights for booking)
    cursor.execute("""
        SELECT source_airport_id, dest_airport_id, departure_time, aircraft_id, economy_price, business_price 
        FROM Flight 
        WHERE flight_status = 'Active' AND departure_time > NOW()
    """)
    flights = cursor.fetchall()
    
    if not available_users or not flights:
        print("No available users or flights for orders")
        return
    
    # Get max order code
    cursor.execute("SELECT MAX(order_code) FROM Order_Table")
    max_order = cursor.fetchone()[0] or 0
    
    orders = []
    order_seats = []
    statuses = ['Active', 'Completed', 'System Cancellation', 'Client Cancellation']
    
    attempts = 0
    max_attempts = needed * 10  # Allow many attempts to find available seats
    
    while len(orders) < needed and attempts < max_attempts:
        attempts += 1
        order_code = max_order + len(orders) + 1
        customer_email = random.choice(available_users)
        flight = random.choice(flights)
        source_id, dest_id, departure_time, aircraft_id, economy_price, business_price = flight
        
        # Order date before flight departure
        order_date = fake_en.date_time_between(
            start_date=departure_time - timedelta(days=90),
            end_date=departure_time - timedelta(hours=1)
        )
        
        # Select seat class
        is_business = random.random() < 0.3 and business_price is not None
        price = business_price if is_business else economy_price
        
        # Get available seats for this flight
        cursor.execute("""
            SELECT s.row_number, s.column_number FROM Seat s
            WHERE s.aircraft_id = %s AND s.is_business = %s
            AND (s.aircraft_id, s.is_business, s.row_number, s.column_number) NOT IN (
                SELECT os.aircraft_id, os.is_business, os.row_number, os.column_number
                FROM Order_Seats os
                JOIN Order_Table ot ON os.order_code = ot.order_code
                WHERE ot.source_airport_id = %s AND ot.dest_airport_id = %s AND ot.departure_time = %s
            )
            ORDER BY s.row_number, s.column_number
            LIMIT 10
        """, (aircraft_id, is_business, source_id, dest_id, departure_time))
        
        available_seats = cursor.fetchall()
        if not available_seats:
            continue  # No available seats for this flight, try another
        
        num_seats = min(random.randint(1, 3), len(available_seats))
        selected_seats = available_seats[:num_seats]
        total_payment = price * num_seats
        
        status = random.choice(statuses)
        
        # Apply 5% cancellation fee for Client Cancellation orders
        if status == 'Client Cancellation':
            total_payment = round(total_payment * 0.05)
        
        orders.append((order_code, order_date, total_payment, status, customer_email, source_id, dest_id, departure_time))
        
        # Add seat assignments
        for row_num, col_num in selected_seats:
            order_seats.append((order_code, aircraft_id, is_business, row_num, col_num))
    
    query = "INSERT IGNORE INTO Order_Table (order_code, order_date, total_payment, order_status, customer_email, source_airport_id, dest_airport_id, departure_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    inserted_count = 0
    for order in orders:
        try:
            cursor.execute(query, order)
            inserted_count += 1
        except mysql.connector.errors.IntegrityError:
            pass  # Duplicate order code, skip
    
    query_seats = "INSERT IGNORE INTO Order_Seats (order_code, aircraft_id, is_business, `row_number`, `column_number`) VALUES (%s, %s, %s, %s, %s)"
    for seat in order_seats:
        execute_insert(cursor, query_seats, seat)
    
    # Verify we have enough orders
    cursor.execute("SELECT COUNT(*) FROM Order_Table")
    final_count = cursor.fetchone()[0]
    if final_count < min_count:
        # Try to generate more orders if we're still short
        additional_needed = min_count - final_count
        additional_attempts = 0
        max_additional_attempts = additional_needed * 20
        
        while final_count < min_count and additional_attempts < max_additional_attempts:
            additional_attempts += 1
            order_code = max_order + final_count + 1
            customer_email = random.choice(available_users)
            flight = random.choice(flights)
            source_id, dest_id, departure_time, aircraft_id, economy_price, business_price = flight
            
            # Try economy class first (more seats available)
            is_business = False
            price = economy_price
            
            cursor.execute("""
                SELECT s.row_number, s.column_number FROM Seat s
                WHERE s.aircraft_id = %s AND s.is_business = %s
                AND (s.aircraft_id, s.is_business, s.row_number, s.column_number) NOT IN (
                    SELECT os.aircraft_id, os.is_business, os.row_number, os.column_number
                    FROM Order_Seats os
                    JOIN Order_Table ot ON os.order_code = ot.order_code
                    WHERE ot.source_airport_id = %s AND ot.dest_airport_id = %s AND ot.departure_time = %s
                )
                LIMIT 1
            """, (aircraft_id, is_business, source_id, dest_id, departure_time))
            
            seat = cursor.fetchone()
            if seat:
                row_num, col_num = seat
                order_date = fake_en.date_time_between(
                    start_date=departure_time - timedelta(days=90),
                    end_date=departure_time - timedelta(hours=1)
                )
                status = random.choice(statuses)
                
                # Apply 5% cancellation fee for Client Cancellation orders
                final_price = price
                if status == 'Client Cancellation':
                    final_price = round(price * 0.05)
                
                try:
                    cursor.execute(query, (order_code, order_date, final_price, status, customer_email, source_id, dest_id, departure_time))
                    cursor.execute(query_seats, (order_code, aircraft_id, is_business, row_num, col_num))
                    final_count += 1
                except mysql.connector.errors.IntegrityError:
                    pass
    
    print(f"Generated orders. Total orders now: {final_count}")

def drop_and_recreate_schema(cursor):
    """Drop all tables and recreate schema."""
    print("=" * 60)
    print("Dropping existing tables and recreating schema...")
    print("=" * 60)
    
    # Read schema file
    with open('sql/schema.sql', 'r') as f:
        schema_sql = f.read()
    
    # Execute all statements (DROP and CREATE)
    statements = schema_sql.split(';')
    for statement in statements:
        if statement.strip():
            try:
                cursor.execute(statement)
            except mysql.connector.errors.ProgrammingError as e:
                # Ignore errors for tables that don't exist (DROP IF EXISTS should handle this, but just in case)
                error_msg = str(e).lower()
                if "doesn't exist" not in error_msg and "unknown table" not in error_msg:
                    # Re-raise if it's a different error
                    raise
            except mysql.connector.errors.OperationalError as e:
                # Some MySQL versions might raise OperationalError
                error_msg = str(e).lower()
                if "doesn't exist" not in error_msg and "unknown table" not in error_msg:
                    raise
    
    print("Schema recreated successfully!")
    print("=" * 60)

def create_fully_booked_flights(cursor):
    """Create some Fully Booked flights by booking all available seats."""
    # Get Active flights that are in the future
    cursor.execute("""
        SELECT F.source_airport_id, F.dest_airport_id, F.departure_time, F.aircraft_id, F.economy_price, F.business_price
        FROM Flight F
        WHERE F.flight_status = 'Active' 
        AND F.departure_time > NOW()
        ORDER BY RAND()
        LIMIT 5
    """)
    flights_to_fill = cursor.fetchall()
    
    # Get available users
    cursor.execute("""
        SELECT u.email FROM User u
        LEFT JOIN Registered_Customer rc ON u.email = rc.email
        LEFT JOIN Employee e ON u.email = CAST(e.id_number AS CHAR)
        LEFT JOIN Manager m ON e.id_number = m.id_number
        WHERE m.id_number IS NULL
    """)
    available_users = [row[0] for row in cursor.fetchall()]
    
    if not available_users:
        return
    
    # Get max order code
    cursor.execute("SELECT COALESCE(MAX(order_code), 0) FROM Order_Table")
    max_order = cursor.fetchone()[0]
    
    order_statuses = ['Active', 'Completed', 'System Cancellation', 'Client Cancellation']
    
    for flight in flights_to_fill:
        source_id, dest_id, departure_time, aircraft_id, economy_price, business_price = flight
        
        # Get all available seats for this flight
        cursor.execute("""
            SELECT s.row_number, s.column_number, s.is_business
            FROM Seat s
            WHERE s.aircraft_id = %s
            AND (s.aircraft_id, s.is_business, s.row_number, s.column_number) NOT IN (
                SELECT os.aircraft_id, os.is_business, os.row_number, os.column_number
                FROM Order_Seats os
                JOIN Order_Table ot ON os.order_code = ot.order_code
                WHERE ot.source_airport_id = %s 
                AND ot.dest_airport_id = %s 
                AND ot.departure_time = %s
                AND ot.order_status NOT IN ('Client Cancellation', 'System Cancellation')
            )
            ORDER BY s.is_business, s.row_number, s.column_number
        """, (aircraft_id, source_id, dest_id, departure_time))
        
        available_seats = cursor.fetchall()
        
        if not available_seats:
            continue  # Already fully booked
        
        # Book all remaining seats
        order_code = max_order + 1
        max_order += 1
        customer_email = random.choice(available_users)
        
        # Calculate total price
        total_price = 0
        for row_num, col_num, is_business in available_seats:
            price = business_price if is_business and business_price else economy_price
            total_price += price
        
        # Order date before flight
        order_date = fake_en.date_time_between(
            start_date=departure_time - timedelta(days=90),
            end_date=departure_time - timedelta(hours=1)
        )
        
        # Use Active status for fully booked flights
        order_status = 'Active'
        
        try:
            # Insert order
            cursor.execute("""
                INSERT INTO Order_Table (order_code, order_date, total_payment, order_status, customer_email, 
                                       source_airport_id, dest_airport_id, departure_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (order_code, order_date, total_price, order_status, customer_email, source_id, dest_id, departure_time))
            
            # Insert all seat assignments
            for row_num, col_num, is_business in available_seats:
                cursor.execute("""
                    INSERT INTO Order_Seats (order_code, aircraft_id, is_business, `row_number`, `column_number`)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_code, aircraft_id, is_business, row_num, col_num))
        except mysql.connector.errors.IntegrityError:
            # Skip if there's a conflict
            pass

def update_flight_statuses_realistic(cursor):
    """Update flight statuses to reflect reality based on seat availability and departure time."""
    # Import the update function from flight_service
    # Since we can't easily import it here, we'll replicate the logic
    
    # 1. Update departed flights to 'Completed'
    cursor.execute("""
        UPDATE Flight 
        SET flight_status = 'Completed'
        WHERE flight_status IN ('Active', 'Fully Booked')
        AND departure_time < NOW()
    """)
    
    # 2. Update Active flights to 'Fully Booked' if all seats are taken
    cursor.execute("""
        UPDATE Flight F
        SET flight_status = 'Fully Booked'
        WHERE F.flight_status = 'Active'
        AND F.departure_time > NOW()
        AND NOT EXISTS (
            SELECT 1
            FROM Seat S
            WHERE S.aircraft_id = F.aircraft_id
            AND NOT EXISTS (
                SELECT 1
                FROM Order_Seats OS
                JOIN Order_Table O ON OS.order_code = O.order_code
                WHERE OS.aircraft_id = S.aircraft_id
                AND OS.is_business = S.is_business
                AND OS.row_number = S.row_number
                AND OS.column_number = S.column_number
                AND O.source_airport_id = F.source_airport_id
                AND O.dest_airport_id = F.dest_airport_id
                AND O.departure_time = F.departure_time
                AND O.order_status NOT IN ('Client Cancellation', 'System Cancellation')
            )
        )
    """)
    
    # 3. Update 'Fully Booked' flights back to 'Active' if seats become available
    cursor.execute("""
        UPDATE Flight F
        SET flight_status = 'Active'
        WHERE F.flight_status = 'Fully Booked'
        AND F.departure_time > NOW()
        AND EXISTS (
            SELECT 1
            FROM Seat S
            WHERE S.aircraft_id = F.aircraft_id
            AND NOT EXISTS (
                SELECT 1
                FROM Order_Seats OS
                JOIN Order_Table O ON OS.order_code = O.order_code
                WHERE OS.aircraft_id = S.aircraft_id
                AND OS.is_business = S.is_business
                AND OS.row_number = S.row_number
                AND OS.column_number = S.column_number
                AND O.source_airport_id = F.source_airport_id
                AND O.dest_airport_id = F.dest_airport_id
                AND O.departure_time = F.departure_time
                AND O.order_status NOT IN ('Client Cancellation', 'System Cancellation')
            )
        )
    """)

def generate_all_fake_data(drop_schema=True):
    """Main function to generate all fake data.
    
    Args:
        drop_schema: If True, drop and recreate schema first. Set to False if schema already exists.
    """
    print("=" * 60)
    print("Starting fake data generation...")
    print("=" * 60)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Drop and recreate schema first (if requested)
        if drop_schema:
            drop_and_recreate_schema(cursor)
            conn.commit()
        
        # Insert seed data first
        print("\n--- INSERTING SEED DATA ---")
        insert_seed_airports(cursor)
        insert_seed_routes(cursor)
        insert_seed_aircraft(cursor)
        insert_seed_aircraft_classes(cursor)
        insert_seed_seats(cursor)
        insert_seed_employees(cursor)
        insert_seed_flight_crew(cursor)
        insert_seed_managers(cursor)
        insert_seed_users(cursor)
        insert_seed_phones(cursor)
        insert_seed_registered_customers(cursor)
        insert_seed_flights(cursor)
        insert_seed_crew_assignments(cursor)
        insert_seed_orders(cursor)
        insert_seed_order_seats(cursor)
        
        conn.commit()
        print("\n--- SEED DATA INSERTED ---\n")
        
        # Generate faker data
        print("--- GENERATING FAKER DATA ---")
        generate_faker_airports(cursor, min_count=20)
        generate_faker_routes(cursor, min_count=20)
        generate_faker_aircraft(cursor, min_count=20)
        generate_faker_aircraft_classes(cursor)
        generate_faker_seats(cursor)
        generate_faker_employees(cursor, min_count=20)
        generate_faker_flight_crew(cursor)
        generate_faker_users(cursor, min_count=20)
        generate_faker_phones(cursor)
        generate_faker_registered_customers(cursor)
        generate_faker_flights(cursor, min_count=50)
        generate_faker_crew_assignments(cursor)
        generate_faker_orders(cursor, min_count=20)
        
        # Create some Fully Booked flights by booking all their seats
        print("Creating Fully Booked flights...")
        create_fully_booked_flights(cursor)
        
        # Update all flight statuses to reflect reality
        print("Updating flight statuses to reflect reality...")
        update_flight_statuses_realistic(cursor)
        
        conn.commit()
        print("\n--- FAKER DATA GENERATED ---\n")
        
        print("=" * 60)
        print("Fake data generation complete!")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    generate_all_fake_data()

