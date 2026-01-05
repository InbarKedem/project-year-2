import db
from datetime import datetime, timedelta
from functools import wraps

def update_all_flight_statuses():
    """
    Updates flight statuses based on current time and departure time.
    Flights that have already departed (departure_time < NOW()) and are still 'Active'
    will be updated to 'Completed'.
    This function should be called before any flight-related queries to ensure
    flight statuses are always up-to-date.
    """
    try:
        db.execute_db("""
            UPDATE Flight 
            SET flight_status = 'Completed'
            WHERE flight_status = 'Active' 
            AND departure_time < NOW()
        """)
    except Exception as e:
        # Error updating flight_statuses - fail silently
        pass

def update_flight_statuses(func):
    """
    Decorator that calls update_all_flight_statuses() before executing the wrapped function.
    Works with both route handlers and service functions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        update_all_flight_statuses()
        return func(*args, **kwargs)
    return wrapper

def get_all_airports():
    return db.query_db("SELECT * FROM Airport ORDER BY airport_name")

def get_all_aircrafts():
    return db.query_db("SELECT * FROM Aircraft ORDER BY aircraft_id")

def get_all_pilots():
    return db.query_db("""
        SELECT E.id_number, E.first_name, E.last_name, FC.trained_for_long_flights
        FROM Employee E 
        JOIN Flight_Crew FC ON E.id_number = FC.id_number 
        WHERE FC.is_pilot = 1
    """)

def get_all_attendants():
    return db.query_db("""
        SELECT E.id_number, E.first_name, E.last_name, FC.trained_for_long_flights
        FROM Employee E 
        JOIN Flight_Crew FC ON E.id_number = FC.id_number 
        WHERE FC.is_pilot = 0
    """)

def get_flight_duration(source_id, dest_id):
    result = db.query_db("""
        SELECT flight_duration FROM Flight_Route 
        WHERE source_airport_id = %s AND dest_airport_id = %s
    """, (source_id, dest_id), one=True)
    return result['flight_duration'] if result else 0

@update_flight_statuses
def get_aircraft_availability(source_id, dest_id, departure_time_str):
    # Convert string to datetime if needed
    if isinstance(departure_time_str, str):
        try:
            departure_time = datetime.strptime(departure_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            try:
                departure_time = datetime.strptime(departure_time_str, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                return []
    else:
        departure_time = departure_time_str

    duration = get_flight_duration(source_id, dest_id)
    arrival_time = departure_time + timedelta(minutes=duration)
    is_long_flight = duration > 360 # 6 hours

    # Get airport names
    source_airport = db.query_db("SELECT airport_name FROM Airport WHERE airport_id = %s", (source_id,), one=True)
    dest_airport = db.query_db("SELECT airport_name FROM Airport WHERE airport_id = %s", (dest_id,), one=True)
    source_name = source_airport['airport_name'] if source_airport else "Unknown"
    dest_name = dest_airport['airport_name'] if dest_airport else "Unknown"

    aircrafts = get_all_aircrafts()
    
    for aircraft in aircrafts:
        aircraft['is_available'] = True
        aircraft['reason'] = ""

        # Check Size for Long Flights
        if is_long_flight and not aircraft['is_large']:
            aircraft['is_available'] = False
            aircraft['reason'] = "Small aircraft cannot be used for long flights (> 6 hours)"
            continue

        # Check Previous Flight
        prev_flight = db.query_db("""
            SELECT F.dest_airport_id, F.departure_time, COALESCE(FR.flight_duration, 0) as flight_duration, A.airport_name
            FROM Flight F
            LEFT JOIN Flight_Route FR ON F.source_airport_id = FR.source_airport_id 
                AND F.dest_airport_id = FR.dest_airport_id
            JOIN Airport A ON F.dest_airport_id = A.airport_id
            WHERE F.aircraft_id = %s 
                AND F.departure_time < %s
                AND F.flight_status = 'Active'
            ORDER BY F.departure_time DESC
            LIMIT 1
        """, (aircraft['aircraft_id'], departure_time), one=True)

        if prev_flight:
            prev_arrival = prev_flight['departure_time'] + timedelta(minutes=prev_flight['flight_duration'])
            if prev_arrival > departure_time:
                aircraft['is_available'] = False
                aircraft['reason'] = f"Busy until {prev_arrival.strftime('%Y-%m-%d %H:%M')}"
            elif str(prev_flight['dest_airport_id']) != str(source_id):
                aircraft['is_available'] = False
                aircraft['reason'] = f"Located at {prev_flight['airport_name']}. Flight departs from {source_name}."
        
        # Check Next Flight
        if aircraft['is_available']:
            next_flight = db.query_db("""
                SELECT F.source_airport_id, F.departure_time, A.airport_name
                FROM Flight F
                JOIN Airport A ON F.source_airport_id = A.airport_id
                WHERE F.aircraft_id = %s
                    AND F.departure_time >= %s
                    AND F.flight_status = 'Active'
                ORDER BY F.departure_time ASC
                LIMIT 1
            """, (aircraft['aircraft_id'], departure_time), one=True)

            if next_flight:
                if arrival_time > next_flight['departure_time']:
                    aircraft['is_available'] = False
                    aircraft['reason'] = f"Conflict with next flight at {next_flight['departure_time'].strftime('%Y-%m-%d %H:%M')}"
                elif str(next_flight['source_airport_id']) != str(dest_id):
                    aircraft['is_available'] = False
                    aircraft['reason'] = f"Next flight departs from {next_flight['airport_name']}. This flight arrives at {dest_name}."

    return aircrafts

@update_flight_statuses
def get_crew_availability(source_id, dest_id, departure_time_str, aircraft_id=None):
    # Convert string to datetime if needed
    if isinstance(departure_time_str, str):
        try:
            departure_time = datetime.strptime(departure_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            try:
                departure_time = datetime.strptime(departure_time_str, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                # Fallback or error
                return {'crew': [], 'requirements': {'pilots': 0, 'attendants': 0}}
    else:
        departure_time = departure_time_str

    duration = get_flight_duration(source_id, dest_id)
    arrival_time = departure_time + timedelta(minutes=duration)
    is_long_flight = duration > 360 # 6 hours

    # Determine Requirements
    requirements = {'pilots': 2, 'attendants': 3} # Default / Small
    
    if aircraft_id:
        aircraft = db.query_db("SELECT is_large FROM Aircraft WHERE aircraft_id = %s", (aircraft_id,), one=True)
        if aircraft:
            if aircraft['is_large']:
                requirements = {'pilots': 3, 'attendants': 6}
            else:
                # Small aircraft
                if is_long_flight:
                    # This shouldn't happen based on business rules, but we can flag it or just return empty
                    # For now, we'll proceed but maybe the UI should block it.
                    pass

    # Get airport names for better messages
    source_airport = db.query_db("SELECT airport_name FROM Airport WHERE airport_id = %s", (source_id,), one=True)
    dest_airport = db.query_db("SELECT airport_name FROM Airport WHERE airport_id = %s", (dest_id,), one=True)
    source_name = source_airport['airport_name'] if source_airport else "Unknown"
    dest_name = dest_airport['airport_name'] if dest_airport else "Unknown"

    # Get all crew
    pilots = get_all_pilots()
    attendants = get_all_attendants()
    
    all_crew = []
    for p in pilots:
        p['role'] = 'Pilot'
        all_crew.append(p)
    for a in attendants:
        a['role'] = 'Attendant'
        all_crew.append(a)

    for crew in all_crew:
        crew['is_available'] = True
        crew['reason'] = ""

        # Check Training for Long Flights
        if is_long_flight and not crew['trained_for_long_flights']:
            crew['is_available'] = False
            crew['reason'] = "Not trained for long flights (> 6 hours)"
            continue

        # Check Previous Flight
        prev_flight = db.query_db("""
            SELECT F.dest_airport_id, F.departure_time, COALESCE(FR.flight_duration, 0) as flight_duration, A.airport_name
            FROM Employee_Flight_Assignment EFA
            JOIN Flight F ON EFA.source_airport_id = F.source_airport_id 
                AND EFA.dest_airport_id = F.dest_airport_id 
                AND EFA.departure_time = F.departure_time
            LEFT JOIN Flight_Route FR ON F.source_airport_id = FR.source_airport_id 
                AND F.dest_airport_id = FR.dest_airport_id
            JOIN Airport A ON F.dest_airport_id = A.airport_id
            WHERE EFA.employee_id = %s 
                AND F.departure_time < %s
            ORDER BY F.departure_time DESC
            LIMIT 1
        """, (crew['id_number'], departure_time), one=True)

        if prev_flight:
            prev_arrival = prev_flight['departure_time'] + timedelta(minutes=prev_flight['flight_duration'])
            if prev_arrival > departure_time:
                crew['is_available'] = False
                crew['reason'] = f"Busy until {prev_arrival.strftime('%Y-%m-%d %H:%M')}"
            elif str(prev_flight['dest_airport_id']) != str(source_id):
                crew['is_available'] = False
                crew['reason'] = f"Located at {prev_flight['airport_name']}. Flight departs from {source_name}."
        
        # Check Next Flight
        if crew['is_available']:
            next_flight = db.query_db("""
                SELECT F.source_airport_id, F.departure_time, A.airport_name
                FROM Employee_Flight_Assignment EFA
                JOIN Flight F ON EFA.source_airport_id = F.source_airport_id 
                    AND EFA.dest_airport_id = F.dest_airport_id 
                    AND EFA.departure_time = F.departure_time
                JOIN Airport A ON F.source_airport_id = A.airport_id
                WHERE EFA.employee_id = %s
                    AND F.departure_time >= %s
                ORDER BY F.departure_time ASC
                LIMIT 1
            """, (crew['id_number'], departure_time), one=True)

            if next_flight:
                if arrival_time > next_flight['departure_time']:
                    crew['is_available'] = False
                    crew['reason'] = f"Conflict with next flight at {next_flight['departure_time'].strftime('%Y-%m-%d %H:%M')}"
                elif str(next_flight['source_airport_id']) != str(dest_id):
                    crew['is_available'] = False
                    crew['reason'] = f"Next flight departs from {next_flight['airport_name']}. This flight arrives at {dest_name}."

    return {'crew': all_crew, 'requirements': requirements}


def create_flight(source_id, dest_id, departure_time, aircraft_id, economy_price, business_price, crew_ids):
    try:
        # 1. Create Flight
        db.execute_db("""
            INSERT INTO Flight (source_airport_id, dest_airport_id, departure_time, flight_status, aircraft_id, economy_price, business_price)
            VALUES (%s, %s, %s, 'Active', %s, %s, %s)
        """, (source_id, dest_id, departure_time, aircraft_id, economy_price, business_price))

        # 2. Assign Crew
        for emp_id in crew_ids:
            db.execute_db("""
                INSERT INTO Employee_Flight_Assignment (employee_id, source_airport_id, dest_airport_id, departure_time)
                VALUES (%s, %s, %s, %s)
            """, (emp_id, source_id, dest_id, departure_time))
            
        return True, "Flight created successfully"
    except Exception as e:
        return False, str(e)

@update_flight_statuses
def get_flights(status=None, source_id=None, dest_id=None, date_from=None, date_to=None):
    
    query = """
        SELECT F.*, A1.airport_name as source, A2.airport_name as dest 
        FROM Flight F
        JOIN Airport A1 ON F.source_airport_id = A1.airport_id
        JOIN Airport A2 ON F.dest_airport_id = A2.airport_id
        WHERE 1=1
    """
    params = []
    
    # Normalize status parameter
    if status:
        status = status.strip() if isinstance(status, str) else str(status).strip()
    
    if status and status != 'All' and status != '':
        query += " AND F.flight_status = %s"
        params.append(status)
        # For Active status, ensure we only get flights with future departure times
        # (update_all_flight_statuses should handle this, but this is a safety check)
        if status == 'Active':
            query += " AND F.departure_time > NOW()"
    
    if source_id and source_id != '':
        query += " AND F.source_airport_id = %s"
        params.append(source_id)
        
    if dest_id and dest_id != '':
        query += " AND F.dest_airport_id = %s"
        params.append(dest_id)
        
    if date_from and date_from != '':
        query += " AND DATE(F.departure_time) >= %s"
        params.append(date_from)
        
    if date_to and date_to != '':
        query += " AND DATE(F.departure_time) <= %s"
        params.append(date_to)
        
    query += " ORDER BY F.departure_time DESC"
    
    results = db.query_db(query, tuple(params))
    
    return results

@update_flight_statuses
def get_active_flights():
    return db.query_db("""
        SELECT F.*, A1.airport_name as source, A2.airport_name as dest 
        FROM Flight F
        JOIN Airport A1 ON F.source_airport_id = A1.airport_id
        JOIN Airport A2 ON F.dest_airport_id = A2.airport_id
        WHERE F.flight_status = 'Active' AND F.departure_time > NOW()
        ORDER BY F.departure_time
    """)

@update_flight_statuses
def cancel_flight(source_id, dest_id, departure_time):
    try:
        # Check flight exists and get current status
        flight = db.query_db("""
            SELECT departure_time, flight_status FROM Flight 
            WHERE source_airport_id = %s AND dest_airport_id = %s AND departure_time = %s
        """, (source_id, dest_id, departure_time), one=True)
        
        if not flight:
            return False, "Flight not found"
        
        # Check if flight is already cancelled
        if flight['flight_status'] == 'Cancelled':
            return False, "Flight is already cancelled"
        
        # Check if flight is completed
        if flight['flight_status'] == 'Completed':
            return False, "Cannot cancel a completed flight"

        # Update flight status to Cancelled (only if >= 72 hours before departure)
        db.execute_db("""
            UPDATE Flight 
            SET flight_status = 'Cancelled'
            WHERE source_airport_id = %s AND dest_airport_id = %s AND departure_time = %s
            AND TIMESTAMPDIFF(HOUR, NOW(), departure_time) >= 72
            AND flight_status != 'Cancelled'
        """, (source_id, dest_id, departure_time))
        
        # Check if flight was actually updated
        updated_flight = db.query_db("""
            SELECT flight_status FROM Flight 
            WHERE source_airport_id = %s AND dest_airport_id = %s AND departure_time = %s
        """, (source_id, dest_id, departure_time), one=True)
        
        if updated_flight['flight_status'] == 'Cancelled':
            # Get affected orders and total refund amount before updating
            affected_orders = db.query_db("""
                SELECT order_code, total_payment, customer_email
                FROM Order_Table 
                WHERE source_airport_id = %s 
                AND dest_airport_id = %s 
                AND departure_time = %s
                AND order_status NOT IN ('Cancelled', 'Customer Cancelled', 'System Cancelled')
            """, (source_id, dest_id, departure_time))
            
            total_refund = sum(float(order['total_payment']) for order in affected_orders)
            order_count = len(affected_orders)
            
            # Update all related orders to 'System Cancelled' and set total_payment to 0 (full refund)
            db.execute_db("""
                UPDATE Order_Table 
                SET order_status = 'System Cancelled',
                    total_payment = 0.00
                WHERE source_airport_id = %s 
                AND dest_airport_id = %s 
                AND departure_time = %s
                AND order_status NOT IN ('Cancelled', 'Customer Cancelled', 'System Cancelled')
            """, (source_id, dest_id, departure_time))
            
            # Build detailed refund message
            if order_count > 0:
                refund_message = f"Flight cancelled successfully. {order_count} order(s) cancelled with full refund of ${total_refund:.2f} processed. All customers will receive their full payment back."
            else:
                refund_message = "Flight cancelled successfully. No active orders were affected."
            
            return True, refund_message
        else:
            return False, "Could not cancel flight (less than 72 hours before departure or already cancelled)"

    except Exception as e:
        return False, str(e)

@update_flight_statuses
def get_flight_details(source_id, dest_id, departure_time):
    # Get flight info + aircraft info
    flight = db.query_db("""
        SELECT F.*, 
               A1.airport_name as source, 
               A2.airport_name as dest,
               AC.manufacturer, AC.is_large
        FROM Flight F
        JOIN Airport A1 ON F.source_airport_id = A1.airport_id
        JOIN Airport A2 ON F.dest_airport_id = A2.airport_id
        LEFT JOIN Aircraft AC ON F.aircraft_id = AC.aircraft_id
        WHERE F.source_airport_id = %s 
          AND F.dest_airport_id = %s 
          AND F.departure_time = %s
    """, (source_id, dest_id, departure_time), one=True)

    if not flight:
        return None

    # Get assigned crew
    crew = db.query_db("""
        SELECT E.first_name, E.last_name, FC.is_pilot
        FROM Employee_Flight_Assignment EFA
        JOIN Employee E ON EFA.employee_id = E.id_number
        JOIN Flight_Crew FC ON E.id_number = FC.id_number
        WHERE EFA.source_airport_id = %s 
          AND EFA.dest_airport_id = %s 
          AND EFA.departure_time = %s
    """, (source_id, dest_id, departure_time))

    flight['crew'] = crew
    return flight

def update_flight_status(source_id, dest_id, departure_time, new_status):
    try:
        db.execute_db("""
            UPDATE Flight 
            SET flight_status = %s
            WHERE source_airport_id = %s AND dest_airport_id = %s AND departure_time = %s
        """, (new_status, source_id, dest_id, departure_time))
        
        # If status is set to 'Cancelled', update all related orders to 'System Cancelled'
        if new_status == 'Cancelled':
            db.execute_db("""
                UPDATE Order_Table 
                SET order_status = 'System Cancelled'
                WHERE source_airport_id = %s 
                AND dest_airport_id = %s 
                AND departure_time = %s
                AND order_status NOT IN ('Cancelled', 'Customer Cancelled', 'System Cancelled')
            """, (source_id, dest_id, departure_time))
            return True, "Flight status updated to Cancelled. All related orders have been cancelled."
        
        return True, "Status updated successfully"
    except Exception as e:
        return False, str(e)

def add_aircraft(aircraft_id, manufacturer, purchase_date, is_large, business_config, economy_config):
    """
    Adds a new aircraft with classes and seats.
    
    Args:
        aircraft_id: Unique aircraft ID (integer)
        manufacturer: Manufacturer name (string)
        purchase_date: Purchase date (date string or date object)
        is_large: Boolean indicating if aircraft is large
        business_config: Dict with 'num_rows' and 'num_columns', or None if no business class
        economy_config: Dict with 'num_rows' and 'num_columns' (required)
    
    Returns:
        (success: bool, message: str)
    """
    try:
        # Check if aircraft already exists
        existing = db.query_db("SELECT aircraft_id FROM Aircraft WHERE aircraft_id = %s", (aircraft_id,), one=True)
        if existing:
            return False, 'Aircraft with this ID already exists.'
        
        # Validate economy_config is provided
        if not economy_config or 'num_rows' not in economy_config or 'num_columns' not in economy_config:
            return False, 'Economy class configuration is required.'
        
        # Insert into Aircraft table
        db.execute_db("""
            INSERT INTO Aircraft (aircraft_id, manufacturer, purchase_date, is_large)
            VALUES (%s, %s, %s, %s)
        """, (aircraft_id, manufacturer, purchase_date, is_large))
        
        # Insert Economy Class (always required)
        db.execute_db("""
            INSERT INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns)
            VALUES (%s, %s, %s, %s)
        """, (aircraft_id, False, economy_config['num_rows'], economy_config['num_columns']))
        
        # Generate Economy seats
        for row in range(1, economy_config['num_rows'] + 1):
            for col in range(1, economy_config['num_columns'] + 1):
                db.execute_db("""
                    INSERT INTO Seat (aircraft_id, is_business, `row_number`, `column_number`)
                    VALUES (%s, %s, %s, %s)
                """, (aircraft_id, False, row, col))
        
        # Insert Business Class if provided
        if business_config and 'num_rows' in business_config and 'num_columns' in business_config:
            db.execute_db("""
                INSERT INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns)
                VALUES (%s, %s, %s, %s)
            """, (aircraft_id, True, business_config['num_rows'], business_config['num_columns']))
            
            # Generate Business seats
            for row in range(1, business_config['num_rows'] + 1):
                for col in range(1, business_config['num_columns'] + 1):
                    db.execute_db("""
                        INSERT INTO Seat (aircraft_id, is_business, `row_number`, `column_number`)
                        VALUES (%s, %s, %s, %s)
                    """, (aircraft_id, True, row, col))
        
        return True, 'Aircraft added successfully!'
    
    except Exception as e:
        return False, f'Error adding aircraft: {str(e)}'

