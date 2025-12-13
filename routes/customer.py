from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import query_db, execute_db

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def index():
    airports = query_db("SELECT airport_name FROM Airport")
    
    # Search Logic
    source = request.args.get('source')
    dest = request.args.get('dest')
    date = request.args.get('date')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    flight_class = request.args.get('class')
    show_all = request.args.get('show_all')
    
    flights = None
    
    if source or dest or date or min_price or max_price or show_all:
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
        if date:
            query += " AND DATE(F.departure_time) = %s"
            params.append(date)
            
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

    return render_template('customer/index.html', airports=airports, flights=flights)

@customer_bp.route('/track_order', methods=['GET', 'POST'])
def track_order():
    order = None
    if request.method == 'POST':
        order_code = request.form.get('order_code')
        email = request.form.get('email')
        
        query = """
            SELECT 
                O.order_code, 
                O.order_date, 
                O.total_payment, 
                O.order_status, 
                O.departure_time,
                A1.airport_name as source_airport,
                A2.airport_name as dest_airport
            FROM Order_Table O
            JOIN Airport A1 ON O.source_airport_id = A1.airport_id
            JOIN Airport A2 ON O.dest_airport_id = A2.airport_id
            WHERE O.order_code = %s AND O.customer_email = %s
        """
        result = query_db(query, (order_code, email))
        
        if result:
            order = result[0]
        else:
            flash('Order not found. Please check your details.', 'danger')
            
    return render_template('customer/track_order.html', order=order)

@customer_bp.route('/my_orders')
def my_orders():
    if session.get('role') != 'customer':
        flash('Please log in as a customer to view your orders.', 'warning')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_id')
    status_filter = request.args.get('status')
    
    query = """
        SELECT 
            O.order_code, 
            O.order_date, 
            O.total_payment, 
            O.order_status, 
            O.departure_time,
            A1.airport_name as source_airport,
            A2.airport_name as dest_airport,
            OS.row_number,
            OS.column_number,
            OS.is_business
        FROM Order_Table O
        JOIN Airport A1 ON O.source_airport_id = A1.airport_id
        JOIN Airport A2 ON O.dest_airport_id = A2.airport_id
        LEFT JOIN Order_Seats OS ON O.order_code = OS.order_code
        WHERE O.customer_email = %s
    """
    params = [email]
    
    if status_filter:
        query += " AND O.order_status = %s"
        params.append(status_filter)
        
    query += " ORDER BY O.order_date DESC"
    
    raw_orders = query_db(query, tuple(params))
    
    # Group seats by order
    orders_map = {}
    total_spending = 0
    
    for row in raw_orders:
        code = row['order_code']
        if code not in orders_map:
            orders_map[code] = {
                'order_code': row['order_code'],
                'order_date': row['order_date'],
                'total_payment': row['total_payment'],
                'order_status': row['order_status'],
                'departure_time': row['departure_time'],
                'source_airport': row['source_airport'],
                'dest_airport': row['dest_airport'],
                'seats': []
            }
            
            # Add to total spending if not cancelled
            if row['order_status'] != 'Cancelled' and row['order_status'] != 'Customer Cancelled' and row['order_status'] != 'System Cancelled':
                total_spending += row['total_payment']
        
        if row['row_number'] is not None:
            orders_map[code]['seats'].append({
                'row': row['row_number'],
                'col': row['column_number'],
                'is_business': row['is_business']
            })
    
    orders = list(orders_map.values())
    
    return render_template('customer/my_orders.html', orders=orders, total_spending=total_spending)

@customer_bp.route('/cancel_order/<int:order_code>', methods=['POST'])
def cancel_order(order_code):
    if session.get('role') != 'customer':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))
        
    email = session.get('user_id')
    
    # Verify order belongs to user and is active
    order = query_db("SELECT * FROM Order_Table WHERE order_code = %s AND customer_email = %s", (order_code, email), one=True)
    
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('customer.my_orders'))
        
    if order['order_status'] in ['Cancelled', 'Customer Cancelled', 'System Cancelled']:
        flash('Order is already cancelled.', 'warning')
        return redirect(url_for('customer.my_orders'))
        
    # Check if flight is in the future (optional but recommended)
    # For now, just allowing cancellation as requested
    
    try:
        execute_db("UPDATE Order_Table SET order_status = 'Customer Cancelled' WHERE order_code = %s", (order_code,))
        flash('Order cancelled successfully.', 'success')
    except Exception as e:
        flash(f'Error cancelling order: {e}', 'danger')
        
    return redirect(url_for('customer.my_orders'))

@customer_bp.route('/book_flight', methods=['GET', 'POST'])
def book_flight():
    if 'user_id' in session and session.get('role') == 'manager':
        flash("Managers cannot book flights. Please log in as a customer.", "danger")
        return redirect(url_for('customer.index'))

    import random
    from datetime import datetime

    source_id = request.args.get('source_id')
    dest_id = request.args.get('dest_id')
    time_str = request.args.get('time')
    
    booking_success = False
    new_order_code = None
    
    if request.method == 'POST':
        # Handle Booking Logic
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        
        # Multiple seats
        seat_rows = request.form.getlist('seat_row')
        seat_cols = request.form.getlist('seat_col')
        seat_classes = request.form.getlist('seat_class')
        
        # Passenger details for 2nd seat
        passenger_2_name = request.form.get('passenger_2_name')
        
        # If user is logged in as customer, use their email
        if 'user_id' in session and session.get('role') == 'customer':
            email = session['user_id']
        
        # 1. Ensure User Exists (or create dummy user for non-registered)
        user_check = query_db("SELECT email FROM User WHERE email = %s", (email,))
        if not user_check:
            # Create new user
            execute_db("INSERT INTO User (email, first_name, last_name) VALUES (%s, %s, %s)", 
                     (email, first_name, last_name))
            execute_db("INSERT INTO Phone (email, phone_number) VALUES (%s, %s)", (email, phone))
            
        # 2. Create Order
        order_code = random.randint(100000, 999999)
        
        # Get price and aircraft_id
        flight_info = query_db(f"SELECT economy_price, business_price, aircraft_id FROM Flight WHERE source_airport_id=%s AND dest_airport_id=%s AND departure_time=%s", 
                               (source_id, dest_id, time_str))
        
        if not flight_info:
            flash("Flight not found.", "danger")
            return redirect(url_for('customer.index'))
            
        economy_price = flight_info[0]['economy_price']
        business_price = flight_info[0]['business_price']
        aircraft_id = flight_info[0]['aircraft_id']
        
        total_price = 0
        for s_class in seat_classes:
            if s_class == 'business':
                total_price += business_price
            else:
                total_price += economy_price
        
        execute_db("""
            INSERT INTO Order_Table (order_code, order_date, total_payment, order_status, customer_email, source_airport_id, dest_airport_id, departure_time)
            VALUES (%s, NOW(), %s, 'Confirmed', %s, %s, %s, %s)
        """, (order_code, total_price, email, source_id, dest_id, time_str))
        
        # 3. Book Seats
        try:
            for i in range(len(seat_rows)):
                row = seat_rows[i]
                col = seat_cols[i]
                s_class = seat_classes[i]
                is_business = (s_class == 'business')
                p_name = None
                
                # Logic: 
                # Seat 1: Main booker (User table handles it via Order_Table link)
                # Seat 2: passenger_2_name
                # Seat 3+: None
                if i == 1:
                    p_name = passenger_2_name
                
                execute_db("""
                    INSERT INTO Order_Seats (order_code, aircraft_id, is_business, `row_number`, `column_number`, passenger_name)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (order_code, aircraft_id, is_business, row, col, p_name))
            
            booking_success = True
            new_order_code = order_code
            
        except Exception as e:
            # Rollback order if seat booking fails (simplified)
            execute_db("DELETE FROM Order_Table WHERE order_code = %s", (order_code,))
            flash(f"Booking failed: {e}", "danger")
            return redirect(request.url)

    # GET Request - Show Seat Map
    
    # 1. Get Flight Info & Aircraft Config for BOTH classes
    flight_query = """
        SELECT F.aircraft_id, AC.is_business, AC.num_rows, AC.num_columns, F.economy_price, F.business_price,
               A1.airport_name as source_airport, A2.airport_name as dest_airport, FR.flight_duration, Aircraft.manufacturer
        FROM Flight F
        JOIN Aircraft_Class AC ON F.aircraft_id = AC.aircraft_id
        JOIN Airport A1 ON F.source_airport_id = A1.airport_id
        JOIN Airport A2 ON F.dest_airport_id = A2.airport_id
        JOIN Flight_Route FR ON F.source_airport_id = FR.source_airport_id AND F.dest_airport_id = FR.dest_airport_id
        JOIN Aircraft ON F.aircraft_id = Aircraft.aircraft_id
        WHERE F.source_airport_id = %s AND F.dest_airport_id = %s AND F.departure_time = %s
    """
    flight_data = query_db(flight_query, (source_id, dest_id, time_str))
    
    if not flight_data:
        flash("Flight details not found.", "danger")
        return redirect(url_for('customer.index'))
        
    configs = {}
    economy_price = 0
    business_price = 0
    flight_details = {
        'source': flight_data[0]['source_airport'],
        'dest': flight_data[0]['dest_airport'],
        'duration': flight_data[0]['flight_duration'],
        'aircraft': flight_data[0]['manufacturer']
    }
    
    for row in flight_data:
        is_biz = (row['is_business'] == 1)
        configs[is_biz] = {'rows': row['num_rows'], 'cols': row['num_columns']}
        if is_biz:
            business_price = row['business_price']
        else:
            economy_price = row['economy_price']
    
    # 2. Get Occupied Seats for ALL classes
    occupied_query = """
        SELECT OS.row_number, OS.column_number, OS.is_business
        FROM Order_Seats OS
        JOIN Order_Table O ON OS.order_code = O.order_code
        WHERE O.source_airport_id = %s AND O.dest_airport_id = %s AND O.departure_time = %s
        AND O.order_status != 'Cancelled'
    """
    occupied_seats = query_db(occupied_query, (source_id, dest_id, time_str))
    
    occupied_economy = set()
    occupied_business = set()
    
    for s in occupied_seats:
        if s['is_business']:
            occupied_business.add((s['row_number'], s['column_number']))
        else:
            occupied_economy.add((s['row_number'], s['column_number']))
            
    # Calculate Availability
    has_economy = False
    has_business = False
    
    if False in configs:
        total_eco = configs[False]['rows'] * configs[False]['cols']
        if len(occupied_economy) < total_eco:
            has_economy = True
            
    if True in configs:
        total_biz = configs[True]['rows'] * configs[True]['cols']
        if len(occupied_business) < total_biz:
            has_business = True
    
    return render_template('customer/book_flight.html', 
                           configs=configs,
                           occupied_economy=occupied_economy,
                           occupied_business=occupied_business,
                           economy_price=economy_price,
                           business_price=business_price,
                           has_economy=has_economy,
                           has_business=has_business,
                           source_id=source_id,
                           dest_id=dest_id,
                           time=time_str,
                           booking_success=booking_success,
                           new_order_code=new_order_code,
                           flight_details=flight_details)
