# FLYTAU Airline Management System

![FLYTAU Logo](static/images/logo.png)

### Final Project - Database Systems & Information Systems Engineering

**Group Number:** 30
**Submitted By:**

- **Name:** Inbar Kedem
- **Name:** Ohz Levi
- **Name:** Eylon Chodnik

---

## 🚀 Features

### Manager Portal

- **Dashboard:** View real-time statistics (revenue, active flights, etc.).
- **Flight Management:** Add new flights with automatic crew and aircraft availability checks.
- **Staff Management:** Manage pilots and flight attendants.
- **Reports:** Generate and view system reports.

### Customer Portal

- **Flight Booking:** Search and book flights.
- **Seat Selection:** Interactive seat map for choosing seats.
- **Order Tracking:** View and manage past and upcoming bookings.
- **Profile:** Manage personal information.

---

## 🌐 Deployment Details (Required)

The system is deployed and accessible at the following URL:
**[https://inbarkedem.pythonanywhere.com](https://inbarkedem.pythonanywhere.com)**

### 🔑 Login Credentials

Per the project requirements, here are the testing credentials for the two required user types:

#### Manager Accounts

| Username    | Password       |
| :---------- | :------------- |
| `111111111` | `Admin@2024`   |
| `222222222` | `Manager#2024` |

#### Customer Accounts

| Email           | Password        |
| :-------------- | :-------------- |
| `reg1@test.com` | `Customer@2024` |
| `reg2@test.com` | `User#2024`     |

---

## 📂 Project Structure

The project is built using **Flask (Python)** and **MySQL**.

- `main.py`: Application entry point.
- `db.py`: Database connection and configuration.
- `init_db.py`: Script to initialize and seed the database.
- `routes/`: Contains blueprints for different modules (Auth, Customer, Manager).
- `services/`: Business logic and database queries.
- `static/`: CSS files for styling.
- `templates/`: HTML templates (Jinja2).
- `sql/`: SQL scripts for schema creation and data seeding.

## ⚙️ How to Run Locally

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/InbarKedem/project-year-2.git
    cd project-year-2
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Database:**

    - Update `db.py` with your local MySQL credentials.
    - Run the initialization script to create tables and seed data:

    ```bash
    python init_db.py
    ```

5.  **Run the App:**
    ```bash
    python main.py
    ```
    The app will be available at `http://127.0.0.1:5000`.

---

## 📝 Features Implemented

- **Authentication:** Registration and Login for Customers and Managers.
- **Customer Interface:** Flight search, Ticket booking, Order history view.
- **Manager Interface:**
  - **Flight Management:** Add flights, Cancel flights (72h rule), View status.
  - **Staff Management:** Add Pilots and Flight Attendants.
  - **Reports:** Occupancy, Revenue, Employee Hours, Cancellations.
