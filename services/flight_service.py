import db

def get_all_airports():
    return db.query_db("SELECT * FROM Airport ORDER BY airport_name")

def get_all_aircrafts():
    return db.query_db("SELECT * FROM Aircraft ORDER BY aircraft_id")

def get_all_pilots():
    return db.query_db("""
        SELECT E.id_number, E.first_name, E.last_name 
        FROM Employee E 
        JOIN Flight_Crew FC ON E.id_number = FC.id_number 
        WHERE FC.is_pilot = 1
    """)

def get_all_attendants():
    return db.query_db("""
        SELECT E.id_number, E.first_name, E.last_name 
        FROM Employee E 
        JOIN Flight_Crew FC ON E.id_number = FC.id_number 
        WHERE FC.is_pilot = 0
    """)

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

def get_active_flights():
    return db.query_db("""
        SELECT F.*, A1.airport_name as source, A2.airport_name as dest 
        FROM Flight F
        JOIN Airport A1 ON F.source_airport_id = A1.airport_id
        JOIN Airport A2 ON F.dest_airport_id = A2.airport_id
        WHERE F.flight_status = 'Active' AND F.departure_time > NOW()
        ORDER BY F.departure_time
    """)

def cancel_flight(source_id, dest_id, departure_time):
    try:
        # Check 72 hours rule
        flight = db.query_db("""
            SELECT departure_time FROM Flight 
            WHERE source_airport_id = %s AND dest_airport_id = %s AND departure_time = %s
        """, (source_id, dest_id, departure_time), one=True)
        
        if not flight:
            return False, "Flight not found"

        # Calculate time difference
        # Note: In a real app, we'd do this check in Python with datetime objects
        # But for now, let's assume the UI handles the initial check or we do it here
        # Let's do a simple SQL check or Python check.
        # Since departure_time is a string or datetime depending on the driver...
        
        # Let's just update status for now, assuming the controller checks the time or we check it in SQL
        db.execute_db("""
            UPDATE Flight 
            SET flight_status = 'Cancelled'
            WHERE source_airport_id = %s AND dest_airport_id = %s AND departure_time = %s
            AND TIMESTAMPDIFF(HOUR, NOW(), departure_time) >= 72
        """, (source_id, dest_id, departure_time))
        
        # Check if it was actually updated (row count) - execute_db returns lastrowid, not rowcount usually in this helper
        # We might need to check the status again
        updated_flight = db.query_db("""
            SELECT flight_status FROM Flight 
            WHERE source_airport_id = %s AND dest_airport_id = %s AND departure_time = %s
        """, (source_id, dest_id, departure_time), one=True)
        
        if updated_flight['flight_status'] == 'Cancelled':
            return True, "Flight cancelled successfully"
        else:
            return False, "Could not cancel flight (less than 72 hours before departure or already cancelled)"

    except Exception as e:
        return False, str(e)

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
        return True, "Status updated successfully"
    except Exception as e:
        return False, str(e)

