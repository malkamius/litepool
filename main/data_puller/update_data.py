import pandas as pd
import os
import requests
import json
from datetime import datetime, timedelta
import time
import logging as baselogging
from shared.mylogging import logging
from .generate_charts import parse_data_generate_charts
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Function to load secrets from the secrets.json file
def load_secrets():
    app_path = os.path.dirname(os.path.abspath(__file__))
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

# Function to send email notifications
def send_email(subject, plain_body, html_body, to_emails):
    secrets = load_secrets()
    smtp_server = secrets['smtp-server']
    smtp_port = secrets['smtp-port']
    smtp_user = secrets['smtp-user']
    smtp_password = secrets['smtp-password']
    if smtp_server:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = ", ".join(to_emails)

        part1 = MIMEText(plain_body, 'plain')
        part2 = MIMEText(html_body, 'html')

        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            #server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_emails, msg.as_string())

# Function to check the most recent file and its timestamp
def get_most_recent_file(data_folder):
    date_files = []
    for file in os.listdir(data_folder):
        try:
            file_datetime = datetime.strptime(file, '%Y-%m-%d_%H.%M.%S')
            date_files.append((file, file_datetime))
        except ValueError:
            continue
    if date_files:
        return max(date_files, key=lambda x: x[1])
    return None, None

# Function to call the API and save the JSON output
def call_api_and_save(logger, data_folder, api_endpoint, api_key, email_notifications):
    request_url = f'{api_endpoint}{api_key}'
    response = requests.get(request_url)
    if response.status_code == 200:
        data = response.json()
        filename = datetime.now().strftime('%Y-%m-%d_%H.%M.%S') + '.json'
        filepath = os.path.join(data_folder, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f)
        logger.info(f'Saved JSON data to {filepath}')
        process_workers(data, logger, data_folder, email_notifications)
        return data
    else:
        logger.error(f'Failed to retrieve data from the API, status code: {response.status_code}')
        return None

# Function to get all JSON files with datetime names and their modification times
def get_json_files(data_folder):
    date_files = []
    for file in os.listdir(data_folder):
        if file.endswith('.json'):
            try:
                file_datetime = datetime.strptime(file, '%Y-%m-%d_%H.%M.%S.json')
                date_files.append((file, file_datetime))
            except ValueError:
                continue
    return date_files

# Function to keep only the most recent files for the last 24 hours
def delete_old_files(logger, data_folder):
    date_files = get_json_files(data_folder)
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    
    recent_files = [file for file, file_datetime in date_files if file_datetime > cutoff]
    
    recent_files.sort(key=lambda x: x[1], reverse=True)
    
    for file, file_datetime in date_files:
        if file_datetime <= cutoff:
            os.remove(os.path.join(data_folder, file))
            logger.info(f"Deleted old file: {file}")

def process_workers(data, logger, data_folder, email_notifications):
    summary_file = os.path.join(data_folder, 'workers_summary.json')
    
    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
    else:
        summary_data = {}

    workers = data.get('workers', {})
    for worker, details in workers.items():
        if worker not in summary_data:
            summary_data[worker] = {'connected': details['connected'], 'disconnected_since': None}
        
        if not details['connected']:
            if summary_data[worker]['disconnected_since'] is None:
                summary_data[worker]['disconnected_since'] = datetime.now().isoformat()
                subject = f"Worker {worker} Disconnected"
                plain_body = f"Worker {worker} has disconnected at {summary_data[worker]['disconnected_since']}."
                html_body = f"""
                <html>
                <body>
                    <h2>Worker {worker} Disconnected</h2>
                    <p>Worker {worker} has disconnected at {summary_data[worker]['disconnected_since']}.</p>
                </body>
                </html>
                """
                send_email(subject, plain_body, html_body, email_notifications)
        else:
            summary_data[worker]['disconnected_since'] = None

    with open(summary_file, 'w') as f:
        json.dump(summary_data, f)

def main():
    logger = logging.get_logger(loglevel=baselogging.DEBUG, loggername=__name__)
    
    app_path = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(app_path, '../data')

    try:
        secrets = load_secrets()
        
        api_endpoint = secrets.get('api-endpoint')
        api_key = secrets.get('api-key')
        email_notifications = secrets.get('email-notifications')

        if api_key and api_endpoint:
            logger.info("Got API Key from secrets.json")
            while True:
                most_recent_file, most_recent_datetime = get_most_recent_file(data_folder)
                if most_recent_datetime is None or datetime.now() - most_recent_datetime > timedelta(minutes=1):
                    logger.info("API Data out of date, retrieving updated JSON")
                    call_api_and_save(logger, data_folder, api_endpoint, api_key, email_notifications)
                    delete_old_files(logger, data_folder)
                    parse_data_generate_charts()
                else:
                    print('Most recent file is within the last minute, skipping API call')
                time.sleep(60)
    except KeyboardInterrupt:
        logger.error("Program interrupted.")
    finally:
        logger.info("Exiting the program...")

if __name__ == "__main__":
    main()