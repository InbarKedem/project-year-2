from db import query_db
from services.flight_service import update_flight_statuses

@update_flight_statuses
def get_occupancy_report():
    return query_db("""
        SELECT
          AVG(f_occ.occupancy_rate) AS avg_occupancy_rate
        FROM (
          SELECT
            f.source_airport_id,
            f.dest_airport_id,
            f.departure_time,
            COALESCE(b.booked_seats, 0) / t.total_seats AS occupancy_rate
          FROM Flight f
          JOIN (
            -- total seats available on the aircraft assigned to the flight
            SELECT
              f2.source_airport_id,
              f2.dest_airport_id,
              f2.departure_time,
              COUNT(*) AS total_seats
            FROM Flight f2
            JOIN Seat s
              ON s.aircraft_id = f2.aircraft_id
            GROUP BY f2.source_airport_id, f2.dest_airport_id, f2.departure_time
          ) t
            ON t.source_airport_id = f.source_airport_id
           AND t.dest_airport_id   = f.dest_airport_id
           AND t.departure_time    = f.departure_time
          LEFT JOIN (
            -- seats booked for each flight (via orders)
            SELECT
              o.source_airport_id,
              o.dest_airport_id,
              o.departure_time,
              COUNT(*) AS booked_seats
            FROM Order_Table o
            JOIN Order_Seats os
              ON os.order_code = o.order_code
            GROUP BY o.source_airport_id, o.dest_airport_id, o.departure_time
          ) b
            ON b.source_airport_id = f.source_airport_id
           AND b.dest_airport_id   = f.dest_airport_id
           AND b.departure_time    = f.departure_time
          WHERE f.aircraft_id IS NOT NULL
        ) AS f_occ
    """)

@update_flight_statuses
def get_revenue_report():
    return query_db("""
        SELECT
            AC.manufacturer,
            AC.is_large,
            os_price.is_business,
            SUM(O.total_payment * os_price.class_value / os_price.order_value) AS total_revenue
        FROM Order_Table O
        JOIN Flight F
          ON O.source_airport_id = F.source_airport_id
         AND O.dest_airport_id   = F.dest_airport_id
         AND O.departure_time    = F.departure_time
        JOIN Aircraft AC
          ON F.aircraft_id = AC.aircraft_id
        JOIN (
            SELECT
                os.order_code,
                os.is_business,
                COUNT(*) *
                CASE
                    WHEN os.is_business = TRUE THEN f.business_price
                    ELSE f.economy_price
                END AS class_value,
                SUM(
                    COUNT(*) *
                    CASE
                        WHEN os.is_business = TRUE THEN f.business_price
                        ELSE f.economy_price
                    END
                ) OVER (PARTITION BY os.order_code) AS order_value
            FROM Order_Seats os
            JOIN Order_Table o2 ON o2.order_code = os.order_code
            JOIN Flight f
              ON o2.source_airport_id = f.source_airport_id
             AND o2.dest_airport_id   = f.dest_airport_id
             AND o2.departure_time    = f.departure_time
            GROUP BY os.order_code, os.is_business
        ) AS os_price
          ON os_price.order_code = O.order_code
        WHERE O.order_status = 'Active'
        GROUP BY
            AC.manufacturer,
            AC.is_large,
            os_price.is_business
    """)

@update_flight_statuses
def get_employee_hours_report():
    return query_db("""
        SELECT 
            E.id_number,
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
          m.aircraft_id,
          m.month,
          m.flights_performed,
          m.flights_cancelled,
          m.utilization,
          (
            SELECT CONCAT(A1.airport_name, ' -> ', A2.airport_name)
            FROM Flight F2
            JOIN Airport A1 ON F2.source_airport_id = A1.airport_id
            JOIN Airport A2 ON F2.dest_airport_id = A2.airport_id
            WHERE F2.aircraft_id = m.aircraft_id
              AND DATE_FORMAT(F2.departure_time, '%Y-%m') = m.month
            GROUP BY F2.source_airport_id, F2.dest_airport_id
            ORDER BY COUNT(*) DESC
            LIMIT 1
          ) AS dominant_route
        FROM (
          SELECT
            F.aircraft_id,
            DATE_FORMAT(F.departure_time, '%Y-%m') AS month,
            COUNT(CASE WHEN F.flight_status != 'Cancelled' THEN 1 END) AS flights_performed,
            COUNT(CASE WHEN F.flight_status = 'Cancelled' THEN 1 END) AS flights_cancelled,
            (SUM(CASE WHEN F.flight_status != 'Cancelled' THEN FR.flight_duration ELSE 0 END) / (30 * 24 * 60)) * 100 AS utilization
          FROM Flight F
          JOIN Flight_Route FR
            ON F.source_airport_id = FR.source_airport_id
           AND F.dest_airport_id   = FR.dest_airport_id
          GROUP BY F.aircraft_id, DATE_FORMAT(F.departure_time, '%Y-%m')
        ) AS m
    """)
