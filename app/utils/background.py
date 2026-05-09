import threading
import time
import logging

# Configure basic logging to see the background tasks in the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_async(func, *args, **kwargs):
    """
    Runs a function in a separate thread so it doesn't block the main request.
    """
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.daemon = True # Ensures thread dies when the main process stops
    thread.start()

def send_assignment_notification(employee_email, lead_name):
    """
    Mock background task for sending an email.
    In a real app, this would use a library like Flask-Mail.
    """
    logger.info(f" [ASYNC] Preparing to send email to {employee_email}...")
    
    # Simulate a slow process (like connecting to an SMTP server)
    time.sleep(3) 
    
    logger.info(f" [ASYNC] SUCCESS: Notification sent to {employee_email} regarding lead '{lead_name}'")

def log_system_event(event_type, details):
    """
    Background task for logging events to a separate audit file or service.
    """
    logger.info(f" [ASYNC EVENT] {event_type.upper()}: {details}")
