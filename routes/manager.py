from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify, Response
from services.reports_service import (
    get_occupancy_report,
    get_revenue_report,
    get_employee_hours_report,
    get_cancellation_report,
    get_plane_activity_report
)
from services.chart_service import (
    generate_occupancy_chart,
    generate_revenue_chart,
    generate_employee_hours_chart,
    generate_cancellation_chart,
    generate_plane_activity_chart,
    generate_filtered_revenue_chart
)
from services.employee_service import add_new_staff
from services.flight_service import (
    get_all_airports, get_all_aircrafts, get_all_pilots, get_all_attendants,
    create_flight, get_active_flights, cancel_flight, get_flight_details, update_flight_status, get_flights,
    get_crew_availability, get_aircraft_availability, get_flight_duration, update_all_flight_statuses
)
from db import query_db
from datetime import datetime

manager_bp = Blueprint('manager', __name__)

def validate_crew_count(crew_ids, aircraft_id, source_id, dest_id, departure_time):
    """
    Validates that the selected crew count matches the requirements.
    Returns (is_valid, message)
    """
    if not crew_ids:
        return False, "No crew members selected."
    
    # Get aircraft type
    aircraft = query_db("SELECT is_large FROM Aircraft WHERE aircraft_id = %s", (aircraft_id,), one=True)
    if not aircraft:
        return False, "Invalid aircraft selected."
    
    # Get flight duration to determine requirements
    duration = get_flight_duration(source_id, dest_id)
    
    # Determine requirements based on aircraft size
    if aircraft['is_large']:
        required_pilots = 3
        required_attendants = 6
    else:
        required_pilots = 2
        required_attendants = 3
    
    # Count selected pilots and attendants
    selected_pilots = []
    selected_attendants = []
    
    for crew_id in crew_ids:
        # Check if it's a pilot or attendant
        pilot_check = query_db("""
            SELECT id_number FROM Flight_Crew 
            WHERE id_number = %s AND is_pilot = 1
        """, (crew_id,), one=True)
        
        if pilot_check:
            selected_pilots.append(crew_id)
        else:
            attendant_check = query_db("""
                SELECT id_number FROM Flight_Crew 
                WHERE id_number = %s AND is_pilot = 0
            """, (crew_id,), one=True)
            if attendant_check:
                selected_attendants.append(crew_id)
    
    # Validate counts
    pilot_count = len(selected_pilots)
    attendant_count = len(selected_attendants)
    
    if pilot_count != required_pilots:
        return False, f"Invalid number of pilots. Required: {required_pilots}, Selected: {pilot_count}"
    
    if attendant_count != required_attendants:
        return False, f"Invalid number of attendants. Required: {required_attendants}, Selected: {attendant_count}"
    
    return True, "Crew count is valid"

@manager_bp.route('/manager')
def manager_dashboard():
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('manager/dashboard.html')

@manager_bp.route('/reports')
def reports():
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))

    # Get report data
    occupancy_data = get_occupancy_report()
    revenue_data = get_revenue_report()
    employee_hours_data = get_employee_hours_report()
    cancellation_data = get_cancellation_report()
    plane_activity_data = get_plane_activity_report()
    
    # Generate charts
    occupancy_chart = generate_occupancy_chart(occupancy_data) if occupancy_data else None
    revenue_chart = generate_revenue_chart(revenue_data) if revenue_data else None
    employee_hours_chart = generate_employee_hours_chart(employee_hours_data) if employee_hours_data else None
    cancellation_chart = generate_cancellation_chart(cancellation_data) if cancellation_data else None
    plane_activity_chart = generate_plane_activity_chart(plane_activity_data) if plane_activity_data else None

    return render_template('manager/reports.html', 
                           occupancy_report=occupancy_data,
                           occupancy_chart=occupancy_chart,
                           revenue_report=revenue_data,
                           revenue_chart=revenue_chart,
                           employee_hours_report=employee_hours_data,
                           employee_hours_chart=employee_hours_chart,
                           cancellation_report=cancellation_data,
                           cancellation_chart=cancellation_chart,
                           plane_activity_report=plane_activity_data,
                           plane_activity_chart=plane_activity_chart)


@manager_bp.route('/api/check_availability')
def check_availability():
    update_all_flight_statuses()
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401
        
    source_id = request.args.get('source_id')
    dest_id = request.args.get('dest_id')
    departure_time = request.args.get('departure_time')
    aircraft_id = request.args.get('aircraft_id')
    
    if not all([source_id, dest_id, departure_time]):
        return jsonify({'error': 'Missing parameters'}), 400
        
    try:
        result = get_crew_availability(source_id, dest_id, departure_time, aircraft_id)
        
        # Also get aircraft availability
        aircrafts = get_aircraft_availability(source_id, dest_id, departure_time)
        result['aircrafts'] = aircrafts
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@manager_bp.route('/add_staff', methods=['GET', 'POST'])
def add_staff():
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        # Extract form data
        id_number = request.form.get('id_number')
        first_name = request.form.get('first_name')
        middle_name = request.form.get('middle_name')
        last_name = request.form.get('last_name')
        city = request.form.get('city')
        street = request.form.get('street')
        house_number = request.form.get('house_number')
        phone = request.form.get('phone')
        start_work_date = request.form.get('start_work_date')
        role = request.form.get('role')
        trained_for_long_flights = 1 if request.form.get('trained_for_long_flights') else 0

        success, message = add_new_staff(
            id_number, first_name, middle_name, last_name, city, street, 
            house_number, phone, start_work_date, role, trained_for_long_flights
        )

        if success:
            flash(message, 'success')
            return redirect(url_for('manager.manager_dashboard'))
        else:
            flash(message, 'danger')
            return render_template('manager/add_staff.html')

    return render_template('manager/add_staff.html')



@manager_bp.route('/add_flight', methods=['GET', 'POST'])
def add_flight():
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        source_id = request.form.get('source_id')
        dest_id = request.form.get('dest_id')
        departure_time = request.form.get('departure_time')
        aircraft_id = request.form.get('aircraft_id')
        economy_price = request.form.get('economy_price')
        business_price = request.form.get('business_price')
        
        # Get list of selected crew members
        crew_ids = request.form.getlist('crew_ids')

        # Validate prices are not negative
        try:
            economy_price_float = float(economy_price) if economy_price else 0
            business_price_float = float(business_price) if business_price else 0
            if economy_price_float < 0 or business_price_float < 0:
                flash('Flight prices cannot be negative.', 'danger')
            elif source_id == dest_id:
                flash('Source and Destination airports cannot be the same.', 'danger')
            elif not crew_ids:
                flash('Please assign at least one crew member.', 'danger')
            else:
                # Validate departure time is not in the past
                if departure_time:
                    try:
                        departure_dt = datetime.strptime(departure_time, '%Y-%m-%dT%H:%M')
                        if departure_dt < datetime.now():
                            flash('Departure time cannot be in the past.', 'danger')
                        else:
                            # Validate crew count matches requirements
                            validation_result = validate_crew_count(crew_ids, aircraft_id, source_id, dest_id, departure_time)
                            if not validation_result[0]:
                                flash(validation_result[1], 'danger')
                            else:
                                success, message = create_flight(
                                    source_id, dest_id, departure_time, aircraft_id, 
                                    economy_price, business_price, crew_ids
                                )
                                
                                if success:
                                    flash(message, 'success')
                                    return redirect(url_for('manager.manager_dashboard'))
                                else:
                                    flash(message, 'danger')
                    except ValueError:
                        flash('Invalid departure time format.', 'danger')
                else:
                    flash('Departure time is required.', 'danger')
        except ValueError:
            flash('Invalid price format. Please enter valid numbers.', 'danger')

    # Fetch data for dropdowns
    airports = get_all_airports()
    aircrafts = get_all_aircrafts()
    pilots = get_all_pilots()
    attendants = get_all_attendants()
    
    # Pass current datetime for the min attribute in datetime-local input
    current_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M')

    return render_template('manager/add_flight.html', 
                           airports=airports, 
                           aircrafts=aircrafts, 
                           pilots=pilots, 
                           attendants=attendants,
                           current_datetime=current_datetime)

@manager_bp.route('/manage_flights')
def manage_flights():
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))
        
    status = request.args.get('status', '').strip()
    source_id = request.args.get('source_id')
    dest_id = request.args.get('dest_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # #region agent log
    import json; log_data = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "A", "location": "routes/manager.py:265", "message": "Status parameter received", "data": {"status_raw": request.args.get('status'), "status_processed": status, "all_args": dict(request.args)}, "timestamp": int(__import__('time').time() * 1000)}; open(r'c:\Users\inked\PycharmProjects\project\.cursor\debug.log', 'a', encoding='utf-8').write(json.dumps(log_data) + '\n')
    # #endregion

    flights = get_flights(status if status else None, source_id, dest_id, date_from, date_to)
    
    # Ensure flights is always a list (never None)
    if flights is None:
        flights = []
    
    # #region agent log
    log_data = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "routes/manager.py:272", "message": "Flights returned from get_flights", "data": {"flight_count": len(flights) if flights else 0, "flights_is_none": flights is None, "flights_type": type(flights).__name__, "first_flight_status": flights[0].get('flight_status') if flights and len(flights) > 0 else None}, "timestamp": int(__import__('time').time() * 1000)}; open(r'c:\Users\inked\PycharmProjects\project\.cursor\debug.log', 'a', encoding='utf-8').write(json.dumps(log_data) + '\n')
    # #endregion
    airports = get_all_airports()
    
    now = datetime.now()
    
    # Add a flag for cancellation eligibility (72 hours and not already cancelled or completed)
    # #region agent log
    log_data = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "routes/manager.py:285", "message": "Before processing flights loop", "data": {"flights_count": len(flights) if flights else 0}, "timestamp": int(__import__('time').time() * 1000)}; open(r'c:\Users\inked\PycharmProjects\project\.cursor\debug.log', 'a', encoding='utf-8').write(json.dumps(log_data) + '\n')
    # #endregion
    try:
        for f in flights:
            # #region agent log
            log_data = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "routes/manager.py:288", "message": "Processing flight", "data": {"flight_status": f.get('flight_status'), "departure_time_type": type(f.get('departure_time')).__name__, "departure_time_value": str(f.get('departure_time'))}, "timestamp": int(__import__('time').time() * 1000)}; open(r'c:\Users\inked\PycharmProjects\project\.cursor\debug.log', 'a', encoding='utf-8').write(json.dumps(log_data) + '\n')
            # #endregion
            # Ensure departure_time is a datetime object
            if isinstance(f['departure_time'], str):
                 f['departure_time'] = datetime.strptime(f['departure_time'], '%Y-%m-%d %H:%M:%S')
             
            time_diff = f['departure_time'] - now
            hours_until_flight = time_diff.total_seconds() / 3600
            
            # Can cancel only if:
            # - >= 72 hours before departure
            # - status is not 'Cancelled'
            # - status is not 'Completed'
            f['can_cancel'] = (
                hours_until_flight >= 72 
                and f.get('flight_status') != 'Cancelled' 
                and f.get('flight_status') != 'Completed'
            )
            
            # Store hours for better messaging
            f['hours_until_flight'] = hours_until_flight
            
            # Convert departure_time back to string for template rendering (url_for needs string)
            if isinstance(f['departure_time'], datetime):
                f['departure_time'] = f['departure_time'].strftime('%Y-%m-%d %H:%M:%S')
                # #region agent log
                log_data = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "routes/manager.py:315", "message": "Converted departure_time to string", "data": {"departure_time_after": f['departure_time'], "departure_time_type_after": type(f['departure_time']).__name__}, "timestamp": int(__import__('time').time() * 1000)}; open(r'c:\Users\inked\PycharmProjects\project\.cursor\debug.log', 'a', encoding='utf-8').write(json.dumps(log_data) + '\n')
                # #endregion
    except Exception as e:
        # #region agent log
        import traceback; log_data = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "routes/manager.py:310", "message": "Exception in flight processing", "data": {"error": str(e), "traceback": traceback.format_exc()}, "timestamp": int(__import__('time').time() * 1000)}; open(r'c:\Users\inked\PycharmProjects\project\.cursor\debug.log', 'a', encoding='utf-8').write(json.dumps(log_data) + '\n')
        # #endregion
        raise
    
    # #region agent log
    log_data = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "routes/manager.py:327", "message": "After processing flights, before render", "data": {"flights_count": len(flights) if flights else 0, "first_flight_can_cancel": flights[0].get('can_cancel') if flights and len(flights) > 0 else None, "first_flight_departure_time": str(flights[0].get('departure_time')) if flights and len(flights) > 0 else None, "first_flight_departure_time_type": type(flights[0].get('departure_time')).__name__ if flights and len(flights) > 0 else None, "all_flight_statuses": [f.get('flight_status') for f in flights] if flights else []}, "timestamp": int(__import__('time').time() * 1000)}; open(r'c:\Users\inked\PycharmProjects\project\.cursor\debug.log', 'a', encoding='utf-8').write(json.dumps(log_data) + '\n')
    # #endregion

    try:
        result = render_template('manager/manage_flights.html', flights=flights, airports=airports)
        # #region agent log
        log_data = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "routes/manager.py:332", "message": "Template rendered successfully", "data": {"response_length": len(result) if result else 0}, "timestamp": int(__import__('time').time() * 1000)}; open(r'c:\Users\inked\PycharmProjects\project\.cursor\debug.log', 'a', encoding='utf-8').write(json.dumps(log_data) + '\n')
        # #endregion
        return result
    except Exception as e:
        # #region agent log
        import traceback; log_data = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "E", "location": "routes/manager.py:337", "message": "Template rendering exception", "data": {"error": str(e), "traceback": traceback.format_exc()}, "timestamp": int(__import__('time').time() * 1000)}; open(r'c:\Users\inked\PycharmProjects\project\.cursor\debug.log', 'a', encoding='utf-8').write(json.dumps(log_data) + '\n')
        # #endregion
        raise

@manager_bp.route('/cancel_flight/<int:source_id>/<int:dest_id>/<path:departure_time>', methods=['POST'])
def cancel_flight_route(source_id, dest_id, departure_time):
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))

    # Decode URL-encoded departure_time (spaces are encoded as %20)
    from urllib.parse import unquote
    departure_time = unquote(departure_time)
    
    # Parse the datetime string properly
    try:
        # Try parsing with space separator first
        departure_time = datetime.strptime(departure_time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            # Try parsing with T separator
            departure_time = datetime.strptime(departure_time, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            flash('Invalid departure time format.', 'danger')
            return redirect(url_for('manager.manage_flights'))
    
    # Convert back to string format expected by the service
    departure_time_str = departure_time.strftime('%Y-%m-%d %H:%M:%S')
    
    success, message = cancel_flight(source_id, dest_id, departure_time_str)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
        
    return redirect(url_for('manager.manage_flights'))


@manager_bp.route('/api/flight_details/<int:source_id>/<int:dest_id>/<departure_time>')
def api_flight_details(source_id, dest_id, departure_time):
    update_all_flight_statuses()
    if session.get('role') != 'manager':
        return jsonify({'error': 'Access denied'}), 403
    
    flight = get_flight_details(source_id, dest_id, departure_time)
    
    if not flight:
        return jsonify({'error': 'Flight not found'}), 404
        
    # Convert datetime objects to strings for JSON serialization
    if flight.get('departure_time'):
        flight['departure_time'] = flight['departure_time'].strftime('%Y-%m-%d %H:%M:%S')
    if flight.get('purchase_date'):
        flight['purchase_date'] = flight['purchase_date'].strftime('%Y-%m-%d')
        
    return jsonify(flight)

@manager_bp.route('/update_flight_status', methods=['POST'])
def update_status():
    if session.get('role') != 'manager':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
        
    data = request.get_json()
    source_id = data.get('source_id')
    dest_id = data.get('dest_id')
    departure_time = data.get('departure_time')
    new_status = data.get('status')
    
    success, message = update_flight_status(source_id, dest_id, departure_time, new_status)
    
    return jsonify({'success': success, 'message': message})

