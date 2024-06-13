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
from shared import load_secrets

# Function to send email notifications
def send_email(subject, plain_body, html_body):
    secrets = load_secrets()
    smtp_server = secrets['smtp-server']
    smtp_port = secrets['smtp-port']
    smtp_user = secrets['smtp-user']
    smtp_password = secrets['smtp-password']
    smtp_use_ssl = secrets['smtp-use-ssl']
    smtp_use_tls = secrets['smtp-use-tls']
    to_emails = secrets["email-notifications"]

    if not isinstance(to_emails, list) or not to_emails:
        print("No valid email addresses found to send emails to.")
        return
    
    try:
        if smtp_server and smtp_port and smtp_user and smtp_password and to_emails:
            with (smtplib.SMTP_SSL(smtp_server, smtp_port) if smtp_use_ssl else smtplib.SMTP(smtp_server, smtp_port)) as server:
                server.login(smtp_user, smtp_password)
                
                if not smtp_use_ssl and smtp_use_tls:
                    server.starttls()

                for email in to_emails:
                    msg = MIMEText(plain_body, 'plain')
                    msg['Subject'] = subject
                    msg['From'] = smtp_user
                    msg['To'] = email
                    msg['Reply-To'] = smtp_user
                    msg['X-Mailer'] = 'Python smtplib'
                    try:
                        server.sendmail(smtp_user, email, msg.as_string())
                    except smtplib.SMTPDataError as e:
                        print(f"Failed to send email to {email}: {e}")
                    except smtplib.SMTPRecipientsRefused as e:
                        print(f"Recipient refused for {email}: {e}")
                    except smtplib.SMTPException as e:
                        print(f"SMTP error occurred for {email}: {e}")
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")

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
def call_api_and_save(logger, data_folder, api_endpoint, api_key):
    request_url = f'{api_endpoint}{api_key}'
    response = requests.get(request_url)
    if response.status_code == 200:
        data = response.json()
        filename = datetime.now().strftime('%Y-%m-%d_%H.%M.%S') + '.json'
        filepath = os.path.join(data_folder, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f)
        logger.info(f'Saved JSON data to {filepath}')
        process_workers(data, logger, data_folder)
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

def process_workers(data, logger, data_folder):
    summary_file = os.path.join(data_folder, 'workers_summary.json')
    
    if os.path.exists(summary_file):
        with open(summary_file, 'r') as f:
            summary_data = json.load(f)
    else:
        summary_data = {}

    workers = data.get('workers', {})
    for worker, details in workers.items():
        if worker not in summary_data:
            summary_data[worker] = {'connected': details['connected'], 'hash_rate': details['hash_rate'], 'disconnected_since': None}
        summary_data[worker]['hash_rate'] = details['hash_rate']
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
                send_email(subject, plain_body, html_body)
        elif details['hash_rate'] == 0:
            if summary_data[worker]['disconnected_since'] is None:
                summary_data[worker]['disconnected_since'] = datetime.now().isoformat()
                subject = f"Worker {worker} :: 0 Hash Rate"
                plain_body = f"Worker {worker} has 0 hash rate at {summary_data[worker]['disconnected_since']}."
                html_body = f"""
                <html>
                <body>
                    <h2>Worker {worker} has 0 Hash Rate</h2>
                    <p>Worker {worker} has 0 hash rate at {summary_data[worker]['disconnected_since']}.</p>
                </body>
                </html>
                """
                send_email(subject, plain_body, html_body)
        else:
            summary_data[worker]['disconnected_since'] = None
        summary_data[worker]["connected"] = details["connected"]
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f)
def _windows_enable_ANSI(std_id):
    """Enable Windows 10 cmd.exe ANSI VT Virtual Terminal Processing."""
    from ctypes import byref, POINTER, windll, WINFUNCTYPE
    from ctypes.wintypes import BOOL, DWORD, HANDLE

    GetStdHandle = WINFUNCTYPE(
        HANDLE,
        DWORD)(('GetStdHandle', windll.kernel32))

    GetFileType = WINFUNCTYPE(
        DWORD,
        HANDLE)(('GetFileType', windll.kernel32))

    GetConsoleMode = WINFUNCTYPE(
        BOOL,
        HANDLE,
        POINTER(DWORD))(('GetConsoleMode', windll.kernel32))

    SetConsoleMode = WINFUNCTYPE(
        BOOL,
        HANDLE,
        DWORD)(('SetConsoleMode', windll.kernel32))

    if std_id == 1:       # stdout
        h = GetStdHandle(-11)
    elif std_id == 2:     # stderr
        h = GetStdHandle(-12)
    else:
        return False

    if h is None or h == HANDLE(-1):
        return False

    FILE_TYPE_CHAR = 0x0002
    if (GetFileType(h) & 3) != FILE_TYPE_CHAR:
        return False

    mode = DWORD()
    if not GetConsoleMode(h, byref(mode)):
        return False

    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    if (mode.value & ENABLE_VIRTUAL_TERMINAL_PROCESSING) == 0:
        SetConsoleMode(h, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
    return True
    
def main():
    logger = logging.get_logger(loglevel=baselogging.DEBUG, loggername=__name__)
    
    app_path = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(app_path, '..', 'data')
    try:
        _windows_enable_ANSI(1)
        _windows_enable_ANSI(2)
    except Exception:
        print("Failed to enable ANSI")
    try:
        secrets = load_secrets()
        
        api_endpoint = secrets.get('api-endpoint')
        api_key = secrets.get('api-key')

        if api_key and api_endpoint:
            logger.info("Got API Key from secrets.json")
            while True:
                most_recent_file, most_recent_datetime = get_most_recent_file(data_folder)
                if most_recent_datetime is None or datetime.now() - most_recent_datetime > timedelta(minutes=1):
                    try:
                        logger.info("API Data out of date, retrieving updated JSON")
                        call_api_and_save(logger, data_folder, api_endpoint, api_key)
                        delete_old_files(logger, data_folder)
                        parse_data_generate_charts()
                    except Exception as e:
                        logger.error(f"Exception: {str(e)}")
                else:
                    print('Most recent file is within the last minute, skipping API call')
                time.sleep(60)
    except KeyboardInterrupt:
        logger.error("Program interrupted.")
    finally:
        logger.info("Exiting the program...")

if __name__ == "__main__":
    main()