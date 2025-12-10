from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from db import query_db, execute_db
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form.get('user_type')
        
        if user_type == 'manager':
            id_number = request.form.get('id_number')
            password = request.form.get('password')
            
            user = query_db('SELECT * FROM Manager WHERE id_number = %s AND password = %s', (id_number, password), one=True)
            if user:
                # Fetch employee details for the name
                emp = query_db('SELECT * FROM Employee WHERE id_number = %s', (id_number,), one=True)
                session['user_id'] = id_number
                session['role'] = 'manager'
                session['name'] = f"{emp['first_name']} {emp['last_name']}"
                flash('Logged in successfully as Manager!', 'success')
                return redirect(url_for('manager.manager_dashboard'))
            else:
                flash('Invalid Manager ID or Password', 'danger')
                
        elif user_type == 'customer':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = query_db('SELECT * FROM Registered_Customer WHERE email = %s AND password = %s', (email, password), one=True)
            if user:
                # Fetch user details for the name
                u = query_db('SELECT * FROM User WHERE email = %s', (email,), one=True)
                session['user_id'] = email
                session['role'] = 'customer'
                session['name'] = f"{u['first_name']} {u['last_name']}"
                flash('Logged in successfully!', 'success')
                return redirect(url_for('customer.index'))
            else:
                flash('Invalid Email or Password', 'danger')
                
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        middle_name = request.form.get('middle_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        passport = request.form.get('passport')
        dob = request.form.get('dob')
        password = request.form.get('password')
        
        # Check if email exists
        if query_db('SELECT email FROM User WHERE email = %s', (email,), one=True):
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
            
        try:
            # Insert into User
            execute_db('INSERT INTO User (email, first_name, middle_name, last_name) VALUES (%s, %s, %s, %s)',
                       (email, first_name, middle_name, last_name))
            
            # Insert into Phone
            if phone:
                execute_db('INSERT INTO Phone (email, phone_number) VALUES (%s, %s)', (email, phone))
                
            # Insert into Registered_Customer
            execute_db('INSERT INTO Registered_Customer (email, passport_number, birth_date, registration_date, password) VALUES (%s, %s, %s, %s, %s)',
                       (email, passport, dob, datetime.date.today(), password))
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('customer.index'))
