import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

class EmailHandler:
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        """Initialize EmailHandler with SMTP server details"""
        # Load environment variables from .env file
        env_path = Path(__file__).resolve().parents[2] / '.env'
        load_dotenv(env_path)
        
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        
        if not self.sender_email or not self.sender_password:
            logging.warning("Email credentials not found in environment variables")
    
    def send_password_recovery_email(self, recipient_email: str, username: str, password: str) -> bool:
        """
        Send password recovery email to the user
        
        Args:
            recipient_email (str): User's email address
            username (str): User's username
            password (str): User's password
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = "Password Recovery - AI Agency"
            
            # Create HTML email body with credentials
            html = f"""
            <html>
                <head>
                    <style>
                        .logo {{
                            font-family: Arial, sans-serif;
                            font-size: 48px;
                            font-weight: bold;
                            display: inline-block;
                        }}
                        .red {{ color: #FF0000; }}
                        .blue {{ color: #0000FF; }}
                        body {{
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            color: #333333;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                        }}
                        .container {{
                            background-color: #ffffff;
                            border-radius: 5px;
                            padding: 20px;
                            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        }}
                        .credentials {{
                            background-color: #f8f9fa;
                            border: 1px solid #dee2e6;
                            border-radius: 4px;
                            padding: 15px;
                            margin: 20px 0;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="logo">
                            <span class="red">A</span><span class="blue">i</span>
                        </div>
                        <h2>Account Recovery</h2>
                        <p>Hello {username},</p>
                        <p>You recently requested to recover your AI Agency account.</p>
                        
                        <div class="credentials">
                            <p><strong>Your account credentials:</strong></p>
                            <p>Username: {username}</p>
                            <p>Your new generated Password: {password}</p>
                        </div>
                        
                        <p>For security reasons, we strongly recommend changing your password after logging in.</p>
                        <p>Best regards,<br>AI Agency Developer Team</p>
                        <p>btw it is me, Rudi:D</p>
                    </div>
                </body>
            </html>
            """
            
            # Create plain text version as fallback
            text = f"""
            Hello {username},
            
            You recently requested to recover your AI Agency account.
            
            Your account credentials:
            Username: {username}
            Temporary Password: {password}
            
            For security reasons, we strongly recommend changing your password after logging in.
            
            Best regards,
            AI Agency Team
            """
            
            message.attach(MIMEText(text, "plain"))
            message.attach(MIMEText(html, "html"))
            
            # Create SMTP session
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logging.info(f"Password recovery email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send password recovery email: {str(e)}")
            return False
    
    def send_test_email(self, recipient_email: str) -> bool:
        """
        Send a test email to verify the configuration
        
        Args:
            recipient_email (str): Email address to send the test to
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = "Test Email - AI Agency"
            
            html = """
            <html>
                <head>
                    <style>
                        .logo {
                            font-family: Arial, sans-serif;
                            font-size: 48px;
                            font-weight: bold;
                            display: inline-block;
                        }
                        .red { color: #FF0000; }
                        .blue { color: #0000FF; }
                        body {
                            font-family: Arial, sans-serif;
                            line-height: 1.6;
                            color: #333333;
                        }
                    </style>
                </head>
                <body>
                    <div class="logo">
                        <span class="red">A</span><span class="blue">i</span>
                    </div>
                    <h2>Test Email</h2>
                    <p>This is a test email to verify your email configuration is working correctly.</p>
                    <p>If you received this email, your email settings are configured properly!</p>
                </body>
            </html>
            """
            
            text = """
            Test Email
            
            This is a test email to verify your email configuration is working correctly.
            If you received this email, your email settings are configured properly!
            """
            
            message.attach(MIMEText(text, "plain"))
            message.attach(MIMEText(html, "html"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logging.info(f"Test email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send test email: {str(e)}")
            return False
    
    def verify_email_exists(self, email: str, username: str) -> bool:
        """
        Verify if the provided email matches the username in the database
        
        Args:
            email (str): Email to verify
            username (str): Username to match against
            
        Returns:
            bool: True if email matches username, False otherwise
        """
        try:
            # Get user profile from server
            from login_server.login_client import LoginClient
            client = LoginClient()
            
            # Use the verify-email endpoint to check if email matches username
            response, status_code = client._make_request('POST', '/verify-email',
                                                     json={"username": username, "email": email})
            
            if status_code == 200:
                return response.get('valid', False)
            
            return False
            
        except Exception as e:
            logging.error(f"Failed to verify email: {str(e)}")
            return False