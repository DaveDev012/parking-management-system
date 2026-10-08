"""
parking.py - Business Logic for Smart Parking Management System
Handles slot allocation, duration computation, fee calculation, and slot states.
"""

import math
from datetime import datetime
from database import get_all_active_records

# Total slots configuration (20 slots total)
CAR_SLOTS = [f"A{str(i).zfill(2)}" for i in range(1, 11)]   # A01 to A10 (10 slots)
BIKE_SLOTS = [f"B{str(i).zfill(2)}" for i in range(1, 11)]  # B01 to B10 (10 slots)

TOTAL_SLOTS_COUNT = len(CAR_SLOTS) + len(BIKE_SLOTS)

# Parking Fee Rates (in INR ₹)
RATES = {
    'Car': {
        'first_hour': 30,
        'additional_hour': 20
    },
    'Bike': {
        'first_hour': 20,
        'additional_hour': 10
    }
}


def get_available_slot(vehicle_type):
    """
    Finds and returns the first available parking slot for the specified vehicle type.
    Car slots: A01 - A10
    Bike slots: B01 - B10
    Returns None if all slots for this type are occupied.
    """
    # 1. Determine the relevant slot pool
    if vehicle_type == 'Car':
        slot_pool = CAR_SLOTS
    elif vehicle_type == 'Bike':
        slot_pool = BIKE_SLOTS
    else:
        return None

    # 2. Get currently occupied slot numbers from the database
    active_records = get_all_active_records()
    occupied_slots = {record['slot_number'] for record in active_records}

    # 3. Find first slot not in occupied_slots
    for slot in slot_pool:
        if slot not in occupied_slots:
            return slot

    # All slots full
    return None


def calculate_duration(entry_time_str, exit_time_str=None):
    """
    Calculates parking duration in hours between entry and exit timestamps.
    Rounds up partial hours to the nearest full hour (math.ceil).
    Minimum duration is 1 hour.
    """
    time_format = '%Y-%m-%d %H:%M:%S'
    entry_dt = datetime.strptime(entry_time_str, time_format)

    if exit_time_str:
        exit_dt = datetime.strptime(exit_time_str, time_format)
    else:
        exit_dt = datetime.now()

    # Time difference in seconds
    delta_seconds = (exit_dt - entry_dt).total_seconds()

    # Convert to hours and round upward (ceil)
    # Any fraction of an hour counts as an additional hour
    hours = math.ceil(delta_seconds / 3600.0)

    # Minimum duration is 1 hour
    return max(1, int(hours))


def calculate_fee(vehicle_type, duration_hours):
    """
    Calculates total parking fee based on vehicle type and duration in hours.
    
    Bike:
      First hour: ₹20
      Each additional hour: ₹10
      Example: 1 hr -> ₹20, 2 hr -> ₹30, 3 hr -> ₹40
      
    Car:
      First hour: ₹30
      Each additional hour: ₹20
      Example: 1 hr -> ₹30, 2 hr -> ₹50, 3 hr -> ₹70
    """
    if vehicle_type not in RATES:
        raise ValueError(f"Unknown vehicle type: {vehicle_type}")

    first_hour_rate = RATES[vehicle_type]['first_hour']
    additional_rate = RATES[vehicle_type]['additional_hour']

    if duration_hours <= 1:
        return float(first_hour_rate)
    else:
        additional_hours = duration_hours - 1
        return float(first_hour_rate + (additional_hours * additional_rate))


def get_all_slots_status():
    """
    Builds a complete list of all 20 slots with their current status:
    - slot_number
    - vehicle_type
    - is_occupied (True / False)
    - vehicle_number (if occupied)
    - owner_name (if occupied)
    - entry_time (if occupied)
    - record_id (if occupied)
    """
    # Fetch all active records currently in the parking lot
    active_records = get_all_active_records()
    active_by_slot = {record['slot_number']: record for record in active_records}

    car_slots_status = []
    for slot in CAR_SLOTS:
        if slot in active_by_slot:
            rec = active_by_slot[slot]
            car_slots_status.append({
                'slot_number': slot,
                'vehicle_type': 'Car',
                'is_occupied': True,
                'vehicle_number': rec['vehicle_number'],
                'owner_name': rec['owner_name'],
                'entry_time': rec['entry_time'],
                'record_id': rec['record_id']
            })
        else:
            car_slots_status.append({
                'slot_number': slot,
                'vehicle_type': 'Car',
                'is_occupied': False,
                'vehicle_number': None,
                'owner_name': None,
                'entry_time': None,
                'record_id': None
            })

    bike_slots_status = []
    for slot in BIKE_SLOTS:
        if slot in active_by_slot:
            rec = active_by_slot[slot]
            bike_slots_status.append({
                'slot_number': slot,
                'vehicle_type': 'Bike',
                'is_occupied': True,
                'vehicle_number': rec['vehicle_number'],
                'owner_name': rec['owner_name'],
                'entry_time': rec['entry_time'],
                'record_id': rec['record_id']
            })
        else:
            bike_slots_status.append({
                'slot_number': slot,
                'vehicle_type': 'Bike',
                'is_occupied': False,
                'vehicle_number': None,
                'owner_name': None,
                'entry_time': None,
                'record_id': None
            })

    return {
        'car_slots': car_slots_status,
        'bike_slots': bike_slots_status,
        'total_car_slots': len(CAR_SLOTS),
        'total_bike_slots': len(BIKE_SLOTS),
        'total_slots': TOTAL_SLOTS_COUNT,
        'occupied_cars': sum(1 for s in car_slots_status if s['is_occupied']),
        'available_cars': sum(1 for s in car_slots_status if not s['is_occupied']),
        'occupied_bikes': sum(1 for s in bike_slots_status if s['is_occupied']),
        'available_bikes': sum(1 for s in bike_slots_status if not s['is_occupied'])
    }
