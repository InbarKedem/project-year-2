from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import query_db, execute_db
from datetime import datetime, timedelta, date
from services.flight_service import update_all_flight_statuses

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def index():
    # Managers can view flights but cannot book them
    update_all_flight_statuses()
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

@customer_bp.route('/track_order', methods=['GET', 'POST'])
def track_order():
    # Prevent managers from tracking orders
    if session.get('role') == 'manager':
        return redirect(url_for('manager.manager_dashboard'))
    
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
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    departure_from = request.args.get('departure_from')
    departure_to = request.args.get('departure_to')
    source_airport = request.args.get('source_airport')
    dest_airport = request.args.get('dest_airport')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    order_code_filter = request.args.get('order_code')
    seat_class_filter = request.args.get('seat_class')
    sort_by = request.args.get('sort_by', 'order_date')
    sort_order = request.args.get('sort_order', 'DESC')
    
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
    
    if date_from:
        query += " AND DATE(O.order_date) >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND DATE(O.order_date) <= %s"
        params.append(date_to)
    
    if departure_from:
        query += " AND DATE(O.departure_time) >= %s"
        params.append(departure_from)
    
    if departure_to:
        query += " AND DATE(O.departure_time) <= %s"
        params.append(departure_to)
    
    if source_airport:
        query += " AND A1.airport_name = %s"
        params.append(source_airport)
    
    if dest_airport:
        query += " AND A2.airport_name = %s"
        params.append(dest_airport)
    
    if order_code_filter:
        try:
            query += " AND O.order_code = %s"
            params.append(int(order_code_filter))
        except ValueError:
            pass
    
    if seat_class_filter:
        # Filter by seat class - need to check if order has seats of that class
        if seat_class_filter == 'business':
            query += " AND EXISTS (SELECT 1 FROM Order_Seats OS2 WHERE OS2.order_code = O.order_code AND OS2.is_business = 1)"
        elif seat_class_filter == 'economy':
            query += " AND EXISTS (SELECT 1 FROM Order_Seats OS2 WHERE OS2.order_code = O.order_code AND OS2.is_business = 0)"
    
    if min_price:
        try:
            query += " AND O.total_payment >= %s"
            params.append(float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            query += " AND O.total_payment <= %s"
            params.append(float(max_price))
        except ValueError:
            pass
    
    # Validate sort_by to prevent SQL injection
    valid_sort_columns = ['order_date', 'departure_time', 'total_payment', 'order_code']
    if sort_by not in valid_sort_columns:
        sort_by = 'order_date'
    
    # Validate sort_order
    if sort_order.upper() not in ['ASC', 'DESC']:
        sort_order = 'DESC'
    
    query += f" ORDER BY O.{sort_by} {sort_order}"
    
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
            
            # Add to total spending:
            # - Active/Confirmed orders: full payment
            # - Customer Cancelled: 5% cancellation fee (stored in total_payment)
            # - System Cancelled: 0 (full refund)
            # - Cancelled (legacy): 0
            if row['order_status'] == 'Customer Cancelled':
                # Customer cancelled orders have the 5% fee stored in total_payment
                total_spending += row['total_payment']
            elif row['order_status'] not in ['Cancelled', 'System Cancelled']:
                # Active, Confirmed orders - full payment
                total_spending += row['total_payment']
        
        if row['row_number'] is not None:
            orders_map[code]['seats'].append({
                'row': row['row_number'],
                'col': row['column_number'],
                'is_business': row['is_business']
            })
    
    orders = list(orders_map.values())
    
    # Get airports for filter dropdown
    airports = query_db("SELECT airport_name FROM Airport ORDER BY airport_name")
    
    return render_template('customer/my_orders.html', 
                          orders=orders, 
                          total_spending=total_spending,
                          airports=airports)

@customer_bp.route('/cancel_order/<int:order_code>', methods=['POST'])
def cancel_order(order_code):
    # Prevent managers from canceling orders
    if session.get('role') == 'manager':
        return redirect(url_for('manager.manager_dashboard'))
    
    # 1. Identify User (Session or Form)
    email = None
    if 'user_id' in session and session.get('role') == 'customer':
        email = session['user_id']
    else:
        # For guests, email must be provided in the form to verify ownership
        email = request.form.get('email')
    
    if not email:
        flash('Authentication failed. Please log in or provide email.', 'danger')
        return redirect(url_for('customer.index'))
    
    # 2. Verify Order
    order = query_db("SELECT * FROM Order_Table WHERE order_code = %s AND customer_email = %s", (order_code, email), one=True)
    
    if not order:
        flash('Order not found or access denied.', 'danger')
        # Redirect back to where they came from if possible, or my_orders/track_order
        if 'user_id' in session:
            return redirect(url_for('customer.my_orders'))
        else:
            return redirect(url_for('customer.track_order'))
        
    if order['order_status'] in ['Cancelled', 'Customer Cancelled', 'System Cancelled']:
        flash('Order is already cancelled.', 'warning')
        if 'user_id' in session:
            return redirect(url_for('customer.my_orders'))
        else:
            # Re-render track order with the order details
            return render_template('customer/track_order.html', order=order)

    # 3. Check 36-hour Rule
    departure_time = order['departure_time']
    # Ensure departure_time is datetime object
    if isinstance(departure_time, str):
        departure_time = datetime.strptime(departure_time, '%Y-%m-%d %H:%M:%S')
        
    time_diff = departure_time - datetime.now()
    hours_until_flight = time_diff.total_seconds() / 3600
    
    if hours_until_flight < 36:
        flash('Cancellation is only allowed up to 36 hours before the flight.', 'danger')
        if 'user_id' in session:
            return redirect(url_for('customer.my_orders'))
        else:
            return render_template('customer/track_order.html', order=order)

    # 4. Apply Cancellation Fee (5%)
    # We don't have a refund column, so we'll just notify the user.
    # In a real system, we would process the refund here.
    fee = float(order['total_payment']) * 0.05
    refund_amount = float(order['total_payment']) - fee
    
    try:
        execute_db("UPDATE Order_Table SET order_status = 'Customer Cancelled', total_payment = %s WHERE order_code = %s", (fee, order_code))
        flash(f'Order cancelled successfully. A 5% cancellation fee (${fee:.2f}) was deducted. Refund amount: ${refund_amount:.2f}', 'success')
    except Exception as e:
        flash(f'Error cancelling order: {e}', 'danger')
        
    if 'user_id' in session:
        return redirect(url_for('customer.my_orders'))
    else:
        # For guests, we need to show the updated status. 
        # Since we can't easily redirect with POST data, we re-fetch and render.
        updated_order = query_db("SELECT * FROM Order_Table WHERE order_code = %s", (order_code,), one=True)
        # We need to join with Airport names again for the template
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
            WHERE O.order_code = %s
        """
        updated_order = query_db(query, (order_code,), one=True)
        return render_template('customer/track_order.html', order=updated_order)

@customer_bp.route('/book_flight', methods=['GET', 'POST'])
def book_flight():
    update_all_flight_statuses()
    if 'user_id' in session and session.get('role') == 'manager':
        return redirect(url_for('manager.manager_dashboard'))

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
        AND O.order_status NOT IN ('Cancelled', 'Customer Cancelled', 'System Cancelled')
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
            
    # Get user details if logged in
    user_details = None
    if 'user_id' in session and session.get('role') == 'customer':
        user_details = query_db("""
            SELECT U.email, U.first_name, U.last_name, P.phone_number 
            FROM User U 
            LEFT JOIN Phone P ON U.email = P.email 
            WHERE U.email = %s
        """, (session['user_id'],), one=True)
    
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
                           flight_details=flight_details,
                           user_details=user_details)
