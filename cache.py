import streamlit as st
from datetime import datetime, timedelta

class Cache:
    @staticmethod
    def get_cached_data(key, ttl_minutes=5):
        """Get cached data if it exists and is not expired"""
        if key not in st.session_state:
            return None
            
        cached = st.session_state[key]
        if not cached or 'timestamp' not in cached:
            return None
            
        # Check if cache is expired
        age = datetime.now() - cached['timestamp']
        if age > timedelta(minutes=ttl_minutes):
            return None
            
        return cached['data']
    
    @staticmethod
    def set_cached_data(key, data):
        """Cache data with timestamp"""
        st.session_state[key] = {
            'data': data,
            'timestamp': datetime.now()
        } 