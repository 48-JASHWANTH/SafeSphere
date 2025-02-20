import streamlit as st
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def handle_api_error(func):
    """Decorator to handle API errors"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API Error in {func.__name__}: {str(e)}")
            return None
    return wrapper

def show_error_message(message, error=None):
    """Display error message to user"""
    if error:
        logger.error(f"{message}: {str(error)}")
    st.error(message) 