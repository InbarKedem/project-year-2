from flask import render_template, redirect, url_for, flash, session, request, jsonify
from services.flight_service import (
    get_all_airports, get_all_aircrafts, get_all_pilots, get_all_attendants,
    create_flight, cancel_flight, get_flight_details, update_flight_status, get_flights,
    get_crew_availability, get_aircraft_availability, update_flight_statuses, add_aircraft
)
from routes.manager import manager_bp
from routes.manager.validators import validate_crew_count
from datetime import datetime
from urllib.parse import unquote

@manager_bp.route('/api/check_availability')
@update_flight_statuses
def check_availability():
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

    flights = get_flights(status if status else None, source_id, dest_id, date_from, date_to)
    
    # Ensure flights is always a list (never None)
    if flights is None:
        flights = []
    airports = get_all_airports()
    
    now = datetime.now()
    
    # Add a flag for cancellation eligibility (72 hours and not already cancelled or completed)
    try:
        for f in flights:
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
    except Exception as e:
        raise
    
    try:
        result = render_template('manager/manage_flights.html', flights=flights, airports=airports)
        return result
    except Exception as e:
        raise

@manager_bp.route('/cancel_flight/<int:source_id>/<int:dest_id>/<path:departure_time>', methods=['POST'])
def cancel_flight_route(source_id, dest_id, departure_time):
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))

    # Decode URL-encoded departure_time (spaces are encoded as %20)
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
@update_flight_statuses
def api_flight_details(source_id, dest_id, departure_time):
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

@manager_bp.route('/add_aircraft', methods=['GET', 'POST'])
def add_aircraft_route():
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        aircraft_id = request.form.get('aircraft_id')
        manufacturer = request.form.get('manufacturer')
        purchase_date = request.form.get('purchase_date')
        is_large = 1 if request.form.get('is_large') else 0
        has_business = request.form.get('has_business')
        
        # Economy config (always required)
        economy_rows = request.form.get('economy_rows')
        economy_columns = request.form.get('economy_columns')
        
        # Business config (conditional)
        business_config = None
        if has_business:
            business_rows = request.form.get('business_rows')
            business_columns = request.form.get('business_columns')
            if business_rows and business_columns:
                business_config = {
                    'num_rows': int(business_rows),
                    'num_columns': int(business_columns)
                }
        
        # Validate required fields
        if not all([aircraft_id, manufacturer, purchase_date, economy_rows, economy_columns]):
            flash('Please fill in all required fields.', 'danger')
        else:
            try:
                economy_config = {
                    'num_rows': int(economy_rows),
                    'num_columns': int(economy_columns)
                }
                
                success, message = add_aircraft(
                    int(aircraft_id),
                    manufacturer,
                    purchase_date,
                    is_large,
                    business_config,
                    economy_config
                )
                
                if success:
                    flash(message, 'success')
                    return redirect(url_for('manager.manager_dashboard'))
                else:
                    flash(message, 'danger')
            except ValueError:
                flash('Invalid number format for rows or columns.', 'danger')
            except Exception as e:
                flash(f'Error: {str(e)}', 'danger')
    
    return render_template('manager/add_aircraft.html')

