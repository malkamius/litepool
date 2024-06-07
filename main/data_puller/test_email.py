import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

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
        
def send_email(subject, plain_body, html_body):
    secrets = load_secrets()
    smtp_server = secrets['smtp-server']
    smtp_port = secrets['smtp-port']
    smtp_user = secrets['smtp-user']
    smtp_password = secrets['smtp-password']
    to_emails = secrets.get('email-notifications')
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
            
subject = f"Test Email"
plain_body = f"Test Email"
html_body = f"""
<html>
<body>
    <h2>Testing</h2>
    <p>Testing 1 2 3 . . .</p>
</body>
</html>
"""

send_email(subject, plain_body, html_body)