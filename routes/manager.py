from flask import Blueprint, render_template, redirect, url_for, flash, session, request, jsonify
from services.reports_service import (
    get_occupancy_report,
    get_revenue_report,
    get_employee_hours_report,
    get_cancellation_report,
    get_plane_activity_report
)
from services.employee_service import add_new_staff
from services.flight_service import (
    get_all_airports, get_all_aircrafts, get_all_pilots, get_all_attendants,
    create_flight, get_active_flights, cancel_flight, get_flight_details, update_flight_status, get_flights,
    get_crew_availability, get_aircraft_availability
)
from datetime import datetime

manager_bp = Blueprint('manager', __name__)

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

    return render_template('manager/reports.html', 
                           occupancy_report=get_occupancy_report(),
                           revenue_report=get_revenue_report(),
                           employee_hours_report=get_employee_hours_report(),
                           cancellation_report=get_cancellation_report(),
                           plane_activity_report=get_plane_activity_report())


@manager_bp.route('/api/check_availability')
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

        if source_id == dest_id:
            flash('Source and Destination airports cannot be the same.', 'danger')
        elif not crew_ids:
            flash('Please assign at least one crew member.', 'danger')
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

    # Fetch data for dropdowns
    airports = get_all_airports()
    aircrafts = get_all_aircrafts()
    pilots = get_all_pilots()
    attendants = get_all_attendants()

    return render_template('manager/add_flight.html', 
                           airports=airports, 
                           aircrafts=aircrafts, 
                           pilots=pilots, 
                           attendants=attendants)

@manager_bp.route('/manage_flights')
def manage_flights():
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))
        
    status = request.args.get('status')
    source_id = request.args.get('source_id')
    dest_id = request.args.get('dest_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    flights = get_flights(status, source_id, dest_id, date_from, date_to)
    airports = get_all_airports()
    
    now = datetime.now()
    
    # Add a flag for cancellation eligibility (72 hours)
    for f in flights:
        # Ensure departure_time is a datetime object
        if isinstance(f['departure_time'], str):
             f['departure_time'] = datetime.strptime(f['departure_time'], '%Y-%m-%d %H:%M:%S')
             
        time_diff = f['departure_time'] - now
        f['can_cancel'] = time_diff.total_seconds() >= 72 * 3600

    return render_template('manager/manage_flights.html', flights=flights, airports=airports)

@manager_bp.route('/cancel_flight/<int:source_id>/<int:dest_id>/<string:departure_time>')
def cancel_flight_route(source_id, dest_id, departure_time):
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))

    success, message = cancel_flight(source_id, dest_id, departure_time)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
        
    return redirect(url_for('manager.manage_flights'))


@manager_bp.route('/api/flight_details/<int:source_id>/<int:dest_id>/<departure_time>')
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

