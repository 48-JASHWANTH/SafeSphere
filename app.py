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
from streamlit_folium import folium_static
from datetime import datetime, time
import pandas as pd
from groq_api import get_disaster_alerts, analyze_risk_level, get_risk_insights
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
    current_time = time_module.time()
    
    # Check if enough time has passed since last update
    if (current_time - st.session_state.last_location_check) < st.session_state.location_update_interval:
        return st.session_state.user_location
    
    # Get precise location
    new_location = get_precise_location()
    if not new_location:
        new_location = get_location()  # Fallback to IP-based location
    
    if new_location:
        # Check if location has changed significantly
        if track_location_changes(st.session_state.user_location, new_location):
            # Calculate movement metrics if we have previous location
            if st.session_state.user_location:
                metrics = calculate_movement_metrics(
                    st.session_state.user_location,
                    new_location
                )
                if metrics:
                    st.session_state.movement_metrics = metrics
            
            # Update location history
            st.session_state.location_history.append({
                'location': new_location,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 100 locations
            if len(st.session_state.location_history) > 100:
                st.session_state.location_history = st.session_state.location_history[-100:]
            
            st.session_state.user_location = new_location
    
    st.session_state.last_location_check = current_time
    return st.session_state.user_location

def main():
    try:
        # Sidebar
        st.sidebar.title("🚨 Safety Dashboard")  # Updated title
        
        # Location tracking settings
        st.sidebar.markdown("---")

        # Display current location and tracking info
        current_location = update_location()
        if current_location:
            st.sidebar.markdown(f"📍 **Current Location:**")
            st.sidebar.markdown(f"City: {current_location['city']}")
            st.sidebar.markdown(f"Region: {current_location['region']}")
            st.sidebar.markdown(f"Accuracy: ±{current_location.get('accuracy', 'N/A')}m")

        # Manual location override
        with st.sidebar.expander("Manual Location Override"):
            new_lat = st.number_input("Latitude", value=current_location['lat'], format="%.6f")
            new_lng = st.number_input("Longitude", value=current_location['lng'], format="%.6f")
            if st.button("Update Location"):
                st.session_state.user_location = {
                    'lat': new_lat,
                    'lng': new_lng,
                    'city': current_location['city'],
                    'region': current_location['region'],
                    'country': current_location['country'],
                    'timestamp': time_module.time()
                }
                st.rerun()

        # Display weather information
        weather = get_weather(current_location)
        if weather:
            st.sidebar.markdown("---")
            st.sidebar.markdown("🌤️ **Weather Conditions:**")
            st.sidebar.markdown(f"Temperature: {weather['temperature']}°C")
            st.sidebar.markdown(f"Humidity: {weather['humidity']}%")
            st.sidebar.markdown(f"Conditions: {weather['description'].title()}")
            st.sidebar.markdown(f"Wind Speed: {weather['wind_speed']} m/s")

        # Main content area with tabs - removed Emergency tab
        tab1, tab2 = st.tabs(["📍 Live Map", "📊 Risk Analysis"])
        
        with tab1:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.header("🗺 Safety Map")
                
                # Get support locations
                support_locations = get_nearby_support_locations(current_location)
                
                # Add location selector
                st.markdown("### 🎯 Select Destination")
                destination_options = [f"{loc['name']} ({loc['type']})" for loc in support_locations]
                selected_index = st.selectbox(
                    "Choose a destination",
                    range(len(destination_options)),
                    format_func=lambda x: destination_options[x]
                )
                
                selected_destination = support_locations[selected_index]
                st.session_state.selected_destination = selected_destination
                
                # Get and display route
                if st.session_state.selected_destination:
                    route_info = get_route_to_location(
                        current_location,
                        st.session_state.selected_destination
                    )
                    st.session_state.route_info = route_info
                    
                    if route_info:
                        st.markdown("### 🚗 Route Information")
                        st.markdown(f"**Distance:** {route_info['distance']}")
                        st.markdown(f"**Duration:** {route_info['duration']}")
                        
                        # Display route map
                        route_map = create_route_map(
                            current_location,
                            st.session_state.selected_destination,
                            route_info
                        )
                        folium_static(route_map)
                        
                        # Display route steps
                        with st.expander("📝 Route Steps", expanded=True):
                            st.markdown("""
                                <style>
                                .route-step {
                                    background-color: #1e1e1e;  /* Dark background */
                                    padding: 15px;
                                    border-radius: 10px;
                                    margin: 10px 0;
                                    border-left: 4px solid #00ff00;  /* Bright green border */
                                    color: white;  /* White text */
                                }
                                .step-number {
                                    color: #00ff00;  /* Bright green text */
                                    font-size: 18px;
                                    font-weight: bold;
                                }
                                .step-distance {
                                    color: #cccccc;  /* Light grey text */
                                    font-size: 14px;
                                    float: right;
                                }
                                .step-duration {
                                    color: #cccccc;  /* Light grey text */
                                    font-size: 14px;
                                    margin-left: 15px;
                                    float: right;
                                }
                                .step-instruction {
                                    margin-top: 5px;
                                    font-size: 16px;
                                    color: white;  /* White text */
                                }
                                .journey-summary {
                                    background-color: #2d2d2d;  /* Darker grey background */
                                    padding: 15px;
                                    border-radius: 10px;
                                    margin-bottom: 20px;
                                    color: white;  /* White text */
                                }
                                .journey-summary h4 {
                                    color: #00ff00;  /* Bright green text */
                                    margin: 0;
                                }
                                .journey-summary p {
                                    margin: 10px 0 0 0;
                                    color: white;  /* White text */
                                }
                                .progress-indicator {
                                    text-align: center;
                                    color: #00ff00;  /* Bright green text */
                                    margin: 5px 0;
                                }
                                .arrival-indicator {
                                    background-color: #006400;  /* Dark green */
                                    color: white;
                                    padding: 15px;
                                    border-radius: 10px;
                                    margin-top: 20px;
                                    text-align: center;
                                }
                                </style>
                            """, unsafe_allow_html=True)

                            total_distance = route_info['distance']
                            total_duration = route_info['duration']
                            st.markdown(f"""
                                <div class="journey-summary">
                                    <h4>Journey Summary</h4>
                                    <p>
                                        🛣️ Total Distance: <strong>{total_distance}</strong> &nbsp;&nbsp;|&nbsp;&nbsp;
                                        ⏱️ Total Duration: <strong>{total_duration}</strong>
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)

                            for i, step in enumerate(route_info['steps'], 1):
                                # Clean up HTML instructions
                                instruction = step['instruction'].replace('<b>', '<strong>').replace('</b>', '</strong>')
                                instruction = instruction.replace('<div style="font-size:0.9em">', '').replace('</div>', '')

                                st.markdown(f"""
                                    <div class="route-step">
                                        <span class="step-number">Step {i}</span>
                                        <span class="step-duration">⏱️ {step['duration']}</span>
                                        <span class="step-distance">🛣️ {step['distance']}</span>
                                        <div class="step-instruction">{instruction}</div>
                                    </div>
                                """, unsafe_allow_html=True)

                                # Add progress indicators between steps
                                if i < len(route_info['steps']):
                                    st.markdown("""
                                        <div class="progress-indicator">
                                            ↓
                                        </div>
                                    """, unsafe_allow_html=True)

                            # Add arrival indicator at the end
                            st.markdown("""
                                <div class="arrival-indicator">
                                    🏁 Arrival at Destination
                                </div>
                            """, unsafe_allow_html=True)
            
            with col2:
                st.header("🚨 Live Alerts")
                alerts = get_disaster_alerts(current_location)
                
                for alert in alerts:
                    if alert['severity'] == 'high':
                        st.error(f"⚠️ {alert['message']}")
                    elif alert['severity'] == 'medium':
                        st.warning(f"⚠️ {alert['message']}")
                    else:
                        st.info(f"ℹ️ {alert['message']}")

        with tab2:
            st.header("📊 Risk Analysis")
            
            # Display risk heatmap
            risk_data = generate_heatmap_data(current_location)
            risk_map = create_risk_heatmap(current_location, risk_data)
            folium_static(risk_map)
            
            # Display risk metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Risk Level", st.session_state.risk_level.upper())
            with col2:
                st.metric("Active Alerts", len(alerts))
            with col3:
                st.metric("Nearby Safe Zones", len(support_locations))
            
            # Display detailed risk insights
            display_risk_insights(current_location)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please refresh the page and try again.")

if __name__ == "__main__":
    main() 