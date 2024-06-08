import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from data_puller.update_data import send_email
        

def run():              
    subject = f"Test mail from my Gmail via python"
    plain_body = f"We'll see if I can send a message from GMail"
    html_body = f"""
    <html>
    <body>
        <h2>Testing</h2>
        <p>Testing 1 2 3 . . .</p>
    </body>
    </html>
    """

    send_email(subject, plain_body, html_body)
    print("Called send_email")