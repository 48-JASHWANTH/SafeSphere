# API Configuration
API_TIMEOUT = 10  # seconds
CACHE_TTL = 5  # minutes

# Map Settings
DEFAULT_LAT = 40.7128
DEFAULT_LNG = -74.0060
DEFAULT_ZOOM = 13

# Risk Levels
RISK_LEVELS = {
    'low': {'color': '#4CAF50', 'score': 1},
    'medium': {'color': '#ffa500', 'score': 2},
    'high': {'color': '#ff4b4b', 'score': 3}
}

# Emergency Types
EMERGENCY_TYPES = [
    "Medical",
    "Fire",
    "Police",
    "Natural Disaster",
    "Other"
] 