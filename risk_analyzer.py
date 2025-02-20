import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from geopy.distance import geodesic
import os

class RiskAnalyzer:
    def __init__(self):
        self.weather_api_key = os.getenv('OPENWEATHER_API_KEY')
        self.crime_api_key = os.getenv('CRIME_DATA_API_KEY')  # If available
        self.historical_data = self.load_historical_data()
        
    def load_historical_data(self):
        """Load or initialize historical risk data"""
        try:
            # In production, this would load from a database
            return {
                'natural_disasters': [],
                'crime_incidents': [],
                'traffic_accidents': [],
                'weather_events': []
            }
        except Exception:
            return None

    def get_weather_risks(self, location):
        """Get detailed weather risks including forecasts"""
        try:
            # Current weather
            current_url = f"http://api.openweathermap.org/data/2.5/weather?lat={location['lat']}&lon={location['lng']}&appid={self.weather_api_key}&units=metric"
            current_response = requests.get(current_url)
            current_data = current_response.json()
            
            # Forecast
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={location['lat']}&lon={location['lng']}&appid={self.weather_api_key}&units=metric"
            forecast_response = requests.get(forecast_url)
            forecast_data = forecast_response.json()
            
            weather_risks = []
            
            # Analyze current conditions
            if current_data:
                temp = current_data['main']['temp']
                wind_speed = current_data['wind']['speed']
                weather_id = current_data['weather'][0]['id']
                
                # Temperature risks
                if temp > 35:
                    weather_risks.append({
                        'type': 'Extreme Heat',
                        'severity': 'high',
                        'description': f'Temperature of {temp}°C poses heat stress risk',
                        'recommendations': [
                            'Stay hydrated',
                            'Avoid outdoor activities',
                            'Find air-conditioned spaces'
                        ]
                    })
                elif temp < 0:
                    weather_risks.append({
                        'type': 'Freezing Conditions',
                        'severity': 'medium',
                        'description': f'Temperature below freezing at {temp}°C',
                        'recommendations': [
                            'Wear warm clothing',
                            'Watch for ice on roads',
                            'Protect water pipes'
                        ]
                    })
                
                # Wind risks
                if wind_speed > 10:
                    weather_risks.append({
                        'type': 'Strong Winds',
                        'severity': 'medium',
                        'description': f'Wind speeds of {wind_speed} m/s',
                        'recommendations': [
                            'Secure loose objects',
                            'Be cautious when driving',
                            'Stay away from trees'
                        ]
                    })
                
                # Severe weather conditions
                if weather_id < 600:  # Rain and thunderstorms
                    weather_risks.append({
                        'type': 'Precipitation',
                        'severity': 'medium',
                        'description': current_data['weather'][0]['description'],
                        'recommendations': [
                            'Carry rain protection',
                            'Watch for flooding',
                            'Drive carefully'
                        ]
                    })
            
            # Analyze forecast for upcoming risks
            if forecast_data and 'list' in forecast_data:
                for forecast in forecast_data['list'][:8]:  # Next 24 hours
                    if forecast['weather'][0]['id'] < 600:  # Precipitation expected
                        weather_risks.append({
                            'type': 'Upcoming Weather',
                            'severity': 'low',
                            'description': f"Expected {forecast['weather'][0]['description']} in {forecast['dt_txt']}",
                            'recommendations': [
                                'Plan indoor activities',
                                'Prepare rain gear',
                                'Check weather updates'
                            ]
                        })
            
            return weather_risks
        except Exception as e:
            print(f"Error fetching weather risks: {str(e)}")
            return []

    def get_traffic_risks(self, location):
        """Analyze traffic conditions and accident history"""
        try:
            # This would integrate with traffic APIs in production
            traffic_risks = []
            
            # Simulate traffic analysis
            rush_hour = self.is_rush_hour()
            if rush_hour:
                traffic_risks.append({
                    'type': 'Heavy Traffic',
                    'severity': 'medium',
                    'description': 'Rush hour congestion expected',
                    'recommendations': [
                        'Allow extra travel time',
                        'Consider alternative routes',
                        'Use public transportation if available'
                    ]
                })
            
            return traffic_risks
        except Exception:
            return []

    def is_rush_hour(self):
        """Check if current time is during rush hour"""
        current_time = datetime.now().time()
        morning_rush = time(7, 0) <= current_time <= time(10, 0)
        evening_rush = time(16, 0) <= current_time <= time(19, 0)
        return morning_rush or evening_rush

    def analyze_location_risks(self, location):
        """Comprehensive risk analysis for a location"""
        all_risks = []
        
        # Get weather risks
        weather_risks = self.get_weather_risks(location)
        all_risks.extend(weather_risks)
        
        # Get traffic risks
        traffic_risks = self.get_traffic_risks(location)
        all_risks.extend(traffic_risks)
        
        # Calculate overall risk level
        risk_scores = {
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        total_score = sum(risk_scores.get(risk['severity'], 0) for risk in all_risks)
        num_risks = len(all_risks) or 1
        
        average_score = total_score / num_risks
        
        overall_risk = 'low'
        if average_score >= 2.5:
            overall_risk = 'high'
        elif average_score >= 1.5:
            overall_risk = 'medium'
        
        return {
            'overall_risk': overall_risk,
            'risks': all_risks,
            'timestamp': datetime.now().isoformat(),
            'location': location
        }

    def get_safety_recommendations(self, risks):
        """Generate safety recommendations based on identified risks"""
        recommendations = []
        
        for risk in risks:
            if 'recommendations' in risk:
                recommendations.extend(risk['recommendations'])
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(recommendations)) 