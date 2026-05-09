import threading
import time
import logging

# Configure basic logging to see the background tasks in the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_async(func, *args, **kwargs):
    # Fire and forget thread runner
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.daemon = True 
    thread.start()

def send_assignment_notification(employee_email, lead_name):
    # This simulates a slow email sending process using a simple sleep
    logger.info(f" [ASYNC] Preparing to send email to {employee_email}...")
    
    time.sleep(3) 
    
    logger.info(f" [ASYNC] SUCCESS: Notification sent to {employee_email} regarding lead '{lead_name}'")

def log_system_event(event_type, details):
    # Simple async logger for system events
    logger.info(f" [ASYNC EVENT] {event_type.upper()}: {details}")
