from flask import render_template, request, redirect, url_for, flash, session
from db import query_db, execute_db
import random
from datetime import datetime
from routes.customer import customer_bp
from services.flight_service import update_flight_statuses

@customer_bp.route('/book_flight', methods=['GET', 'POST'])
@update_flight_statuses
def book_flight():
    if 'user_id' in session and session.get('role') == 'manager':
        flash('Managers cannot book flights. Please log in as a customer to make a booking.', 'warning')
        return redirect(url_for('manager.manager_dashboard'))

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
        
        # Validate required fields
        if not first_name or not first_name.strip():
            flash('First name is required.', 'danger')
            return redirect(request.url)
        
        if not last_name or not last_name.strip():
            flash('Last name is required.', 'danger')
            return redirect(request.url)
        
        if not phone or not phone.strip():
            flash('Phone number is required.', 'danger')
            return redirect(request.url)
        
        # Multiple seats
        seat_rows = request.form.getlist('seat_row')
        seat_cols = request.form.getlist('seat_col')
        seat_classes = request.form.getlist('seat_class')
        
        # If user is logged in as customer, use their email
        is_logged_in = 'user_id' in session and session.get('role') == 'customer'
        if is_logged_in:
            email = session['user_id']
        
        # 1. Ensure User Exists (or create dummy user for non-registered)
        user_check = query_db("SELECT email FROM User WHERE email = %s", (email,))
        if not user_check:
            # Create new user
            execute_db("INSERT INTO User (email, first_name, last_name) VALUES (%s, %s, %s)", 
                     (email, first_name, last_name))
            execute_db("INSERT INTO Phone (email, phone_number) VALUES (%s, %s)", (email, phone))
        else:
            # User exists - update their information if logged in
            if is_logged_in:
                # Update User table with new first_name and last_name
                execute_db("UPDATE User SET first_name=%s, last_name=%s WHERE email=%s", 
                         (first_name, last_name, email))
                
                # Handle phone number - check if it already exists for this user
                existing_phone = query_db("SELECT phone_number FROM Phone WHERE email=%s AND phone_number=%s", 
                                         (email, phone), one=True)
                
                if not existing_phone:
                    # Phone number doesn't exist, add it
                    # Since schema allows multiple phone numbers, we'll insert the new one
                    try:
                        execute_db("INSERT INTO Phone (email, phone_number) VALUES (%s, %s)", (email, phone))
                    except Exception:
                        # If insert fails (e.g., duplicate), that's okay - phone already exists
                        pass
            
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
                
                execute_db("""
                    INSERT INTO Order_Seats (order_code, aircraft_id, is_business, `row_number`, `column_number`)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_code, aircraft_id, is_business, row, col))
            
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
            
    # Get user details if logged in (including all phone numbers)
    user_details = None
    if 'user_id' in session and session.get('role') == 'customer':
        # Get user basic info
        user_info = query_db("""
            SELECT U.email, U.first_name, U.last_name 
            FROM User U 
            WHERE U.email = %s
        """, (session['user_id'],), one=True)
        
        # Get all phone numbers for this user
        phone_numbers = query_db("""
            SELECT phone_number 
            FROM Phone 
            WHERE email = %s
            ORDER BY phone_number
        """, (session['user_id'],))
        
        if user_info:
            user_details = user_info
            user_details['phone_numbers'] = [p['phone_number'] for p in phone_numbers] if phone_numbers else []
    
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

