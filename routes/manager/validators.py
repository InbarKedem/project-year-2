from db import query_db
from services.flight_service import get_flight_duration

def validate_crew_count(crew_ids, aircraft_id, source_id, dest_id, departure_time):
    """
    Validates that the selected crew count matches the requirements.
    Returns (is_valid, message)
    """
    if not crew_ids:
        return False, "No crew members selected."
    
    # Get aircraft type
    aircraft = query_db("SELECT is_large FROM Aircraft WHERE aircraft_id = %s", (aircraft_id,), one=True)
    if not aircraft:
        return False, "Invalid aircraft selected."
    
    # Get flight duration to determine requirements
    duration = get_flight_duration(source_id, dest_id)
    
    # Determine requirements based on aircraft size
    if aircraft['is_large']:
        required_pilots = 3
        required_attendants = 6
    else:
        required_pilots = 2
        required_attendants = 3
    
    # Count selected pilots and attendants
    selected_pilots = []
    selected_attendants = []
    
    for crew_id in crew_ids:
        # Check if it's a pilot or attendant
        pilot_check = query_db("""
            SELECT id_number FROM Flight_Crew 
            WHERE id_number = %s AND is_pilot = 1
        """, (crew_id,), one=True)
        
        if pilot_check:
            selected_pilots.append(crew_id)
        else:
            attendant_check = query_db("""
                SELECT id_number FROM Flight_Crew 
                WHERE id_number = %s AND is_pilot = 0
            """, (crew_id,), one=True)
            if attendant_check:
                selected_attendants.append(crew_id)
    
    # Validate counts
    pilot_count = len(selected_pilots)
    attendant_count = len(selected_attendants)
    
    if pilot_count != required_pilots:
        return False, f"Invalid number of pilots. Required: {required_pilots}, Selected: {pilot_count}"
    
    if attendant_count != required_attendants:
        return False, f"Invalid number of attendants. Required: {required_attendants}, Selected: {attendant_count}"
    
    return True, "Crew count is valid"

