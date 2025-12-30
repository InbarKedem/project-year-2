-- 1. Airports
INSERT INTO Airport (airport_id, airport_name) VALUES
(1, 'Ben Gurion (TLV)'),
(2, 'John F. Kennedy (JFK)'),
(3, 'Heathrow (LHR)'),
(4, 'Charles de Gaulle (CDG)');

-- 2. Routes
INSERT INTO Flight_Route (source_airport_id, dest_airport_id, flight_duration) VALUES
(1, 2, 660), -- TLV -> JFK (11h)
(2, 1, 660), -- JFK -> TLV
(1, 3, 300), -- TLV -> LHR (5h)
(3, 1, 300), -- LHR -> TLV
(1, 4, 270), -- TLV -> CDG (4.5h)
(4, 1, 270); -- CDG -> TLV

-- 3. Aircraft
-- Large: 1, 2, 6
-- Small: 3, 4, 5
INSERT INTO Aircraft (aircraft_id, manufacturer, purchase_date, is_large) VALUES
(1, 'Boeing', '2020-01-01', TRUE),
(2, 'Airbus', '2021-05-15', TRUE),
(3, 'Dassault', '2022-03-10', FALSE),
(4, 'Boeing', '2019-11-20', FALSE),
(5, 'Airbus', '2023-02-28', FALSE),
(6, 'Dassault', '2024-07-01', TRUE);

-- 4. Aircraft_Class & Seats
-- Plane 1 (Large): Business (2 rows, 2 cols), Economy (5 rows, 4 cols)
INSERT INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns) VALUES
(1, TRUE, 2, 2),
(1, FALSE, 5, 4);

-- Plane 3 (Small): Economy (5 rows, 4 cols)
INSERT INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns) VALUES
(3, FALSE, 5, 4);

-- Plane 2 (Large)
INSERT INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns) VALUES
(2, TRUE, 2, 2),
(2, FALSE, 5, 4);

-- Plane 4 (Small)
INSERT INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns) VALUES
(4, FALSE, 5, 4);

-- Plane 5 (Small)
INSERT INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns) VALUES
(5, FALSE, 5, 4);

-- Plane 6 (Large)
INSERT INTO Aircraft_Class (aircraft_id, is_business, num_rows, num_columns) VALUES
(6, TRUE, 2, 2),
(6, FALSE, 5, 4);

-- Generate Seats for Plane 1 (Large)
-- Business
INSERT INTO Seat (aircraft_id, is_business, `row_number`, `column_number`) VALUES
(1, TRUE, 1, 1), (1, TRUE, 1, 2),
(1, TRUE, 2, 1), (1, TRUE, 2, 2);
-- Economy
INSERT INTO Seat (aircraft_id, is_business, `row_number`, `column_number`) VALUES
(1, FALSE, 1, 1), (1, FALSE, 1, 2), (1, FALSE, 1, 3), (1, FALSE, 1, 4),
(1, FALSE, 2, 1), (1, FALSE, 2, 2), (1, FALSE, 2, 3), (1, FALSE, 2, 4),
(1, FALSE, 3, 1), (1, FALSE, 3, 2), (1, FALSE, 3, 3), (1, FALSE, 3, 4),
(1, FALSE, 4, 1), (1, FALSE, 4, 2), (1, FALSE, 4, 3), (1, FALSE, 4, 4),
(1, FALSE, 5, 1), (1, FALSE, 5, 2), (1, FALSE, 5, 3), (1, FALSE, 5, 4);

-- Generate Seats for Plane 3 (Small)
INSERT INTO Seat (aircraft_id, is_business, `row_number`, `column_number`) VALUES
(3, FALSE, 1, 1), (3, FALSE, 1, 2), (3, FALSE, 1, 3), (3, FALSE, 1, 4),
(3, FALSE, 2, 1), (3, FALSE, 2, 2), (3, FALSE, 2, 3), (3, FALSE, 2, 4),
(3, FALSE, 3, 1), (3, FALSE, 3, 2), (3, FALSE, 3, 3), (3, FALSE, 3, 4),
(3, FALSE, 4, 1), (3, FALSE, 4, 2), (3, FALSE, 4, 3), (3, FALSE, 4, 4),
(3, FALSE, 5, 1), (3, FALSE, 5, 2), (3, FALSE, 5, 3), (3, FALSE, 5, 4);

-- Plane 2 (Large)
INSERT INTO Seat (aircraft_id, is_business, `row_number`, `column_number`) VALUES
(2, TRUE, 1, 1), (2, TRUE, 1, 2), (2, TRUE, 2, 1), (2, TRUE, 2, 2);
INSERT INTO Seat (aircraft_id, is_business, `row_number`, `column_number`) VALUES
(2, FALSE, 1, 1), (2, FALSE, 1, 2), (2, FALSE, 1, 3), (2, FALSE, 1, 4),
(2, FALSE, 2, 1), (2, FALSE, 2, 2), (2, FALSE, 2, 3), (2, FALSE, 2, 4),
(2, FALSE, 3, 1), (2, FALSE, 3, 2), (2, FALSE, 3, 3), (2, FALSE, 3, 4),
(2, FALSE, 4, 1), (2, FALSE, 4, 2), (2, FALSE, 4, 3), (2, FALSE, 4, 4),
(2, FALSE, 5, 1), (2, FALSE, 5, 2), (2, FALSE, 5, 3), (2, FALSE, 5, 4);

-- Plane 4 (Small)
INSERT INTO Seat (aircraft_id, is_business, `row_number`, `column_number`) VALUES
(4, FALSE, 1, 1), (4, FALSE, 1, 2), (4, FALSE, 1, 3), (4, FALSE, 1, 4),
(4, FALSE, 2, 1), (4, FALSE, 2, 2), (4, FALSE, 2, 3), (4, FALSE, 2, 4),
(4, FALSE, 3, 1), (4, FALSE, 3, 2), (4, FALSE, 3, 3), (4, FALSE, 3, 4),
(4, FALSE, 4, 1), (4, FALSE, 4, 2), (4, FALSE, 4, 3), (4, FALSE, 4, 4),
(4, FALSE, 5, 1), (4, FALSE, 5, 2), (4, FALSE, 5, 3), (4, FALSE, 5, 4);


-- 5. Employees
-- Managers
INSERT INTO Employee (id_number, first_name, middle_name, last_name, city, street, house_number, phone, start_work_date) VALUES
('111111111', 'Moshe', NULL, 'Cohen', 'Tel Aviv', 'Rothschild', 10, '0501111111', '2020-01-01'),
('222222222', 'Sarah', 'Lee', 'Levi', 'Haifa', 'Herzl', 20, '0502222222', '2021-02-01');

INSERT INTO Manager (id_number, password) VALUES
('111111111', 'admin123'),
('222222222', 'admin456');

-- Pilots (10)
INSERT INTO Employee (id_number, first_name, middle_name, last_name, city, street, house_number, phone, start_work_date) VALUES
('300000001', 'Pilot', 'One', 'Smith', 'TA', 'St', 1, '0503000001', '2022-01-01'),
('300000002', 'Pilot', 'Two', 'Jones', 'TA', 'St', 2, '0503000002', '2022-01-01'),
('300000003', 'Pilot', 'Three', 'Brown', 'TA', 'St', 3, '0503000003', '2022-01-01'),
('300000004', 'Pilot', 'Four', 'Davis', 'TA', 'St', 4, '0503000004', '2022-01-01'),
('300000005', 'Pilot', 'Five', 'Miller', 'TA', 'St', 5, '0503000005', '2022-01-01'),
('300000006', 'Pilot', 'Six', 'Wilson', 'TA', 'St', 6, '0503000006', '2022-01-01'),
('300000007', 'Pilot', 'Seven', 'Moore', 'TA', 'St', 7, '0503000007', '2022-01-01'),
('300000008', 'Pilot', 'Eight', 'Taylor', 'TA', 'St', 8, '0503000008', '2022-01-01'),
('300000009', 'Pilot', 'Nine', 'Anderson', 'TA', 'St', 9, '0503000009', '2022-01-01'),
('300000010', 'Pilot', 'Ten', 'Thomas', 'TA', 'St', 10, '0503000010', '2022-01-01');

INSERT INTO Flight_Crew (id_number, trained_for_long_flights, is_pilot) VALUES
('300000001', TRUE, TRUE), ('300000002', TRUE, TRUE),
('300000003', TRUE, TRUE), ('300000004', TRUE, TRUE),
('300000005', FALSE, TRUE), ('300000006', FALSE, TRUE),
('300000007', FALSE, TRUE), ('300000008', FALSE, TRUE),
('300000009', FALSE, TRUE), ('300000010', FALSE, TRUE);

-- Attendants (20)
INSERT INTO Employee (id_number, first_name, middle_name, last_name, city, street, house_number, phone, start_work_date) VALUES
('400000001', 'Att', 'One', 'A', 'TA', 'St', 1, '0504000001', '2023-01-01'),
('400000002', 'Att', 'Two', 'B', 'TA', 'St', 2, '0504000002', '2023-01-01'),
('400000003', 'Att', 'Three', 'C', 'TA', 'St', 3, '0504000003', '2023-01-01'),
('400000004', 'Att', 'Four', 'D', 'TA', 'St', 4, '0504000004', '2023-01-01'),
('400000005', 'Att', 'Five', 'E', 'TA', 'St', 5, '0504000005', '2023-01-01'),
('400000006', 'Att', 'Six', 'F', 'TA', 'St', 6, '0504000006', '2023-01-01'),
('400000007', 'Att', 'Seven', 'G', 'TA', 'St', 7, '0504000007', '2023-01-01'),
('400000008', 'Att', 'Eight', 'H', 'TA', 'St', 8, '0504000008', '2023-01-01'),
('400000009', 'Att', 'Nine', 'I', 'TA', 'St', 9, '0504000009', '2023-01-01'),
('400000010', 'Att', 'Ten', 'J', 'TA', 'St', 10, '0504000010', '2023-01-01');

INSERT INTO Flight_Crew (id_number, trained_for_long_flights, is_pilot) VALUES
('400000001', TRUE, FALSE), ('400000002', TRUE, FALSE),
('400000003', TRUE, FALSE), ('400000004', TRUE, FALSE),
('400000005', TRUE, FALSE), ('400000006', TRUE, FALSE),
('400000007', FALSE, FALSE), ('400000008', FALSE, FALSE),
('400000009', FALSE, FALSE), ('400000010', FALSE, FALSE);


-- 6. Users
INSERT INTO User (email, first_name, middle_name, last_name) VALUES
('reg1@test.com', 'Reg', 'I', 'User'),
('reg2@test.com', 'Reg', 'II', 'User'),
('guest1@test.com', 'Guest', 'I', 'User'),
('guest2@test.com', 'Guest', 'II', 'User');

INSERT INTO Registered_Customer (email, passport_number, birth_date, registration_date, password) VALUES
('reg1@test.com', 'P12345678', '1990-01-01', '2025-01-01', 'pass1'),
('reg2@test.com', 'P87654321', '1995-05-05', '2025-02-01', 'pass2');

-- Phone numbers for all users
INSERT INTO Phone (email, phone_number) VALUES
('reg1@test.com', '0501234567'),
('reg2@test.com', '0509876543'),
('guest1@test.com', '0501111111'),
('guest2@test.com', '0502222222');

-- 7. Flights
-- Flight 1: TLV->JFK (Long), Plane 1 (Large), 2026-01-01 08:00
INSERT INTO Flight (source_airport_id, dest_airport_id, departure_time, aircraft_id, flight_status, economy_price, business_price) VALUES
(1, 2, '2026-01-01 08:00:00', 1, 'Active', 800.00, 1500.00);

-- Flight 2: TLV->LHR (Short), Plane 3 (Small), 2026-01-02 10:00
INSERT INTO Flight (source_airport_id, dest_airport_id, departure_time, aircraft_id, flight_status, economy_price, business_price) VALUES
(1, 3, '2026-01-02 10:00:00', 3, 'Active', 400.00, 900.00);

-- Flight 3: JFK->TLV (Long), Plane 2 (Large), 2026-01-03 12:00
INSERT INTO Flight (source_airport_id, dest_airport_id, departure_time, aircraft_id, flight_status, economy_price, business_price) VALUES
(2, 1, '2026-01-03 12:00:00', 2, 'Active', 850.00, 1600.00);

-- Flight 4: LHR->TLV (Short), Plane 4 (Small), 2026-01-04 14:00
INSERT INTO Flight (source_airport_id, dest_airport_id, departure_time, aircraft_id, flight_status, economy_price, business_price) VALUES
(3, 1, '2026-01-04 14:00:00', 4, 'Active', 450.00, 950.00);

-- 8. Crew Assignments
INSERT INTO Employee_Flight_Assignment (employee_id, source_airport_id, dest_airport_id, departure_time) VALUES
('300000001', 1, 2, '2026-01-01 08:00:00'),
('300000002', 1, 2, '2026-01-01 08:00:00'),
('300000003', 1, 2, '2026-01-01 08:00:00'),
('400000001', 1, 2, '2026-01-01 08:00:00'),
('400000002', 1, 2, '2026-01-01 08:00:00'),
('400000003', 1, 2, '2026-01-01 08:00:00'),
('400000004', 1, 2, '2026-01-01 08:00:00'),
('400000005', 1, 2, '2026-01-01 08:00:00'),
('400000006', 1, 2, '2026-01-01 08:00:00');

-- 9. Orders
-- Order 1: Reg1, Flight 1, 1 Seat (Business)
INSERT INTO Order_Table (order_code, order_date, total_payment, order_status, customer_email, source_airport_id, dest_airport_id, departure_time) VALUES
(1, '2025-12-01', 1500.00, 'Active', 'reg1@test.com', 1, 2, '2026-01-01 08:00:00');

INSERT INTO Order_Seats (order_code, aircraft_id, is_business, `row_number`, `column_number`, passenger_name) VALUES
(1, 1, TRUE, 1, 1, NULL);

-- Order 2: Reg2, Flight 2, 1 Seat (Economy)
INSERT INTO Order_Table (order_code, order_date, total_payment, order_status, customer_email, source_airport_id, dest_airport_id, departure_time) VALUES
(2, '2025-12-02', 500.00, 'Active', 'reg2@test.com', 1, 3, '2026-01-02 10:00:00');

INSERT INTO Order_Seats (order_code, aircraft_id, is_business, `row_number`, `column_number`, passenger_name) VALUES
(2, 3, FALSE, 1, 1, NULL);

-- Order 3: Guest1, Flight 1, 1 Seat (Economy)
INSERT INTO Order_Table (order_code, order_date, total_payment, order_status, customer_email, source_airport_id, dest_airport_id, departure_time) VALUES
(3, '2025-12-03', 800.00, 'Active', 'guest1@test.com', 1, 2, '2026-01-01 08:00:00');

INSERT INTO Order_Seats (order_code, aircraft_id, is_business, `row_number`, `column_number`, passenger_name) VALUES
(3, 1, FALSE, 1, 1, NULL);

-- Order 4: Guest2, Flight 3, 1 Seat (Business)
INSERT INTO Order_Table (order_code, order_date, total_payment, order_status, customer_email, source_airport_id, dest_airport_id, departure_time) VALUES
(4, '2025-12-04', 1600.00, 'Active', 'guest2@test.com', 2, 1, '2026-01-03 12:00:00');

INSERT INTO Order_Seats (order_code, aircraft_id, is_business, `row_number`, `column_number`, passenger_name) VALUES
(4, 2, TRUE, 1, 1, NULL);