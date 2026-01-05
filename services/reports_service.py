from db import query_db
from services.flight_service import update_flight_statuses

@update_flight_statuses
def get_occupancy_report():
    return query_db("""
        SELECT 
            A1.airport_name as source, 
            A2.airport_name as dest, 
            F.departure_time,
            (COUNT(OS.order_code) / (SELECT COUNT(*) FROM Seat S WHERE S.aircraft_id = F.aircraft_id)) * 100 as occupancy_percentage
        FROM Flight F
        JOIN Airport A1 ON F.source_airport_id = A1.airport_id
        JOIN Airport A2 ON F.dest_airport_id = A2.airport_id
        LEFT JOIN Order_Table O ON F.source_airport_id = O.source_airport_id 
                                AND F.dest_airport_id = O.dest_airport_id 
                                AND F.departure_time = O.departure_time
                                AND O.order_status = 'Active'
        LEFT JOIN Order_Seats OS ON O.order_code = OS.order_code
        WHERE F.departure_time < NOW() AND F.flight_status != 'Canceled'
        GROUP BY F.source_airport_id, F.dest_airport_id, F.departure_time, F.aircraft_id
    """)

@update_flight_statuses
def get_revenue_report():
    return query_db("""
        SELECT 
            AC.manufacturer, 
            AC.is_large, 
            OS.is_business, 
            SUM(O.total_payment) as total_revenue
        FROM Order_Table O
        JOIN Flight F ON O.source_airport_id = F.source_airport_id 
                      AND O.dest_airport_id = F.dest_airport_id 
                      AND O.departure_time = F.departure_time
        JOIN Aircraft AC ON F.aircraft_id = AC.aircraft_id
        JOIN (SELECT DISTINCT order_code, is_business FROM Order_Seats) OS ON O.order_code = OS.order_code
        WHERE O.order_status = 'Active'
        GROUP BY AC.manufacturer, AC.is_large, OS.is_business
    """)

@update_flight_statuses
def get_employee_hours_report():
    return query_db("""
        SELECT 
            E.first_name, 
            E.last_name, 
            CASE WHEN FC.is_pilot THEN 'Pilot' ELSE 'Attendant' END as role,
            SUM(CASE WHEN FR.flight_duration > 360 THEN FR.flight_duration ELSE 0 END) / 60 as long_hours,
            SUM(CASE WHEN FR.flight_duration <= 360 THEN FR.flight_duration ELSE 0 END) / 60 as short_hours,
            SUM(FR.flight_duration) / 60 as total_hours
        FROM Employee E
        JOIN Flight_Crew FC ON E.id_number = FC.id_number
        JOIN Employee_Flight_Assignment EFA ON E.id_number = EFA.employee_id
        JOIN Flight F ON EFA.source_airport_id = F.source_airport_id 
                      AND EFA.dest_airport_id = F.dest_airport_id 
                      AND EFA.departure_time = F.departure_time
        JOIN Flight_Route FR ON F.source_airport_id = FR.source_airport_id 
                             AND F.dest_airport_id = FR.dest_airport_id
        WHERE F.flight_status != 'Canceled'
        GROUP BY E.id_number
    """)

def get_cancellation_report():
    return query_db("""
        SELECT 
            DATE_FORMAT(order_date, '%Y-%m') as month,
            COUNT(*) as total_orders,
            SUM(CASE WHEN order_status IN ('System Cancellation', 'Client Cancellation') THEN 1 ELSE 0 END) as cancelled_orders,
            (SUM(CASE WHEN order_status IN ('System Cancellation', 'Client Cancellation') THEN 1 ELSE 0 END) / COUNT(*)) * 100 as cancellation_rate
        FROM Order_Table
        GROUP BY DATE_FORMAT(order_date, '%Y-%m')
    """)

@update_flight_statuses
def get_plane_activity_report():
    return query_db("""
        SELECT 
            F.aircraft_id,
            DATE_FORMAT(F.departure_time, '%Y-%m') as month,
            COUNT(CASE WHEN F.flight_status != 'Canceled' THEN 1 END) as flights_performed,
            COUNT(CASE WHEN F.flight_status = 'Canceled' THEN 1 END) as flights_cancelled,
            (SUM(CASE WHEN F.flight_status != 'Canceled' THEN FR.flight_duration ELSE 0 END) / (30 * 24 * 60)) * 100 as utilization,
            (SELECT CONCAT(A1.airport_name, ' -> ', A2.airport_name) 
             FROM Flight F2 
             JOIN Airport A1 ON F2.source_airport_id = A1.airport_id
             JOIN Airport A2 ON F2.dest_airport_id = A2.airport_id
             WHERE F2.aircraft_id = F.aircraft_id 
               AND DATE_FORMAT(F2.departure_time, '%Y-%m') = DATE_FORMAT(F.departure_time, '%Y-%m')
             GROUP BY F2.source_airport_id, F2.dest_airport_id
             ORDER BY COUNT(*) DESC LIMIT 1) as dominant_route
        FROM Flight F
        JOIN Flight_Route FR ON F.source_airport_id = FR.source_airport_id AND F.dest_airport_id = FR.dest_airport_id
        GROUP BY F.aircraft_id, DATE_FORMAT(F.departure_time, '%Y-%m')
    """)
