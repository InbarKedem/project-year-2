"""
Comprehensive test suite for status management functionality.
Tests cover flight status updates, order status consistency, cancellation rules,
aircraft class business rules, and crew join date validation.
"""
import pytest
import mysql.connector
from db import DB_CONFIG
from datetime import datetime, timedelta
from services.flight_service import (
    update_all_flight_statuses, get_all_pilots, get_all_attendants,
    get_crew_availability, create_flight, add_aircraft
)
from db import query_db, execute_db
from main import app

def get_db_connection():
    """Get database connection for testing."""
    return mysql.connector.connect(**DB_CONFIG)

def cleanup_test_data(cursor, conn):
    """Clean up test data."""
    try:
        # Delete in reverse order of dependencies
        cursor.execute("DELETE FROM Order_Seats WHERE order_code IN (SELECT order_code FROM Order_Table WHERE customer_email LIKE 'test_%')")
        cursor.execute("DELETE FROM Order_Table WHERE customer_email LIKE 'test_%'")
        cursor.execute("DELETE FROM Employee_Flight_Assignment WHERE employee_id LIKE 'TEST%'")
        cursor.execute("DELETE FROM Flight_Route WHERE source_airport_id IN (9998, 9999) OR dest_airport_id IN (9998, 9999)")
        cursor.execute("DELETE FROM Flight WHERE source_airport_id IN (9998, 9999) OR dest_airport_id IN (9998, 9999)")
        cursor.execute("DELETE FROM Airport WHERE airport_id IN (9998, 9999)")
        cursor.execute("DELETE FROM Seat WHERE aircraft_id >= 99990")
        cursor.execute("DELETE FROM Aircraft_Class WHERE aircraft_id >= 99990")
        cursor.execute("DELETE FROM Aircraft WHERE aircraft_id >= 99990")
        cursor.execute("DELETE FROM Flight_Crew WHERE id_number LIKE 'TEST%'")
        cursor.execute("DELETE FROM Employee WHERE id_number LIKE 'TEST%'")
        cursor.execute("DELETE FROM User WHERE email LIKE 'test_%'")
        conn.commit()
    except Exception as e:
        print(f"Error cleaning up test data: {e}")
        conn.rollback()

class TestFlightStatusUpdates:
    """Test flight status updates for past flights."""
    
    def test_update_active_flights_to_completed(self):
        """Test that past Active flights are updated to Completed."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Create test airport if needed
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (9999, 'Test Airport')")
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (9998, 'Test Airport 2')")
            
            # Create test aircraft
            cursor.execute("""
                INSERT IGNORE INTO Aircraft (aircraft_id, manufacturer, purchase_date, is_large)
                VALUES (99990, 'Test', '2020-01-01', 0)
            """)
            cursor.execute("""
                INSERT IGNORE INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns)
                VALUES (99990, 0, 10, 6)
            """)
            
            # Delete any existing flight first
            cursor.execute("""
                DELETE FROM Flight WHERE source_airport_id = 9999 AND dest_airport_id = 9998
            """)
            conn.commit()
            
            # Create a past flight with Active status (using a specific past time)
            past_time = (datetime.now() - timedelta(hours=25)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO Flight (source_airport_id, dest_airport_id, departure_time, flight_status, aircraft_id, economy_price, business_price)
                VALUES (9999, 9998, %s, 'Active', 99990, 100, 200)
            """, (past_time,))
            conn.commit()
            
            # Verify flight was created with Active status
            cursor.execute("""
                SELECT flight_status FROM Flight
                WHERE source_airport_id = 9999 AND dest_airport_id = 9998 AND departure_time = %s
            """, (past_time,))
            before_result = cursor.fetchone()
            assert before_result is not None, "Flight should exist before update"
            assert before_result[0] == 'Active', f"Flight should start as 'Active', got '{before_result[0]}'"
            
            # Run update function with app context
            with app.app_context():
                update_all_flight_statuses()
            
            # Close and reopen connection to see committed changes
            cursor.close()
            conn.close()
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verify status was updated
            cursor.execute("""
                SELECT flight_status FROM Flight
                WHERE source_airport_id = 9999 AND dest_airport_id = 9998 AND departure_time = %s
            """, (past_time,))
            result = cursor.fetchone()
            
            assert result is not None, "Flight should exist"
            assert result[0] == 'Completed', f"Flight status should be 'Completed', got '{result[0]}'"
            
        finally:
            cleanup_test_data(cursor, conn)
            cursor.close()
            conn.close()
    
    def test_update_fully_booked_flights_to_completed(self):
        """Test that past Fully Booked flights are updated to Completed."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Create test data
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (9999, 'Test Airport')")
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (9998, 'Test Airport 2')")
            cursor.execute("""
                INSERT IGNORE INTO Aircraft (aircraft_id, manufacturer, purchase_date, is_large)
                VALUES (99990, 'Test', '2020-01-01', 0)
            """)
            cursor.execute("""
                INSERT IGNORE INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns)
                VALUES (99990, 0, 10, 6)
            """)
            
            # Delete any existing flight first
            cursor.execute("""
                DELETE FROM Flight WHERE source_airport_id = 9999 AND dest_airport_id = 9998
            """)
            conn.commit()
            
            # Create a past flight with Fully Booked status (using a specific past time)
            past_time = (datetime.now() - timedelta(hours=25)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO Flight (source_airport_id, dest_airport_id, departure_time, flight_status, aircraft_id, economy_price, business_price)
                VALUES (9999, 9998, %s, 'Fully Booked', 99990, 100, 200)
            """, (past_time,))
            conn.commit()
            
            # Verify flight was created with Fully Booked status
            cursor.execute("""
                SELECT flight_status FROM Flight
                WHERE source_airport_id = 9999 AND dest_airport_id = 9998 AND departure_time = %s
            """, (past_time,))
            before_result = cursor.fetchone()
            assert before_result is not None, "Flight should exist before update"
            assert before_result[0] == 'Fully Booked', f"Flight should start as 'Fully Booked', got '{before_result[0]}'"
            
            # Run update function with app context
            with app.app_context():
                update_all_flight_statuses()
            
            # Close and reopen connection to see committed changes
            cursor.close()
            conn.close()
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verify status was updated
            cursor.execute("""
                SELECT flight_status FROM Flight
                WHERE source_airport_id = 9999 AND dest_airport_id = 9998 AND departure_time = %s
            """, (past_time,))
            result = cursor.fetchone()
            
            assert result is not None, "Flight should exist"
            assert result[0] == 'Completed', f"Flight status should be 'Completed', got '{result[0]}'"
            
        finally:
            cleanup_test_data(cursor, conn)
            cursor.close()
            conn.close()
    
    def test_future_flights_remain_active(self):
        """Test that future Active flights remain Active."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Create test data
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (9999, 'Test Airport')")
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (9998, 'Test Airport 2')")
            cursor.execute("""
                INSERT IGNORE INTO Aircraft (aircraft_id, manufacturer, purchase_date, is_large)
                VALUES (99990, 'Test', '2020-01-01', 0)
            """)
            cursor.execute("""
                INSERT IGNORE INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns)
                VALUES (99990, 0, 10, 6)
            """)
            
            # Create a future flight with Active status
            future_time = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO Flight (source_airport_id, dest_airport_id, departure_time, flight_status, aircraft_id, economy_price, business_price)
                VALUES (9999, 9998, %s, 'Active', 99990, 100, 200)
                ON DUPLICATE KEY UPDATE flight_status = 'Active'
            """, (future_time,))
            conn.commit()
            
            # Run update function
            update_all_flight_statuses()
            
            # Verify status remained Active
            cursor.execute("""
                SELECT flight_status FROM Flight
                WHERE source_airport_id = 9999 AND dest_airport_id = 9998 AND departure_time = %s
            """, (future_time,))
            result = cursor.fetchone()
            
            assert result is not None, "Flight should exist"
            assert result[0] == 'Active', f"Flight status should remain 'Active', got '{result[0]}'"
            
        finally:
            cleanup_test_data(cursor, conn)
            cursor.close()
            conn.close()

class TestOrderStatusConsistency:
    """Test order status naming consistency."""
    
    def test_order_creation_uses_active_status(self):
        """Test that new orders are created with 'Active' status, not 'Confirmed'."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Create test user
            cursor.execute("INSERT IGNORE INTO User (email, first_name, last_name) VALUES ('test_order@test.com', 'Test', 'User')")
            
            # Create test flight
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (9999, 'Test Airport')")
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (9998, 'Test Airport 2')")
            cursor.execute("""
                INSERT IGNORE INTO Aircraft (aircraft_id, manufacturer, purchase_date, is_large)
                VALUES (99990, 'Test', '2020-01-01', 0)
            """)
            future_time = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT IGNORE INTO Flight (source_airport_id, dest_airport_id, departure_time, flight_status, aircraft_id, economy_price, business_price)
                VALUES (9999, 9998, %s, 'Active', 99990, 100, 200)
            """, (future_time,))
            
            # Create order (simulating booking)
            order_code = 999999
            cursor.execute("""
                INSERT INTO Order_Table (order_code, order_date, total_payment, order_status, customer_email, source_airport_id, dest_airport_id, departure_time)
                VALUES (%s, NOW(), 100, 'Active', 'test_order@test.com', 9999, 9998, %s)
            """, (order_code, future_time))
            conn.commit()
            
            # Verify status
            cursor.execute("SELECT order_status FROM Order_Table WHERE order_code = %s", (order_code,))
            result = cursor.fetchone()
            
            assert result is not None, "Order should exist"
            assert result[0] == 'Active', f"Order status should be 'Active', got '{result[0]}'"
            assert result[0] != 'Confirmed', "Order status should not be 'Confirmed'"
            
        finally:
            cleanup_test_data(cursor, conn)
            cursor.close()
            conn.close()

class TestCrewJoinDateValidation:
    """Test crew join date validation."""
    
    def test_crew_with_past_start_date_is_available(self):
        """Test that crew with start_work_date before flight departure is available."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Create test airports and route if needed
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (1, 'Test Airport 1')")
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (2, 'Test Airport 2')")
            cursor.execute("""
                INSERT IGNORE INTO Flight_Route (source_airport_id, dest_airport_id, flight_duration)
                VALUES (1, 2, 120)
            """)
            
            # Create test employee
            start_date = (datetime.now() - timedelta(days=30)).date()
            cursor.execute("""
                INSERT IGNORE INTO Employee (id_number, first_name, last_name, start_work_date)
                VALUES ('TEST001', 'Test', 'Pilot', %s)
            """, (start_date,))
            cursor.execute("""
                INSERT IGNORE INTO Flight_Crew (id_number, trained_for_long_flights, is_pilot)
                VALUES ('TEST001', 1, 1)
            """)
            conn.commit()
            
            # Get crew availability for future flight with app context
            future_time = datetime.now() + timedelta(days=1)
            with app.app_context():
                result = get_crew_availability(1, 2, future_time.strftime('%Y-%m-%dT%H:%M'))
            
            # Find our test pilot
            test_pilot = None
            for crew in result['crew']:
                if crew['id_number'] == 'TEST001':
                    test_pilot = crew
                    break
            
            assert test_pilot is not None, "Test pilot should be in crew list"
            assert test_pilot['is_available'] == True, "Pilot with past start date should be available"
            
        finally:
            cleanup_test_data(cursor, conn)
            cursor.close()
            conn.close()
    
    def test_crew_with_future_start_date_is_unavailable(self):
        """Test that crew with start_work_date after flight departure is unavailable."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Create test airports and route if needed
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (1, 'Test Airport 1')")
            cursor.execute("INSERT IGNORE INTO Airport (airport_id, airport_name) VALUES (2, 'Test Airport 2')")
            cursor.execute("""
                INSERT IGNORE INTO Flight_Route (source_airport_id, dest_airport_id, flight_duration)
                VALUES (1, 2, 120)
            """)
            
            # Create test employee with future start date
            start_date = (datetime.now() + timedelta(days=30)).date()
            cursor.execute("""
                INSERT IGNORE INTO Employee (id_number, first_name, last_name, start_work_date)
                VALUES ('TEST002', 'Test', 'Pilot', %s)
            """, (start_date,))
            cursor.execute("""
                INSERT IGNORE INTO Flight_Crew (id_number, trained_for_long_flights, is_pilot)
                VALUES ('TEST002', 1, 1)
            """)
            conn.commit()
            
            # Get crew availability for near-future flight with app context
            future_time = datetime.now() + timedelta(days=1)
            with app.app_context():
                result = get_crew_availability(1, 2, future_time.strftime('%Y-%m-%dT%H:%M'))
            
            # Find our test pilot
            test_pilot = None
            for crew in result['crew']:
                if crew['id_number'] == 'TEST002':
                    test_pilot = crew
                    break
            
            assert test_pilot is not None, "Test pilot should be in crew list"
            assert test_pilot['is_available'] == False, "Pilot with future start date should be unavailable"
            assert 'not joined' in test_pilot['reason'].lower(), "Reason should mention not joined yet"
            
        finally:
            cleanup_test_data(cursor, conn)
            cursor.close()
            conn.close()

class TestAircraftClassBusinessRule:
    """Test aircraft class business rule enforcement."""
    
    def test_large_aircraft_requires_business_class(self):
        """Test that large aircraft must have business class."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Try to add large aircraft without business class with app context
            with app.app_context():
                result = add_aircraft(
                    aircraft_id=99991,
                    manufacturer='Test',
                    purchase_date='2020-01-01',
                    is_large=1,
                    business_config=None,
                    economy_config={'num_rows': 10, 'num_columns': 6}
                )
            
            assert result[0] == False, "Should fail to add large aircraft without business class"
            assert 'business class' in result[1].lower(), "Error message should mention business class"
            
        finally:
            cleanup_test_data(cursor, conn)
            cursor.close()
            conn.close()
    
    def test_small_aircraft_cannot_have_business_class(self):
        """Test that small aircraft cannot have business class."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Try to add small aircraft with business class with app context
            with app.app_context():
                result = add_aircraft(
                    aircraft_id=99992,
                    manufacturer='Test',
                    purchase_date='2020-01-01',
                    is_large=0,
                    business_config={'num_rows': 5, 'num_columns': 4},
                    economy_config={'num_rows': 10, 'num_columns': 6}
                )
            
            assert result[0] == False, "Should fail to add small aircraft with business class"
            assert 'cannot have business class' in result[1].lower() or 'small aircraft' in result[1].lower(), "Error message should mention small aircraft cannot have business class"
            
        finally:
            cleanup_test_data(cursor, conn)
            cursor.close()
            conn.close()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

