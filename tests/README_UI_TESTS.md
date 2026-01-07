# UI Browser Automation Tests

This directory contains browser automation tests using Playwright to verify UI fixes and functionality.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
python -m playwright install chromium
```

## Running Tests

### Run all UI tests:
```bash
pytest tests/test_ui_fixes.py tests/test_ui_fixes_additional.py -v
```

### Run specific test file:
```bash
pytest tests/test_ui_fixes.py -v
pytest tests/test_ui_fixes_additional.py -v
```

### Run specific test:
```bash
pytest tests/test_ui_fixes.py::test_track_order_link_visible_when_logged_out -v
```

### Run with browser visible (headed mode):
```bash
pytest tests/test_ui_fixes.py --headed -v
```

### Run with slow motion (for debugging):
```bash
pytest tests/test_ui_fixes.py --slowmo=1000 -v
```

## Test Coverage

The UI tests verify the following fixes (40 total tests):

### 1. Track Order Link Visibility (4 tests)
   - Link is visible when logged out
   - Link is visible when logged in
   - Link navigates correctly
   - Link works when logged in

### 2. Flight Duration Formatting (6 tests)
   - Integer durations display as "2 hours" not "2.0 hours"
   - Decimal durations display correctly as "1.5 hours"
   - Exact hours (1, 2, etc.) display as integers
   - Half-hours display with decimals

### 3. Aircraft Selection on Purchase Date (3 tests)
   - Aircraft can be selected for flights on the same date they were purchased
   - Aircraft purchased yesterday is available today
   - Aircraft purchased tomorrow is not available today

### 4. Aircraft Class Business Rules (8 tests)
   - Large aircraft auto-checks business class
   - Small aircraft cannot have business class
   - Form validation enforces rules
   - Toggle behavior between large/small
   - Business config required fields
   - Full add aircraft flows

### 5. Order Status Management (6 tests)
   - "Client Cancellation" status displayed correctly
   - "System Cancellation" status displayed correctly
   - "Confirmed" status removed
   - Completed orders cannot be cancelled
   - Active orders can be cancelled
   - Order filtering by status

### 6. Flight Status Updates (2 tests)
   - Past flights show "Completed" status
   - Future flights show "Active" status
   - Status badges display correctly

### 7. Track Order Page (4 tests)
   - Page accessible without login
   - Correct status badges (no "Confirmed")
   - Form submission works
   - Invalid order code handling

### 8. Crew Join Date Validation (2 tests)
   - Crew with future start date unavailable
   - Crew with past start date available

### 9. Order Creation (1 test)
   - New orders created with "Active" status (not "Confirmed")

## Requirements

- Flask app must be running on `http://127.0.0.1:5000`
- Database must be initialized with test data
- Manager credentials: `111111111` / `Admin@2024`

## Note

These tests require the Flask application to be running. Start the app before running tests:
```bash
python main.py
```

