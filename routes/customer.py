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
    
    try:
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
        
        # Build response dict manually to handle all data types properly
        order_dict = {
            'order_code': int(order['order_code']) if order['order_code'] else None,
            'order_date': order['order_date'].strftime('%Y-%m-%d %H:%M:%S') if order.get('order_date') else None,
            'total_payment': float(order['total_payment']) if order['total_payment'] else 0.0,
            'order_status': str(order['order_status']) if order['order_status'] else '',
            'departure_time': order['departure_time'].strftime('%Y-%m-%d %H:%M:%S') if order.get('departure_time') else None,
            'source_airport_id': int(order['source_airport_id']) if order['source_airport_id'] else None,
            'dest_airport_id': int(order['dest_airport_id']) if order['dest_airport_id'] else None,
            'source_airport': str(order['source_airport']) if order['source_airport'] else '',
            'dest_airport': str(order['dest_airport']) if order['dest_airport'] else '',
            'economy_price': float(order['economy_price']) if order['economy_price'] else 0.0,
            'business_price': float(order['business_price']) if order['business_price'] else 0.0,
            'flight_status': str(order['flight_status']) if order['flight_status'] else '',
            'aircraft_id': int(order['aircraft_id']) if order['aircraft_id'] else None,
            'manufacturer': str(order['manufacturer']) if order.get('manufacturer') else None,
            'is_large': bool(order['is_large']) if order.get('is_large') is not None else False,
            'seats': int(order['seats']) if order['seats'] else 0
        }
        
        # Convert seats to list of dicts with proper type handling
        seats_list = []
        for seat in seats:
            seats_list.append({
                'aircraft_id': int(seat['aircraft_id']) if seat['aircraft_id'] else None,
                'is_business': bool(seat['is_business']) if seat.get('is_business') is not None else False,
                'row_number': int(seat['row_number']) if seat['row_number'] else 0,
                'column_number': int(seat['column_number']) if seat['column_number'] else 0
            })
        
        order_dict['seats_details'] = seats_list
        
        return jsonify(order_dict)
    except Exception as e:
        # Log the error for debugging with more details
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in api_order_details: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500
