from db import execute_db, query_db

def add_new_staff(id_number, first_name, middle_name, last_name, city, street, house_number, phone, start_work_date, role, trained_for_long_flights):
    try:
        # Check if employee already exists
        existing = query_db('SELECT id_number FROM Employee WHERE id_number = %s', (id_number,), one=True)
        if existing:
            return False, 'Employee with this ID already exists.'

        is_pilot = 1 if role == 'pilot' else 0
        
        # Insert into Employee table
        execute_db('''
            INSERT INTO Employee (id_number, first_name, middle_name, last_name, city, street, house_number, phone, start_work_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (id_number, first_name, middle_name, last_name, city, street, house_number, phone, start_work_date))

        # Insert into Flight_Crew table
        execute_db('''
            INSERT INTO Flight_Crew (id_number, trained_for_long_flights, is_pilot)
            VALUES (%s, %s, %s)
        ''', (id_number, trained_for_long_flights, is_pilot))

        return True, 'Staff member added successfully!'

    except Exception as e:
        return False, f'Error adding staff member: {str(e)}'
