# Smart Parking Management System

A simple, modern, and professional web-based **Smart Parking Management System** built with **Python Flask** and **SQLite3**. Designed specifically for a college Python Programming mini-project and viva demonstration.

---

## 🚀 Key Features

1. **Modern SaaS Dashboard**:
   - Fixed left sidebar navigation with sections (Main, Parking, Records, Analytics, System).
   - Top header with dynamic date display and live "System Online" indicator.
   - 4 Dynamic KPI Cards: Total Slots, Available Slots, Occupied Slots, and Today's Revenue.
   - Interactive Chart.js Occupancy Doughnut Chart (Available vs Occupied).
   - Today's Activity Tracker (Vehicles Entered vs Exited).
   - Recent 5 parking transactions with status badges.

2. **Automated Vehicle Entry**:
   - Input vehicle registration number, owner/driver name, and vehicle type (Car or Bike).
   - Duplicate prevention: Rejects registration if a vehicle is already parked.
   - Automated sequential slot assignment:
     - **Car**: Slots `A01` - `A10` (10 slots)
     - **Bike**: Slots `B01` - `B10` (10 slots)
   - Real-time availability indicator pills.

3. **Visual Parking Slots Map**:
   - Color-coded slot cards: Green for Available, Red for Occupied.
   - Displays vehicle number, driver name, and entry time on occupied bays.
   - Direct 1-click "Exit Vehicle" button on occupied slots.

4. **Vehicle Exit & Fee Settlement**:
   - Search by vehicle license plate or select directly from the active roster.
   - Automated duration calculation (partial hours rounded upward using `math.ceil()`).
   - Automated fee calculation based on tariff rules.
   - Confirmation step releases the parking slot immediately and records the completed session.

5. **Parking History**:
   - Complete tabular record of all active and completed transactions.
   - Real-time search filter by vehicle registration number or owner name.

6. **Reports & Analytics**:
   - Key analytics metrics: Total Vehicles, Completed Sessions, Total Revenue, Average Duration.
   - Vehicle Type Distribution Chart (Car vs Bike).
   - Daily Revenue Trend Bar Chart.

7. **Settings & Specifications**:
   - Clean display of facility capacity, tariff breakdown, and technical architecture specs.

---

## 💰 Parking Fee Rules

| Vehicle Type | First Hour Rate | Each Additional Hour |
| :--- | :--- | :--- |
| **Bike (2-Wheeler)** | **₹20** | **₹10 / hour** |
| **Car (4-Wheeler)** | **₹30** | **₹20 / hour** |

*Note: Partial hours are rounded upward to the next full hour with a 1-hour minimum charge.*

---

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Flask
- **Database**: SQLite3 (Built-in Python module, zero configuration)
- **Frontend**: HTML5, Vanilla CSS3 (Custom SaaS Design System), Vanilla JavaScript
- **Data Visualization**: Chart.js (Occupancy doughnut chart & Revenue trend)

---

## 📁 Project Structure

```text
Parking System Final/
├── app.py              # Main Flask application with routes and controllers
├── database.py         # SQLite connection, schema initialization, and SQL queries
├── parking.py          # Business logic: slot allocation, duration, and fee calculation
├── requirements.txt    # Python dependencies (Flask)
├── parking.db          # SQLite database (auto-created on first run)
├── README.md           # Project documentation and viva guide
│
├── templates/          # Jinja2 HTML templates
│   ├── base.html       # Global layout (sidebar, header, alerts)
│   ├── dashboard.html  # Main dashboard with KPI cards and charts
│   ├── entry.html      # Vehicle check-in form
│   ├── exit.html       # Vehicle check-out and billing preview
│   ├── slots.html      # Visual parking bays map (A01-A10, B01-B10)
│   ├── history.html    # Full parking records table with search
│   ├── reports.html    # Analytics and revenue reports
│   └── settings.html   # Facility and rate card information
│
└── static/
    ├── css/
    │   └── style.css   # Clean, modern light theme stylesheet
    └── js/
        └── main.js     # Sidebar toggle, alert dismissals, and confirmation modals
```

---

## 🏃 How to Run the Project

### 1. Install Dependencies
Open your terminal in this project directory and run:
```bash
pip install -r requirements.txt
```

### 2. Start the Application
Run the Python script:
```bash
python app.py
```

### 3. Open in Browser
Open your web browser and go to:
```
http://127.0.0.1:5000
```

---

## 🎓 College Viva Preparation Guide

Here are standard questions the examiner may ask and how to answer them:

1. **How is a parking slot assigned to a vehicle?**
   - In `parking.py`, the `get_available_slot(vehicle_type)` function fetches all currently occupied slots (`status = 'PARKED'`) from the database. It compares them against the predefined list (`A01-A10` for cars, `B01-B10` for bikes) and returns the first slot that is not in the occupied set.

2. **Why don't slots have their own separate database table?**
   - The slot configuration is fixed at 20 bays (10 for cars, 10 for bikes). Generating them programmatically in Python keeps the database schema clean and lightweight (only 2 tables: `vehicles` and `parking_records`), avoiding unnecessary database joins.

3. **How does the system prevent duplicate parking?**
   - When a vehicle entry is requested in `/entry`, the backend calls `get_active_record_by_vehicle(vehicle_number)`. If a record with `status = 'PARKED'` already exists for that registration number, an alert is triggered and the entry is rejected.

4. **How are duration and fee calculated?**
   - The entry timestamp and exit timestamp are converted to `datetime` objects. The difference in seconds is divided by 3600 and rounded upward using Python's built-in `math.ceil()`. The fee is then computed using the formula:
     - `Bike: 20 + (duration_hours - 1) * 10`
     - `Car: 30 + (duration_hours - 1) * 20`
