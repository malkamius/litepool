import threading
import signal
import sys
import requests
import os
from shared.mylogging import logging
import logging as baselogging

from data_puller import run as run_data_puller
from webserver import run as run_webserver

def shutdown_flask_app():
    try:
        requests.post('http://127.0.0.1:3000/shutdown')
    except requests.exceptions.RequestException as e:
        print(f"Error shutting down Flask server: {e}")

def main():
    logger = logging.get_logger(loglevel=baselogging.DEBUG, loggername=__name__)
    try:
        app_path = os.path.dirname(os.path.abspath(__file__))
        data_folder = os.path.join(app_path, "..\\data")
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        
        # Start the Flask app in a separate thread
        flask_app_thread = threading.Thread(target=run_webserver)
        flask_app_thread.daemon = True
        flask_app_thread.start()
        
        def signal_handler(sig, frame):
            print('Exiting main script...')
            shutdown_flask_app()
            sys.exit(0)

        run_data_puller()
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    except KeyboardInterrupt:
        logger.error("Program interrupted.")
    finally:
        logger.info("Exiting the program...")
        
if __name__ == "__main__":
    main()