import threading
import signal
import sys
import requests
import os

from data_puller import run as run_data_puller
from webserver import run as run_webserver

def shutdown_flask_app():
    try:
        requests.post('http://127.0.0.1:3000/shutdown')
    except requests.exceptions.RequestException as e:
        print(f"Error shutting down Flask server: {e}")

def main():

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

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    run_data_puller()
    # Wait for both threads to complete
    #data_puller_thread.join()
    #flask_app_thread.join()

if __name__ == "__main__":
    main()