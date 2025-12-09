-- Create Database
DROP DATABASE IF EXISTS flytau;
CREATE DATABASE IF NOT EXISTS flytau CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE flytau;

-- 1. Infrastructure & Planes

CREATE TABLE Airport (
    airport_id INT PRIMARY KEY,
    airport_name VARCHAR(100) NOT NULL
);

CREATE TABLE Flight_Route (
    source_airport_id INT NOT NULL,
    dest_airport_id INT NOT NULL,
    flight_duration INT NOT NULL, -- in minutes
    PRIMARY KEY (source_airport_id, dest_airport_id),
    FOREIGN KEY (source_airport_id) REFERENCES Airport(airport_id),
    FOREIGN KEY (dest_airport_id) REFERENCES Airport(airport_id)
);

CREATE TABLE Aircraft (
    aircraft_id INT PRIMARY KEY,
    manufacturer VARCHAR(100),
    purchase_date DATE,
    is_large BOOLEAN
);

CREATE TABLE Aircraft_Class (
    aircraft_id INT NOT NULL,
    is_business BOOLEAN NOT NULL,
    num_rows INT NOT NULL,
    num_columns INT NOT NULL,
    PRIMARY KEY (aircraft_id, is_business),
    FOREIGN KEY (aircraft_id) REFERENCES Aircraft(aircraft_id)
);

CREATE TABLE Seat (
    aircraft_id INT NOT NULL,
    is_business BOOLEAN NOT NULL,
    `row_number` INT NOT NULL,
    `column_number` INT NOT NULL,
    PRIMARY KEY (aircraft_id, is_business, `row_number`, `column_number`),
    FOREIGN KEY (aircraft_id, is_business)
        REFERENCES Aircraft_Class(aircraft_id, is_business)
);

-- 2. Employees

CREATE TABLE Employee (
    id_number CHAR(9) PRIMARY KEY,
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    city VARCHAR(50),
    street VARCHAR(50),
    house_number INT,
    phone VARCHAR(20),
    start_work_date DATE
);

CREATE TABLE Flight_Crew (
    id_number CHAR(9) PRIMARY KEY,
    trained_for_long_flights BOOLEAN,
    is_pilot BOOLEAN,
    FOREIGN KEY (id_number) REFERENCES Employee(id_number)
);

CREATE TABLE Manager (
    id_number CHAR(9) PRIMARY KEY,
    password VARCHAR(100) NOT NULL,
    FOREIGN KEY (id_number) REFERENCES Employee(id_number)
);

-- 3. Flight Operations

CREATE TABLE Flight (
    source_airport_id INT NOT NULL,
    dest_airport_id INT NOT NULL,
    departure_time DATETIME NOT NULL,
    flight_status VARCHAR(50), -- Active, Full, Completed, Cancelled
    aircraft_id INT,
    PRIMARY KEY (source_airport_id, dest_airport_id, departure_time),
    FOREIGN KEY (source_airport_id) REFERENCES Airport(airport_id),
    FOREIGN KEY (dest_airport_id) REFERENCES Airport(airport_id),
    FOREIGN KEY (aircraft_id) REFERENCES Aircraft(aircraft_id)
);

CREATE TABLE Employee_Flight_Assignment (
    employee_id CHAR(9) NOT NULL,
    source_airport_id INT NOT NULL,
    dest_airport_id INT NOT NULL,
    departure_time DATETIME NOT NULL,
    PRIMARY KEY (employee_id, source_airport_id, dest_airport_id, departure_time),
    FOREIGN KEY (employee_id) REFERENCES Flight_Crew(id_number), -- Changed to Flight_Crew for strictness
    FOREIGN KEY (source_airport_id, dest_airport_id, departure_time)
        REFERENCES Flight(source_airport_id, dest_airport_id, departure_time)
);

-- 4. Customers & Orders

CREATE TABLE User (
    email VARCHAR(100) PRIMARY KEY,
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50)
);

-- Note: System_Admin table removed as it conflicts with Manager (Employee) and requirements.

CREATE TABLE Phone (
    email VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    PRIMARY KEY (email, phone_number),
    FOREIGN KEY (email) REFERENCES User(email)
);

CREATE TABLE Registered_Customer (
    email VARCHAR(100) PRIMARY KEY,
    passport_number VARCHAR(20),
    birth_date DATE,
    registration_date DATE,
    password VARCHAR(100),
    FOREIGN KEY (email) REFERENCES User(email)
);

CREATE TABLE Order_Table (
    order_code INT PRIMARY KEY, -- Changed to INT as per user schema, though VARCHAR is often better for codes
    order_date DATETIME, -- Changed to DATETIME to capture exact time of order
    total_payment DECIMAL(10,2),
    order_status VARCHAR(50),
    customer_email VARCHAR(100),
    source_airport_id INT,
    dest_airport_id INT,
    departure_time DATETIME, -- Merged Date/Time to match Flight PK
    FOREIGN KEY (customer_email) REFERENCES User(email), -- Changed to User to allow Guests
    FOREIGN KEY (source_airport_id, dest_airport_id, departure_time) 
        REFERENCES Flight(source_airport_id, dest_airport_id, departure_time)
);

CREATE TABLE Order_Seats (
    order_code INT NOT NULL,
    aircraft_id INT NOT NULL,
    is_business BOOLEAN NOT NULL,
    `row_number` INT NOT NULL,
    `column_number` INT NOT NULL,
    PRIMARY KEY (order_code, aircraft_id, is_business, `row_number`, `column_number`),
    FOREIGN KEY (order_code) REFERENCES Order_Table(order_code),
    FOREIGN KEY (aircraft_id, is_business, `row_number`, `column_number`)
        REFERENCES Seat(aircraft_id, is_business, `row_number`, `column_number`)
);
