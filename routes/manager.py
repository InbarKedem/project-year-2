from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from services.reports_service import (
    get_occupancy_report,
    get_revenue_report,
    get_employee_hours_report,
    get_cancellation_report,
    get_plane_activity_report
)
from services.employee_service import add_new_staff

manager_bp = Blueprint('manager', __name__)

@manager_bp.route('/manager')
def manager_dashboard():
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('manager_dashboard.html')

@manager_bp.route('/reports')
def reports():
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('reports.html', 
                           occupancy_report=get_occupancy_report(),
                           revenue_report=get_revenue_report(),
                           employee_hours_report=get_employee_hours_report(),
                           cancellation_report=get_cancellation_report(),
                           plane_activity_report=get_plane_activity_report())


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
            return render_template('add_staff.html')

    return render_template('add_staff.html')

