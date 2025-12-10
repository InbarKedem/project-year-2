from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from db import query_db, execute_db
from datetime import datetime
import json

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def index():
    # Get all airports for dropdown
    airports = query_db('SELECT airport_id, airport_name FROM Airport ORDER BY airport_name')
    if not airports:
        airports = []
    
    # Get search parameters
    source_id = request.args.get('source')
    dest_id = request.args.get('dest')
    date = request.args.get('date')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    flight_status = request.args.get('flight_status')
    time_from = request.args.get('time_from')
    time_to = request.args.get('time_to')
    
    flights = None
    
    # Only search if basic criteria are provided
    if source_id and dest_id and date:
        query = """
            SELECT 
                F.source_airport_id,
                F.dest_airport_id,
                F.departure_time,
                F.flight_status,
                F.aircraft_id,
                F.economy_price,
                F.business_price,
                A1.airport_name as source_airport,
                A2.airport_name as dest_airport,
                FR.flight_duration
            FROM Flight F
            JOIN Airport A1 ON F.source_airport_id = A1.airport_id
            JOIN Airport A2 ON F.dest_airport_id = A2.airport_id
            JOIN Flight_Route FR ON F.source_airport_id = FR.source_airport_id 
                AND F.dest_airport_id = FR.dest_airport_id
            WHERE F.source_airport_id = %s 
                AND F.dest_airport_id = %s
                AND DATE(F.departure_time) = %s
        """
        params = [source_id, dest_id, date]
        
        # Apply advanced filters
        if min_price:
            query += " AND (F.economy_price >= %s AND F.business_price >= %s)"
            params.extend([min_price, min_price])
        
        if max_price:
            query += " AND (F.economy_price <= %s OR F.business_price <= %s)"
            params.extend([max_price, max_price])
        
        if flight_status:
            query += " AND F.flight_status = %s"
            params.append(flight_status)
        
        if time_from:
            query += " AND TIME(F.departure_time) >= %s"
            params.append(time_from)
        
        if time_to:
            query += " AND TIME(F.departure_time) <= %s"
            params.append(time_to)
        
        query += " ORDER BY F.departure_time"
        
        flights = query_db(query, tuple(params))
    
    return render_template('customer/index.html', 
                         airports=airports, 
                         flights=flights)

@customer_bp.route('/book_flight')
def book_flight():
    if not (request.args.get('source_id') and request.args.get('dest_id') and request.args.get('departure_time')):
        flash('Invalid flight selection.', 'danger')
        return redirect(url_for('customer.index'))
    
    source_id = request.args.get('source_id')
    dest_id = request.args.get('dest_id')
    departure_time = request.args.get('departure_time')
    
    # Get flight details
    flight = query_db("""
        SELECT 
            F.source_airport_id,
            F.dest_airport_id,
            F.departure_time,
            F.flight_status,
            F.aircraft_id,
            F.economy_price,
            F.business_price,
            A1.airport_name as source_airport,
            A2.airport_name as dest_airport,
            FR.flight_duration,
            AC.manufacturer
        FROM Flight F
        JOIN Airport A1 ON F.source_airport_id = A1.airport_id
        JOIN Airport A2 ON F.dest_airport_id = A2.airport_id
        JOIN Flight_Route FR ON F.source_airport_id = FR.source_airport_id 
            AND F.dest_airport_id = FR.dest_airport_id
        LEFT JOIN Aircraft AC ON F.aircraft_id = AC.aircraft_id
        WHERE F.source_airport_id = %s 
            AND F.dest_airport_id = %s
            AND F.departure_time = %s
    """, (source_id, dest_id, departure_time), one=True)
    
    if not flight:
        flash('Flight not found.', 'danger')
        return redirect(url_for('customer.index'))
    
    if flight['flight_status'] != 'Active':
        flash('This flight is not available for booking.', 'danger')
        return redirect(url_for('customer.index'))
    
    # Get aircraft seat layout
    economy_layout = query_db("""
        SELECT num_rows, num_columns 
        FROM Aircraft_Class 
        WHERE aircraft_id = %s AND is_business = 0
    """, (flight['aircraft_id'],), one=True)
    
    business_layout = query_db("""
        SELECT num_rows, num_columns 
        FROM Aircraft_Class 
        WHERE aircraft_id = %s AND is_business = 1
    """, (flight['aircraft_id'],), one=True)
    
    # Get occupied seats for this flight
    occupied_seats = query_db("""
        SELECT DISTINCT OS.aircraft_id, OS.is_business, OS.row_number, OS.column_number
        FROM Order_Seats OS
        JOIN Order_Table O ON OS.order_code = O.order_code
        WHERE O.source_airport_id = %s 
            AND O.dest_airport_id = %s
            AND O.departure_time = %s
            AND O.order_status = 'Active'
    """, (source_id, dest_id, departure_time))
    
    return render_template('customer/book_flight.html',
                         flight=flight,
                         economy_layout=economy_layout if economy_layout else {'num_rows': 0, 'num_columns': 0},
                         business_layout=business_layout if business_layout else {'num_rows': 0, 'num_columns': 0},
                         occupied_seats=occupied_seats)

@customer_bp.route('/confirm_booking', methods=['POST'])
def confirm_booking():
    try:
        source_id = request.form.get('source_id')
        dest_id = request.form.get('dest_id')
        departure_time = request.form.get('departure_time')
        aircraft_id = request.form.get('aircraft_id')
        selected_seats_json = request.form.get('selected_seats')
        
        if not selected_seats_json:
            flash('Please select at least one seat.', 'danger')
            return redirect(url_for('customer.book_flight', 
                                  source_id=source_id, 
                                  dest_id=dest_id, 
                                  departure_time=departure_time))
        
        selected_seats = json.loads(selected_seats_json)
        
        # Get flight prices
        flight = query_db("""
            SELECT economy_price, business_price 
            FROM Flight 
            WHERE source_airport_id = %s 
                AND dest_airport_id = %s 
                AND departure_time = %s
        """, (source_id, dest_id, departure_time), one=True)
        
        if not flight:
            flash('Flight not found.', 'danger')
            return redirect(url_for('customer.index'))
        
        # Calculate total payment
        total_payment = 0
        for seat in selected_seats:
            if seat['class'] == 'economy':
                total_payment += float(flight['economy_price'])
            else:
                total_payment += float(flight['business_price'])
        
        # Handle user info (registered or not)
        if session.get('user_id'):
            customer_email = session.get('user_id')
        else:
            # Non-registered user
            email = request.form.get('email')
            first_name = request.form.get('first_name')
            middle_name = request.form.get('middle_name')
            last_name = request.form.get('last_name')
            
            # Check if user exists
            user = query_db('SELECT email FROM User WHERE email = %s', (email,), one=True)
            
            if not user:
                # Create user
                execute_db("""
                    INSERT INTO User (email, first_name, middle_name, last_name) 
                    VALUES (%s, %s, %s, %s)
                """, (email, first_name, middle_name, last_name))
            
            customer_email = email
        
        # Generate order code (get max + 1)
        max_order = query_db('SELECT MAX(order_code) as max_code FROM Order_Table', one=True)
        order_code = (max_order['max_code'] or 0) + 1
        
        # Insert order
        execute_db("""
            INSERT INTO Order_Table 
            (order_code, order_date, total_payment, order_status, customer_email, 
             source_airport_id, dest_airport_id, departure_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (order_code, datetime.now(), total_payment, 'Active', customer_email,
              source_id, dest_id, departure_time))
        
        # Insert seat assignments
        for seat in selected_seats:
            is_business = 1 if seat['class'] == 'business' else 0
            execute_db("""
                INSERT INTO Order_Seats 
                (order_code, aircraft_id, is_business, row_number, column_number)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_code, aircraft_id, is_business, seat['row'], seat['col']))
        
        flash(f'Booking confirmed! Your order code is {order_code}.', 'success')
        
        if session.get('user_id'):
            return redirect(url_for('customer.my_orders'))
        else:
            return redirect(url_for('customer.order_lookup', order_id=order_code, email=customer_email))
    
    except Exception as e:
        flash(f'Error processing booking: {str(e)}', 'danger')
        return redirect(url_for('customer.index'))

@customer_bp.route('/order_lookup')
def order_lookup():
    order_id = request.args.get('order_id')
    email = request.args.get('email')
    
    order = None
    seats = None
    aircraft_layout = None
    searched = False  # Flag to track if a search was performed
    
    if order_id and email:
        searched = True  # User has submitted a search
        # Get order details
        order = query_db("""
            SELECT 
                O.order_code,
                O.order_date,
                O.total_payment,
                O.order_status,
                O.departure_time,
                O.customer_email,
                A1.airport_name as source_airport,
                A2.airport_name as dest_airport,
                U.first_name,
                U.middle_name,
                U.last_name,
                (SELECT COUNT(*) FROM Order_Seats OS WHERE OS.order_code = O.order_code) as seats_count,
                F.aircraft_id
            FROM Order_Table O
            JOIN Airport A1 ON O.source_airport_id = A1.airport_id
            JOIN Airport A2 ON O.dest_airport_id = A2.airport_id
            JOIN User U ON O.customer_email = U.email
            JOIN Flight F ON O.source_airport_id = F.source_airport_id
                AND O.dest_airport_id = F.dest_airport_id
                AND O.departure_time = F.departure_time
            WHERE O.order_code = %s AND O.customer_email = %s
        """, (order_id, email), one=True)
        
        if order:
            # Format customer name
            name_parts = [order['first_name']]
            if order['middle_name']:
                name_parts.append(order['middle_name'])
            name_parts.append(order['last_name'])
            order['customer_name'] = ' '.join(name_parts)
            
            # Get seat details
            seats = query_db("""
                SELECT aircraft_id, is_business, row_number, column_number
                FROM Order_Seats
                WHERE order_code = %s
                ORDER BY is_business DESC, row_number, column_number
            """, (order_id,))
            
            # Add column letters
            for seat in seats:
                seat['column_letter'] = chr(64 + seat['column_number'])
            
            # Get aircraft layout for visualization
            if order['aircraft_id']:
                economy = query_db("""
                    SELECT num_rows, num_columns 
                    FROM Aircraft_Class 
                    WHERE aircraft_id = %s AND is_business = 0
                """, (order['aircraft_id'],), one=True)
                
                business = query_db("""
                    SELECT num_rows, num_columns 
                    FROM Aircraft_Class 
                    WHERE aircraft_id = %s AND is_business = 1
                """, (order['aircraft_id'],), one=True)
                
                aircraft_layout = {
                    'economy': economy if economy else {'num_rows': 0, 'num_columns': 0},
                    'business': business if business else {'num_rows': 0, 'num_columns': 0}
                }
    
    return render_template('customer/order_lookup.html',
                         order=order,
                         seats=seats,
                         aircraft_layout=aircraft_layout,
                         searched=searched)

@customer_bp.route('/my_orders')
def my_orders():
    if session.get('role') != 'customer':
        flash('Please log in as a customer to view your orders.', 'warning')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_id')
    
    # Get all filter parameters
    order_code_filter = request.args.get('order_code')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    route_filter = request.args.get('route')
    departure_from = request.args.get('departure_from')
    departure_to = request.args.get('departure_to')
    seats_filter = request.args.get('seats')
    payment_min = request.args.get('payment_min')
    payment_max = request.args.get('payment_max')
    status_filter = request.args.get('status')
    
    query = """
        SELECT 
            O.order_code, 
            O.order_date, 
            O.total_payment, 
            O.order_status, 
            O.departure_time,
            O.source_airport_id,
            O.dest_airport_id,
            A1.airport_name as source_airport,
            A2.airport_name as dest_airport,
            (SELECT COUNT(*) FROM Order_Seats OS WHERE OS.order_code = O.order_code) as seats
        FROM Order_Table O
        JOIN Airport A1 ON O.source_airport_id = A1.airport_id
        JOIN Airport A2 ON O.dest_airport_id = A2.airport_id
        WHERE O.customer_email = %s
    """
    params = [email]
    
    # Apply filters
    if order_code_filter:
        query += " AND O.order_code = %s"
        params.append(order_code_filter)
    
    if date_from:
        query += " AND DATE(O.order_date) >= %s"
        params.append(date_from)
    
    if date_to:
        query += " AND DATE(O.order_date) <= %s"
        params.append(date_to)
    
    if route_filter:
        query += " AND (A1.airport_name LIKE %s OR A2.airport_name LIKE %s)"
        params.append(f"%{route_filter}%")
        params.append(f"%{route_filter}%")
    
    if departure_from:
        query += " AND DATE(O.departure_time) >= %s"
        params.append(departure_from)
    
    if departure_to:
        query += " AND DATE(O.departure_time) <= %s"
        params.append(departure_to)
    
    if payment_min:
        query += " AND O.total_payment >= %s"
        params.append(payment_min)
    
    if payment_max:
        query += " AND O.total_payment <= %s"
        params.append(payment_max)
    
    if status_filter:
        query += " AND O.order_status = %s"
        params.append(status_filter)
    
    query += " ORDER BY O.order_date DESC"
    
    orders = query_db(query, tuple(params))
    
    # Apply seats filter after query (post-processing since seats is calculated in SELECT)
    if seats_filter:
        try:
            seats_num = int(seats_filter)
            orders = [order for order in orders if order['seats'] == seats_num]
        except ValueError:
            # Ignore invalid seats filter value
            pass
    
    # Add cancellation eligibility flag
    now = datetime.now()
    for order in orders:
        # Ensure departure_time is a datetime object
        if isinstance(order['departure_time'], str):
            order['departure_time'] = datetime.strptime(order['departure_time'], '%Y-%m-%d %H:%M:%S')
        
        time_diff = order['departure_time'] - now
        order['can_cancel'] = (
            time_diff.total_seconds() >= 72 * 3600 and 
            order['order_status'] == 'Active'
        )
    
    return render_template('customer/my_orders.html', orders=orders)

@customer_bp.route('/cancel_order/<int:order_code>')
def cancel_order(order_code):
    if session.get('role') != 'customer':
        flash('Please log in as a customer to cancel orders.', 'warning')
        return redirect(url_for('auth.login'))
    
    email = session.get('user_id')
    
    # Verify order belongs to customer and check if cancellation is allowed
    order = query_db("""
        SELECT order_code, departure_time, order_status 
        FROM Order_Table 
        WHERE order_code = %s AND customer_email = %s
    """, (order_code, email), one=True)
    
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('customer.my_orders'))
    
    if order['order_status'] != 'Active':
        flash('Only active orders can be cancelled.', 'danger')
        return redirect(url_for('customer.my_orders'))
    
    # Check 72 hour rule
    if isinstance(order['departure_time'], str):
        departure_time = datetime.strptime(order['departure_time'], '%Y-%m-%d %H:%M:%S')
    else:
        departure_time = order['departure_time']
    
    time_diff = departure_time - datetime.now()
    if time_diff.total_seconds() < 72 * 3600:
        flash('Cannot cancel order less than 72 hours before departure.', 'danger')
        return redirect(url_for('customer.my_orders'))
    
    # Update order status to Customer Cancelled
    try:
        execute_db("""
            UPDATE Order_Table 
            SET order_status = 'Customer Cancelled'
            WHERE order_code = %s
        """, (order_code,))
        flash('Order cancelled successfully.', 'success')
    except Exception as e:
        flash(f'Error cancelling order: {str(e)}', 'danger')
    
    return redirect(url_for('customer.my_orders'))

@customer_bp.route('/api/order_details/<int:order_code>')
def api_order_details(order_code):
    if session.get('role') != 'customer':
        return jsonify({'error': 'Access denied'}), 403
    
    email = session.get('user_id')
    
    # Get order and flight details
    order = query_db("""
        SELECT 
            O.order_code,
            O.order_date,
            O.total_payment,
            O.order_status,
            O.departure_time,
            O.source_airport_id,
            O.dest_airport_id,
            A1.airport_name as source_airport,
            A2.airport_name as dest_airport,
            F.economy_price,
            F.business_price,
            F.flight_status,
            F.aircraft_id,
            AC.manufacturer,
            AC.is_large,
            (SELECT COUNT(*) FROM Order_Seats OS WHERE OS.order_code = O.order_code) as seats
        FROM Order_Table O
        JOIN Airport A1 ON O.source_airport_id = A1.airport_id
        JOIN Airport A2 ON O.dest_airport_id = A2.airport_id
        JOIN Flight F ON O.source_airport_id = F.source_airport_id 
            AND O.dest_airport_id = F.dest_airport_id 
            AND O.departure_time = F.departure_time
        LEFT JOIN Aircraft AC ON F.aircraft_id = AC.aircraft_id
        WHERE O.order_code = %s AND O.customer_email = %s
    """, (order_code, email), one=True)
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Get seat details
    seats = query_db("""
        SELECT aircraft_id, is_business, row_number, column_number
        FROM Order_Seats
        WHERE order_code = %s
        ORDER BY is_business DESC, row_number, column_number
    """, (order_code,))
    
    # Convert datetime objects to strings for JSON serialization
    if order.get('departure_time'):
        order['departure_time'] = order['departure_time'].strftime('%Y-%m-%d %H:%M:%S')
    if order.get('order_date'):
        order['order_date'] = order['order_date'].strftime('%Y-%m-%d %H:%M:%S')
    
    order['seats_details'] = seats
    
    return jsonify(order)
