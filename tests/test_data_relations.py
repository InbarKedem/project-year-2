"""
Comprehensive test suite to verify all relationships and business rules are enforced.
"""
import pytest
import mysql.connector
from db import DB_CONFIG
from datetime import datetime

# Business rules constants
BIG_PLANE_PILOTS = 3
BIG_PLANE_ATTENDANTS = 6
SMALL_PLANE_PILOTS = 2
SMALL_PLANE_ATTENDANTS = 3
SHORT_FLIGHT_MAX_HOURS = 6
LONG_FLIGHT_MIN_HOURS = 6

def get_db_connection():
    """Get database connection for testing."""
    return mysql.connector.connect(**DB_CONFIG)

class TestForeignKeyRelations:
    """Test all foreign key relationships."""
    
    def test_flight_route_airport_references(self):
        """Verify all Flight_Route references valid Airport IDs."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fr.source_airport_id, fr.dest_airport_id
            FROM Flight_Route fr
            LEFT JOIN Airport a1 ON fr.source_airport_id = a1.airport_id
            LEFT JOIN Airport a2 ON fr.dest_airport_id = a2.airport_id
            WHERE a1.airport_id IS NULL OR a2.airport_id IS NULL
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Flight_Route entries with invalid Airport references"
    
    def test_aircraft_class_aircraft_references(self):
        """Verify all Aircraft_Class references valid Aircraft IDs."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ac.aircraft_id
            FROM Aircraft_Class ac
            LEFT JOIN Aircraft a ON ac.aircraft_id = a.aircraft_id
            WHERE a.aircraft_id IS NULL
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Aircraft_Class entries with invalid Aircraft references"
    
    def test_seat_aircraft_class_references(self):
        """Verify all Seat references valid Aircraft_Class combinations."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.aircraft_id, s.is_business
            FROM Seat s
            LEFT JOIN Aircraft_Class ac ON s.aircraft_id = ac.aircraft_id 
                AND s.is_business = ac.is_business
            WHERE ac.aircraft_id IS NULL
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Seat entries with invalid Aircraft_Class references"
    
    def test_flight_crew_employee_references(self):
        """Verify all Flight_Crew references valid Employee IDs."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fc.id_number
            FROM Flight_Crew fc
            LEFT JOIN Employee e ON fc.id_number = e.id_number
            WHERE e.id_number IS NULL
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Flight_Crew entries with invalid Employee references"
    
    def test_manager_employee_references(self):
        """Verify all Manager references valid Employee IDs."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id_number
            FROM Manager m
            LEFT JOIN Employee e ON m.id_number = e.id_number
            WHERE e.id_number IS NULL
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Manager entries with invalid Employee references"
    
    def test_employee_flight_assignment_references(self):
        """Verify all Employee_Flight_Assignment references valid Flight_Crew and Flight."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT efa.employee_id, efa.source_airport_id, efa.dest_airport_id, efa.departure_time
            FROM Employee_Flight_Assignment efa
            LEFT JOIN Flight_Crew fc ON efa.employee_id = fc.id_number
            LEFT JOIN Flight f ON efa.source_airport_id = f.source_airport_id
                AND efa.dest_airport_id = f.dest_airport_id
                AND efa.departure_time = f.departure_time
            WHERE fc.id_number IS NULL OR f.source_airport_id IS NULL
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Employee_Flight_Assignment entries with invalid references"
    
    def test_phone_user_references(self):
        """Verify all Phone references valid User emails."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.email
            FROM Phone p
            LEFT JOIN User u ON p.email = u.email
            WHERE u.email IS NULL
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Phone entries with invalid User references"
    
    def test_registered_customer_user_references(self):
        """Verify all Registered_Customer references valid User emails."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rc.email
            FROM Registered_Customer rc
            LEFT JOIN User u ON rc.email = u.email
            WHERE u.email IS NULL
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Registered_Customer entries with invalid User references"
    
    def test_order_table_references(self):
        """Verify all Order_Table references valid User emails and Flights."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ot.order_code
            FROM Order_Table ot
            LEFT JOIN User u ON ot.customer_email = u.email
            LEFT JOIN Flight f ON ot.source_airport_id = f.source_airport_id
                AND ot.dest_airport_id = f.dest_airport_id
                AND ot.departure_time = f.departure_time
            WHERE u.email IS NULL OR f.source_airport_id IS NULL
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Order_Table entries with invalid references"
    
    def test_order_seats_references(self):
        """Verify all Order_Seats references valid Order_Table and Seat combinations."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT os.order_code
            FROM Order_Seats os
            LEFT JOIN Order_Table ot ON os.order_code = ot.order_code
            LEFT JOIN Seat s ON os.aircraft_id = s.aircraft_id
                AND os.is_business = s.is_business
                AND os.row_number = s.row_number
                AND os.column_number = s.column_number
            WHERE ot.order_code IS NULL OR s.aircraft_id IS NULL
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Order_Seats entries with invalid references"

class TestBusinessRules:
    """Test all business rules enforcement."""
    
    def test_big_plane_crew_requirements(self):
        """Test Big Plane flights have exactly 3 Pilots and 6 Flight Attendants."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.source_airport_id, f.dest_airport_id, f.departure_time,
                   COUNT(CASE WHEN fc.is_pilot = TRUE THEN 1 END) as pilot_count,
                   COUNT(CASE WHEN fc.is_pilot = FALSE THEN 1 END) as attendant_count
            FROM Flight f
            JOIN Aircraft a ON f.aircraft_id = a.aircraft_id
            JOIN Employee_Flight_Assignment efa ON f.source_airport_id = efa.source_airport_id
                AND f.dest_airport_id = efa.dest_airport_id
                AND f.departure_time = efa.departure_time
            JOIN Flight_Crew fc ON efa.employee_id = fc.id_number
            WHERE a.is_large = TRUE
            GROUP BY f.source_airport_id, f.dest_airport_id, f.departure_time
            HAVING pilot_count != %s OR attendant_count != %s
        """, (BIG_PLANE_PILOTS, BIG_PLANE_ATTENDANTS))
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Big Plane flights with incorrect crew counts"
    
    def test_small_plane_crew_requirements(self):
        """Test Small Plane flights have exactly 2 Pilots and 3 Flight Attendants."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.source_airport_id, f.dest_airport_id, f.departure_time,
                   COUNT(CASE WHEN fc.is_pilot = TRUE THEN 1 END) as pilot_count,
                   COUNT(CASE WHEN fc.is_pilot = FALSE THEN 1 END) as attendant_count
            FROM Flight f
            JOIN Aircraft a ON f.aircraft_id = a.aircraft_id
            JOIN Employee_Flight_Assignment efa ON f.source_airport_id = efa.source_airport_id
                AND f.dest_airport_id = efa.dest_airport_id
                AND f.departure_time = efa.departure_time
            JOIN Flight_Crew fc ON efa.employee_id = fc.id_number
            WHERE a.is_large = FALSE
            GROUP BY f.source_airport_id, f.dest_airport_id, f.departure_time
            HAVING pilot_count != %s OR attendant_count != %s
        """, (SMALL_PLANE_PILOTS, SMALL_PLANE_ATTENDANTS))
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Small Plane flights with incorrect crew counts"
    
    def test_big_planes_have_both_classes(self):
        """Test Big Planes have both Economy and Business classes."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.aircraft_id
            FROM Aircraft a
            WHERE a.is_large = TRUE
            AND (
                (SELECT COUNT(*) FROM Aircraft_Class ac WHERE ac.aircraft_id = a.aircraft_id AND ac.is_business = TRUE) = 0
                OR (SELECT COUNT(*) FROM Aircraft_Class ac WHERE ac.aircraft_id = a.aircraft_id AND ac.is_business = FALSE) = 0
            )
        """)
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Big Planes missing Economy or Business class"
    
    def test_small_planes_only_economy(self):
        """Test Small Planes have only Economy class."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.aircraft_id
            FROM Aircraft a
            WHERE a.is_large = FALSE
            AND (SELECT COUNT(*) FROM Aircraft_Class ac WHERE ac.aircraft_id = a.aircraft_id AND ac.is_business = TRUE) > 0
        """)
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Small Planes with Business class (should only have Economy)"
    
    def test_long_flights_only_big_planes(self):
        """Test Long flights (6+ hours) only use Big Planes."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.source_airport_id, f.dest_airport_id, f.departure_time, fr.flight_duration, a.is_large
            FROM Flight f
            JOIN Flight_Route fr ON f.source_airport_id = fr.source_airport_id
                AND f.dest_airport_id = fr.dest_airport_id
            JOIN Aircraft a ON f.aircraft_id = a.aircraft_id
            WHERE fr.flight_duration >= %s AND a.is_large = FALSE
        """, (LONG_FLIGHT_MIN_HOURS * 60,))
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Long flights using Small Planes"
    
    def test_crew_qualification_short_flights(self):
        """Test crew without 'Long Distance' training only assigned to Short Flights."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT efa.employee_id, efa.source_airport_id, efa.dest_airport_id, efa.departure_time
            FROM Employee_Flight_Assignment efa
            JOIN Flight_Crew fc ON efa.employee_id = fc.id_number
            JOIN Flight f ON efa.source_airport_id = f.source_airport_id
                AND efa.dest_airport_id = f.dest_airport_id
                AND efa.departure_time = f.departure_time
            JOIN Flight_Route fr ON f.source_airport_id = fr.source_airport_id
                AND f.dest_airport_id = fr.dest_airport_id
            WHERE fc.trained_for_long_flights = FALSE
            AND fr.flight_duration >= %s
        """, (LONG_FLIGHT_MIN_HOURS * 60,))
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} untrained crew assigned to Long Flights"
    
    def test_user_role_exclusivity(self):
        """Test no employee is both Pilot and Flight Attendant."""
        conn = get_db_connection()
        cursor = conn.cursor()
        # Check that each employee in Flight_Crew has only one role (either pilot or attendant, not both)
        # Since is_pilot is a boolean, an employee can only have one value, but let's verify
        # by checking that all employees have a consistent is_pilot value
        cursor.execute("""
            SELECT id_number, COUNT(DISTINCT is_pilot) as role_count
            FROM Flight_Crew
            GROUP BY id_number
            HAVING role_count > 1
        """)
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} employees with conflicting roles (this should be impossible with boolean field)"
    
    def test_managers_not_in_flight_crew(self):
        """Test Managers are NOT in Flight_Crew table."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id_number
            FROM Manager m
            JOIN Flight_Crew fc ON m.id_number = fc.id_number
        """)
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Managers in Flight_Crew table"
    
    def test_managers_no_orders(self):
        """Test no Orders exist for users who are Managers."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ot.order_code
            FROM Order_Table ot
            JOIN Manager m ON ot.customer_email = CAST(m.id_number AS CHAR)
        """)
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Orders for Managers"

class TestDataIntegrity:
    """Test data integrity constraints."""
    
    def test_required_fields_not_null(self):
        """Verify all required fields are not NULL."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check Airport
        cursor.execute("SELECT COUNT(*) FROM Airport WHERE airport_name IS NULL")
        assert cursor.fetchone()[0] == 0, "Airport has NULL airport_name"
        
        # Check Manager password
        cursor.execute("SELECT COUNT(*) FROM Manager WHERE password IS NULL")
        assert cursor.fetchone()[0] == 0, "Manager has NULL password"
        
        cursor.close()
        conn.close()
    
    def test_email_formats(self):
        """Verify email formats are valid."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM User WHERE email NOT LIKE '%@%.%'")
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} invalid email formats"
    
    def test_date_ranges(self):
        """Verify dates are in valid ranges."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check Registered_Customer: birth_date < registration_date
        cursor.execute("""
            SELECT email FROM Registered_Customer
            WHERE birth_date >= registration_date
        """)
        invalid = cursor.fetchall()
        assert len(invalid) == 0, f"Found {len(invalid)} Registered_Customers with invalid date ranges"
        
        # Check Employee: start_work_date <= today
        cursor.execute("""
            SELECT id_number FROM Employee
            WHERE start_work_date > CURDATE()
        """)
        invalid = cursor.fetchall()
        assert len(invalid) == 0, f"Found {len(invalid)} Employees with future start dates"
        
        cursor.close()
        conn.close()
    
    def test_order_dates_before_flight(self):
        """Verify order dates are before flight departure times."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ot.order_code
            FROM Order_Table ot
            JOIN Flight f ON ot.source_airport_id = f.source_airport_id
                AND ot.dest_airport_id = f.dest_airport_id
                AND ot.departure_time = f.departure_time
            WHERE ot.order_date >= f.departure_time
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Orders with dates after flight departure"
    
    def test_prices_positive(self):
        """Verify prices are positive numbers."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT source_airport_id, dest_airport_id, departure_time
            FROM Flight
            WHERE economy_price <= 0 OR (business_price IS NOT NULL AND business_price <= 0)
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Flights with non-positive prices"
    
    def test_seat_assignments_match_aircraft(self):
        """Verify seat assignments match the aircraft used in the flight."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT os.order_code
            FROM Order_Seats os
            JOIN Order_Table ot ON os.order_code = ot.order_code
            JOIN Flight f ON ot.source_airport_id = f.source_airport_id
                AND ot.dest_airport_id = f.dest_airport_id
                AND ot.departure_time = f.departure_time
            WHERE os.aircraft_id != f.aircraft_id
        """)
        invalid = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(invalid) == 0, f"Found {len(invalid)} Order_Seats with mismatched aircraft"

class TestDataCompleteness:
    """Test data completeness requirements."""
    
    def test_minimum_row_counts(self):
        """Verify minimum row counts: 20+ per table (except Flights: 50+)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        tables = {
            'Airport': 20,
            'Flight_Route': 20,
            'Aircraft': 20,
            'Employee': 20,
            'User': 20,
            'Order_Table': 20,
            'Flight': 50
        }
        
        violations = []
        for table, min_count in tables.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count < min_count:
                violations.append(f"{table}: {count} < {min_count}")
        
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Row count violations: {', '.join(violations)}"
    
    def test_aircraft_have_classes(self):
        """Verify all aircraft have corresponding Aircraft_Class entries."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.aircraft_id
            FROM Aircraft a
            LEFT JOIN Aircraft_Class ac ON a.aircraft_id = ac.aircraft_id
            WHERE ac.aircraft_id IS NULL
        """)
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Aircraft without Aircraft_Class entries"
    
    def test_aircraft_classes_have_seats(self):
        """Verify all Aircraft_Class entries have corresponding Seat entries."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ac.aircraft_id, ac.is_business
            FROM Aircraft_Class ac
            LEFT JOIN Seat s ON ac.aircraft_id = s.aircraft_id
                AND ac.is_business = s.is_business
            WHERE s.aircraft_id IS NULL
        """)
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Aircraft_Class entries without Seat entries"
    
    def test_flights_have_crew_assignments(self):
        """Verify all flights have crew assignments."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.source_airport_id, f.dest_airport_id, f.departure_time
            FROM Flight f
            LEFT JOIN Employee_Flight_Assignment efa ON f.source_airport_id = efa.source_airport_id
                AND f.dest_airport_id = efa.dest_airport_id
                AND f.departure_time = efa.departure_time
            WHERE efa.employee_id IS NULL
        """)
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Flights without crew assignments"
    
    def test_registered_customers_have_passports(self):
        """Verify all registered customers have passport numbers."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT email FROM Registered_Customer
            WHERE passport_number IS NULL OR passport_number = ''
        """)
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Registered_Customers without passport numbers"
    
    def test_orders_have_seat_assignments(self):
        """Verify all orders have at least one seat assignment."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ot.order_code
            FROM Order_Table ot
            LEFT JOIN Order_Seats os ON ot.order_code = os.order_code
            WHERE os.order_code IS NULL
        """)
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(violations) == 0, f"Found {len(violations)} Orders without seat assignments"

class TestSeedDataPreservation:
    """Test that seed data is preserved."""
    
    def test_seed_airports_exist(self):
        """Verify seed airports (IDs 1-4) exist with correct names."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT airport_id, airport_name FROM Airport
            WHERE airport_id IN (1, 2, 3, 4)
            ORDER BY airport_id
        """)
        airports = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(airports) == 4, f"Expected 4 seed airports, found {len(airports)}"
        expected_names = ['Ben Gurion (TLV)', 'John F. Kennedy (JFK)', 'Heathrow (LHR)', 'Charles de Gaulle (CDG)']
        for i, (airport_id, name) in enumerate(airports):
            assert name == expected_names[i], f"Airport {airport_id} has incorrect name: {name}"
    
    def test_seed_employees_exist(self):
        """Verify seed employees (managers, pilots, attendants) exist with correct IDs."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check managers
        cursor.execute("SELECT id_number FROM Manager WHERE id_number IN ('111111111', '222222222')")
        managers = cursor.fetchall()
        assert len(managers) == 2, f"Expected 2 seed managers, found {len(managers)}"
        
        # Check pilots (300000001-300000010)
        cursor.execute("SELECT id_number FROM Flight_Crew WHERE (id_number LIKE '30000000%' OR id_number = '300000010') AND is_pilot = TRUE")
        pilots = cursor.fetchall()
        assert len(pilots) >= 10, f"Expected at least 10 seed pilots, found {len(pilots)}"
        
        # Check attendants (400000001-400000010)
        cursor.execute("SELECT id_number FROM Flight_Crew WHERE (id_number LIKE '40000000%' OR id_number = '400000010') AND is_pilot = FALSE")
        attendants = cursor.fetchall()
        assert len(attendants) >= 10, f"Expected at least 10 seed attendants, found {len(attendants)}"
        
        cursor.close()
        conn.close()
    
    def test_seed_users_exist(self):
        """Verify seed users (reg1@test.com, etc.) exist."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT email FROM User
            WHERE email IN ('reg1@test.com', 'reg2@test.com', 'guest1@test.com', 'guest2@test.com')
        """)
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        assert len(users) == 4, f"Expected 4 seed users, found {len(users)}"
    
    def test_seed_flights_exist(self):
        """Verify seed flights exist with correct relationships."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM Flight
            WHERE (source_airport_id = 1 AND dest_airport_id = 2 AND departure_time = '2026-01-01 08:00:00')
            OR (source_airport_id = 1 AND dest_airport_id = 3 AND departure_time = '2026-01-02 10:00:00')
            OR (source_airport_id = 2 AND dest_airport_id = 1 AND departure_time = '2026-01-03 12:00:00')
            OR (source_airport_id = 3 AND dest_airport_id = 1 AND departure_time = '2026-01-04 14:00:00')
        """)
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        assert count == 4, f"Expected 4 seed flights, found {count}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

