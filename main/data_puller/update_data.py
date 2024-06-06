import pandas as pd
import os
import requests
import json
from datetime import datetime, timedelta
import time
import logging as baselogging
from shared.mylogging import logging
from .generate_charts import parse_data_generate_charts
import pandas as pd
# Function to load secrets from the secrets.json file
def load_secrets():
    app_path = os.path.dirname(os.path.abspath(__file__))
    # Define the data and secrets folder paths
    data_folder = os.path.join(app_path, '../data')
    secrets_folder = os.path.join(app_path, '../secrets')
    secrets_file = os.path.join(secrets_folder, 'secrets.json')
    live_secrets_folder = os.path.join(app_path, '../live_secrets')
    live_secrets_file = os.path.join(live_secrets_folder, 'secrets.json')
    if os.path.exists(live_secrets_file):
        with open(live_secrets_file, 'r') as f:
            secrets = json.load(f)
        return secrets
    elif os.path.exists(secrets_file):
        with open(secrets_file, 'r') as f:
            secrets = json.load(f)
        return secrets
    else:
        raise FileNotFoundError(f"Secrets file not found at {secrets_file}")

# Function to check the most recent file and its timestamp
def get_most_recent_file(data_folder):
    date_files = []
    for file in os.listdir(data_folder):
        try:
            # Try to parse the filename as a datetime object
            file_datetime = datetime.strptime(file, '%Y-%m-%d_%H.%M.%S')
            date_files.append((file, file_datetime))
        except ValueError:
            # If parsing fails, skip this file
            continue
    if date_files:
        # Return the most recent file and its timestamp
        return max(date_files, key=lambda x: x[1])
    return None, None

# Function to call the API and save the JSON output
def call_api_and_save(logger, data_folder, api_endpoint, api_key):
    request_url = f'{api_endpoint}{api_key}'
    response = requests.get(request_url)
    if response.status_code == 200:
        data = response.json()
        # Create a new filename with the current date and time
        filename = datetime.now().strftime('%Y-%m-%d_%H.%M.%S') + '.json'
        filepath = os.path.join(data_folder, filename)
        # Save the JSON output to a file
        with open(filepath, 'w') as f:
            json.dump(data, f)
        logger.info(f'Saved JSON data to {filepath}')
    else:
        logger.error(f'Failed to retrieve data from the API, status code: {response.status_code}')
# Function to get all JSON files with datetime names and their modification times
def get_json_files(data_folder):
    date_files = []
    for file in os.listdir(data_folder):
        if file.endswith('.json'):
            try:
                # Try to parse the filename as a datetime object
                file_datetime = datetime.strptime(file, '%Y-%m-%d_%H.%M.%S.json')
                date_files.append((file, file_datetime))
            except ValueError:
                # If parsing fails, skip this file
                continue
    return date_files

# Function to keep only the most recent files for the last 24 hours
def delete_old_files(logger, data_folder):
    date_files = get_json_files(data_folder)
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    
    # Filter files that are within the last 24 hours
    recent_files = [file for file, file_datetime in date_files if file_datetime > cutoff]
    
    # Sort by datetime
    recent_files.sort(key=lambda x: x[1], reverse=True)
    
    # Delete files older than 24 hours
    for file, file_datetime in date_files:
        if file_datetime <= cutoff:
            os.remove(os.path.join(data_folder, file))
            logger.info(f"Deleted old file: {file}")

def main():
    logger = logging.get_logger(loglevel=baselogging.DEBUG, loggername=__name__)
    
    app_path = os.path.dirname(os.path.abspath(__file__))
    # Define the data and secrets folder paths
    data_folder = os.path.join(app_path, '../data')

    try:
        # Load secrets
        secrets = load_secrets()
        
        api_endpoint = secrets.get('api-endpoint')
        api_key = secrets.get('api-key')
        
        if api_key and api_endpoint:
            logger.info("Got API Key from secrets.json")
            # Main loop to check and call the API once a minute
            while True:
                most_recent_file, most_recent_datetime = get_most_recent_file(data_folder)
                if most_recent_datetime is None or datetime.now() - most_recent_datetime > timedelta(minutes=1):
                    logger.info("API Data out of date, retrieving updated JSON")
                    call_api_and_save(logger, data_folder, api_endpoint, api_key)
                    delete_old_files(logger, data_folder)
                    parse_data_generate_charts()
                else:
                    print('Most recent file is within the last minute, skipping API call')
                
                # Wait for one minute before checking again
                time.sleep(60)
    except KeyboardInterrupt:
        logger.error("Program interrupted.")
    finally:
        logger.info("Exiting the program...")
        
if __name__ == "__main__":
    main()