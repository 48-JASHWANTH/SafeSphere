from datetime import datetime
import random

def get_disaster_alerts(location):
    """Generate simulated disaster alerts"""
    alerts = []
    
    # Simulate some alerts based on location
    possible_alerts = [
        {
            'message': 'Heavy rainfall expected in your area',
            'severity': 'medium',
            'type': 'weather'
        },
        {
            'message': 'High temperature warning',
            'severity': 'high',
            'type': 'weather'
        },
        {
            'message': 'Air quality alert',
            'severity': 'low',
            'type': 'environmental'
        }
    ]
    
    # Randomly select 1-2 alerts
    num_alerts = random.randint(1, 2)
    selected_alerts = random.sample(possible_alerts, num_alerts)
    
    for alert in selected_alerts:
        alerts.append({
            **alert,
            'timestamp': datetime.now().isoformat()
        })
    
    return alerts

def analyze_risk_level(alerts):
    """Analyze risk level based on alerts"""
    if not alerts:
        return 'low'
        
    severity_scores = {
        'high': 3,
        'medium': 2,
        'low': 1
    }
    
    total_score = sum(severity_scores[alert['severity']] for alert in alerts)
    avg_score = total_score / len(alerts)
    
    if avg_score >= 2.5:
        return 'high'
    elif avg_score >= 1.5:
        return 'medium'
    return 'low' 