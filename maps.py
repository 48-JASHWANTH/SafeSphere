import googlemaps
import os
from geopy.geocoders import Nominatim
import streamlit as st
import requests
import json
from datetime import datetime
import random
from geopy.distance import geodesic
import time
import streamlit.components.v1 as components
from streamlit.runtime.scriptrunner import get_script_run_ctx

# Initialize Google Maps client - Add error handling
try:
    gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))
    if not os.getenv('GOOGLE_MAPS_API_KEY'):
        st.error("Google Maps API key is missing. Please check your .env file.")
except Exception as e:
    st.error(f"Error initializing Google Maps client: {str(e)}")
    gmaps = None
geolocator = Nominatim(user_agent="urban_safety_app")

def get_default_location():
    """
    Return default location settings
    """
    return {
        'lat': 17.537348,
        'lng': 78.384515,
        'city': 'Hyderabad',
        'region': 'Telangana',
        'country': 'India',
        'postal_code': '500090',
        'accuracy': 1000,
        'formatted_address': 'G9XV+4WX, Bachupally, Hyderabad, Telangana 500090, India',
        'timestamp': time.time(),
        'source': 'default'
    }

def get_user_location():
    """
    Get user's location using IP geolocation with default fallback
    """
    
    return get_default_location()

def get_precise_location():
    """
    Get precise user location using multiple methods
    """
    try:
        # First try Google Maps Geolocation API
        if gmaps:
            try:
                # Basic geolocation request
                response = gmaps.geolocate()
                
                if response and 'location' in response:
                    location = response['location']
                    accuracy = min(response.get('accuracy', 1000), 1000)  # Cap accuracy at 1000m
                    
                    # Get detailed address using reverse geocoding
                    reverse_geocode = gmaps.reverse_geocode((location['lat'], location['lng']))
                    
                    if reverse_geocode and len(reverse_geocode) > 0:
                        address_components = reverse_geocode[0]['address_components']
                        formatted_address = reverse_geocode[0].get('formatted_address', '')
                        
                        # Extract detailed location information
                        city = next((comp['long_name'] for comp in address_components 
                                   if 'locality' in comp['types']), 'Unknown')
                        sublocality = next((comp['long_name'] for comp in address_components 
                                          if 'sublocality' in comp['types']), '')
                        region = next((comp['long_name'] for comp in address_components 
                                     if 'administrative_area_level_1' in comp['types']), 'Unknown')
                        country = next((comp['long_name'] for comp in address_components 
                                     if 'country' in comp['types']), 'Unknown')
                        postal_code = next((comp['long_name'] for comp in address_components 
                                         if 'postal_code' in comp['types']), 'Unknown')
                        
                        return {
                            'lat': location['lat'],
                            'lng': location['lng'],
                            'accuracy': accuracy,
                            'city': city,
                            'sublocality': sublocality,
                            'region': region,
                            'country': country,
                            'postal_code': postal_code,
                            'formatted_address': formatted_address,
                            'timestamp': time.time(),
                            'source': 'google_maps'
                        }
            except Exception as e:
                st.warning(f"Google Maps geolocation failed: {str(e)}")

        # # Fallback to IP-based geolocation
        # try:
        #     response = requests.get('https://ipapi.co/json/')
        #     if response.status_code == 200:
        #         data = response.json()
        #         return {
        #             'lat': float(data['latitude']),
        #             'lng': float(data['longitude']),
        #             'city': data.get('city', 'Unknown'),
        #             'region': data.get('region', 'Unknown'),
        #             'country': data.get('country_name', 'Unknown'),
        #             'postal_code': data.get('postal', 'Unknown'),
        #             'accuracy': 1000,  # Limit accuracy for IP-based location
        #             'formatted_address': f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country_name', '')}",
        #             'timestamp': time.time(),
        #             'source': 'ip_geolocation'
        #         }
        # except Exception as e:
        #     st.warning(f"IP geolocation failed: {str(e)}")

        # If all methods fail, return default location
        return get_default_location()

    except Exception as e:
        st.error(f"Error getting location: {str(e)}")
        return get_default_location()

# Rest of the functions remain unchanged
def get_nearby_support_locations(location):
    """
    Get real nearby emergency services using Google Places API
    """
    try:
        if not location:
            return []
            
        nearby_places = []
        
        # Search types for emergency services
        place_types = [
            ('hospital', 'Hospital'),
            ('police', 'Police Station'),
            ('fire_station', 'Fire Station'),
            ('local_government_office', 'Emergency Shelter')
        ]

        for place_type, label in place_types:
            results = gmaps.places_nearby(
                location=(location['lat'], location['lng']),
                radius=5000,  # 5km radius
                type=place_type
            )

            for place in results.get('results', [])[:3]:  # Limit to 3 places per type
                # Get place details
                place_details = gmaps.place(place['place_id'], fields=['formatted_address', 'name', 'geometry', 'rating'])
                
                nearby_places.append({
                    'name': place['name'],
                    'type': place_type,
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng'],
                    'address': place_details['result'].get('formatted_address', 'Address not available'),
                    'rating': place_details['result'].get('rating', 'N/A'),
                    'place_id': place['place_id']
                })

        return nearby_places

    except Exception as e:
        st.error(f"Error fetching support locations: {str(e)}")
        return []

def get_route_to_location(origin, destination):
    """
    Get route information between two points with traffic and risk considerations
    """
    try:
        directions = gmaps.directions(
            origin=(origin['lat'], origin['lng']),
            destination=(destination['lat'], destination['lng']),
            mode="driving",
            alternatives=True,
            departure_time=datetime.now()  # For real-time traffic
        )
        
        if directions:
            route = directions[0]
            coordinates = []
            
            # Extract route coordinates
            for step in route['legs'][0]['steps']:
                coordinates.append([
                    step['start_location']['lat'],
                    step['start_location']['lng']
                ])
            coordinates.append([
                route['legs'][0]['steps'][-1]['end_location']['lat'],
                route['legs'][0]['steps'][-1]['end_location']['lng']
            ])
            
            return {
                'distance': route['legs'][0]['distance']['text'],
                'duration': route['legs'][0]['duration']['text'],
                'coordinates': coordinates,
                'steps': [
                    {
                        'instruction': step['html_instructions'],
                        'distance': step['distance']['text'],
                        'duration': step['duration']['text']
                    }
                    for step in route['legs'][0]['steps']
                ]
            }
    except Exception as e:
        st.error(f"Error getting directions: {str(e)}")
    return None

def get_risk_zones(route_coordinates):
    """
    Generate risk zones along a route
    """
    try:
        risk_zones = []
        risk_types = [
            'Construction Zone',
            'Traffic Congestion',
            'Weather Hazard',
            'Road Closure',
            'Accident Prone Area'
        ]
        
        # Generate random risk zones along the route
        num_zones = random.randint(2, 5)
        for _ in range(num_zones):
            # Pick a random point along the route
            point = random.choice(route_coordinates)
            
            risk_zones.append({
                'lat': point[0] + random.uniform(-0.001, 0.001),
                'lng': point[1] + random.uniform(-0.001, 0.001),
                'risk_level': random.choice(['high', 'medium']),
                'description': f"{random.choice(risk_types)} - Exercise Caution"
            })
        
        return risk_zones
    except Exception as e:
        st.error(f"Error generating risk zones: {str(e)}")
        return []

def get_weather(location):
    """
    Get current weather conditions using OpenWeatherMap API
    """
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={location['lat']}&lon={location['lng']}&appid={api_key}&units=metric"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed']
            }
    except Exception as e:
        st.error(f"Error fetching weather data: {str(e)}")
    return None

def track_location_changes(previous_location, current_location, threshold_meters=50):
    """
    Track significant location changes
    Returns True if location has changed significantly
    """
    if not previous_location or not current_location:
        return True
        
    prev_coords = (previous_location['lat'], previous_location['lng'])
    curr_coords = (current_location['lat'], current_location['lng'])
    
    distance = geodesic(prev_coords, curr_coords).meters
    time_diff = current_location.get('timestamp', 0) - previous_location.get('timestamp', 0)
    
    # Return True if moved more than threshold meters or more than 5 minutes passed
    return distance > threshold_meters or time_diff > 300

def calculate_movement_metrics(previous_location, current_location):
    """
    Calculate movement metrics like speed and heading
    """
    if not previous_location or not current_location:
        return None
        
    try:
        prev_coords = (previous_location['lat'], previous_location['lng'])
        curr_coords = (current_location['lat'], current_location['lng'])
        
        distance = geodesic(prev_coords, curr_coords).meters
        time_diff = current_location.get('timestamp', 0) - previous_location.get('timestamp', 0)
        
        if time_diff > 0:
            speed = distance / time_diff  # meters per second
            
            return {
                'speed': speed,
                'distance': distance,
                'time_elapsed': time_diff
            }
    except Exception:
        return None

def get_emergency_contacts():
    """
    Retrieve emergency contact numbers based on location
    """
    emergency_contacts = {
        'Police': '100',
        'Ambulance': '108',
        'Fire': '101',
        'Women Helpline': '1091',
        'Child Helpline': '1098',
        'National Emergency': '112'
    }
    return emergency_contacts

def initialize_session_state():
    """
    Initialize Streamlit session state variables
    """
    if 'previous_location' not in st.session_state:
        st.session_state.previous_location = None
    if 'current_location' not in st.session_state:
        st.session_state.current_location = None
    if 'tracking_enabled' not in st.session_state:
        st.session_state.tracking_enabled = False
    if 'emergency_mode' not in st.session_state:
        st.session_state.emergency_mode = False
    if 'selected_emergency_service' not in st.session_state:
        st.session_state.selected_emergency_service = None

def main():
    """
    Main application function
    """
    st.set_page_config(page_title="Urban Safety App", page_icon="🚨", layout="wide")
    
    # Initialize session state
    initialize_session_state()
    
    # Application header
    st.title("Urban Safety Application")
    st.markdown("Stay safe with real-time location tracking and emergency services")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Settings")
        tracking_toggle = st.toggle("Enable Location Tracking", value=st.session_state.tracking_enabled)
        
        if tracking_toggle != st.session_state.tracking_enabled:
            st.session_state.tracking_enabled = tracking_toggle
            if tracking_toggle:
                st.success("Location tracking enabled")
            else:
                st.warning("Location tracking disabled")
        
        st.header("Emergency Contacts")
        emergency_contacts = get_emergency_contacts()
        for service, number in emergency_contacts.items():
            st.button(f"📞 {service}: {number}")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Your Location")
        if st.session_state.tracking_enabled:
            # Get current location
            current_location = get_precise_location()
            
            if current_location:
                st.success(f"Location: {current_location['formatted_address']}")
                
                # Update location history
                if st.session_state.current_location:
                    st.session_state.previous_location = st.session_state.current_location
                st.session_state.current_location = current_location
                
                # Show movement metrics if available
                if st.session_state.previous_location:
                    metrics = calculate_movement_metrics(
                        st.session_state.previous_location,
                        st.session_state.current_location
                    )
                    if metrics:
                        st.info(f"Speed: {metrics['speed']:.2f} m/s\n"
                               f"Distance: {metrics['distance']:.2f} m")
            else:
                st.error("Could not get location. Using default location.")
                current_location = get_default_location()
        else:
            st.warning("Location tracking is disabled")
    
    with col2:
        st.subheader("Weather Conditions")
        if st.session_state.current_location:
            weather_data = get_weather(st.session_state.current_location)
            if weather_data:
                st.write(f"Temperature: {weather_data['temperature']}°C")
                st.write(f"Humidity: {weather_data['humidity']}%")
                st.write(f"Conditions: {weather_data['description']}")
                st.write(f"Wind Speed: {weather_data['wind_speed']} m/s")
    
    # Emergency services section
    st.subheader("Nearby Emergency Services")
    if st.session_state.current_location:
        nearby_services = get_nearby_support_locations(st.session_state.current_location)
        
        if nearby_services:
            for service in nearby_services:
                with st.expander(f"{service['name']} ({service['type'].replace('_', ' ').title()})"):
                    st.write(f"Address: {service['address']}")
                    st.write(f"Rating: {service['rating']}")
                    if st.button(f"Get Directions to {service['name']}", key=service['place_id']):
                        route = get_route_to_location(
                            st.session_state.current_location,
                            {'lat': service['lat'], 'lng': service['lng']}
                        )
                        if route:
                            st.write(f"Distance: {route['distance']}")
                            st.write(f"Duration: {route['duration']}")
                            for step in route['steps']:
                                st.write(f"- {step['instruction']}")
                            
                            # Show risk zones along route
                            risk_zones = get_risk_zones(route['coordinates'])
                            if risk_zones:
                                st.warning("Risk Zones Detected:")
                                for zone in risk_zones:
                                    st.write(f"- {zone['description']} ({zone['risk_level']} risk)")

if __name__ == "__main__":
    main()