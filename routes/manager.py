from flask import Blueprint, render_template, redirect, url_for, flash, session
from services.reports_service import (
    get_occupancy_report,
    get_revenue_report,
    get_employee_hours_report,
    get_cancellation_report,
    get_plane_activity_report
)

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
