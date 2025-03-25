import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Optional, Tuple

class EmailService:
    _instance = None
    GMAIL_SMTP_SERVER = "smtp.gmail.com"
    GMAIL_SMTP_PORT = 587

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmailService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize email configuration"""
        self.smtp_server = os.getenv("SMTP_SERVER", self.GMAIL_SMTP_SERVER)
        self.smtp_port = int(os.getenv("SMTP_PORT", self.GMAIL_SMTP_PORT))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")

        if not all([self.smtp_username, self.smtp_password]):
            raise ValueError("Email configuration is incomplete. Please check your environment variables.")

    def _validate_gmail_config(self) -> Tuple[bool, Optional[str]]:
        """Validate Gmail-specific configuration"""
        if not self.smtp_username or not self.smtp_password:
            return False, "Email credentials not configured. Check console for setup instructions."
        
        if self.smtp_server == self.GMAIL_SMTP_SERVER:
            if not self.smtp_username.endswith('@gmail.com'):
                return False, "When using Gmail, SMTP_USERNAME must be a Gmail address"
            
            if len(self.smtp_password) != 16:
                return False, "When using Gmail, SMTP_PASSWORD should be a 16-character App Password"
        
        return True, None

    def send_email(self, to_email: str, subject: str, body: str, is_html: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Send an email
        Returns: (success, error_message)
        """
        try:
            # Validate configuration
            is_valid, error = self._validate_gmail_config()
            if not is_valid:
                return False, error

            msg = MIMEMultipart()
            msg["From"] = self.smtp_username
            msg["To"] = to_email
            msg["Subject"] = subject

            # Add body with appropriate content type
            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, content_type))

            # Create SMTP connection
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                try:
                    server.login(self.smtp_username, self.smtp_password)
                except smtplib.SMTPAuthenticationError:
                    if self.smtp_server == self.GMAIL_SMTP_SERVER:
                        return False, ("Gmail authentication failed. Make sure you're using an App Password, "
                                     "not your regular Gmail password. Check console for setup instructions.")
                    return False, "SMTP authentication failed"
                
                server.send_message(msg)

            return True, None

        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, str(e) 