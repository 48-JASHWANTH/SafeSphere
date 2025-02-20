import os
import logging
import requests
import googlemaps
from datetime import datetime
import streamlit as st
from constants import DEFAULT_LAT, DEFAULT_LNG

logger = logging.getLogger(__name__)

# Initialize Google Maps client if API key exists
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None

def get_nearby_support_locations(location):
    """Get nearby emergency services"""
    if not gmaps:
        # Return mock data if no API key
        return [
            {
                'name': 'Central Hospital',
                'type': 'hospital',
                'lat': location['lat'] + 0.01,
                'lng': location['lng'] + 0.01,
                'address': '123 Main St',
                'rating': 4.5
            },
            {
                'name': 'Police Station',
                'type': 'police',
                'lat': location['lat'] - 0.01,
                'lng': location['lng'] - 0.01,
                'address': '456 Safety Ave',
                'rating': 4.0
            }
        ]
    
    try:
        nearby_places = []
        place_types = [
            ('hospital', 'Hospital'),
            ('police', 'Police Station'),
            ('fire_station', 'Fire Station')
        ]

        for place_type, label in place_types:
            results = gmaps.places_nearby(
                location=(location['lat'], location['lng']),
                radius=5000,
                type=place_type
            )
            
            for place in results.get('results', [])[:3]:
                nearby_places.append({
                    'name': place['name'],
                    'type': place_type,
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng'],
                    'address': place.get('vicinity', 'Address not available'),
                    'rating': place.get('rating', 'N/A')
                })
                
        return nearby_places
    except Exception as e:
        logger.error(f"Error getting nearby locations: {e}")
        return []

def get_weather(location):
    """Get weather data"""
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return {
                'temperature': 20,
                'humidity': 65,
                'description': 'Weather data unavailable',
                'wind_speed': 0
            }
            
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={location['lat']}&lon={location['lng']}&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'description': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed']
            }
    except Exception as e:
        logger.warning(f"Weather data unavailable: {e}")
        
    return {
        'temperature': 20,
        'humidity': 65,
        'description': 'Weather data unavailable',
        'wind_speed': 0
    } 