import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

def send_otp_email(recipient_email, otp):
    """Sends an OTP to the specified email address."""
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", 587)
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # On platforms like Render, env vars might not be set for free tiers.
    # This provides a fallback for demonstration purposes by logging the OTP.
    if not all([smtp_server, smtp_port, smtp_user, smtp_password]):
        logging.warning("SMTP environment variables not set. Cannot send real email.")
        logging.warning(f"DEMO MODE: OTP for {recipient_email} is {otp}")
        return True # Pretend it was sent successfully

    sender_email = smtp_user
    
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Your Verification Code for ADHD AI Coach is {otp}"
    message["From"] = sender_email
    message["To"] = recipient_email

    text = f"Hi,\n\nYour One-Time Password (OTP) is: {otp}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this, please ignore this email.\n\nThanks,\nThe ADHD AI Coach Team"
    html = f"""
    <html>
      <body style="font-family: sans-serif;">
        <p>Hi,</p>
        <p>Your One-Time Password (OTP) for the ADHD AI Coach is:</p>
        <p style="font-size: 24px; font-weight: bold; letter-spacing: 2px;">{otp}</p>
        <p>This code will expire in 10 minutes.</p>
        <p>If you did not request this, please ignore this email.</p>
        <p>Thanks,<br>The ADHD AI Coach Team</p>
      </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    try:
        with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        logging.info(f"OTP email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {recipient_email}: {e}")
        return False