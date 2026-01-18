"""
Generate fake data for FLYTAU database using Faker library.
Merges seed data with improved naming and extends with faker-generated data.
"""
import mysql.connector
from faker import Faker
from datetime import datetime, timedelta
import random
import math
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

# Well-known names for employees and users
WELL_KNOWN_FIRST_NAMES = [
    'Michael', 'David', 'James', 'Robert', 'John', 'William', 'Richard', 'Joseph',
    'Thomas', 'Christopher', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald',
    'Steven', 'Paul', 'Andrew', 'Joshua', 'Kenneth', 'Kevin', 'Brian', 'George',
    'Sarah', 'Emily', 'Jessica', 'Jennifer', 'Michelle', 'Melissa', 'Amy',
    'Rebecca', 'Laura', 'Elizabeth', 'Lauren', 'Nicole', 'Ashley', 'Amanda',
    'Lisa', 'Stephanie', 'Kimberly', 'Megan', 'Rachel', 'Angela', 'Emma'
]

WELL_KNOWN_LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas',
    'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris',
    'Clark', 'Lewis', 'Robinson', 'Walker', 'Young', 'King', 'Wright', 'Scott',
    'Green', 'Adams', 'Baker', 'Nelson', 'Hill', 'Campbell', 'Mitchell', 'Roberts'
]

# Common Hebrew names for managers, pilots, and flight attendants
HEBREW_MALE_FIRST_NAMES = [
    'דוד', 'יוסף', 'משה', 'אברהם', 'יעקב', 'דני', 'רון', 'אור', 'נועם', 'איתי',
    'יונתן', 'עמית', 'אלון', 'תומר', 'עומר', 'יובל', 'אורן', 'ארז', 'עידו', 'רועי',
    'שי', 'עמיר', 'אליעד', 'אופק', 'אליאור', 'אלירן', 'אליאב', 'יואב', 'אוריאל', 'אליעזר',
    'אליהו', 'אלישע', 'בנימין', 'גד', 'יהודה', 'ראובן', 'שמעון', 'אשר', 'נפתלי', 'דן',
    'זבולון', 'אפרים', 'מנשה', 'יואל', 'עמוס', 'מיכאל', 'גבריאל', 'רפאל', 'אליה', 'אליאן'
]

HEBREW_FEMALE_FIRST_NAMES = [
    'שרה', 'רחל', 'לאה', 'מיכל', 'תמר', 'נועה', 'מאיה', 'עדי', 'רותם', 'יעל',
    'מור', 'ליאור', 'שירה', 'אביגיל', 'אלה', 'ענבר', 'רוני', 'דנה', 'ליה', 'רות',
    'אסתר', 'מרים', 'חנה', 'דבורה', 'רבקה', 'אורית', 'עינת', 'לימור', 'שרית', 'מירי',
    'אורלי', 'ענת', 'ליאת', 'שירי', 'מירב', 'נילי', 'גלית', 'טל', 'קרן', 'חגית'
]

HEBREW_LAST_NAMES = [
    'כהן', 'לוי', 'מזרחי', 'דוד', 'אברהם', 'ישראלי', 'בן דוד', 'עזרא', 'שלום', 'יוסף',
    'משה', 'יעקב', 'אהרון', 'יצחק', 'דניאל', 'שמואל', 'בן ישי', 'בן שמואל', 'בן משה', 'בן יוסף',
    'בן יעקב', 'בן אברהם', 'בן יצחק', 'בן אהרון', 'בן דניאל', 'בן שמואל', 'בן יוסף', 'בן יעקב', 'בן אברהם', 'בן יצחק',
    'בן אהרון', 'בן דניאל', 'בן שמואל', 'בן יוסף', 'בן יעקב', 'בן אברהם', 'בן יצחק', 'בן אהרון', 'בן דניאל', 'בן שמואל'
]

def get_db_connection():
    """Get database connection."""
    return mysql.connector.connect(**DB_CONFIG)

def execute_insert(cursor, query, values):
    """Execute INSERT IGNORE query."""
    try:
        cursor.execute(query, values)
    except mysql.connector.errors.IntegrityError:
        pass  # Ignore duplicates

def validate_crew_join_date(cursor, employee_id, departure_time):
    """
    Validate that crew member's start_work_date is before or equal to departure_time.
    
    Args:
        cursor: Database cursor
        employee_id: Employee ID to check
        departure_time: Flight departure time (datetime or string)
    
    Returns:
        True if valid (start_work_date <= departure_time), False otherwise
    """
    try:
        # Get employee start_work_date
        cursor.execute("SELECT start_work_date FROM Employee WHERE id_number = %s", (employee_id,))
        result = cursor.fetchone()
        if not result or not result[0]:
            return True  # No start date means always valid
        
        start_work_date = result[0]
        
        # Parse start_work_date
        if isinstance(start_work_date, str):
            try:
                start_work_date = datetime.strptime(start_work_date, '%Y-%m-%d').date()
            except ValueError:
                try:
                    start_work_date = datetime.strptime(start_work_date, '%Y-%m-%d %H:%M:%S').date()
                except ValueError:
                    return True  # Can't parse, assume valid
        elif isinstance(start_work_date, datetime):
            start_work_date = start_work_date.date()
        elif hasattr(start_work_date, 'date'):
            start_work_date = start_work_date.date()
        
        # Parse departure_time
        if isinstance(departure_time, str):
            try:
                departure_dt = datetime.strptime(departure_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    departure_dt = datetime.strptime(departure_time, '%Y-%m-%dT%H:%M')
                except ValueError:
                    return True  # Can't parse, assume valid
        else:
            departure_dt = departure_time
        
        departure_date = departure_dt.date() if isinstance(departure_dt, datetime) else departure_dt
        
        # Validate: start_work_date must be <= departure_date
        return start_work_date <= departure_date
    except Exception:
        return True  # On error, assume valid to avoid blocking generation

def check_crew_conflict(cursor, employee_id, departure_time, flight_duration_minutes):
    """
    Check if crew member has a conflicting assignment at the same time.
    
    Args:
        cursor: Database cursor
        employee_id: Employee ID to check
        departure_time: Flight departure time (datetime or string)
        flight_duration_minutes: Flight duration in minutes
    
    Returns:
        True if there's a conflict, False otherwise
    """
    try:
        # Parse departure_time
        if isinstance(departure_time, str):
            try:
                departure_dt = datetime.strptime(departure_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    departure_dt = datetime.strptime(departure_time, '%Y-%m-%dT%H:%M')
                except ValueError:
                    return False  # Can't parse, assume no conflict
        else:
            departure_dt = departure_time
        
        # Calculate arrival time (departure + duration)
        arrival_time = departure_dt + timedelta(minutes=flight_duration_minutes)
        
        # Check for overlapping assignments
        # A conflict exists if another flight's time window overlaps with this one
        cursor.execute("""
            SELECT EFA.source_airport_id, EFA.dest_airport_id, EFA.departure_time, FR.flight_duration
            FROM Employee_Flight_Assignment EFA
            JOIN Flight_Route FR ON EFA.source_airport_id = FR.source_airport_id
                AND EFA.dest_airport_id = FR.dest_airport_id
            WHERE EFA.employee_id = %s
            AND (
                (EFA.departure_time >= %s AND EFA.departure_time < %s)
                OR (EFA.departure_time + INTERVAL FR.flight_duration MINUTE > %s 
                    AND EFA.departure_time + INTERVAL FR.flight_duration MINUTE <= %s)
                OR (EFA.departure_time < %s AND EFA.departure_time + INTERVAL FR.flight_duration MINUTE > %s)
            )
        """, (employee_id, departure_dt, arrival_time, departure_dt, arrival_time, departure_dt, departure_dt))
        
        conflicts = cursor.fetchall()
        return len(conflicts) > 0
    except Exception:
        return False  # On error, assume no conflict

def validate_aircraft_purchase_date(cursor, aircraft_id, departure_time):
    """
    Validate that aircraft purchase_date is before or equal to departure_time.
    
    Args:
        cursor: Database cursor
        aircraft_id: Aircraft ID to check
        departure_time: Flight departure time (datetime or string)
    
    Returns:
        True if valid (purchase_date <= departure_time), False otherwise
    """
    try:
        # Get aircraft purchase_date
        cursor.execute("SELECT purchase_date FROM Aircraft WHERE aircraft_id = %s", (aircraft_id,))
        result = cursor.fetchone()
        if not result or not result[0]:
            return True  # No purchase date means always valid
        
        purchase_date = result[0]
        
        # Parse purchase_date
        if isinstance(purchase_date, str):
            try:
                purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            except ValueError:
                try:
                    purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d %H:%M:%S').date()
                except ValueError:
                    return True  # Can't parse, assume valid
        elif isinstance(purchase_date, datetime):
            purchase_date = purchase_date.date()
        elif hasattr(purchase_date, 'date'):
            purchase_date = purchase_date.date()
        
        # Parse departure_time
        if isinstance(departure_time, str):
            try:
                departure_dt = datetime.strptime(departure_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    departure_dt = datetime.strptime(departure_time, '%Y-%m-%dT%H:%M')
                except ValueError:
                    return True  # Can't parse, assume valid
        else:
            departure_dt = departure_time
        
        departure_date = departure_dt.date() if isinstance(departure_dt, datetime) else departure_dt
        
        # Validate: purchase_date must be <= departure_date
        return purchase_date <= departure_date
    except Exception:
        return True  # On error, assume valid to avoid blocking generation

def format_employee_id(prefix, index):
    """Format employee ID with proper zero-padding to 9 digits total."""
    # prefix is 7 chars (e.g., '3000000'), need 2 more digits for 9-char ID
    # So for index 1-9: prefix + '00' + index, for 10-99: prefix + '0' + index, for 100+: prefix + index
    if index < 10:
        return f'{prefix}00{index}'
    elif index < 100:
        return f'{prefix}0{index}'
    else:
        return f'{prefix}{index}'

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

def get_airport_code(airport_name):
    """Extract airport code from airport name like 'Ben Gurion (TLV)' -> 'TLV'."""
    if '(' in airport_name and ')' in airport_name:
        return airport_name.split('(')[1].split(')')[0].strip()
    return None

def get_airport_coordinates(airport_code):
    """Get approximate coordinates for major airports (lat, lon)."""
    # Major airport coordinates (latitude, longitude)
    airport_coords = {
        'TLV': (32.0114, 34.8867),   # Tel Aviv
        'JFK': (40.6413, -73.7781),  # New York
        'LHR': (51.4700, -0.4543),   # London
        'CDG': (49.0097, 2.5479),    # Paris
        'DXB': (25.2532, 55.3657),   # Dubai
        'SIN': (1.3644, 103.9915),   # Singapore
        'HND': (35.5494, 139.7798),  # Tokyo Haneda
        'FRA': (50.0379, 8.5622),    # Frankfurt
        'AMS': (52.3105, 4.7683),    # Amsterdam
        'MAD': (40.4839, -3.5680),   # Madrid
        'FCO': (41.8003, 12.2389),   # Rome
        'BCN': (41.2971, 2.0785),     # Barcelona
        'MUC': (48.3538, 11.7861),    # Munich
        'VIE': (48.1103, 16.5697),    # Vienna
        'ZRH': (47.4647, 8.5492),     # Zurich
        'BRU': (50.9014, 4.4844),     # Brussels
        'CPH': (55.6180, 12.6561),    # Copenhagen
        'ARN': (59.6519, 17.9186),   # Stockholm
        'OSL': (60.1939, 11.1004),   # Oslo
        'HEL': (60.3172, 24.9633),    # Helsinki
        'DUB': (53.4264, -6.2499),    # Dublin
        'MAN': (53.3537, -2.2749),    # Manchester
        'BHX': (52.4539, -1.7480),    # Birmingham
        'GLA': (55.8719, -4.4331),    # Glasgow
        'EDI': (55.9500, -3.3725),    # Edinburgh
        'MXP': (45.6306, 8.7281),     # Milan
        'VCE': (45.5053, 12.3519),    # Venice
        'ATH': (37.9364, 23.9445),    # Athens
        'IST': (41.2753, 28.7519),    # Istanbul
        'CAI': (30.1127, 31.4000),   # Cairo
        'DOH': (25.2611, 51.5651),    # Doha
        'AUH': (24.4330, 54.6511),    # Abu Dhabi
        'BKK': (13.6811, 100.7472),   # Bangkok
        'HKG': (22.3080, 113.9185),   # Hong Kong
        'ICN': (37.4602, 126.4407),   # Seoul
        'SYD': (-33.9399, 151.1753),  # Sydney
        'MEL': (-37.6733, 144.8433),  # Melbourne
        'YYZ': (43.6772, -79.6306),   # Toronto
        'YVR': (49.1947, -123.1792),  # Vancouver
        'YUL': (45.4577, -73.7497),   # Montreal
        'MEX': (19.4363, -99.0721),   # Mexico City
        'GRU': (-23.4321, -46.4691),  # São Paulo
        'EZE': (-34.8222, -58.5358),  # Buenos Aires
        'JNB': (-26.1392, 28.2460),   # Johannesburg
        'CPT': (-33.9648, 18.6017),   # Cape Town
        'NBO': (-1.3192, 36.9278),    # Nairobi
        'LOS': (6.5774, 3.3211),      # Lagos
    }
    return airport_coords.get(airport_code)

def calculate_flight_duration_minutes(source_code, dest_code):
    """Calculate realistic flight duration in minutes based on airport codes.
    
    Uses known durations for common routes, or calculates based on distance.
    """
    # Known realistic flight durations (in minutes) for common routes
    known_durations = {
        ('TLV', 'JFK'): 660,   # ~11 hours (Tel Aviv to New York)
        ('JFK', 'TLV'): 660,   # ~11 hours (New York to Tel Aviv)
        ('TLV', 'LHR'): 300,   # ~5 hours (Tel Aviv to London)
        ('LHR', 'TLV'): 300,   # ~5 hours (London to Tel Aviv)
        ('TLV', 'CDG'): 270,   # ~4.5 hours (Tel Aviv to Paris)
        ('CDG', 'TLV'): 270,   # ~4.5 hours (Paris to Tel Aviv)
        ('JFK', 'LHR'): 420,   # ~7 hours (New York to London)
        ('LHR', 'JFK'): 420,   # ~7 hours (London to New York)
        ('JFK', 'CDG'): 450,   # ~7.5 hours (New York to Paris)
        ('CDG', 'JFK'): 450,   # ~7.5 hours (Paris to New York)
        ('LHR', 'CDG'): 75,    # ~1.25 hours (London to Paris)
        ('CDG', 'LHR'): 75,    # ~1.25 hours (Paris to London)
        ('DXB', 'TLV'): 180,  # ~3 hours (Dubai to Tel Aviv)
        ('TLV', 'DXB'): 180,   # ~3 hours (Tel Aviv to Dubai)
        ('DXB', 'LHR'): 420,   # ~7 hours (Dubai to London)
        ('LHR', 'DXB'): 420,   # ~7 hours (London to Dubai)
        ('SIN', 'DXB'): 480,   # ~8 hours (Singapore to Dubai)
        ('DXB', 'SIN'): 480,   # ~8 hours (Dubai to Singapore)
        ('HND', 'JFK'): 780,   # ~13 hours (Tokyo to New York)
        ('JFK', 'HND'): 780,   # ~13 hours (New York to Tokyo)
        ('SYD', 'DXB'): 840,   # ~14 hours (Sydney to Dubai)
        ('DXB', 'SYD'): 840,   # ~14 hours (Dubai to Sydney)
    }
    
    # Check if we have a known duration
    route_key = (source_code, dest_code)
    if route_key in known_durations:
        return known_durations[route_key]
    
    # Calculate based on distance using Haversine formula
    source_coords = get_airport_coordinates(source_code)
    dest_coords = get_airport_coordinates(dest_code)
    
    if source_coords and dest_coords:
        # Haversine formula to calculate great-circle distance
        lat1, lon1 = math.radians(source_coords[0]), math.radians(source_coords[1])
        lat2, lon2 = math.radians(dest_coords[0]), math.radians(dest_coords[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in miles
        R = 3959
        distance_miles = R * c
        
        # Average commercial jet speed: ~500 mph (800 km/h)
        # Add 30 minutes for takeoff/landing/taxiing
        flight_hours = (distance_miles / 500) + 0.5
        duration_minutes = int(flight_hours * 60)
        
        # Ensure minimum duration of 60 minutes and maximum of 1080 minutes (18 hours)
        duration_minutes = max(60, min(1080, duration_minutes))
        
        return duration_minutes
    else:
        # Default duration if airport codes not found: 3-6 hours
        return random.randint(180, 360)

def get_flight_duration_from_airports(cursor, source_airport_id, dest_airport_id):
    """Get realistic flight duration in minutes from airport IDs."""
    # Get airport names
    cursor.execute("SELECT airport_name FROM Airport WHERE airport_id = %s", (source_airport_id,))
    source_result = cursor.fetchone()
    cursor.execute("SELECT airport_name FROM Airport WHERE airport_id = %s", (dest_airport_id,))
    dest_result = cursor.fetchone()
    
    if source_result and dest_result:
        source_name = source_result[0]
        dest_name = dest_result[0]
        source_code = get_airport_code(source_name)
        dest_code = get_airport_code(dest_name)
        
        if source_code and dest_code:
            return calculate_flight_duration_minutes(source_code, dest_code)
    
    # Fallback: return a reasonable default (3-6 hours)
    return random.randint(180, 360)

def insert_seed_routes(cursor):
    """Insert seed flight routes with realistic durations."""
    print("Inserting seed routes...")
    routes = [
        (1, 2, 660),  # TLV -> JFK (~11h)
        (2, 1, 660),  # JFK -> TLV (~11h)
        (1, 3, 300),  # TLV -> LHR (~5h)
        (3, 1, 300),  # LHR -> TLV (~5h)
        (1, 4, 270),  # TLV -> CDG (~4.5h)
        (4, 1, 270)   # CDG -> TLV (~4.5h)
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
        cursor.execute("SELECT is_large FROM Aircraft WHERE aircraft_id = %s", (aircraft_id,))
        result = cursor.fetchone()
        is_large = result and result[0]
        
        if is_large:
            # Large plane: Business (2x2) and Economy (5x4)
            seats = [(aircraft_id, True, row, col) for row in range(1, 3) for col in range(1, 3)]
            seats.extend([(aircraft_id, False, row, col) for row in range(1, 6) for col in range(1, 5)])
        else:
            # Small plane: Economy only (5x4)
            seats = [(aircraft_id, False, row, col) for row in range(1, 6) for col in range(1, 5)]
        
        for seat in seats:
            execute_insert(cursor, query, seat)

def insert_seed_employees(cursor):
    """Insert seed employees with improved names."""
    print("Inserting seed employees with improved names...")
    
    # Managers with Hebrew names
    managers = [
        ('111111111', random.choice(HEBREW_MALE_FIRST_NAMES), None, random.choice(HEBREW_LAST_NAMES), 'Tel Aviv', 'Main Street', 10, '0501234567', '2020-01-01'),
        ('222222222', random.choice(HEBREW_MALE_FIRST_NAMES), random.choice(HEBREW_MALE_FIRST_NAMES), random.choice(HEBREW_LAST_NAMES), 'Haifa', 'Park Avenue', 20, '0502345678', '2021-02-01')
    ]
    
    # Pilots with Hebrew names (40 pilots = 4x original 10)
    used_full_names = set()
    pilots = []
    for i in range(1, 41):
        pilot_id = format_employee_id('3000000', i)
        # Ensure unique full name to avoid duplicates in reports
        for _ in range(100):
            first_name = random.choice(HEBREW_MALE_FIRST_NAMES)
            middle_name = random.choice(HEBREW_MALE_FIRST_NAMES) if random.random() > 0.5 else None
            last_name = random.choice(HEBREW_LAST_NAMES)
            full_name_key = (first_name, middle_name or "", last_name)
            if full_name_key not in used_full_names:
                used_full_names.add(full_name_key)
                break
        pilots.append((
            pilot_id, first_name, middle_name, last_name, 'Tel Aviv', fake_en.street_name(),
            i, f'050{3000000 + i}', '2022-01-01'
        ))
    
    # Attendants with Hebrew names (40 attendants = 4x original 10)
    attendants = []
    for i in range(1, 41):
        attendant_id = format_employee_id('4000000', i)
        # Ensure unique full name to avoid duplicates in reports
        for _ in range(100):
            first_name = random.choice(HEBREW_FEMALE_FIRST_NAMES)
            middle_name = random.choice(HEBREW_FEMALE_FIRST_NAMES) if random.random() > 0.5 else None
            last_name = random.choice(HEBREW_LAST_NAMES)
            full_name_key = (first_name, middle_name or "", last_name)
            if full_name_key not in used_full_names:
                used_full_names.add(full_name_key)
                break
        attendants.append((
            attendant_id, first_name, middle_name, last_name, 'Tel Aviv', fake_en.street_name(),
            i, f'050{4000000 + i}', '2023-01-01'
        ))
    
    query = "INSERT IGNORE INTO Employee (id_number, first_name, middle_name, last_name, city, street, house_number, phone, start_work_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    
    for emp in managers + pilots + attendants:
        execute_insert(cursor, query, emp)
    
    # Verify all pilots were inserted (300000001-300000040)
    cursor.execute("SELECT id_number FROM Employee WHERE id_number LIKE '3000000%' ORDER BY id_number")
    inserted_pilots = [row[0] for row in cursor.fetchall()]
    if len(inserted_pilots) < 40:
        print(f"WARNING: Only {len(inserted_pilots)} pilots inserted. Expected 40. IDs: {inserted_pilots}")
        # Try to insert missing pilots
        for pilot in pilots:
            if pilot[0] not in inserted_pilots:
                execute_insert(cursor, query, pilot)

def dedupe_employee_names(cursor):
    """Ensure employee display names are unique by appending id to duplicates."""
    print("De-duplicating employee names...")
    cursor.execute("""
        UPDATE Employee e
        JOIN (
            SELECT first_name, last_name, COUNT(*) AS cnt
            FROM Employee
            GROUP BY first_name, last_name
            HAVING COUNT(*) > 1
        ) d
          ON e.first_name = d.first_name
         AND e.last_name = d.last_name
        SET e.last_name = CONCAT(e.last_name, ' #', e.id_number)
        WHERE e.last_name NOT LIKE '% #%'
    """)
    print(f"Updated {cursor.rowcount} duplicate employee names.")

def insert_seed_flight_crew(cursor):
    """Insert seed flight crew assignments."""
    print("Inserting seed flight crew...")
    
    # Pilots: first 16 trained for long flights (4x original 4), rest not
    pilots_crew = [(format_employee_id('3000000', i), i <= 16, True) for i in range(1, 41)]
    
    # Attendants: first 24 trained for long flights (4x original 6), rest not
    attendants_crew = [(format_employee_id('4000000', i), i <= 24, False) for i in range(1, 41)]
    
    query = "INSERT IGNORE INTO Flight_Crew (id_number, trained_for_long_flights, is_pilot) VALUES (%s, %s, %s)"
    for crew in pilots_crew + attendants_crew:
        execute_insert(cursor, query, crew)
    
    # Verify all pilots were inserted into Flight_Crew (300000001-300000040)
    cursor.execute("SELECT id_number FROM Flight_Crew WHERE id_number LIKE '3000000%' AND is_pilot = TRUE ORDER BY id_number")
    inserted_crew_pilots = [row[0] for row in cursor.fetchall()]
    if len(inserted_crew_pilots) < 40:
        print(f"WARNING: Only {len(inserted_crew_pilots)} pilots in Flight_Crew. Expected 40. IDs: {inserted_crew_pilots}")
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
    
    # Validate seed order statuses based on flight departure times
    # Update 'Active' orders for past flights to 'Completed'
    cursor.execute("""
        UPDATE Order_Table
        SET order_status = 'Completed'
        WHERE order_status = 'Active'
        AND departure_time < NOW()
    """)
    updated_count = cursor.rowcount
    if updated_count > 0:
        print(f"  Updated {updated_count} seed orders for past flights to Completed")

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

def ensure_all_airport_routes(cursor):
    """Ensure every pair of airports has a route from one to another."""
    print("Ensuring all airport pairs have routes...")
    
    # Get all airports
    cursor.execute("SELECT airport_id FROM Airport ORDER BY airport_id")
    airport_ids = [row[0] for row in cursor.fetchall()]
    
    if len(airport_ids) < 2:
        print("Not enough airports to generate routes")
        return
    
    # Get existing routes
    cursor.execute("SELECT source_airport_id, dest_airport_id FROM Flight_Route")
    existing = set((row[0], row[1]) for row in cursor.fetchall())
    
    # Generate all possible routes (every airport to every other airport)
    all_routes = []
    for source in airport_ids:
        for dest in airport_ids:
            if source != dest:
                all_routes.append((source, dest))
    
    # Find missing routes
    missing_routes = [r for r in all_routes if r not in existing]
    
    if not missing_routes:
        expected_count = len(airport_ids) * (len(airport_ids) - 1)
        print(f"All {expected_count} routes already exist for {len(airport_ids)} airports")
        return
    
    # Generate routes for missing pairs with realistic durations
    query = "INSERT IGNORE INTO Flight_Route (source_airport_id, dest_airport_id, flight_duration) VALUES (%s, %s, %s)"
    inserted_count = 0
    for source, dest in missing_routes:
        # Calculate realistic duration based on airport locations
        duration = get_flight_duration_from_airports(cursor, source, dest)
        try:
            cursor.execute(query, (source, dest, duration))
            inserted_count += 1
        except mysql.connector.errors.IntegrityError:
            pass  # Duplicate route, skip
    
    cursor.execute("SELECT COUNT(*) FROM Flight_Route")
    final_count = cursor.fetchone()[0]
    expected_count = len(airport_ids) * (len(airport_ids) - 1)
    print(f"Ensured all routes exist: {final_count} routes (expected {expected_count} for {len(airport_ids)} airports, inserted {inserted_count} new routes)")
    
    if final_count < expected_count:
        print(f"WARNING: Missing {expected_count - final_count} routes")

def generate_faker_routes(cursor, min_count=20):
    """Generate routes - ensures every airport pair has a route."""
    # Ensure all routes exist (n*(n-1) routes for n airports)
    ensure_all_airport_routes(cursor)

def generate_faker_aircraft(cursor, min_count=50):
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
    
    manufacturers = ['Boeing', 'Airbus', 'Dassault']
    aircraft = [
        (max_id + i + 1, random.choice(manufacturers), 
         fake_en.date_between(start_date='-10y', end_date='today'),
         random.choice([True, False]))
        for i in range(needed)
    ]
    
    query = "INSERT IGNORE INTO Aircraft (aircraft_id, manufacturer, purchase_date, is_large) VALUES (%s, %s, %s, %s)"
    for ac in aircraft:
        execute_insert(cursor, query, ac)
    print(f"Generated {len(aircraft)} additional aircraft")

def generate_faker_aircraft_classes(cursor):
    """Generate aircraft classes for all aircraft.
    Enforces business rule: Large aircraft MUST have business class, Small aircraft MUST NOT have business class.
    """
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
            # Big plane: MUST have Business and Economy
            business_rows = random.randint(2, 4)
            business_cols = random.randint(2, 4)
            economy_rows = random.randint(8, 15)
            economy_cols = random.randint(4, 6)
            execute_insert(cursor, query, (aircraft_id, True, business_rows, business_cols))
            execute_insert(cursor, query, (aircraft_id, False, economy_rows, economy_cols))
        else:
            # Small plane: Economy only (NO business class)
            economy_rows = random.randint(5, 10)
            economy_cols = random.randint(4, 6)
            execute_insert(cursor, query, (aircraft_id, False, economy_rows, economy_cols))
    print("Generated aircraft classes for all aircraft")

def validate_aircraft_class_rules(cursor):
    """Validate that aircraft class business rules are enforced:
    - Large aircraft MUST have business class
    - Small aircraft MUST NOT have business class
    """
    print("Validating aircraft class business rules...")
    
    # Check 1: All large aircraft must have business class
    cursor.execute("""
        SELECT a.aircraft_id, a.is_large
        FROM Aircraft a
        LEFT JOIN Aircraft_Class ac ON a.aircraft_id = ac.aircraft_id AND ac.is_business = TRUE
        WHERE a.is_large = TRUE AND ac.aircraft_id IS NULL
    """)
    large_without_business = cursor.fetchall()
    if large_without_business:
        print(f"ERROR: Found {len(large_without_business)} large aircraft without business class!")
        for aircraft_id, is_large in large_without_business:
            print(f"  Aircraft {aircraft_id} (is_large={is_large}) is missing business class")
        # Fix: Add business class to large aircraft missing it
        query = "INSERT IGNORE INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns) VALUES (%s, %s, %s, %s)"
        for aircraft_id, _ in large_without_business:
            business_rows = random.randint(2, 4)
            business_cols = random.randint(2, 4)
            execute_insert(cursor, query, (aircraft_id, True, business_rows, business_cols))
            print(f"  Fixed: Added business class to aircraft {aircraft_id}")
    
    # Check 2: No small aircraft should have business class
    cursor.execute("""
        SELECT DISTINCT a.aircraft_id, a.is_large
        FROM Aircraft a
        JOIN Aircraft_Class ac ON a.aircraft_id = ac.aircraft_id
        WHERE a.is_large = FALSE AND ac.is_business = TRUE
    """)
    small_with_business = cursor.fetchall()
    if small_with_business:
        print(f"ERROR: Found {len(small_with_business)} small aircraft with business class!")
        for aircraft_id, is_large in small_with_business:
            print(f"  Aircraft {aircraft_id} (is_large={is_large}) incorrectly has business class")
        # Fix: Remove business class from small aircraft
        for aircraft_id, _ in small_with_business:
            cursor.execute("DELETE FROM Aircraft_Class WHERE aircraft_id = %s AND is_business = TRUE", (aircraft_id,))
            # Also delete seats for business class
            cursor.execute("DELETE FROM Seat WHERE aircraft_id = %s AND is_business = TRUE", (aircraft_id,))
            print(f"  Fixed: Removed business class from aircraft {aircraft_id}")
    
    if not large_without_business and not small_with_business:
        print("All aircraft class business rules are correctly enforced")
    else:
        print("Fixed violations and re-validated")

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
        
        # Generate all seats for this class
        seats = [(aircraft_id, is_business, row, col) 
                 for row in range(1, num_rows + 1) 
                 for col in range(1, num_columns + 1)]
        for seat in seats:
            execute_insert(cursor, query, seat)
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
    
    employees = []
    cities = ['Tel Aviv', 'Haifa', 'Jerusalem', 'Beer Sheva', 'Netanya', 'Eilat']
    for i in range(needed):
        emp_id = str(max_id + i + 1).zfill(9)
        # Use Hebrew names for employees (they will become pilots/attendants)
        # Alternate between male and female names
        if random.random() > 0.5:
            first_name = random.choice(HEBREW_MALE_FIRST_NAMES)
            middle_name = random.choice(HEBREW_MALE_FIRST_NAMES) if random.random() > 0.5 else None
        else:
            first_name = random.choice(HEBREW_FEMALE_FIRST_NAMES)
            middle_name = random.choice(HEBREW_FEMALE_FIRST_NAMES) if random.random() > 0.5 else None
        last_name = random.choice(HEBREW_LAST_NAMES)
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
    # - With 100 flights, we need good coverage
    # - Minimum: 180 pilots (136 trained for long flights) and 220 attendants (148 trained for long flights) - 4x original
    min_pilots = 180  # 4x original 45
    min_trained_pilots = 136  # 4x original 34, for long flights
    min_attendants = 220  # 4x original 55
    min_trained_attendants = 148  # 4x original 37, for long flights
    
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
    
    users = [
        (fake_en.email(), 
         random.choice(WELL_KNOWN_FIRST_NAMES),
         random.choice(WELL_KNOWN_FIRST_NAMES) if random.random() > 0.5 else None,
         random.choice(WELL_KNOWN_LAST_NAMES))
        for _ in range(needed)
    ]
    
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
        
        # Select aircraft with purchase date validation
        aircraft_id = None
        max_retries = 10
        retry_count = 0
        
        while aircraft_id is None and retry_count < max_retries:
            if is_long:
                candidate_aircraft = random.choice(big_aircraft)
            else:
                # Short flights can use both
                candidate_aircraft = random.choice(big_aircraft + small_aircraft)
            
            # Validate aircraft purchase date
            if validate_aircraft_purchase_date(cursor, candidate_aircraft, departure_time):
                aircraft_id = candidate_aircraft
            else:
                retry_count += 1
        
        # Skip this flight if no valid aircraft found
        if aircraft_id is None:
            continue
        
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
        # Also validate join dates and check for conflicts
        available_pilots = []
        for p in pilots:
            # Check training requirement
            if is_long and not p[1]:
                continue  # Not trained for long flights
            # Check join date
            if not validate_crew_join_date(cursor, p[0], departure_time):
                continue  # Not yet joined
            # Check for conflicts
            if check_crew_conflict(cursor, p[0], departure_time, duration):
                continue  # Has conflicting assignment
            available_pilots.append(p)
        
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
        # Also validate join dates and check for conflicts
        available_attendants = []
        for a in attendants:
            # Check training requirement
            if is_long and not a[1]:
                continue  # Not trained for long flights
            # Check join date
            if not validate_crew_join_date(cursor, a[0], departure_time):
                continue  # Not yet joined
            # Check for conflicts
            if check_crew_conflict(cursor, a[0], departure_time, duration):
                continue  # Has conflicting assignment
            available_attendants.append(a)
        
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
                
                # Try with all pilots/attendants (relax training requirement if needed, but still validate join dates and conflicts)
                all_pilots = []
                for p in (pilots if not is_long else [p for p in pilots if p[1]] or pilots):
                    if validate_crew_join_date(cursor, p[0], departure_time) and not check_crew_conflict(cursor, p[0], departure_time, duration):
                        all_pilots.append(p)
                
                all_attendants = []
                for a in (attendants if not is_long else [a for a in attendants if a[1]] or attendants):
                    if validate_crew_join_date(cursor, a[0], departure_time) and not check_crew_conflict(cursor, a[0], departure_time, duration):
                        all_attendants.append(a)
                
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
        
        # Get available seats for this flight (explicitly exclude canceled orders)
        cursor.execute("""
            SELECT s.row_number, s.column_number FROM Seat s
            WHERE s.aircraft_id = %s AND s.is_business = %s
            AND (s.aircraft_id, s.is_business, s.row_number, s.column_number) NOT IN (
                SELECT os.aircraft_id, os.is_business, os.row_number, os.column_number
                FROM Order_Seats os
                JOIN Order_Table ot ON os.order_code = ot.order_code
                WHERE ot.source_airport_id = %s AND ot.dest_airport_id = %s AND ot.departure_time = %s
                AND ot.order_status NOT IN ('Client Cancellation', 'System Cancellation')
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
        
        # Validate order status matches flight departure time
        # 'Completed' orders can only exist for past flights
        if status == 'Completed' and departure_time > datetime.now():
            status = 'Active'  # Force Active for future flights
        
        # Apply payment rules based on status:
        # - Client Cancellation: 5% cancellation fee
        # - System Cancellation: 0 (full refund)
        if status == 'Client Cancellation':
            total_payment = round(total_payment * 0.05)
        elif status == 'System Cancellation':
            total_payment = 0  # Full refund for system cancellations
        
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
            
            # If System Cancellation, also cancel the corresponding flight
            if order[3] == 'System Cancellation':  # order[3] is order_status
                cursor.execute("""
                    UPDATE Flight 
                    SET flight_status = 'Canceled'
                    WHERE source_airport_id = %s 
                    AND dest_airport_id = %s 
                    AND departure_time = %s
                    AND flight_status != 'Canceled'
                """, (order[5], order[6], order[7]))  # order[5]=source_id, order[6]=dest_id, order[7]=departure_time
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
                    AND ot.order_status NOT IN ('Client Cancellation', 'System Cancellation')
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
                
                # Validate order status matches flight departure time
                # 'Completed' orders can only exist for past flights
                if status == 'Completed' and departure_time > datetime.now():
                    status = 'Active'  # Force Active for future flights
                
                # Apply payment rules based on status:
                # - Client Cancellation: 5% cancellation fee
                # - System Cancellation: 0 (full refund)
                final_price = price
                if status == 'Client Cancellation':
                    final_price = round(price * 0.05)
                elif status == 'System Cancellation':
                    final_price = 0  # Full refund for system cancellations
                
                try:
                    cursor.execute(query, (order_code, order_date, final_price, status, customer_email, source_id, dest_id, departure_time))
                    cursor.execute(query_seats, (order_code, aircraft_id, is_business, row_num, col_num))
                    
                    # If System Cancellation, also cancel the corresponding flight
                    if status == 'System Cancellation':
                        cursor.execute("""
                            UPDATE Flight 
                            SET flight_status = 'Canceled'
                            WHERE source_airport_id = %s 
                            AND dest_airport_id = %s 
                            AND departure_time = %s
                            AND flight_status != 'Canceled'
                        """, (source_id, dest_id, departure_time))
                    
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
    """
    Find some flights and book all their seats to create fully booked flights.
    This tests edge cases in seat availability.
    """
    # Get some random active future flights
    cursor.execute("""
        SELECT F.source_airport_id, F.dest_airport_id, F.departure_time, F.aircraft_id, F.economy_price, F.business_price
        FROM Flight F
        WHERE F.flight_status = 'Active' AND F.departure_time > NOW()
        ORDER BY RAND()
        LIMIT 3
    """)
    flights_to_book = cursor.fetchall()
    
    for flight in flights_to_book:
        source_id, dest_id, departure_time, aircraft_id, economy_price, business_price = flight
        
        # Get all available seats for this flight
        cursor.execute("""
            SELECT s.aircraft_id, s.is_business, s.row_number, s.column_number
            FROM Seat s
            WHERE s.aircraft_id = %s
            AND (s.aircraft_id, s.is_business, s.row_number, s.column_number) NOT IN (
                SELECT os.aircraft_id, os.is_business, os.row_number, os.column_number
                FROM Order_Seats os
                JOIN Order_Table ot ON os.order_code = ot.order_code
                WHERE ot.source_airport_id = %s AND ot.dest_airport_id = %s AND ot.departure_time = %s
                AND ot.order_status NOT IN ('Client Cancellation', 'System Cancellation')
            )
        """, (aircraft_id, source_id, dest_id, departure_time))
        
        available_seats = cursor.fetchall()
        if not available_seats:
            continue
        
        # Get a random customer
        cursor.execute("""
            SELECT email FROM Registered_Customer
            ORDER BY RAND()
            LIMIT 1
        """)
        customer = cursor.fetchone()
        if not customer:
            continue
        
        customer_email = customer[0]
        
        # Get max order code
        cursor.execute("SELECT MAX(order_code) FROM Order_Table")
        max_order = cursor.fetchone()[0] or 0
        order_code = max_order + 1
        
        # Create an order for all remaining seats
        order_date = fake_en.date_time_between(
            start_date=departure_time - timedelta(days=30),
            end_date=departure_time - timedelta(hours=1)
        )
        
        # Calculate total payment
        total_payment = sum(
            (business_price if seat[1] else economy_price)
            for seat in available_seats
        )
        
        # Insert order
        cursor.execute("""
            INSERT INTO Order_Table (order_code, order_date, total_payment, order_status, email, source_airport_id, dest_airport_id, departure_time)
            VALUES (%s, %s, %s, 'Active', %s, %s, %s, %s)
        """, (order_code, order_date, total_payment, customer_email, source_id, dest_id, departure_time))
        
        # Insert all seat bookings
        for seat in available_seats:
            cursor.execute("""
                INSERT INTO Order_Seats (order_code, aircraft_id, is_business, row_number, column_number)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_code, seat[0], seat[1], seat[2], seat[3]))

def generate_test_data_for_reports(cursor):
    """
    Generate additional test data specifically to ensure all manager reports charts have data.
    This includes:
    1. Completed flights with orders (for occupancy chart)
    2. More cancelled orders (for cancellation chart)
    3. Flights spread across multiple months (for plane activity chart)
    4. Employee flight assignments (for employee hours chart)
    """
    print("Generating data for occupancy chart (completed flights with orders)...")
    
    # 1. Create completed flights with orders for occupancy chart
    # Get some past flights
    cursor.execute("""
        SELECT F.source_airport_id, F.dest_airport_id, F.departure_time, F.aircraft_id, F.economy_price, F.business_price
        FROM Flight F
        WHERE F.departure_time < NOW() AND F.flight_status = 'Completed'
        ORDER BY RAND()
        LIMIT 10
    """)
    past_flights = cursor.fetchall()
    
    if not past_flights:
        # Create some past flights if none exist
        print("Creating past flights for occupancy testing...")
        cursor.execute("""
            SELECT source_airport_id, dest_airport_id FROM Flight_Route
            ORDER BY RAND() LIMIT 5
        """)
        routes = cursor.fetchall()
        
        cursor.execute("SELECT aircraft_id FROM Aircraft WHERE aircraft_id IS NOT NULL ORDER BY RAND() LIMIT 3")
        aircraft = cursor.fetchall()
        
        if routes and aircraft:
            for _ in range(10):
                route = random.choice(routes)
                aircraft_id = random.choice(aircraft)[0]
                
                # Create flight 30-90 days in the past
                departure_time = fake_en.date_time_between(start_date='-90d', end_date='-30d')
                
                cursor.execute("""
                    SELECT economy_price, business_price FROM Flight_Route
                    WHERE source_airport_id = %s AND dest_airport_id = %s
                """, route)
                prices = cursor.fetchone()
                
                if prices:
                    cursor.execute("""
                        INSERT IGNORE INTO Flight (source_airport_id, dest_airport_id, departure_time, aircraft_id, economy_price, business_price, flight_status)
                        VALUES (%s, %s, %s, %s, %s, %s, 'Completed')
                    """, (route[0], route[1], departure_time, aircraft_id, prices[0], prices[1]))
            
            # Re-fetch past flights
            cursor.execute("""
                SELECT F.source_airport_id, F.dest_airport_id, F.departure_time, F.aircraft_id, F.economy_price, F.business_price
                FROM Flight F
                WHERE F.departure_time < NOW() AND F.flight_status = 'Completed'
                ORDER BY RAND()
                LIMIT 10
            """)
            past_flights = cursor.fetchall()
    
    # Create orders for past flights
    if past_flights:
        print(f"Creating orders for {len(past_flights)} past flights...")
        cursor.execute("SELECT MAX(order_code) FROM Order_Table")
        max_order = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT email FROM Registered_Customer ORDER BY RAND()")
        customers = [row[0] for row in cursor.fetchall()]
        
        if customers:
            for flight in past_flights:
                source_id, dest_id, departure_time, aircraft_id, economy_price, business_price = flight
                
                # Get available seats
                cursor.execute("""
                    SELECT `row_number`, `column_number`, `is_business` FROM Seat
                    WHERE aircraft_id = %s
                    ORDER BY RAND()
                    LIMIT 20
                """, (aircraft_id,))
                seats = cursor.fetchall()
                
                if seats:
                    # Create 2-3 orders for this flight to simulate occupancy
                    for _ in range(random.randint(2, 3)):
                        max_order += 1
                        customer_email = random.choice(customers)
                        order_date = fake_en.date_time_between(
                            start_date=departure_time - timedelta(days=60),
                            end_date=departure_time - timedelta(hours=1)
                        )
                        
                        # Select random seats
                        num_seats = min(random.randint(1, 4), len(seats))
                        selected_seats = random.sample(seats, num_seats)
                        
                        # Calculate payment
                        total_payment = sum(
                            (business_price if seat[2] else economy_price)
                            for seat in selected_seats
                        )
                        
                        try:
                            cursor.execute("""
                                INSERT INTO Order_Table (order_code, order_date, total_payment, order_status, email, source_airport_id, dest_airport_id, departure_time)
                                VALUES (%s, %s, %s, 'Completed', %s, %s, %s, %s)
                            """, (max_order, order_date, total_payment, customer_email, source_id, dest_id, departure_time))
                            
                            # Insert seats
                            for seat in selected_seats:
                                cursor.execute("""
                                    INSERT INTO Order_Seats (order_code, aircraft_id, is_business, row_number, column_number)
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (max_order, aircraft_id, seat[2], seat[0], seat[1]))
                        except:
                            pass  # Ignore duplicates
    
    # 2. Generate more cancelled orders for cancellation chart
    print("Generating cancelled orders for cancellation chart...")
    cursor.execute("SELECT MAX(order_code) FROM Order_Table")
    max_order = cursor.fetchone()[0] or 0
    
    cursor.execute("""
        SELECT F.source_airport_id, F.dest_airport_id, F.departure_time, F.aircraft_id, F.economy_price, F.business_price
        FROM Flight F
        WHERE F.departure_time > NOW() AND F.flight_status = 'Active'
        ORDER BY RAND()
        LIMIT 15
    """)
    flights_for_cancellation = cursor.fetchall()
    
    cursor.execute("SELECT email FROM Registered_Customer ORDER BY RAND()")
    customers = [row[0] for row in cursor.fetchall()]
    
    if flights_for_cancellation and customers:
        for flight in flights_for_cancellation:
            source_id, dest_id, departure_time, aircraft_id, economy_price, business_price = flight
            
            max_order += 1
            customer_email = random.choice(customers)
            order_date = fake_en.date_time_between(
                start_date=departure_time - timedelta(days=60),
                end_date=departure_time - timedelta(days=1)
            )
            
            # 50% chance of Client Cancellation, 50% System Cancellation
            status = random.choice(['Client Cancellation', 'System Cancellation'])
            
            # Get a seat
            cursor.execute("""
                SELECT `row_number`, `column_number`, `is_business` FROM Seat
                WHERE aircraft_id = %s
                ORDER BY RAND()
                LIMIT 1
            """, (aircraft_id,))
            seat = cursor.fetchone()
            
            if seat:
                price = business_price if seat[2] else economy_price
                total_payment = price * 0.05 if status == 'Client Cancellation' else 0
                
                try:
                    cursor.execute("""
                        INSERT INTO Order_Table (order_code, order_date, total_payment, order_status, email, source_airport_id, dest_airport_id, departure_time)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (max_order, order_date, total_payment, status, customer_email, source_id, dest_id, departure_time))
                    
                    cursor.execute("""
                        INSERT INTO Order_Seats (order_code, aircraft_id, is_business, row_number, column_number)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (max_order, aircraft_id, seat[2], seat[0], seat[1]))
                except:
                    pass
    
    # 3. Ensure employee flight assignments exist
    print("Ensuring employee flight assignments for employee hours chart...")
    cursor.execute("""
        SELECT COUNT(*) FROM Employee_Flight_Assignment
    """)
    assignment_count = cursor.fetchone()[0]
    
    if assignment_count < 50:
        print(f"Only {assignment_count} assignments exist, generating more...")
        # This will be handled by the existing generate_faker_crew_assignments function
        # Just ensure it runs
    
    print("Test data generation for reports complete!")

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

def validate_orders_for_canceled_flights(cursor):
    """
    Validate that all orders for canceled flights are marked as System Cancellation with payment = 0.
    """
    print("Validating orders for canceled flights...")
    cursor.execute("""
        UPDATE Order_Table O
        JOIN Flight F ON O.source_airport_id = F.source_airport_id
            AND O.dest_airport_id = F.dest_airport_id
            AND O.departure_time = F.departure_time
        SET O.order_status = 'System Cancellation',
            O.total_payment = 0
        WHERE F.flight_status = 'Canceled'
        AND O.order_status = 'Active'
    """)
    updated_count = cursor.rowcount
    if updated_count > 0:
        print(f"  Updated {updated_count} orders for canceled flights to System Cancellation")

def update_orders_for_past_flights(cursor):
    """
    Update all Active orders for past flights to Completed status.
    """
    print("Updating orders for past flights...")
    cursor.execute("""
        UPDATE Order_Table
        SET order_status = 'Completed'
        WHERE order_status = 'Active'
        AND departure_time < NOW()
    """)
    updated_count = cursor.rowcount
    if updated_count > 0:
        print(f"  Updated {updated_count} orders for past flights to Completed")

def validate_order_flight_relationships(cursor):
    """
    Comprehensive validation of order-flight relationships.
    Ensures:
    - No Completed orders for future flights
    - All System Cancellation orders have corresponding Canceled flights
    - All orders for canceled flights are System Cancellation
    - All orders for past flights are Completed
    """
    print("Validating order-flight relationships...")
    
    # Check 1: No Completed orders for future flights
    cursor.execute("""
        SELECT COUNT(*) FROM Order_Table
        WHERE order_status = 'Completed'
        AND departure_time > NOW()
    """)
    invalid_completed = cursor.fetchone()[0]
    if invalid_completed > 0:
        print(f"  WARNING: Found {invalid_completed} Completed orders for future flights")
        cursor.execute("""
            UPDATE Order_Table
            SET order_status = 'Active'
            WHERE order_status = 'Completed'
            AND departure_time > NOW()
        """)
        print(f"  Fixed: Updated {cursor.rowcount} orders to Active")
    
    # Check 2: All System Cancellation orders should have Canceled flights
    cursor.execute("""
        SELECT COUNT(*) FROM Order_Table O
        LEFT JOIN Flight F ON O.source_airport_id = F.source_airport_id
            AND O.dest_airport_id = F.dest_airport_id
            AND O.departure_time = F.departure_time
        WHERE O.order_status = 'System Cancellation'
        AND (F.flight_status IS NULL OR F.flight_status != 'Canceled')
    """)
    invalid_system_cancel = cursor.fetchone()[0]
    if invalid_system_cancel > 0:
        print(f"  WARNING: Found {invalid_system_cancel} System Cancellation orders without Canceled flights")
        cursor.execute("""
            UPDATE Flight F
            JOIN Order_Table O ON F.source_airport_id = O.source_airport_id
                AND F.dest_airport_id = O.dest_airport_id
                AND F.departure_time = O.departure_time
            SET F.flight_status = 'Canceled'
            WHERE O.order_status = 'System Cancellation'
            AND F.flight_status != 'Canceled'
        """)
        print(f"  Fixed: Updated {cursor.rowcount} flights to Canceled")
    
    # Check 3: All orders for canceled flights should be System Cancellation
    cursor.execute("""
        SELECT COUNT(*) FROM Order_Table O
        JOIN Flight F ON O.source_airport_id = F.source_airport_id
            AND O.dest_airport_id = F.dest_airport_id
            AND O.departure_time = F.departure_time
        WHERE F.flight_status = 'Canceled'
        AND O.order_status != 'System Cancellation'
    """)
    invalid_canceled_flight_orders = cursor.fetchone()[0]
    if invalid_canceled_flight_orders > 0:
        print(f"  WARNING: Found {invalid_canceled_flight_orders} orders for Canceled flights that are not System Cancellation")
        cursor.execute("""
            UPDATE Order_Table O
            JOIN Flight F ON O.source_airport_id = F.source_airport_id
                AND O.dest_airport_id = F.dest_airport_id
                AND O.departure_time = F.departure_time
            SET O.order_status = 'System Cancellation',
                O.total_payment = 0
            WHERE F.flight_status = 'Canceled'
            AND O.order_status != 'System Cancellation'
        """)
        print(f"  Fixed: Updated {cursor.rowcount} orders to System Cancellation")
    
    # Check 4: All orders for past flights should be Completed
    cursor.execute("""
        SELECT COUNT(*) FROM Order_Table
        WHERE order_status = 'Active'
        AND departure_time < NOW()
    """)
    invalid_past_orders = cursor.fetchone()[0]
    if invalid_past_orders > 0:
        print(f"  WARNING: Found {invalid_past_orders} Active orders for past flights")
        cursor.execute("""
            UPDATE Order_Table
            SET order_status = 'Completed'
            WHERE order_status = 'Active'
            AND departure_time < NOW()
        """)
        print(f"  Fixed: Updated {cursor.rowcount} orders to Completed")
    
    print("  Order-flight relationship validation complete")

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
        validate_aircraft_class_rules(cursor)  # Ensure seed data follows business rules
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
        generate_faker_aircraft(cursor, min_count=50)
        generate_faker_aircraft_classes(cursor)
        validate_aircraft_class_rules(cursor)  # Ensure business rules are enforced
        generate_faker_seats(cursor)
        generate_faker_employees(cursor, min_count=20)
        dedupe_employee_names(cursor)
        generate_faker_flight_crew(cursor)
        generate_faker_users(cursor, min_count=20)
        generate_faker_phones(cursor)
        generate_faker_registered_customers(cursor)
        generate_faker_flights(cursor, min_count=100)
        generate_faker_crew_assignments(cursor)
        generate_faker_orders(cursor, min_count=20)
        
        # Create some Fully Booked flights by booking all their seats
        print("Creating Fully Booked flights...")
        create_fully_booked_flights(cursor)
        
        # Generate additional test data for manager reports dashboard
        print("\n--- GENERATING TEST DATA FOR REPORTS ---")
        generate_test_data_for_reports(cursor)
        
        # Run validation functions to ensure data consistency
        print("\n--- VALIDATING DATA CONSISTENCY ---")
        validate_orders_for_canceled_flights(cursor)
        update_orders_for_past_flights(cursor)
        validate_order_flight_relationships(cursor)
        
        # Update all flight statuses to reflect reality
        print("Updating flight statuses to reflect reality...")
        update_flight_statuses_realistic(cursor)
        
        # Final validation pass after status updates
        print("Running final validation pass...")
        validate_order_flight_relationships(cursor)
        
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

