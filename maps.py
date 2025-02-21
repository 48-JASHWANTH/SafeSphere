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

def get_user_location():
    """
    Get user's location using IP geolocation as fallback
    """
    try:
        # First try IP-based geolocation
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
        st.warning(f"Could not get precise location: {str(e)}")
        # Fallback to New York coordinates
        return {
            'lat': 40.7128,
            'lng': -74.0060,
            'city': 'New York',
            'region': 'New York',
            'country': 'United States'
        }

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

def get_precise_location():
    """
    Get precise user location using multiple methods
    """
    try:
        # Check if we already have browser location in session state
        if st.session_state.get('user_location'):
            return st.session_state.user_location

        # Try Google Maps Geolocation API
        if gmaps:
            try:
                response = gmaps.geolocate()
                if response and 'location' in response:
                    location = response['location']
                    accuracy = min(response.get('accuracy', 1000), 1000)
                    
                    # Get detailed address using reverse geocoding
                    reverse_geocode = gmaps.reverse_geocode((location['lat'], location['lng']))
                    
                    if reverse_geocode and len(reverse_geocode) > 0:
                        address_components = reverse_geocode[0]['address_components']
                        formatted_address = reverse_geocode[0].get('formatted_address', '')
                        
                        return {
                            'lat': location['lat'],
                            'lng': location['lng'],
                            'accuracy': accuracy,
                            'city': next((comp['long_name'] for comp in address_components 
                                        if 'locality' in comp['types']), 'Unknown'),
                            'region': next((comp['long_name'] for comp in address_components 
                                          if 'administrative_area_level_1' in comp['types']), 'Unknown'),
                            'country': next((comp['long_name'] for comp in address_components 
                                          if 'country' in comp['types']), 'Unknown'),
                            'postal_code': next((comp['long_name'] for comp in address_components 
                                              if 'postal_code' in comp['types']), 'Unknown'),
                            'formatted_address': formatted_address,
                            'timestamp': time.time(),
                            'source': 'google_maps'
                        }
            except Exception as e:
                st.warning(f"Google Maps geolocation failed: {str(e)}")

        # Fallback to IP-based geolocation
        try:
            response = requests.get('https://ipapi.co/json/')
            if response.status_code == 200:
                data = response.json()
                return {
                    'lat': float(data['latitude']),
                    'lng': float(data['longitude']),
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('region', 'Unknown'),
                    'country': data.get('country_name', 'Unknown'),
                    'postal_code': data.get('postal', 'Unknown'),
                    'accuracy': 1000,
                    'formatted_address': f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country_name', '')}",
                    'timestamp': time.time(),
                    'source': 'ip_geolocation'
                }
        except Exception as e:
            st.warning(f"IP geolocation failed: {str(e)}")

        return None

    except Exception as e:
        st.error(f"Error getting location: {str(e)}")
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