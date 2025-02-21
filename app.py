import streamlit as st
# Set page config first, before any other st commands
st.set_page_config(
    page_title="SafeSphere - AI-Powered Disaster Alert System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

import folium
from folium import plugins
from folium.plugins import HeatMap
from streamlit_folium import folium_static
from datetime import datetime, time
import pandas as pd
from groq_api import get_disaster_alerts, analyze_risk_level, get_risk_insights, get_weather_alerts, get_traffic_incidents, get_seismic_activity, get_current_weather
from maps import (
    get_nearby_support_locations, 
    get_weather, 
    get_route_to_location,
    get_risk_zones,
    get_precise_location,
    track_location_changes,
    calculate_movement_metrics
)
from utils import generate_heatmap_data
import json
from dotenv import load_dotenv
import os
import requests
import time as time_module
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

# Load environment variables
load_dotenv()

# Verify required API keys
if not os.getenv('GOOGLE_MAPS_API_KEY'):
    st.error("Google Maps API key is missing")
if not os.getenv('GROQ_API_KEY'):
    st.error("Groq API key is missing")
if not os.getenv('OPENWEATHER_API_KEY'):
    st.error("OpenWeather API key is missing")

# CSS styling
st.markdown("""
<style>
    .stButton > button {
        background-color: #ff4b4b;
        color: white;
        font-size: 20px;
        padding: 20px;
        border-radius: 10px;
    }
    .stButton > button:hover {
        background-color: #ff0000;
    }
    .safe-button > button {
        background-color: #4CAF50 !important;
    }
    .safe-button > button:hover {
        background-color: #45a049 !important;
    }
    .location-prompt {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .risk-high {
        color: #ff4b4b;
        font-weight: bold;
    }
    .risk-medium {
        color: #ffa500;
        font-weight: bold;
    }
    .risk-low {
        color: #4CAF50;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session states
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'risk_level' not in st.session_state:
    st.session_state.risk_level = 'low'
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
if 'selected_destination' not in st.session_state:
    st.session_state.selected_destination = None
if 'route_info' not in st.session_state:
    st.session_state.route_info = None
if 'location_history' not in st.session_state:
    st.session_state.location_history = []
if 'last_location_check' not in st.session_state:
    st.session_state.last_location_check = 0
if 'location_update_interval' not in st.session_state:
    st.session_state.location_update_interval = 30  # seconds

def get_location():
    """Get user location using IP-based geolocation"""
    try:
        response = requests.get('https://ipapi.co/json/')
        if response.status_code == 200:
            data = response.json()
            return {
                'lat': float(data['latitude']),
                'lng': float(data['longitude']),
                'city': data.get('city', 'Unknown'),
                'region': data.get('region', 'Unknown'),
                'country': data.get('country_name', 'Unknown')
            }
    except Exception as e:
        st.error(f"Error getting location: {str(e)}")
    return None

def send_notification(message):
    """Simplified notification function using Streamlit toast"""
    st.toast(message)

def create_risk_heatmap(location, risk_data):
    """Create a heatmap layer for risk visualization"""
    try:
        m = folium.Map(
            location=[location['lat'], location['lng']],
            zoom_start=13
        )
        
        if risk_data:
            plugins.HeatMap(
                risk_data,
                radius=15,
                gradient={0.4: 'blue', 0.65: 'yellow', 0.9: 'red'}
            ).add_to(m)
        
        return m
    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")
        return folium.Map(location=[location['lat'], location['lng']], zoom_start=13)

def create_route_map(user_location, destination, route_info):
    """Create a map with route visualization"""
    m = folium.Map(
        location=[user_location['lat'], user_location['lng']],
        zoom_start=13
    )
    
    # Add user marker
    folium.Marker(
        [user_location['lat'], user_location['lng']],
        popup="Your Location",
        icon=folium.Icon(color='red', icon='info-sign', prefix='fa')
    ).add_to(m)
    
    # Add destination marker
    folium.Marker(
        [destination['lat'], destination['lng']],
        popup=f"Destination: {destination['name']}",
        icon=folium.Icon(color='green', icon='flag', prefix='fa')
    ).add_to(m)
    
    # Add route polyline if coordinates are provided
    if route_info and 'coordinates' in route_info:
        folium.PolyLine(
            route_info['coordinates'],
            weight=3,
            color='blue',
            opacity=0.8
        ).add_to(m)
        
        # Add risk zones along route
        risk_zones = get_risk_zones(route_info['coordinates'])
        for zone in risk_zones:
            color = 'red' if zone['risk_level'] == 'high' else 'orange'
            folium.Circle(
                location=[zone['lat'], zone['lng']],
                radius=100,
                color=color,
                fill=True,
                popup=f"Risk Zone: {zone['description']}"
            ).add_to(m)
    
    return m

def display_risk_insights(location):
    """Display detailed risk insights"""
    insights = get_risk_insights(location)
    
    st.subheader("🔍 Risk Insights")
    
    # Display overall risk level
    risk_level = insights['risk_level']
    risk_color = {
        'high': 'risk-high',
        'medium': 'risk-medium',
        'low': 'risk-low'
    }.get(risk_level.lower(), '')
    
    st.markdown(f"**Overall Risk Level:** <span class='{risk_color}'>{risk_level.upper()}</span>", 
                unsafe_allow_html=True)
    
    # Display risk factors
    st.markdown("### Risk Factors:")
    for factor in insights['risk_factors']:
        severity = factor['severity']
        icon = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }.get(severity.lower(), '⚪')
        st.markdown(f"{icon} **{factor['type']}**")
        st.markdown(f"- Severity: {severity.upper()}")
        st.markdown(f"- Description: {factor['description']}")
        
        # Display safety tips
        if factor['safety_tips']:
            with st.expander("Safety Tips"):
                for tip in factor['safety_tips']:
                    st.markdown(f"• {tip}")
    
    # Display recommended actions
    if insights['recommended_actions']:
        st.markdown("### 📋 Recommended Actions:")
        for action in insights['recommended_actions']:
            st.markdown(f"• {action}")

def update_location():
    """Update user location with improved tracking"""
    if not st.session_state.user_location:
        # Get initial location
        new_location = get_precise_location()
        if not new_location:
            new_location = get_location()  # Fallback to IP-based location
        
        if new_location:
            st.session_state.user_location = new_location
            st.session_state.last_location_check = time_module.time()
    
    return st.session_state.user_location

def create_dynamic_heatmap(heatmap_data, current_location):
    """Create an interactive heatmap with tooltips and legend"""
    try:
        # Create base map centered on current location
        center_lat = current_location['lat']
        center_lng = current_location['lng']
        
        m = folium.Map(location=[center_lat, center_lng], zoom_start=13)
        
        # Add current location marker with pulsing effect
        plugins.LocateControl().add_to(m)
        plugins.Fullscreen().add_to(m)
        
        # Add a distinctive marker for current location
        folium.Marker(
            location=[center_lat, center_lng],
            popup='Your Location',
            icon=folium.Icon(color='red', icon='info-sign'),
            tooltip='You are here'
        ).add_to(m)
        
        # Add circle to show accuracy radius
        folium.Circle(
            location=[center_lat, center_lng],
            radius=current_location.get('accuracy', 1000),
            color='red',
            fill=True,
            fillColor='red',
            fillOpacity=0.1,
            popup='Location Accuracy Range'
        ).add_to(m)
        
        # Add heatmap layer with gradient
        gradient = {
            0.2: '#00ff00',  # Low risk - Green
            0.4: '#ffff00',  # Medium-low risk - Yellow
            0.6: '#ffa500',  # Medium risk - Orange
            0.8: '#ff4500',  # Medium-high risk - Orange-red
            1.0: '#ff0000'   # High risk - Red
        }
        
        # Prepare heatmap data
        heat_data = [[point['lat'], point['lng'], point['intensity']] for point in heatmap_data]
        
        # Add heatmap layer
        if heat_data:  # Only add heatmap if there's data
            HeatMap(
                data=heat_data,
                radius=25,
                gradient=gradient,
                min_opacity=0.3,
                max_zoom=18,
            ).add_to(m)
        
        # Add legend
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; 
                    background-color: white;
                    border: 2px solid grey; 
                    z-index: 1000;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 3px 3px 3px rgba(0,0,0,0.3)">
            <p style="text-align: center;"><b>Risk Level Legend</b></p>
            <div style="display: flex; align-items: center; margin: 5px;">
                <div style="width: 20px; height: 20px; background: #00ff00; margin-right: 5px;"></div>
                <span>Low Risk</span>
            </div>
            <div style="display: flex; align-items: center; margin: 5px;">
                <div style="width: 20px; height: 20px; background: #ffff00; margin-right: 5px;"></div>
                <span>Medium-Low Risk</span>
            </div>
            <div style="display: flex; align-items: center; margin: 5px;">
                <div style="width: 20px; height: 20px; background: #ffa500; margin-right: 5px;"></div>
                <span>Medium Risk</span>
            </div>
            <div style="display: flex; align-items: center; margin: 5px;">
                <div style="width: 20px; height: 20px; background: #ff4500; margin-right: 5px;"></div>
                <span>Medium-High Risk</span>
            </div>
            <div style="display: flex; align-items: center; margin: 5px;">
                <div style="width: 20px; height: 20px; background: #ff0000; margin-right: 5px;"></div>
                <span>High Risk</span>
            </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Add tooltips for each risk point
        for point in heatmap_data:
            risk_level = get_risk_level(point['intensity'])
            tooltip_html = f"""
                <div style="background-color: white; padding: 10px; border-radius: 5px;">
                    <h4 style="margin: 0;">Risk Information</h4>
                    <p style="margin: 5px 0;"><b>Risk Level:</b> {risk_level}</p>
                    <p style="margin: 5px 0;"><b>Intensity:</b> {point['intensity']:.2f}</p>
                    <p style="margin: 5px 0;"><b>Type:</b> {point.get('type', 'General Risk')}</p>
                    <p style="margin: 5px 0;"><b>Description:</b> {point.get('description', 'Area of potential risk')}</p>
                </div>
            """
            
            folium.CircleMarker(
                location=[point['lat'], point['lng']],
                radius=1,
                color="transparent",
                fill=False,
                popup=folium.Popup(tooltip_html, max_width=300),
                tooltip="Click for details"
            ).add_to(m)
        
        return m
    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")
        return folium.Map(location=[40.7128, -74.0060], zoom_start=10)  # Return default map on error

def get_risk_level(intensity):
    """Convert intensity value to risk level description"""
    if intensity <= 0.2:
        return "Low Risk"
    elif intensity <= 0.4:
        return "Medium-Low Risk"
    elif intensity <= 0.6:
        return "Medium Risk"
    elif intensity <= 0.8:
        return "Medium-High Risk"
    else:
        return "High Risk"

def notify_user(message):
    """
    Notify the user about potential dangers.
    """
    st.warning(message)  # Example notification

def main():
    try:
        # Sidebar
        st.sidebar.title("🚨 Safety Dashboard")
        current_location = update_location()
        
        if current_location:
            st.sidebar.markdown(f"📍 **Current Location:**")
            
            # Display formatted address if available
            if 'formatted_address' in current_location:
                st.sidebar.markdown(f"**Address:** {current_location['formatted_address']}")
            
            # Display detailed location information
            if 'sublocality' in current_location and current_location['sublocality']:
                st.sidebar.markdown(f"**Area:** {current_location['sublocality']}")
            st.sidebar.markdown(f"**City:** {current_location['city']}")
            st.sidebar.markdown(f"**Region:** {current_location['region']}")
            if 'postal_code' in current_location:
                st.sidebar.markdown(f"**Postal Code:** {current_location['postal_code']}")
            
            # Display accuracy and source
            accuracy_meters = current_location.get('accuracy', 'N/A')
            source = current_location.get('source', 'Unknown')
            
            accuracy_color = "#00ff00" if accuracy_meters < 100 else "#ffa500" if accuracy_meters < 1000 else "#ff4b4b"
            
            st.sidebar.markdown(f"""
                <div style='background-color: #1e1e1e; padding: 10px; border-radius: 5px; margin: 10px 0;'>
                    <div style='color: {accuracy_color};'>
                        📡 Accuracy: ±{accuracy_meters}m
                    </div>
                    <div style='color: #cccccc; font-size: 12px;'>
                        Source: {source}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Display weather information in sidebar
            weather = get_weather(current_location)
            if weather:
                st.sidebar.markdown("---")
                st.sidebar.markdown("🌤️ **Weather Report**")
                
                # Create a styled container for weather info
                st.sidebar.markdown(
                    f"""
                    <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                        <div style='color: #00ff00; font-size: 24px; margin-bottom: 10px;'>
                            {weather['temperature']}°C
                        </div>
                        <div style='color: white; margin-bottom: 5px;'>
                            {weather['description'].title()}
                        </div>
                        <hr style='border-color: #333333; margin: 10px 0;'>
                        <div style='color: #cccccc;'>
                            💧 Humidity: {weather['humidity']}%<br>
                            💨 Wind Speed: {weather['wind_speed']} m/s
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Add weather alerts if any
                weather_alerts = get_weather_alerts(current_location)
                if weather_alerts:
                    st.sidebar.markdown("⚠️ **Weather Alerts**")
                    for alert in weather_alerts:
                        st.sidebar.markdown(
                            f"""
                            <div style='background-color: #ff4b4b; padding: 10px; border-radius: 5px; margin: 5px 0; color: white;'>
                                {alert['description']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

        # Manual location override
        with st.sidebar.expander("Manual Location Override"):
            try:
                default_lat = current_location['lat'] if current_location else 0.0
                default_lng = current_location['lng'] if current_location else 0.0
                
                new_lat = st.number_input("Latitude", 
                                        value=float(default_lat),
                                        min_value=-90.0,
                                        max_value=90.0,
                                        format="%.6f")
                new_lng = st.number_input("Longitude", 
                                        value=float(default_lng),
                                        min_value=-180.0,
                                        max_value=180.0,
                                        format="%.6f")
                
                if st.button("Update Location"):
                    try:
                        # Use geopy to get location details
                        geolocator = Nominatim(user_agent="my_safety_app")
                        location = geolocator.reverse(f"{new_lat}, {new_lng}", language='en')
                        
                        if location and location.raw:
                            address = location.raw.get('address', {})
                            
                            # Update session state with new location
                            st.session_state.user_location = {
                                'lat': new_lat,
                                'lng': new_lng,
                                'city': address.get('city', address.get('town', address.get('village', 'Unknown'))),
                                'region': address.get('state', 'Unknown'),
                                'country': address.get('country', 'Unknown'),
                                'timestamp': time_module.time(),
                                'accuracy': 0
                            }
                            
                            st.success("Location updated successfully!")
                            st.rerun()
                        else:
                            st.error("Could not find location details. Please try different coordinates.")
                    except Exception as e:
                        st.error(f"Error updating location: {str(e)}")
            except Exception as e:
                st.error(f"Error in location input: {str(e)}")

        # Main content area with tabs
        tab1, tab2 = st.tabs(["📍 Live Map", "📊 Risk Analysis"])
        
        with tab1:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.header("🗺 Safety Map")
                
                # Get support locations with error handling
                support_locations = get_nearby_support_locations(current_location)
                
                # Create and display the safety map first
                if current_location:
                    safety_map = folium.Map(
                        location=[current_location['lat'], current_location['lng']],
                        zoom_start=13
                    )
                    
                    # Add current location marker
                    folium.Marker(
                        [current_location['lat'], current_location['lng']],
                        popup='Your Location',
                        icon=folium.Icon(color='red', icon='info-sign'),
                        tooltip='You are here'
                    ).add_to(safety_map)
                    
                    # Add support locations to map
                    if support_locations:
                        for location in support_locations:
                            folium.Marker(
                                [location['lat'], location['lng']],
                                popup=f"{location['name']} ({location['type']})",
                                icon=folium.Icon(color='green', icon='info-sign'),
                                tooltip=location['name']
                            ).add_to(safety_map)
                    
                    # Display the map
                    folium_static(safety_map)
                
                # Rest of the destination selection and route display
                if support_locations and len(support_locations) > 0:
                    # Add location selector
                    st.markdown("### 🎯 Select Destination")
                    destination_options = [f"{loc['name']} ({loc['type']})" for loc in support_locations]
                    selected_index = st.selectbox(
                        "Choose a destination",
                        range(len(destination_options)),
                        format_func=lambda x: destination_options[x]
                    )
                    
                    selected_location = support_locations[selected_index]
                    route_info = get_route_to_location(current_location, selected_location)
                    
                    if route_info and 'steps' in route_info:
                        st.markdown("### 🚗 Route Information")
                        st.markdown(f"**Distance:** {route_info['distance']}")
                        st.markdown(f"**Duration:** {route_info['duration']}")
                        
                        st.markdown("### 🚶 Step-by-Step Directions")
                        for i, step in enumerate(route_info['steps']):
                            st.markdown(f"""
                                <div style='background-color: #1e1e1e; padding: 10px; border-radius: 5px; margin: 5px 0;'>
                                    <strong>Step {i+1}:</strong> {step['instruction']}
                                    <br><small>Distance: {step['distance']}</small>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Add progress indicators between steps, but not after the last step
                            if i < len(route_info['steps']) - 1:
                                st.markdown("""
                                    <div class="progress-indicator">
                                        ↓
                                    </div>
                                """, unsafe_allow_html=True)
                        
                        # Add arrival indicator only once at the end
                        st.markdown("""
                            <div class="arrival-indicator" style='background-color: #4CAF50; padding: 10px; border-radius: 5px; margin: 10px 0; text-align: center; color: white;'>
                                🏁 Arrival at Destination
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No support locations found in your area. Please try a different location or refresh the page.")
            
            with col2:
                st.header("🚨 Live Alerts")
                alerts = get_disaster_alerts(current_location)
                
                if alerts:
                    # Group alerts by type
                    alert_types = {
                        'weather': '🌦️',
                        'air_quality': '💨',
                        'earthquake': '🌋',
                        'traffic': '🚗'
                    }
                    
                    for alert in alerts:
                        alert_icon = alert_types.get(alert['type'], '⚠️')
                        
                        if alert['severity'] == 'high':
                            st.markdown(f"""
                                <div style='background-color: #ff4b4b; padding: 15px; border-radius: 10px; margin: 10px 0; color: white;'>
                                    <strong>{alert_icon} {alert['type'].upper()}</strong><br>
                                    {alert['message']}
                                </div>
                            """, unsafe_allow_html=True)
                        elif alert['severity'] == 'medium':
                            st.markdown(f"""
                                <div style='background-color: #ffa500; padding: 15px; border-radius: 10px; margin: 10px 0; color: white;'>
                                    <strong>{alert_icon} {alert['type'].upper()}</strong><br>
                                    {alert['message']}
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                                <div style='background-color: #4CAF50; padding: 15px; border-radius: 10px; margin: 10px 0; color: white;'>
                                    <strong>{alert_icon} {alert['type'].upper()}</strong><br>
                                    {alert['message']}
                                </div>
                            """, unsafe_allow_html=True)
                    
                    # Add auto-refresh functionality
                    st.markdown("""
                        <div style='text-align: center; color: #666; font-size: 12px; margin-top: 20px;'>
                            Alerts auto-refresh every 5 minutes
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.success("No active alerts in your area at this time.")

        with tab2:
            st.header("📊 Risk Analysis")
            
            # Add explanation of the heatmap
            st.markdown("""
                <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                    <h4 style='color: #00ff00; margin: 0;'>How to Read the Risk Heatmap</h4>
                    <ul style='color: white; margin: 10px 0;'>
                        <li>Colors indicate risk levels from green (low) to red (high)</li>
                        <li>Hover over colored areas to see detailed risk information</li>
                        <li>Click on points for additional details about specific risks</li>
                        <li>Consider avoiding red zones during your journey</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            
            # Fetch live data
            current_weather = get_current_weather(current_location)  # Fetch current weather
            weather_alerts = get_weather_alerts(current_location)
            traffic_incidents = get_traffic_incidents(current_location)
            seismic_activity = get_seismic_activity()

            # Check if it is currently raining
            if current_weather and 'weather' in current_weather:
                is_raining = any(condition['main'].lower() == 'rain' for condition in current_weather['weather'])
                rain_status = "It is currently raining." if is_raining else "It is not raining."
                st.markdown(f"<div style='background-color: #4CAF50; padding: 10px; border-radius: 5px; margin: 5px 0;'>"
                            f"<strong>Weather Status:</strong> {rain_status}</div>", unsafe_allow_html=True)

            # Define a function to calculate distance
            def calculate_distance(lat1, lon1, lat2, lon2):
                return geodesic((lat1, lon1), (lat2, lon2)).meters

            # Prepare data for heatmap and filter incidents
            heatmap_data = []
            nearby_incidents = []
            radius = 5000  # 5 km radius for filtering incidents

            # Process weather alerts for rain
            rain_alerts = [alert for alert in weather_alerts if 'rain' in alert['event'].lower()]

            if rain_alerts:
                for alert in rain_alerts:
                    st.markdown(f"<div style='background-color: #ff4b4b; padding: 10px; border-radius: 5px; margin: 5px 0;'>"
                                f"<strong>Weather Alert:</strong> {alert['description']}</div>", unsafe_allow_html=True)

            # Process traffic incidents
            if traffic_incidents:
                for incident in traffic_incidents[:4]:  # Limit to first 4 incidents
                    incident_lat = incident['geometry']['location']['lat']
                    incident_lng = incident['geometry']['location']['lng']
                    distance = calculate_distance(current_location['lat'], current_location['lng'], incident_lat, incident_lng)
                    if distance <= radius:
                        nearby_incidents.append({
                            'type': 'Traffic Incident',
                            'description': incident['name'],
                            'distance': distance,
                            'precautions': "Avoid the area if possible and follow detour signs."
                        })
                        heatmap_data.append({
                            'lat': incident_lat,
                            'lng': incident_lng,
                            'intensity': 1  # Example intensity
                        })

            if seismic_activity:
                for quake in seismic_activity:
                    quake_lat = quake['geometry']['coordinates'][1]
                    quake_lng = quake['geometry']['coordinates'][0]
                    distance = calculate_distance(current_location['lat'], current_location['lng'], quake_lat, quake_lng)
                    if distance <= radius:
                        nearby_incidents.append({
                            'type': 'Earthquake',
                            'description': f"Magnitude {quake['properties']['mag']} at {quake['properties']['place']}",
                            'distance': distance,
                            'precautions': "Drop, Cover, and Hold On. Stay away from windows."
                        })
                        heatmap_data.append({
                            'lat': quake_lat,
                            'lng': quake_lng,
                            'intensity': 1  # Example intensity
                        })

            # Create heatmap
            heatmap = create_dynamic_heatmap(heatmap_data, current_location)
            folium_static(heatmap)

            # Display nearby incidents with descriptions and precautions
            if nearby_incidents:
                st.subheader("⚠️ Nearby Incidents")
                for incident in nearby_incidents:
                    st.markdown(f"<div style='background-color: #ff4b4b; padding: 10px; border-radius: 5px; margin: 5px 0;'>"
                                f"<strong>{incident['type']}</strong>: {incident['description']}<br>"
                                f"Distance: {incident['distance']:.2f} meters<br>"
                                f"<em>Precautions: {incident['precautions']}</em></div>", unsafe_allow_html=True)
            else:
                st.success("No nearby incidents at this time.")

            # Refresh button for live data
            if st.button("Refresh Data"):
                st.rerun()

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please refresh the page and try again.")

if __name__ == "__main__":
    main() 