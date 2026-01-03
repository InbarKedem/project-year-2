from flask import render_template, request, redirect, url_for, flash, session
from db import query_db, execute_db
from datetime import datetime
from routes.customer import customer_bp

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
            params.append(int(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            query += " AND O.total_payment <= %s"
            params.append(int(max_price))
        except ValueError:
            pass
    
    # Default ordering: newest orders first
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
            
            # Add to total spending:
            # - Active orders: full payment
            # - Client Cancellation: 5% cancellation fee (stored in total_payment)
            # - System Cancellation: 0 (full refund)
            if row['order_status'] == 'Client Cancellation':
                # Client cancelled orders have the 5% fee stored in total_payment
                total_spending += row['total_payment']
            elif row['order_status'] not in ['System Cancellation', 'Client Cancellation']:
                # Active, Completed orders - full payment
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
        
    if order['order_status'] in ['System Cancellation', 'Client Cancellation']:
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
    total_payment = int(order['total_payment'])
    fee = round(total_payment * 0.05)
    refund_amount = total_payment - fee
    
    try:
        execute_db("UPDATE Order_Table SET order_status = 'Client Cancellation', total_payment = %s WHERE order_code = %s", (fee, order_code))
        
        # Update flight status after cancellation (Fully Booked flights may become Active again)
        from services.flight_service import update_all_flight_statuses
        update_all_flight_statuses()
        
        flash(f'Order cancelled successfully. A 5% cancellation fee (${fee}) was deducted. Refund amount: ${refund_amount}', 'success')
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

