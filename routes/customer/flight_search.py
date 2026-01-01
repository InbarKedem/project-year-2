from flask import render_template, request
from db import query_db
from datetime import date
from routes.customer import customer_bp
from services.flight_service import update_flight_statuses

@customer_bp.route('/')
@update_flight_statuses
def index():
    # Managers can view flights but cannot book them
    airports = query_db("SELECT airport_name FROM Airport")
    
    # Search Logic
    source = request.args.get('source')
    dest = request.args.get('dest')
    search_date = request.args.get('date')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    flight_class = request.args.get('class')
    show_all = request.args.get('show_all')
    
    flights = None
    
    if source or dest or search_date or min_price or max_price or show_all:
        query = """
            SELECT 
                F.source_airport_id, F.dest_airport_id, F.departure_time,
                F.economy_price, F.business_price, F.flight_status,
                A1.airport_name as source_airport,
                A2.airport_name as dest_airport,
                AC.manufacturer, AC.is_large,
                FR.flight_duration
            FROM Flight F
            JOIN Airport A1 ON F.source_airport_id = A1.airport_id
            JOIN Airport A2 ON F.dest_airport_id = A2.airport_id
            JOIN Aircraft AC ON F.aircraft_id = AC.aircraft_id
            JOIN Flight_Route FR ON F.source_airport_id = FR.source_airport_id AND F.dest_airport_id = FR.dest_airport_id
            WHERE F.flight_status = 'Active'
        """
        params = []
        
        if source:
            query += " AND A1.airport_name LIKE %s"
            params.append(f"%{source}%")
        if dest:
            query += " AND A2.airport_name LIKE %s"
            params.append(f"%{dest}%")
        if search_date:
            query += " AND DATE(F.departure_time) = %s"
            params.append(search_date)
            
        if min_price:
            if flight_class == 'Business':
                query += " AND F.business_price >= %s"
            else:
                query += " AND F.economy_price >= %s"
            params.append(min_price)
            
        if max_price:
            if flight_class == 'Business':
                query += " AND F.business_price <= %s"
            else:
                query += " AND F.economy_price <= %s"
            params.append(max_price)

        query += " ORDER BY F.departure_time"
        flights = query_db(query, tuple(params))
    
    # Pass today's date for the min attribute in date input
    today_date = date.today().isoformat()

    return render_template('customer/index.html', airports=airports, flights=flights, today_date=today_date)

