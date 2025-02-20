import streamlit as st
from datetime import datetime, timedelta
import random

def load_help_requests():
    """
    Load help requests from temporary storage
    """
    # In production, consider using a lightweight database
    return []

def save_help_request(request):
    """
    Save a new help request
    """
    if 'help_requests' not in st.session_state:
        st.session_state.help_requests = []
    
    # Add request to session state
    st.session_state.help_requests.append(request)
    
    # Remove requests older than 24 hours
    current_time = datetime.now()
    st.session_state.help_requests = [
        req for req in st.session_state.help_requests
        if datetime.fromisoformat(req['timestamp']) > current_time - timedelta(days=1)
    ]

def generate_heatmap_data(location):
    """
    Generate heatmap data for risk visualization
    Args:
        location (dict): Dictionary containing 'lat' and 'lng' keys
    Returns:
        list: List of [lat, lng, intensity] points for heatmap
    """
    try:
        # Generate simulated risk data points around the location
        risk_data = []
        base_lat, base_lng = location['lat'], location['lng']
        
        # Create a grid of points around the location
        for i in range(-5, 6):
            for j in range(-5, 6):
                lat = base_lat + (i * 0.002)
                lng = base_lng + (j * 0.002)
                # Random risk intensity between 0 and 1
                intensity = random.uniform(0, 1)
                risk_data.append([lat, lng, intensity])
        
        return risk_data

    except Exception as e:
        st.error(f"Error generating heatmap data: {str(e)}")
        return []

def clean_old_requests():
    """
    Remove help requests older than 24 hours
    """
    if 'help_requests' in st.session_state:
        current_time = datetime.now()
        st.session_state.help_requests = [
            req for req in st.session_state.help_requests
            if datetime.fromisoformat(req['timestamp']) > current_time - timedelta(days=1)
        ]

def format_timestamp(timestamp_str):
    """
    Format timestamp string to human-readable format
    """
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp_str 