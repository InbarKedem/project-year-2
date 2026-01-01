from flask import render_template, redirect, url_for, flash, session
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
    generate_plane_activity_chart
)
from routes.manager import manager_bp

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

