from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import query_db

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/')
def index():
    return render_template('index.html')

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
            (SELECT COUNT(*) FROM Order_Seats OS WHERE OS.order_code = O.order_code) as seats
        FROM Order_Table O
        JOIN Airport A1 ON O.source_airport_id = A1.airport_id
        JOIN Airport A2 ON O.dest_airport_id = A2.airport_id
        WHERE O.customer_email = %s
    """
    params = [email]
    
    if status_filter:
        query += " AND O.order_status = %s"
        params.append(status_filter)
        
    query += " ORDER BY O.order_date DESC"
    
    orders = query_db(query, tuple(params))
    
    return render_template('my_orders.html', orders=orders)
