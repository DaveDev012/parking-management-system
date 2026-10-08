"""
app.py - Main Flask Application for Smart Parking Management System
Provides web routes, handles HTTP requests, and integrates templates and database.
"""

from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

from database import (
    init_db,
    add_or_get_vehicle,
    get_active_record_by_vehicle,
    get_active_record_by_id,
    create_parking_record,
    complete_parking_record,
    get_all_active_records,
    get_recent_records,
    get_parking_history,
    get_dashboard_stats,
    get_reports_stats
)
from parking import (
    get_available_slot,
    calculate_duration,
    calculate_fee,
    get_all_slots_status,
    CAR_SLOTS,
    BIKE_SLOTS,
    TOTAL_SLOTS_COUNT,
    RATES
)

# Initialize Flask application
app = Flask(__name__)
app.secret_key = 'smart_parking_secret_key_college_project'


# Context processor to make common data available across all templates
@app.context_processor
def inject_global_data():
    return {
        'current_date': datetime.now().strftime('%d %B %Y'),
        'total_slots_count': TOTAL_SLOTS_COUNT,
        'car_slots_count': len(CAR_SLOTS),
        'bike_slots_count': len(BIKE_SLOTS)
    }


# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def dashboard():
    """
    Main Dashboard Page:
    - 4 KPI cards: Total Slots, Available Slots, Occupied Slots, Today's Revenue.
    - Parking Occupancy Chart (Available vs Occupied).
    - Today's Activity (Entered vs Exited).
    - Recent Parking Activity (latest 5 records).
    """
    stats = get_dashboard_stats(TOTAL_SLOTS_COUNT)
    recent_records = get_recent_records(5)
    return render_template('dashboard.html', stats=stats, recent_records=recent_records, active_page='dashboard')


@app.route('/entry', methods=['GET', 'POST'])
def entry():
    """
    Vehicle Entry Page:
    - GET: Displays entry form and available slot count.
    - POST: Validates input, assigns first free slot, saves record, flashes message.
    """
    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number', '').strip().upper()
        owner_name = request.form.get('owner_name', '').strip()
        vehicle_type = request.form.get('vehicle_type', '').strip()

        # 1. Validation: Required fields
        if not vehicle_number or not owner_name or not vehicle_type:
            flash("All fields are required. Please fill in all vehicle details.", "danger")
            return redirect(url_for('entry'))

        # 2. Validation: Check if vehicle is already parked
        active_record = get_active_record_by_vehicle(vehicle_number)
        if active_record:
            flash(f"Vehicle {vehicle_number} is already parked in slot {active_record['slot_number']}!", "warning")
            return redirect(url_for('entry'))

        # 3. Check for available slot
        slot = get_available_slot(vehicle_type)
        if not slot:
            flash(f"No available parking slot for this vehicle type ({vehicle_type}).", "danger")
            return redirect(url_for('entry'))

        # 4. Save vehicle and record
        vehicle_id = add_or_get_vehicle(vehicle_number, owner_name, vehicle_type)
        entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        create_parking_record(vehicle_id, slot, entry_time)

        flash(f"Vehicle {vehicle_number} successfully parked in {slot}.", "success")
        return redirect(url_for('slots'))

    slots_data = get_all_slots_status()
    return render_template('entry.html', slots_data=slots_data, active_page='entry')


@app.route('/exit')
def exit_vehicle():
    """
    Vehicle Exit Page:
    - Search for a parked vehicle by vehicle number.
    - Displays preview of entry time, calculated duration, and fee.
    - Also lists all currently parked vehicles for quick 1-click select.
    """
    query_number = request.args.get('vehicle_number', '').strip().upper()
    preview = None

    if query_number:
        active_record = get_active_record_by_vehicle(query_number)
        if active_record:
            duration = calculate_duration(active_record['entry_time'])
            fee = calculate_fee(active_record['vehicle_type'], duration)
            preview = {
                'record_id': active_record['record_id'],
                'vehicle_number': active_record['vehicle_number'],
                'owner_name': active_record['owner_name'],
                'vehicle_type': active_record['vehicle_type'],
                'slot_number': active_record['slot_number'],
                'entry_time': active_record['entry_time'],
                'current_exit_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'duration_hours': duration,
                'fee': fee
            }
        else:
            flash(f"No actively parked vehicle found with number '{query_number}'.", "warning")

    active_records = get_all_active_records()
    return render_template('exit.html', preview=preview, query_number=query_number, active_records=active_records, active_page='exit')


@app.route('/exit/confirm/<int:record_id>', methods=['POST'])
def exit_confirm(record_id):
    """
    Finalizes vehicle exit:
    - Computes final duration and parking fee.
    - Updates database record to 'COMPLETED'.
    - Slot becomes immediately available.
    """
    active_record = get_active_record_by_id(record_id)
    if not active_record:
        flash("Record not found or vehicle has already exited.", "danger")
        return redirect(url_for('exit_vehicle'))

    exit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    duration = calculate_duration(active_record['entry_time'], exit_time)
    fee = calculate_fee(active_record['vehicle_type'], duration)

    completed = complete_parking_record(record_id, exit_time, duration, fee)
    if completed:
        flash(
            f"Vehicle {active_record['vehicle_number']} has exited slot {active_record['slot_number']}. "
            f"Duration: {duration} hr(s) | Fee: ₹{int(fee)}.",
            "success"
        )
    else:
        flash("Error processing vehicle exit. Please try again.", "danger")

    return redirect(url_for('history'))


@app.route('/slots')
def slots():
    """
    Parking Slots Page:
    - Visual layout of Car slots (A01 - A10) and Bike slots (B01 - B10).
    - Highlights Available (Green) and Occupied (Red).
    - Clicking an occupied slot provides a direct exit action.
    """
    slots_data = get_all_slots_status()
    return render_template('slots.html', slots_data=slots_data, active_page='slots')


@app.route('/history')
def history():
    """
    Parking History Page:
    - Lists all previous and active parking transactions.
    - Simple search box to filter by vehicle number or owner name.
    """
    search_query = request.args.get('search', '').strip()
    records = get_parking_history(search_query if search_query else None)
    return render_template('history.html', records=records, search_query=search_query, active_page='history')


@app.route('/reports')
def reports():
    """
    Reports & Analytics Page:
    - Summary KPI cards: Total Vehicles, Completed Sessions, Total Revenue, Avg Duration.
    - Chart 1: Vehicle Type Distribution (Car vs Bike).
    - Chart 2: Daily Revenue over recent days.
    """
    report_stats = get_reports_stats()
    return render_template('reports.html', report_stats=report_stats, active_page='reports')


@app.route('/settings')
def settings():
    """
    Settings Page:
    - Clean informational view of parking capacity, rate cards, and system specs.
    """
    return render_template('settings.html', rates=RATES, active_page='settings')


# ==========================================
# APPLICATION ENTRY POINT
# ==========================================

if __name__ == '__main__':
    # Initialize database tables on startup
    init_db(seed_demo_data=True)
    print("=" * 60)
    print(" Smart Parking Management System - Online")
    print(" Access at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
