from flask import Flask, render_template, request, redirect, url_for, flash, session
from db import get_db, close_db, query_db, execute_db
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this for production

# Register the teardown context to close DB connection
app.teardown_appcontext(close_db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
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
                return redirect(url_for('manager_dashboard'))
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
                return redirect(url_for('index'))
            else:
                flash('Invalid Email or Password', 'danger')
                
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
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
            return redirect(url_for('register'))
            
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
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/manager')
def manager_dashboard():
    if session.get('role') != 'manager':
        flash('Access denied. Managers only.', 'danger')
        return redirect(url_for('login'))
    return render_template('manager_dashboard.html')

@app.route('/my_orders')
def my_orders():
    if session.get('role') != 'customer':
        flash('Please log in as a customer to view your orders.', 'warning')
        return redirect(url_for('login'))
    
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

if __name__ == '__main__':
    app.run(debug=True)
