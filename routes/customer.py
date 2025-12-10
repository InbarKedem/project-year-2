from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from db import query_db, execute_db
from datetime import datetime

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def index():
    return render_template('customer/index.html')

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
    
    if seats_filter:
        # This will be handled with HAVING since seats is calculated
        pass
    
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
    
    # Apply seats filter after query if needed
    if seats_filter:
        orders = [order for order in orders if order['seats'] == int(seats_filter)]
    
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
        SELECT is_business, row_number, column_number
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
