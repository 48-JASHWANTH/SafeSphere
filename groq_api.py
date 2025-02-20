import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import streamlit as st
import random
from datetime import datetime

# Remove Groq client initialization
analyzer = SentimentIntensityAnalyzer()

def get_disaster_alerts(location):
    """
    Fetch and analyze disaster alerts for a given location
    """
    try:
        # Simulate disaster alerts for demo purposes
        # In production, integrate with real disaster alert APIs
        sample_alerts = [
            {
                'message': 'Heavy rainfall expected in your area. Possible flooding in low-lying areas.',
                'severity': 'medium',
                'type': 'weather',
                'timestamp': datetime.now().isoformat()
            },
            {
                'message': 'Air quality index is moderate. Sensitive groups should take precautions.',
                'severity': 'low',
                'type': 'air_quality',
                'timestamp': datetime.now().isoformat()
            },
            {
                'message': 'High temperature warning. Stay hydrated and avoid outdoor activities.',
                'severity': 'high',
                'type': 'weather',
                'timestamp': datetime.now().isoformat()
            }
        ]
        return sample_alerts
    except Exception as e:
        st.error(f"Error fetching disaster alerts: {str(e)}")
        return []

def analyze_risk_level(location, alerts=None):
    """
    Analyze the risk level for a given location based on current alerts
    Returns: 'low', 'medium', or 'high'
    """
    try:
        if alerts is None:
            alerts = get_disaster_alerts(location)
        
        # Count alerts by severity
        severity_counts = {
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for alert in alerts:
            severity_counts[alert['severity']] += 1
        
        # Calculate risk level
        if severity_counts['high'] > 0:
            return 'high'
        elif severity_counts['medium'] > 0:
            return 'medium'
        else:
            return 'low'
    except Exception as e:
        st.error(f"Error analyzing risk level: {str(e)}")
        return 'low'

def get_risk_insights(location):
    """
    Generate detailed risk insights for a location
    """
    try:
        # Simulate risk insights
        risk_factors = [
            {
                'type': 'Weather',
                'severity': 'medium',
                'description': 'Heavy rainfall expected in the next 6 hours',
                'safety_tips': [
                    'Avoid flood-prone areas',
                    'Keep emergency supplies ready',
                    'Monitor local weather updates'
                ]
            },
            {
                'type': 'Traffic',
                'severity': 'high',
                'description': 'Major road construction on main routes',
                'safety_tips': [
                    'Use alternative routes',
                    'Allow extra travel time',
                    'Follow traffic updates'
                ]
            },
            {
                'type': 'Health',
                'severity': 'low',
                'description': 'Moderate air quality conditions',
                'safety_tips': [
                    'Sensitive groups should limit outdoor activities',
                    'Keep windows closed during peak hours',
                    'Use air purifiers if available'
                ]
            }
        ]

        recommended_actions = [
            'Stay updated with local emergency broadcasts',
            'Keep emergency contacts readily available',
            'Plan alternative routes for essential travel',
            'Ensure emergency kit is well-stocked'
        ]

        return {
            'risk_level': analyze_risk_level(location),
            'risk_factors': risk_factors,
            'recommended_actions': recommended_actions,
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        st.error(f"Error generating risk insights: {str(e)}")
        return {
            'risk_level': 'low',
            'risk_factors': [],
            'recommended_actions': ['System is currently unable to provide detailed insights'],
            'last_updated': datetime.now().isoformat()
        }

def analyze_community_update(text):
    """
    Analyze community updates using sentiment analysis
    """
    try:
        sentiment = analyzer.polarity_scores(text)
        return {
            'credible': sentiment['compound'] > -0.5,  # Filter out extremely negative/suspicious posts
            'sentiment': sentiment
        }
    except Exception as e:
        st.error(f"Error analyzing text: {str(e)}")
        return {'credible': False, 'sentiment': None}

def get_risk_data(location):
    """
    Generate risk data for heatmap visualization
    Returns: List of [lat, lng, weight] for heatmap
    """
    try:
        # Simulate risk data points around the given location
        risk_points = []
        lat, lng = location['lat'], location['lng']
        
        # Generate 20 random points around the location
        for _ in range(20):
            # Random offset between -0.02 and 0.02 degrees
            lat_offset = random.uniform(-0.02, 0.02)
            lng_offset = random.uniform(-0.02, 0.02)
            
            # Random weight between 0 and 1
            weight = random.uniform(0, 1)
            
            risk_points.append([lat + lat_offset, lng + lng_offset, weight])
        
        return risk_points
    except Exception as e:
        st.error(f"Error generating risk data: {str(e)}")
        return [] 