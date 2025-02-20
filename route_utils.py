import folium
import streamlit as st
import logging
from constants import DEFAULT_LAT, DEFAULT_LNG

logger = logging.getLogger(__name__)

def create_route_map(user_location, destination, route_info=None):
    """Create a map with route visualization"""
    try:
        m = folium.Map(
            location=[user_location['lat'], user_location['lng']],
            zoom_start=13
        )
        
        # Add user marker
        folium.Marker(
            [user_location['lat'], user_location['lng']],
            popup="Your Location",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Add destination marker if provided
        if destination:
            folium.Marker(
                [destination['lat'], destination['lng']],
                popup=f"Destination: {destination.get('name', 'Unknown')}",
                icon=folium.Icon(color='green', icon='flag')
            ).add_to(m)
        
        # Add route polyline if provided
        if route_info and 'coordinates' in route_info:
            folium.PolyLine(
                route_info['coordinates'],
                weight=3,
                color='blue',
                opacity=0.8
            ).add_to(m)
        
        return m
    except Exception as e:
        logger.error(f"Error creating route map: {e}")
        # Return default map on error
        return folium.Map(
            location=[DEFAULT_LAT, DEFAULT_LNG],
            zoom_start=13
        )

def format_route_step(step, index):
    """Format route step with icons and simplified instructions"""
    icons = {
        'left': "↰",
        'right': "↱",
        'straight': "⬆",
        'merge': "↱",
        'destination': "📍",
        'start': "🚩"
    }
    
    # Get basic instruction
    instruction = step.get('instruction', '').replace('<b>', '').replace('</b>', '')
    
    # Get icon
    icon = icons.get('straight')  # default icon
    for key, symbol in icons.items():
        if key in instruction.lower():
            icon = symbol
            break
    
    if index == 1:
        icon = icons['start']
    
    # Format distance and duration
    distance = step.get('distance', '')
    duration = step.get('duration', '')
    time_info = f"({duration})" if duration else ""
    
    return f"{icon} {instruction} - {distance} {time_info}" 